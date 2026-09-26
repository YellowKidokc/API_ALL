"""Framework for native (engine-built) stations.

A station script is small: it declares its stages and hands one function per item to
Station.run(). The framework provides, identically for every station:
  * the standard flags (items, --limit, --workers, --provider, --model, --focus, --redo,
    --dry-run, --channel) plus any extra flags the station adds;
  * item discovery (papers, videos or both) and parallel processing, many items at once,
    with every API call passing through the one global limiter (engine/llm.py, gateway);
  * three-level focus appended to every prompt, with its text and hash in the receipt;
  * stage cache: a finished stage is reused when source hash + prompt hash + model + focus
    hash are unchanged, so a rerun only pays for what changed (--redo ignores it);
  * the dated output bundle (json / xlsx / html / run.json) and paper.json bookkeeping;
  * a live progress line and a non-zero exit code when any item fails.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import llm
from .focus import append, compose
from .goals import goal_id
from .items import Item, discover
from .output import dated_run_dir, write_bundle
from .paths import API_HOME, PathConfigurationError, configured, external
from .progress import Progress


def station_meta(label: str) -> dict:
    return json.loads((API_HOME / "stations" / label / "station.json").read_text(encoding="utf-8"))


def prompt_hash(station_dir: Path, files: list[str]) -> str:
    """Hash of every prompt/rubric/lexicon file the station sends, so editing one re-runs it."""
    h = hashlib.sha256()
    for name in sorted(set(files) | {"PROMPT.md"}):
        for path in sorted(station_dir.glob(name)) if any(c in name for c in "*?") else [station_dir / name]:
            if path.is_file():
                h.update(path.name.encode())
                h.update(path.read_bytes())
    return h.hexdigest()[:16]


@dataclass
class ItemResult:
    data: Any
    html: str
    sheets: dict[str, list[dict]] | None = None
    markdown: str | None = None
    headline: dict[str, Any] = field(default_factory=dict)


class Context:
    """Everything one item's processing needs; collects receipts for its calls."""

    def __init__(self, station: "Station", item: Item | None):
        self.station = station
        self.item = item
        self.args = station.args
        self.receipts: list[dict] = []
        self.calls: list[dict] = []   # every reply, saved as calls/<goal id>-<n>.json
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.lock = threading.Lock()
        channel_focus = None
        if item is not None and item.kind == "video" and configured("yt_focus"):
            candidate = external("yt_focus") / f"{item.meta.get('channel', '')}.json"
            channel_focus = candidate if candidate.exists() else None
        self.focus_text, self.focus_hash = compose(station.dir, item.folder if item else None,
                                                   station.args.focus, channel_focus)
        self._text: str | None = None
        self.cache_root: Path | None = None   # topic-level stations cache here instead of an item folder
        self.steps: list[str] = []   # everything this item did, saved as steps.log

    def step(self, message: str) -> None:
        """Show one step of the work, live, and keep it for steps.log."""
        stamp = datetime.now().strftime("%H:%M:%S")
        who = self.item.id if self.item else getattr(self, "who", self.station.label)
        line = f"{stamp} [{self.station.label[:2]}] {who[:18]:<18} {message}"
        with self.lock:
            self.steps.append(line)
        self.station.say(line)

    # ----------------------------------------------------------------- text
    @property
    def text(self) -> str:
        if self._text is None:
            self._text = self.item.text() if self.item else ""
        return self._text

    # ----------------------------------------------------------------- calls
    def prompt(self, body: str, focus: bool = True) -> str:
        return append(body, self.focus_text) if focus else body

    def call_json(self, task: str, prompt: str, *, focus: bool = True, system: str | None = None,
                  temperature: float | None = None, max_tokens: int | None = None) -> Any:
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": self.prompt(prompt, focus)}]
        self.step(f"-> {goal_id(self.station.label, task)} {task}: sending {len(messages[-1]['content']):,} chars")
        data, result = llm.call_json(messages, provider=self.args.provider, model=self.args.model, task=task,
                                     station=self.station.label, temperature=temperature,
                                     max_tokens=max_tokens or self.station.settings.get("output_token_cap"))
        self._record(task, result, data)
        return data

    def call_text(self, task: str, prompt: str, *, focus: bool = True, system: str | None = None,
                  temperature: float | None = None, max_tokens: int | None = None) -> str | None:
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": self.prompt(prompt, focus)}]
        self.step(f"-> {goal_id(self.station.label, task)} {task}: sending {len(messages[-1]['content']):,} chars")
        result = llm.call(messages, provider=self.args.provider, model=self.args.model, task=task,
                          station=self.station.label, temperature=temperature,
                          max_tokens=max_tokens or self.station.settings.get("output_token_cap"))
        self._record(task, result, {"text": result.text} if result.ok else None)
        return result.text if result.ok else None

    def _record(self, task: str, result: llm.LLMResult, reply: Any = None) -> None:
        gid = goal_id(self.station.label, task)
        fallback = result.extra.get("fallback_failures")
        if fallback:
            self.step(f"   fallback: {', '.join(f['provider'] + ' failed' for f in fallback)}; answered by {result.provider}:{result.model}")
        if result.ok:
            self.step(f"<- {gid} {task}: ok · {result.tokens:,} tokens · {result.elapsed_seconds:.1f}s · {result.provider}:{result.model}")
        else:
            self.step(f"<- {gid} {task}: FAILED · {result.error}")
        with self.lock:
            receipt = llm.receipt(result, task=task, goal_id=gid)
            self.receipts.append(receipt)
            self.calls.append({"goal_id": gid, "task": task, "ok": result.ok, "error": result.error,
                               "provider": result.provider, "model": result.model, "tokens": result.tokens,
                               "reply": reply})
            if not result.ok:
                self.errors.append(f"{task}: {result.error}")
        self.station.progress.add_tokens(result.tokens)

    def parallel(self, fn: Callable[[Any], Any], jobs: list[Any], width: int = 8) -> list[Any]:
        """Run independent calls side by side. The global limiter bounds the real concurrency."""
        if len(jobs) <= 1:
            return [fn(j) for j in jobs]
        with ThreadPoolExecutor(max_workers=min(width, len(jobs))) as pool:
            return list(pool.map(fn, jobs))

    # ----------------------------------------------------------------- cache
    def cache_key(self, stage: str, extra: str = "") -> str:
        parts = [stage, self.item.source_hash if self.item else "", self.station.prompt_version,
                 self.args.provider, self.args.model, self.focus_hash, extra]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:20]

    def cached(self, stage: str, compute: Callable[[], Any], extra: str = "", api: bool = True) -> Any:
        """Reuse a finished stage (same source, prompts, model, focus). Only error-free results are cached."""
        folder = self.cache_root or ((self.item.folder if self.item else self.station.dir / "_work") / "02_RUNS" / self.station.label / "_cache")
        path = folder / f"{stage}-{self.cache_key(stage, extra) if api else hashlib.sha256((stage + extra + (self.item.source_hash if self.item else '')).encode()).hexdigest()[:20]}.json"
        if path.exists() and not self.args.redo:
            self.step(f"stage '{stage}': reused finished result ({path.name})")
            return json.loads(path.read_text(encoding="utf-8"))
        self.step(f"stage '{stage}': start")
        before = len(self.errors)
        value = compute()
        self.step(f"stage '{stage}': {'done' if len(self.errors) == before else 'had errors'}")
        if len(self.errors) == before and value is not None:
            folder.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return value


class Station:
    def __init__(self, label: str, *, kind: str | None = None, extra_args: Callable[[argparse.ArgumentParser], None] | None = None,
                 prompt_files: list[str] | None = None, per_item: bool = True, depends_on: list[str] | None = None):
        self.label = label
        self.dir = API_HOME / "stations" / label
        self.meta = station_meta(label)
        self.kind = kind or self.meta.get("items", "papers")
        self.settings = llm.settings()
        self.per_item = per_item
        self.depends_on = depends_on or []
        parser = argparse.ArgumentParser(prog=f"{label}", description=self.meta.get("description", ""))
        parser.add_argument("items", nargs="*", help="item folders, transcripts, channel folders (default: all)")
        parser.add_argument("--limit", type=int, help="how many items")
        parser.add_argument("--workers", type=int, default=self.settings["max_concurrent_calls"], help="concurrent calls")
        parser.add_argument("--provider", default=self.settings["default_provider"])
        parser.add_argument("--model", default=None)
        parser.add_argument("--focus", action="append", default=[], help="extra focus (repeatable)")
        parser.add_argument("--redo", action="store_true", help="ignore finished work and run again")
        parser.add_argument("--dry-run", action="store_true", help="show what would run, call nothing")
        parser.add_argument("--channel", help="YouTube channel folder name")
        if extra_args:
            extra_args(parser)
        self.args = parser.parse_args()
        self.args.model = self.args.model or self.settings["models"].get(self.args.provider) or llm.PROVIDERS.get(self.args.provider, {}).get("default_model", "")
        self.prompt_version = prompt_hash(self.dir, (prompt_files or []) + self.meta.get("prompt_files", []))
        llm.configure(self.args.workers)
        self.progress = Progress(0, label)
        self._print_lock = threading.Lock()

    # --------------------------------------------------------------------------
    def say(self, line: str) -> None:
        with self._print_lock:
            if sys.stderr.isatty():
                sys.stderr.write("\r" + " " * 160 + "\r")
            print(line, flush=True)

    def items(self) -> list[Item]:
        return discover(self.args.items, self.kind, self.args.limit, self.args.channel)

    def run(self, process: Callable[[Context], ItemResult | None], items: list[Item] | None = None) -> int:
        try:
            items = self.items() if items is None else items
        except (PathConfigurationError, FileNotFoundError) as exc:
            print(f"{self.label}: {exc}", file=sys.stderr)
            return 2
        if not items:
            print(f"{self.label}: nothing to do (no items found)")
            return 0
        print(f"{self.label}: {len(items)} item(s) · provider {self.args.provider} · model {self.args.model} · "
              f"prompt version {self.prompt_version} · workers {self.args.workers}")
        if self.args.dry_run:
            for item in items:
                print(f"  would run {item.label()}  ({item.folder})")
            return 0
        self.progress = Progress(len(items), self.label)
        failures = 0
        lock = threading.Lock()

        def one(item: Item) -> None:
            nonlocal failures
            self.progress.start()
            ok = self._run_item(item, process)
            if not ok:
                with lock:
                    failures += 1
            self.progress.finish(ok)

        width = max(1, min(self.args.workers, len(items)))
        with ThreadPoolExecutor(max_workers=width) as pool:
            list(pool.map(one, items))
        self.progress.close()
        if failures:
            print(f"{self.label}: {failures} of {len(items)} item(s) failed; see their .run.json receipts", file=sys.stderr)
        return 1 if failures else 0

    def upstream(self, item: Item) -> dict[str, str]:
        """The runs this station builds on; a newer upstream run makes this item due again."""
        out = {}
        for label in self.depends_on:
            run = latest_run(item, label)
            out[label] = run.name if run else ""
        return out

    def _run_item(self, item: Item, process: Callable[[Context], ItemResult | None]) -> bool:
        ctx = Context(self, item)
        started = time.monotonic()
        ctx.step(f"start: {item.title[:60]}  ({item.folder.name})")
        if ctx.focus_text:
            ctx.step(f"focus added to every prompt: {ctx.focus_hash[:10]} ({ctx.focus_text.count(chr(10) + '- ')} point(s))")
        if not self.args.redo and self.per_item:
            prior = latest_run(item, self.label)
            if prior:
                saved = json.loads((prior / f"{self.label}.run.json").read_text(encoding="utf-8"))
                same = (saved.get("source_hash"), saved.get("prompt_version"), saved.get("model"), saved.get("focus_hash"),
                        saved.get("depends", {})) == \
                       (item.source_hash, self.prompt_version, self.args.model, ctx.focus_hash, self.upstream(item))
                if same:
                    print(f"  SKIP {item.label()} already done -> {prior}  (use --redo to run again)")
                    return True
        result = None
        try:
            result = process(ctx)
        except Exception as exc:  # isolate: one bad item never stops the batch
            ctx.errors.append(f"{type(exc).__name__}: {exc}")
            traceback.print_exc()
        if result is None and not ctx.errors:
            return True  # skipped deliberately (e.g. gate not met)
        return self.write(ctx, result, started)

    def write(self, ctx: Context, result: ItemResult | None, started: float, folder: Path | None = None) -> bool:
        item = ctx.item
        receipt = {
            "station": self.label, "item": item.id if item else None, "kind": item.kind if item else None,
            "source_hash": item.source_hash if item else None, "provider": self.args.provider, "model": self.args.model,
            "prompt_version": self.prompt_version, "focus_text": ctx.focus_text, "focus_hash": ctx.focus_hash,
            "tokens": sum(r.get("tokens", 0) for r in ctx.receipts),
            "time_seconds": round(time.monotonic() - started, 2), "errors": ctx.errors, "warnings": ctx.warnings,
            "depends": self.upstream(item) if item else {},
            "calls": ctx.receipts, "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        folder = folder or (item.folder if item else self.dir / "_work")
        out = dated_run_dir(folder, self.label)
        if result is None:
            result = ItemResult({"errors": ctx.errors}, "<p>This run failed; see the receipt.</p>")
        write_bundle(out, self.label, result.data, result.html, receipt, result.sheets)
        if result.markdown:
            (out / f"{self.label}.md").write_text(result.markdown, encoding="utf-8")
        if ctx.calls:
            calls_dir = out / "calls"
            calls_dir.mkdir(exist_ok=True)
            counters: dict[str, int] = {}
            for call in ctx.calls:
                counters[call["goal_id"]] = counters.get(call["goal_id"], 0) + 1
                name = f"{call['goal_id']}-{counters[call['goal_id']]:03d}.json"
                (calls_dir / name).write_text(json.dumps(call, indent=2, ensure_ascii=False), encoding="utf-8")
        ctx.step(f"saved -> {out}")
        (out / "steps.log").write_text("\n".join(ctx.steps) + "\n", encoding="utf-8")
        if item:
            meta = item.meta
            meta.setdefault("stations_run", []).append({"station": self.label, "run": str(out.relative_to(item.folder)),
                                                        "ok": not ctx.errors, "at": receipt["finished_at"]})
            if result.headline:
                meta.setdefault("headline_scores", {}).update(result.headline)
            item.save_meta(meta)
        self.last_out = out
        print(f"  {'OK ' if not ctx.errors else 'ERR'} {item.label() if item else self.label} -> {out}")
        return not ctx.errors


def latest_run(item: Item, label: str) -> Path | None:
    folder = item.folder / "02_RUNS" / label
    if not folder.is_dir():
        return None
    for run in sorted((p for p in folder.iterdir() if p.is_dir() and not p.name.startswith("_")), reverse=True):
        receipt = run / f"{label}.run.json"
        if receipt.exists() and not json.loads(receipt.read_text(encoding="utf-8")).get("errors"):
            return run
    return None


def latest_data(item: Item, label: str) -> Any:
    run = latest_run(item, label)
    return json.loads((run / f"{label}.json").read_text(encoding="utf-8")) if run else None
