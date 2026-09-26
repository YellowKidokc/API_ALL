"""ONE_MENU: the single front door. ONE_MENU.bat runs this file.

  1  What to run?   one number, several ("8 9 44"), or a routine letter ("Y"). Enter = repeat last run.
  2  Options        only the options the chosen stations really accept (turbo, how many, provider, redo, topic ...)
  3  Anything else? type what you want the AI to look at, one per line (or a saved focus number); blank = done
  4  Confirm        the exact plan (stations, items, focus, tokens, time), then it runs

No questions when arguments are given:
  ONE_MENU.bat 30 --limit 1 --focus "entropy"
  ONE_MENU.bat Y --channel "Daily Dose Of Wisdom" --turbo 3
  ONE_MENU.bat 48 --topic resurrection
  ONE_MENU.bat find resurrection --min 5        tagger search
  ONE_MENU.bat goals                            list every API goal id
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import focus as focus_lib  # noqa: E402
from engine.gateway import Gateway, summary_line  # noqa: E402
from engine.paths import API_HOME, ensure_runtime_dirs  # noqa: E402

FAMILIES = [("01", "19", "YouTube"), ("20", "29", "CKG"), ("30", "39", "Evidence"), ("40", "49", "Papers + bridge layer"),
            ("50", "59", "Lean + axioms"), ("60", "89", "Prompt stations"), ("90", "99", "Tools")]
ASKABLE = ["limit", "turbo", "provider", "redo", "channel", "topic"]


def load(name: str):
    return json.loads((API_HOME / "config" / name).read_text(encoding="utf-8"))


def registry() -> dict[str, dict]:
    reg = {}
    for row in load("stations.json"):
        if row.get("retired"):
            continue
        meta = json.loads((API_HOME / row["folder"] / "station.json").read_text(encoding="utf-8"))
        reg[row["number"]] = {**meta, **row}
    return reg


def usage_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for log in (API_HOME / "LOGS").glob("run-*.json"):
        try:
            for label in json.loads(log.read_text(encoding="utf-8")).get("stations", []):
                counts[label[:2]] = counts.get(label[:2], 0) + 1
        except (ValueError, OSError):
            continue
    return counts


def display(show_all: bool = True) -> None:
    reg = registry()
    rows = sorted(reg.values(), key=lambda x: x["number"])
    routines = load("routines.json")
    top = load("top20.json").get("top", [])[:20]
    print("\n  ONE_MENU\n")
    print("  Top 20 (your favourites, config/top20.json)")
    if not top:
        print("   (empty: add the numbers or routine letters you use most)")
    for entry in top:
        if entry.upper() in routines:
            r = routines[entry.upper()]
            print(f"   {entry.upper():>2}  {r['name']:<28}  {' '.join(r['stations'])}")
        elif entry.zfill(2) in reg:
            print(f"   {entry.zfill(2)}  {reg[entry.zfill(2)]['name']}")
    used = usage_counts()
    unpinned = [n for n, c in sorted(used.items(), key=lambda x: -x[1]) if n not in top and c >= 3][:5]
    if unpinned:
        print(f"   suggestion: you run {', '.join(unpinned)} often; pin them in config/top20.json")
    print()
    for lo, hi, family in FAMILIES:
        members = [r for r in rows if lo <= r["number"] <= hi]
        if not members:
            continue
        print(f"  {family}")
        for r in members:
            api = "" if r.get("uses_api") else "  (local)"
            print(f"   {r['number']}  {r['name']:<28}{api}")
        print()
    print("  Routines: " + "   ".join(f"{k} = {v['name']} ({' '.join(v['stations'])})" for k, v in routines.items()))
    print("  Also: find <tag> · goals · Enter = repeat last run")


def resolve(tokens: list[str]) -> list[str]:
    routines, reg, out = load("routines.json"), registry(), []
    for token in tokens:
        key = token.upper()
        numbers = routines[key]["stations"] if key in routines else [token.zfill(2) if token.isdigit() else token]
        for n in numbers:
            if n not in reg:
                raise SystemExit(f"Unknown station or routine: {token}")
            if n not in out:
                out.append(n)
    return out


def count_items(stations: list[dict], args: argparse.Namespace) -> tuple[int, int, str]:
    """(found, already done, description) for the first station that works on items."""
    from engine.paths import configured, external
    for station in stations:
        kind = station.get("items") or station.get("count")
        label = station["label"]
        try:
            if args.item:
                return len(args.item), 0, "items you named"
            total, done_total, parts = 0, 0, []
            if kind in ("videos", "both") and configured("yt_subtitles"):
                base = external("yt_subtitles") / args.channel if args.channel else external("yt_subtitles")
                found = [p for p in base.rglob("*.md") if "_originals" not in p.parts and not p.name.startswith("_")] if base.exists() else []
                done = 0
                if configured("yt_work"):
                    done = sum(1 for p in external("yt_work").glob(f"{args.channel or '*'}/*/02_RUNS/{label}") if p.is_dir())
                total, done_total = total + len(found), done_total + done
                parts.append(f"{len(found):,} transcripts" + (f" in {args.channel}" if args.channel else ""))
            if kind in ("papers", "both", "own") and configured("papers_root") and not (kind == "both" and args.channel):
                papers = list(external("papers_root").glob("*/paper.json"))
                if kind == "own":
                    papers = [p for p in papers if json.loads(p.read_text(encoding="utf-8")).get("own_work")]
                done = sum(1 for p in papers if (p.parent / "02_RUNS" / label).is_dir())
                total, done_total = total + len(papers), done_total + done
                parts.append(f"{len(papers):,} {'of your own ' if kind == 'own' else ''}papers")
            if parts:
                return total, done_total, " + ".join(parts)
            inbox = {"20": "ckg_root", "22": "ckg_root", "30": "evidence_root", "39": "evidence_chain_root"}.get(station["number"])
            if inbox and configured(inbox):
                files = [p for p in (external(inbox) / "INBOX").rglob("*") if p.is_file()]
                return len(files), 0, f"files waiting in {inbox}/INBOX"
        except OSError:
            continue
    return 0, 0, ""


def interrupted_run(state: Path) -> dict | None:
    if not state.exists():
        return None
    last = json.loads(state.read_text(encoding="utf-8"))
    return last if last.get("status") == "running" else None


def parse(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="One front door for every API pipeline")
    p.add_argument("selection", nargs="*")
    p.add_argument("--item", action="append", default=[], help="item: paper folder, transcript, channel folder, source file")
    p.add_argument("--turbo", help="concurrency preset (1=10, 2=30, 3=50, 4=60) or low/normal/high/max")
    p.add_argument("--workers", type=int, help="exact number of concurrent calls")
    p.add_argument("--limit", type=int)
    p.add_argument("--provider")
    p.add_argument("--model")
    p.add_argument("--redo", action="store_true")
    p.add_argument("--focus", action="append", default=[])
    p.add_argument("--channel")
    p.add_argument("--topic")
    p.add_argument("--yes", action="store_true", help="skip the confirm question")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--min", dest="minimum", type=int, default=5)
    p.add_argument("--mock", action="store_true", help="fake replies, no API (plumbing test)")
    return p.parse_args(argv)


def accepted_options(numbers: list[str]) -> set[str]:
    reg, opts = registry(), set()
    for n in numbers:
        opts |= set(reg[n].get("options", []))
    if opts & {"workers"}:
        opts.add("turbo")
    return opts


def ask(question: str, default: str = "") -> str:
    answer = input(f"  {question} ").strip()
    return answer or default


def interactive(args: argparse.Namespace, state: Path) -> None:
    unfinished = interrupted_run(state)
    if unfinished:
        print(f"\n  The last run ({' '.join(unfinished['selection'])}, started {unfinished.get('started_at', '?')[:16]}) did not finish.")
        if ask("Resume it? Finished items are skipped. [Y/n]:", "y").lower().startswith("y"):
            for key in ("selection", "limit", "turbo", "workers", "provider", "redo", "focus", "channel", "topic", "item"):
                if key in unfinished:
                    setattr(args, key, unfinished[key])
            args.resume = True
            return
    display(True)
    raw = input("\n1  What to run? ").strip()
    if not raw and state.exists():
        last = json.loads(state.read_text(encoding="utf-8"))
        print(f"   repeating: {' '.join(last['selection'])}")
        for key in ("selection", "limit", "turbo", "workers", "provider", "redo", "focus", "channel", "topic", "item"):
            if key in last:
                setattr(args, key, last[key])
        return
    args.selection = shlex.split(raw)
    stations = [registry()[n] for n in resolve(args.selection)]
    opts = accepted_options([s["number"] for s in stations])
    settings = load("settings.json")
    print("\n2  Options (Enter = default)")
    if "channel" in opts:
        args.channel = ask("Which channel folder? [all]:") or None
    if "topic" in opts:
        args.topic = ask("Topic (e.g. resurrection):") or None
    found, done, where = count_items(stations, args)
    if found:
        extra = f", {done} already done (skipped unless you redo)" if done else ""
        print(f"   Found {where}{extra}.")
    if "limit" in opts:
        amount = ask("Run them all, or how many? [all]:")
        args.limit = int(amount) if amount.isdigit() else None
    if "turbo" in opts:
        default = settings["max_concurrent_calls"]
        answer = ask(f"How many in parallel? [{default}] (10, 30, 50, 60 ...):", str(default))
        args.workers = int(answer) if answer.isdigit() else default
    if "provider" in opts:
        from engine.llm import PROVIDERS
        names = [n for n in PROVIDERS] + ["mock"]
        while True:
            answer = ask(f"Provider [{settings['default_provider']}] ({', '.join(names)}):", settings["default_provider"]).lower()
            if answer in names:
                args.provider = answer
                break
            print(f"   '{answer}' is not a provider I know; pick one of the list.")
    if "redo" in opts:
        args.redo = ask("Redo items already finished? [N]:", "n").lower().startswith("y")


def anything_else(args: argparse.Namespace, stations: list[dict]) -> None:
    """Asked on every run, after the plan: David's extra requests go to every station that can take them."""
    library = focus_lib.library()
    takes = [s["number"] for s in stations if "focus" in s.get("options", [])]
    print("\n3  Is there anything else you want to add?")
    if not takes:
        print("   (these stations have no prompt to add to; anything you type is saved with the run log)")
    if library:
        print("   Saved focus: " + "   ".join(f"{x['number']} = {x['name']}" for x in library))
    print("   One thing per line (or a saved number). Blank line when done.")
    lines = []
    while True:
        line = input("   > ").strip()
        if not line:
            break
        lines.append(line)
    args.focus = list(args.focus or []) + lines
    typed = [x for x in lines if not x.replace(",", " ").replace(" ", "").isdigit()]
    if typed:
        name = ask("Save these as a reusable focus? Type a name, or Enter to skip:")
        if name:
            print(f"   saved as focus {focus_lib.save_to_library(name, typed)}")


def workers_for(args: argparse.Namespace, settings: dict) -> int:
    if args.workers:
        return args.workers
    presets = settings["turbo_presets"]
    return int(presets.get(str(args.turbo), settings["max_concurrent_calls"])) if args.turbo else settings["max_concurrent_calls"]


def command_for(station: dict, args: argparse.Namespace, workers: int, provider: str, model: str | None) -> list[str]:
    accepted = set(station.get("options", []))
    cmd = [sys.executable, str(API_HOME / station["folder"] / station["script"]), *args.item]
    for flag, value in (("limit", args.limit), ("workers", workers), ("provider", provider), ("model", model),
                        ("channel", args.channel), ("topic", args.topic)):
        if flag in accepted and value not in (None, ""):
            cmd += [f"--{flag}", str(value)]
    if "focus" in accepted:
        for point in focus_lib.resolve_run_focus(args.focus):
            cmd += ["--focus", point]
    if args.redo and "redo" in accepted:
        cmd.append("--redo")
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd


def estimate(stations: list[dict], limit: int | None, settings: dict, workers: int) -> tuple[int, int]:
    items = limit or 1
    api = [s for s in stations if s.get("uses_api")]
    calls = items * sum(max(1, len(s.get("goals", []))) for s in api)
    tokens = items * len(api) * settings["estimated_tokens_per_item"]
    seconds = int(calls / max(1, workers) * settings.get("estimated_seconds_per_call", 40)) if calls else 0
    return tokens, seconds


def run(argv=None) -> int:
    ensure_runtime_dirs()
    args = parse(argv)
    if args.selection and args.selection[0].lower() == "find":
        from engine.tagger import print_search
        return print_search(" ".join(args.selection[1:]), args.minimum)
    if args.selection and args.selection[0].lower() == "goals":
        from engine.goals import write_catalog
        path = write_catalog()
        print(path.read_text(encoding="utf-8"))
        return 0
    state = API_HOME / "STATE" / "last_run.json"
    if not args.selection:
        if not sys.stdin.isatty():
            raise SystemExit("Give a station number or routine letter (non-interactive mode).")
        interactive(args, state)
    numbers = resolve(args.selection)
    reg = registry()
    stations = [reg[n] for n in numbers]
    settings = load("settings.json")
    workers = workers_for(args, settings)
    args.resume = getattr(args, "resume", False)
    provider = "mock" if args.mock else (args.provider or settings["default_provider"])
    from engine.llm import PROVIDERS
    model = args.model or settings["models"].get(provider) or PROVIDERS.get(provider, {}).get("default_model")
    found, done, where = count_items(stations, args)
    planned = min(args.limit, found) if args.limit and found else (found - (0 if args.redo else done)) if found else args.limit
    tokens, seconds = estimate(stations, planned, settings, workers)
    run_focus = focus_lib.resolve_run_focus(args.focus)
    plan = {"selection": args.selection, "stations": [s["label"] for s in stations], "items": args.item,
            "found": where + (f" ({done} done)" if done else "") if found else None, "limit": args.limit,
            "channel": args.channel, "topic": args.topic, "workers": workers, "provider": provider, "model": model,
            "fallback": [f"{f['provider']}:{f['model']}" for f in settings.get("fallback", [])], "redo": args.redo,
            "focus": run_focus, "estimated_tokens": tokens, "estimated_minutes": round(seconds / 60, 1), "dry_run": args.dry_run}
    def show_plan() -> None:
        print("\n   Here is everything that will run:")
        for key, value in plan.items():
            if value not in (None, [], "", False):
                print(f"   {key:<18} {value}")
    show_plan()
    if sys.stdin.isatty() and not args.yes and not getattr(args, "resume", False):
        anything_else(args, stations)
        plan["focus"] = run_focus = focus_lib.resolve_run_focus(args.focus)
        if run_focus:
            show_plan()
        if not args.dry_run and ask("\n4  Run it? [Y/n]:", "y").lower().startswith("n"):
            return 1
    saved = {**plan, "selection": args.selection, "turbo": args.turbo, "workers": workers, "item": args.item,
             "focus": args.focus, "status": "running", "started_at": datetime.now(timezone.utc).isoformat()}
    state.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    gateway = Gateway(workers, run_id, mock=(provider == "mock")).start()
    results = []
    started = time.monotonic()
    try:
        for station in stations:
            label = station["label"]
            standing, _ = focus_lib.compose(API_HOME / station["folder"], None, run_focus)
            gateway.focus[label] = standing if station.get("focus") == "gateway" else ""
            cmd = command_for(station, args, workers, provider, model)
            env = {**os.environ, **gateway.env_for(label), "ONE_MENU_RUN_ID": run_id}
            if provider == "mock":  # legacy scripts skip a route without a key; the relay never sends these anywhere
                for key_name in ("DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "MOONSHOT_API_KEY"):
                    env.setdefault(key_name, "mock-key-not-sent")
            print(f"\n[{station['number']}] {station['name']}\n$ {' '.join(shlex.quote(c) for c in cmd[1:])}", flush=True)
            t0 = time.monotonic()
            code = subprocess.run(cmd, cwd=API_HOME, env=env).returncode
            stats = gateway.stats.snapshot()
            by = stats["by_station"].get(label, {"calls": 0, "failed": 0, "tokens": 0})
            results.append({"station": label, "returncode": code, "seconds": round(time.monotonic() - t0, 1), **by})
            print(f"[{station['number']}] {'OK' if code == 0 else f'FAILED (exit {code})'} · calls {by['calls']} · "
                  f"failed calls {by['failed']} · tokens {by['tokens']:,}")
    finally:
        stats = gateway.stats.snapshot()
        gateway.stop()
    record = {**plan, "run_id": run_id, "elapsed_seconds": round(time.monotonic() - started, 1), "results": results,
              "api": {k: v for k, v in stats.items() if k != "by_station"}, "call_receipts": str(gateway.receipts)}
    log = API_HOME / "LOGS" / f"run-{run_id}.json"
    log.write_text(json.dumps(record, indent=2), encoding="utf-8")
    saved["status"] = "completed" if not args.dry_run else "dry-run"
    state.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    failed = [r["station"] for r in results if r["returncode"] != 0]
    print(f"\nDone · stations ok {len(results) - len(failed)} · failed {len(failed)} {failed if failed else ''}· "
          f"{summary_line(stats)} · log {log}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
