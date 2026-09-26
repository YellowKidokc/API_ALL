"""Core CKG workbench: intake, runner, checkpointing, and I/O primitives."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator

INBOX_DIRS = ["01_PRIORITY", "02_SERIES", "03_GENERAL"]
WAITING_DIR = "00_WAITING_NOT_PROCESSED"
SUPPORTED_EXTS = {".md", ".txt", ".lean", ".tex", ".html"}
MAX_SOURCE_CHARS = 100_000
DEFAULT_STAGES = ["map"] + [f"S{i:02d}" for i in range(1, 11)] + ["audit"]


def _config_dir(root: Path) -> Path:
    """Return CONFIG dir, preferring the hidden _BACKSIDE location."""
    hidden = root.parent / "_BACKSIDE" / "CKG" / "CONFIG"
    if hidden.exists():
        return hidden
    legacy = root / "CONFIG"
    if legacy.exists():
        return legacy
    return hidden


def master_template_path(root: Path) -> Path:
    """Return the master template, preferring the hidden _BACKSIDE location."""
    name = "CKG_ATOM_MASTER_TEMPLATE.md"
    hidden = root.parent / "_BACKSIDE" / "CKG" / "templates" / name
    if hidden.exists():
        return hidden
    return root / "templates" / name


@dataclass
class RunResult:
    item: Path
    status: str
    paper_uuid: str | None = None
    stage: str | None = None
    error: str | None = None


def initialize(root: Path) -> None:
    """Create the full CKG station directory tree."""
    dirs = [
        "INBOX/01_PRIORITY",
        "INBOX/02_SERIES",
        "INBOX/03_GENERAL",
        "INBOX/00_WAITING_NOT_PROCESSED",
        "OUTBOX/00_ORIGINAL_UNTOUCHED",
        "OUTBOX/00_ORIGINAL",
        "OUTBOX/02_BY_DOMAIN",
        "OUTBOX/03_BY_TAG",
        "OUTBOX/04_BY_SERIES",
        "OUTBOX/CLAIMS_PROOFS_EVIDENCE",
        "SYSTEM/RECORDS",
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)


def scan_verbose(
    root: Path,
) -> tuple[list[Path], int, dict[str, int], list[str]]:
    """Return eligible items, total files seen, exclusion counts, and reasons.

    Excludes the waiting folder, unsupported extensions, oversized readable
    files, and content duplicates (priority > series > general). Files that
    cannot be decoded as UTF-8 are still passed through so the runner can mark
    them NEEDS_ATTENTION rather than silently truncating.
    """
    total = 0
    seen_hashes: dict[str, Path] = {}
    eligible: list[Path] = []
    counts: dict[str, int] = defaultdict(int)
    excluded: list[str] = []

    for sub in [WAITING_DIR] + INBOX_DIRS:
        inbox = root / "INBOX" / sub
        if not inbox.exists():
            continue
        for path in sorted(inbox.rglob("*")):
            if not path.is_file():
                continue
            total += 1
            if sub == WAITING_DIR:
                counts["waiting"] += 1
                excluded.append(f"WAITING: {path}")
                continue
            if path.suffix.lower() not in SUPPORTED_EXTS:
                counts["unsupported"] += 1
                excluded.append(f"UNSUPPORTED: {path}")
                continue
            try:
                text = path.read_text(encoding="utf-8")
                if len(text) > MAX_SOURCE_CHARS:
                    counts["oversized"] += 1
                    excluded.append(f"OVERSIZED: {path}")
                    continue
                content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                if content_hash in seen_hashes:
                    counts["duplicate"] += 1
                    original = seen_hashes[content_hash]
                    excluded.append(f"DUPLICATE: {path} (same as {original})")
                    continue
                seen_hashes[content_hash] = path
            except UnicodeDecodeError:
                # Binary-looking file: let the runner fail it visibly.
                pass
            eligible.append(path)

    counts["eligible"] = len(eligible)
    return eligible, total, dict(counts), excluded


def scan(root: Path) -> tuple[list[Path], int]:
    """Thin wrapper around :func:`scan_verbose`."""
    eligible, total, _, _ = scan_verbose(root)
    return eligible, total


def valid_stage(stage: str, data: Any, source_text: str) -> bool:
    """Validate a single stage result.

    - ``map`` requires the expected schema and rejects invented quotes.
    - Other stages require expected keys and non-empty markdown.
    """
    if not isinstance(data, dict):
        raise ValueError(f"Stage {stage} result must be a JSON object")

    if stage == "map":
        required = [
            "title",
            "domain",
            "project",
            "purpose",
            "summary",
            "objects",
            "unmapped",
        ]
        for key in required:
            if key not in data:
                raise ValueError(f"Map result missing required key: {key}")
        objects = data.get("objects", [])
        if not isinstance(objects, list):
            raise ValueError("Map 'objects' must be a list")
        for obj in objects:
            if not isinstance(obj, dict):
                raise ValueError("Each object in 'objects' must be an object")
            quote = obj.get("quote", "")
            if quote and str(quote) not in source_text:
                raise ValueError(f"Map object quote is not present in source: {quote!r}")
        return True

    required = ["status", "markdown"]
    for key in required:
        if key not in data:
            raise ValueError(f"Stage {stage} result missing required key: {key}")
    markdown = str(data.get("markdown", "")).strip()
    if not markdown:
        raise ValueError(f"Stage {stage} produced empty markdown")
    return True


def atomic(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` atomically using temp-and-rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.{os.getpid()}.tmp"
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def save(path: Path, data: Any) -> None:
    """Write ``data`` as indented JSON atomically."""
    atomic(path, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))


@contextlib.contextmanager
def lock(root: Path) -> Iterator[None]:
    """Context manager that rejects a simultaneous second runner.

    Uses a PID lockfile under ``SYSTEM/CKG.lock``. Stale locks from dead
    processes are overwritten; locks held by live processes raise RuntimeError.
    """
    lockfile = root / "SYSTEM" / "CKG.lock"
    lockfile.parent.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()

    if lockfile.exists():
        try:
            old_pid = int(lockfile.read_text(encoding="utf-8").strip())
        except ValueError:
            old_pid = None
        if old_pid == pid:
            yield
            return
        if old_pid is not None:
            try:
                os.kill(old_pid, 0)
                raise RuntimeError(
                    f"Another CKG runner is already active (PID {old_pid})."
                )
            except ProcessLookupError:
                pass
            except OSError:
                # Process is not queryable on this platform; treat as stale.
                pass

    atomic(lockfile, str(pid).encode("utf-8"))
    try:
        yield
    finally:
        try:
            lockfile.unlink()
        except FileNotFoundError:
            pass


class Runner:
    """Execute the CKG pipeline for a set of source documents."""

    def __init__(self, root: Path, provider: Any, stages: list[str] | None = None):
        self.root = root
        self.provider = provider
        self.stages = stages or DEFAULT_STAGES
        self.template_path = master_template_path(root)
        self.config_path = _config_dir(root) / "ckg.json"
        self.records_dir = root / "SYSTEM" / "RECORDS"
        self.outbox_dir = root / "OUTBOX"

        self.template = (
            self.template_path.read_text(encoding="utf-8")
            if self.template_path.exists()
            else ""
        )
        try:
            self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {}
        self.model = getattr(provider, "model", None) or self.config.get(
            "model", "deepseek-chat"
        )
        self.provider_name = getattr(provider, "name", "unknown")

    def _paper_uuid(self, item: Path) -> str:
        """Stable UUID-like identifier derived from the item's relative path."""
        try:
            rel = item.relative_to(self.root)
        except ValueError:
            rel = item
        return hashlib.sha256(str(rel).encode("utf-8")).hexdigest()

    def _source_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _template_hash(self) -> str:
        return hashlib.sha256(self.template.encode("utf-8")).hexdigest()

    def _checkpoint_path(self, paper_uuid: str, stage: str) -> Path:
        return self.records_dir / paper_uuid / f"{stage}.json"

    def _build_prompt(self, stage: str, source_text: str, stage_results: dict[str, Any]) -> str:
        if stage == "map":
            schema = json.dumps({
                "title": "document title",
                "domain": "primary knowledge domain",
                "project": "collection or project name",
                "purpose": "paper | note | draft | objection | evidence | synthesis",
                "summary": "one-paragraph summary",
                "keywords": ["keyword"],
                "objects": [
                    {
                        "key": "C1",
                        "type": "CLAIM | DEFINITION | AXIOM | EVIDENCE | OBJECTION",
                        "register": "e.g. FORMAL_MATHEMATICAL, THEOLOGICAL, EMPIRICAL",
                        "quote": "exact substring from the source, or empty",
                        "statement": "paraphrased or formal statement",
                        "reason": "why the object is classified this way"
                    }
                ],
                "unmapped": ["important content not captured above"]
            }, indent=2, ensure_ascii=False)
            return (
                "Map this document as JSON. Return ONLY a single JSON object matching the schema below.\n"
                "CRITICAL RULE: every non-empty 'quote' must be copied EXACTLY from the SOURCE text.\n"
                "If you cannot find an exact verbatim substring, leave 'quote' empty.\n"
                "Never invent, paraphrase, or approximate a quotation.\n\n"
                f"SCHEMA:\n{schema}\n\n"
                f"SOURCE:\n{source_text}\n"
            )
        prior = "\n\n".join(
            f"## {k}\n{json.dumps(v, ensure_ascii=False)}" for k, v in stage_results.items()
        )
        section_schema = json.dumps({
            "status": "AI_PROPOSED",
            "reason": "concise rationale for the section content",
            "markdown": "the section content in GitHub-Flavored Markdown",
            "object_keys": ["C1"]
        }, indent=2, ensure_ascii=False)
        return (
            f"Execute CKG section {stage}. Return ONLY a single JSON object matching this schema.\n\n"
            f"SCHEMA:\n{section_schema}\n\n"
            f"TEMPLATE:\n{self.template}\n\n"
            f"PRIOR STAGES:\n{prior}\n\n"
            f"SOURCE:\n{source_text}\n"
        )

    def _checkpoint_valid(self, checkpoint_file: Path, source_text: str) -> bool:
        try:
            cp = json.loads(checkpoint_file.read_text(encoding="utf-8"))
        except Exception:
            return False
        return (
            cp.get("source_hash") == self._source_hash(source_text)
            and cp.get("template_hash") == self._template_hash()
            and cp.get("model") == self.model
            and cp.get("provider") == self.provider_name
            and cp.get("stages") == self.stages
        )

    def _wrap_checkpoint(self, data: Any, source_text: str) -> dict[str, Any]:
        return {
            "data": data,
            "source_hash": self._source_hash(source_text),
            "template_hash": self._template_hash(),
            "model": self.model,
            "provider": self.provider_name,
            "stages": self.stages,
            "saved_at": time.time(),
        }

    def _build_companion(
        self, paper_uuid: str, item: Path, source_text: str, stage_results: dict[str, Any]
    ) -> str:
        lines = [
            "---",
            f"paper_uuid: {paper_uuid}",
            f"source_path: {item}",
            f"source_hash: {self._source_hash(source_text)}",
            f"model: {self.model}",
            f"provider: {self.provider_name}",
            "grade: UNSCORED",
            "---",
            "",
            f"# CKG Companion — {paper_uuid}",
            "",
            "## Source",
            "",
            source_text,
            "",
        ]
        for stage, result in stage_results.items():
            lines.append(f"## {stage}")
            lines.append("")
            if isinstance(result, dict) and "markdown" in result:
                lines.append(result["markdown"])
            else:
                lines.append(json.dumps(result, indent=2, ensure_ascii=False))
            lines.append("")
        return "\n".join(lines)

    def _run_stage(
        self,
        stage: str,
        source_text: str,
        stage_results: dict[str, Any],
        checkpoint_file: Path,
    ) -> Any:
        if checkpoint_file.exists() and self._checkpoint_valid(checkpoint_file, source_text):
            return json.loads(checkpoint_file.read_text(encoding="utf-8"))["data"]

        prompt = self._build_prompt(stage, source_text, stage_results)
        system_prompt = self.template if stage != "map" else None
        result = self.provider.complete(prompt, system_prompt, json_mode=True)
        content = result.content if hasattr(result, "content") else str(result)
        try:
            data = self._parse_json(content)
        except ValueError:
            # Usually the reply hit the output limit and was cut off mid-JSON.
            # Ask once more for a tighter answer before failing the paper.
            retry_prompt = (
                prompt
                + "\n\nIMPORTANT: your previous answer was too long and was cut off. "
                "Return the same JSON structure, complete and valid, but more compact: "
                "shorter strings, at most the most important items per list."
            )
            result = self.provider.complete(retry_prompt, system_prompt, json_mode=True)
            content = result.content if hasattr(result, "content") else str(result)
            data = self._parse_json(content)
        data = self._sanitize(stage, data, source_text)
        valid_stage(stage, data, source_text)
        save(checkpoint_file, self._wrap_checkpoint(data, source_text))
        return data

    def _sanitize(
        self, stage: str, data: dict[str, Any], source_text: str
    ) -> dict[str, Any]:
        """Best-effort cleanup of common model errors.

        For the map stage, any object whose 'quote' is not a verbatim substring
        of the source is corrected to an empty quote rather than failing the
        whole paper. This preserves the object while guarding against invented
        quotations.
        """
        if stage != "map" or not isinstance(data, dict):
            return data
        objects = data.get("objects")
        if not isinstance(objects, list):
            return data
        changed = False
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            quote = obj.get("quote", "")
            if quote and str(quote) not in source_text:
                obj["quote"] = ""
                changed = True
        if changed:
            data["_sanitized"] = True
        return data

    def _parse_json(self, text: str) -> Any:
        """Parse JSON from a provider response, stripping fences if needed."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Strip markdown code fence and optional language tag.
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Provider returned non-JSON response: {text[:200]!r}") from exc

    def _process_item(self, item: Path) -> RunResult:
        paper_uuid = self._paper_uuid(item)
        try:
            source_text = item.read_text(encoding="utf-8")
        except Exception as e:
            return RunResult(
                item=item,
                status="NEEDS_ATTENTION",
                paper_uuid=paper_uuid,
                error=f"Cannot read source: {e}",
            )

        checkpoint_dir = self.records_dir / paper_uuid
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        short_uuid = paper_uuid[:8]
        print(f"[{short_uuid}] {item.name} — starting", flush=True)

        # Preserve the untouched original in the outbox as soon as it is opened.
        untouched_dir = self.root / "OUTBOX" / "00_ORIGINAL_UNTOUCHED"
        untouched_dest = untouched_dir / f"{paper_uuid}{item.suffix}"
        if not untouched_dest.exists():
            untouched_dir.mkdir(parents=True, exist_ok=True)
            atomic(untouched_dest, item.read_bytes())

        stage_results: dict[str, Any] = {}
        try:
            for idx, stage in enumerate(self.stages, start=1):
                checkpoint_file = self._checkpoint_path(paper_uuid, stage)
                cached = checkpoint_file.exists() and self._checkpoint_valid(
                    checkpoint_file, source_text
                )
                if cached:
                    print(
                        f"[{short_uuid}] {item.name} — stage {idx}/{len(self.stages)}: {stage} (cached)",
                        flush=True,
                    )
                else:
                    print(
                        f"[{short_uuid}] {item.name} — stage {idx}/{len(self.stages)}: {stage} ...",
                        flush=True,
                    )
                stage_results[stage] = self._run_stage(
                    stage, source_text, stage_results, checkpoint_file
                )
        except Exception as e:
            return RunResult(
                item=item,
                status="NEEDS_ATTENTION",
                paper_uuid=paper_uuid,
                stage=stage,
                error=str(e),
            )

        companion = self._build_companion(paper_uuid, item, source_text, stage_results)
        companion_path = self.outbox_dir / f"{paper_uuid}.md"
        atomic(companion_path, companion.encode("utf-8"))
        print(f"[{short_uuid}] {item.name} — companion written", flush=True)

        session_record = {
            "paper_uuid": paper_uuid,
            "source_path": str(item),
            "source_hash": self._source_hash(source_text),
            "model": self.model,
            "provider": self.provider_name,
            "status": "SOURCE_REVIEW_COMPLETE",
            "stages": self.stages,
        }
        save(self.records_dir / f"{paper_uuid}_session.json", session_record)

        return RunResult(item=item, status="SOURCE_REVIEW_COMPLETE", paper_uuid=paper_uuid)

    def batch(self, items: list[Path], workers: int) -> list[dict[str, Any]]:
        """Process ``items`` with up to ``workers`` concurrent workers."""
        results: list[dict[str, Any]] = []
        workers = max(1, workers)
        total = len(items)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self._process_item, item): item for item in items}
            for future in as_completed(futures):
                res = future.result()
                results.append(
                    {
                        "item": res.item,
                        "status": res.status,
                        "paper_uuid": res.paper_uuid,
                        "stage": res.stage,
                        "error": res.error,
                    }
                )
                short_uuid = res.paper_uuid[:8] if res.paper_uuid else "????????"
                label = futures[future].name
                if res.status == "SOURCE_REVIEW_COMPLETE":
                    print(
                        f"[{short_uuid}] {label} — DONE ({len(results)}/{total})",
                        flush=True,
                    )
                else:
                    print(
                        f"[{short_uuid}] {label} — FAILED at {res.stage}: {res.error} ({len(results)}/{total})",
                        flush=True,
                    )
        return results

    def completed(self, item: Path) -> bool:
        """Return True if all stages are saved and unchanged for ``item``."""
        try:
            source_text = item.read_text(encoding="utf-8")
        except Exception:
            return False
        paper_uuid = self._paper_uuid(item)
        for stage in self.stages:
            checkpoint_file = self._checkpoint_path(paper_uuid, stage)
            if not checkpoint_file.exists():
                return False
            if not self._checkpoint_valid(checkpoint_file, source_text):
                return False
        companion_path = self.outbox_dir / f"{paper_uuid}.md"
        return companion_path.exists()

    def process(self, item: Path) -> dict[str, Any]:
        """Process a single item, reusing saved checkpoints when valid."""
        res = self._process_item(item)
        return {
            "item": res.item,
            "status": res.status,
            "paper_uuid": res.paper_uuid,
            "stage": res.stage,
            "error": res.error,
        }
