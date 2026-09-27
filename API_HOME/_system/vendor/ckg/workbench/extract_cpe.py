"""Extract claims, proofs, and evidence atoms from CKG companions.

Reads the map checkpoint for each companion and writes one markdown file per
atomic object into OUTBOX/CLAIMS_PROOFS_EVIDENCE/{claims,proofs,evidence}/.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from workbench.ckg import atomic

BUCKET_MAP = {
    "CLAIM": "claims",
    "EVIDENCE": "evidence",
    "AXIOM": "proofs",
    "DEFINITION": "proofs",
    "OBJECTION": "claims",
}


def _safe_filename(text: str) -> str:
    safe = re.sub(r"[^\w\s-]", "", str(text).strip()).strip()
    safe = re.sub(r"[-\s]+", "_", safe)
    return safe[:60].strip("_")


def _frontmatter(path: Path) -> dict[str, Any]:
    """Return the YAML frontmatter of a companion as a flat dict."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = text[3:end].strip()
    data: dict[str, Any] = {}
    for line in fm.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        data[key.strip()] = val.strip().strip('"').strip("'")
    return data


def _find_map_json(root: Path, paper_uuid: str) -> Path | None:
    """Locate a map checkpoint, tolerating visible and hidden record roots."""
    candidates = [
        root / "SYSTEM" / "RECORDS" / paper_uuid / "map.json",
        root.parent / "_BACKSIDE" / "CKG" / "SYSTEM" / "RECORDS" / paper_uuid / "map.json",
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def _load_map_from_companion(path: Path) -> dict[str, Any]:
    """Fallback: parse the JSON object in the companion's `## map` section."""
    text = path.read_text(encoding="utf-8", errors="replace")
    marker = "\n## map\n"
    idx = text.find(marker)
    if idx == -1:
        return {}
    block = text[idx + len(marker) :]
    # Stop at the next top-level section
    next_section = re.search(r"\n## ", block)
    if next_section:
        block = block[: next_section.start()]
    try:
        return json.loads(block.strip())
    except json.JSONDecodeError:
        return {}


def _load_map(root: Path, paper_uuid: str, companion: Path) -> dict[str, Any]:
    path = _find_map_json(root, paper_uuid)
    if path is not None:
        try:
            wrapped = json.loads(path.read_text(encoding="utf-8"))
            return wrapped.get("data", {})
        except (json.JSONDecodeError, OSError):
            pass
    return _load_map_from_companion(companion)


def _derive_output_name(paper_uuid: str, obj: dict[str, Any]) -> str:
    key = str(obj.get("key") or "UNKNOWN")
    statement = str(obj.get("statement") or obj.get("quote") or "").strip()
    snippet = _safe_filename(statement)[:40] if statement else "no_statement"
    return f"{paper_uuid}_{key}_{snippet}.md"


def _render_atom(
    root: Path,
    paper_uuid: str,
    title: str,
    source_path: str,
    obj: dict[str, Any],
) -> Path | None:
    obj_type = str(obj.get("type") or "").upper()
    bucket = BUCKET_MAP.get(obj_type)
    if bucket is None:
        return None

    out_dir = root / "OUTBOX" / "CLAIMS_PROOFS_EVIDENCE" / bucket
    out_dir.mkdir(parents=True, exist_ok=True)

    name = _derive_output_name(paper_uuid, obj)
    dest = out_dir / name

    fm = {
        "paper_uuid": paper_uuid,
        "paper_title": title,
        "source_path": source_path,
        "atom_key": obj.get("key"),
        "atom_type": obj_type,
        "register": obj.get("register"),
        "bucket": bucket,
    }
    lines = ["---"]
    for k, v in fm.items():
        if v is not None:
            lines.append(f'{k}: "{str(v).replace(chr(34), chr(92)+chr(34))}"')
    lines.append("---")
    lines.append("")
    lines.append(f"# {obj_type}: {obj.get('key')}")
    lines.append("")
    if obj.get("statement"):
        lines.append(f"**Statement:** {obj['statement']}")
        lines.append("")
    if obj.get("quote"):
        lines.append("**Source quote:**")
        lines.append(f"> {obj['quote']}")
        lines.append("")
    if obj.get("reason"):
        lines.append(f"**Reason:** {obj['reason']}")
        lines.append("")
    body = "\n".join(lines) + "\n"

    # Avoid collisions: if an identical file already exists, keep it.
    if dest.exists():
        if dest.read_text(encoding="utf-8") == body:
            return dest
        # Content differs (e.g., source changed); append a short counter.
        stem = dest.stem
        suffix = dest.suffix
        for i in range(1, 1000):
            cand = dest.with_name(f"{stem}_{i:03d}{suffix}")
            if not cand.exists() or cand.read_text(encoding="utf-8") == body:
                dest = cand
                break

    atomic(dest, body.encode("utf-8"))
    return dest


def extract_from_companion(root: Path, companion: Path) -> list[Path]:
    """Extract CPE atoms from a single companion file."""
    fm = _frontmatter(companion)
    paper_uuid = fm.get("paper_uuid") or companion.stem
    title = fm.get("title") or companion.stem
    source_path = fm.get("source_path") or ""

    map_data = _load_map(root, paper_uuid, companion)
    objects = map_data.get("objects", []) if isinstance(map_data, dict) else []

    written: list[Path] = []
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        out = _render_atom(root, paper_uuid, title, source_path, obj)
        if out is not None:
            written.append(out)
    return written


def extract_all(root: Path, input_dirs: list[Path] | None = None) -> dict[str, int]:
    """Scan input companion folders and write CPE atoms."""
    if input_dirs is None:
        input_dirs = [root / "OUTBOX"]

    counts: dict[str, int] = {"claims": 0, "proofs": 0, "evidence": 0}
    for input_dir in input_dirs:
        if not input_dir.exists():
            continue
        for path in sorted(input_dir.glob("*.md")):
            # Skip untouched/processed source copies; extract from companions only.
            if path.name.endswith("_original.md"):
                continue
            # Skip subfolder duplicates unless explicitly requested.
            if path.parent != input_dir:
                continue
            # On the NAS share a listing can still show a file that was just
            # renamed or moved by the routing step; skip it rather than crash.
            if not path.exists():
                continue
            try:
                outs = extract_from_companion(root, path)
            except FileNotFoundError:
                continue
            for out in outs:
                bucket = out.parent.name
                counts[bucket] = counts.get(bucket, 0) + 1
    return counts
