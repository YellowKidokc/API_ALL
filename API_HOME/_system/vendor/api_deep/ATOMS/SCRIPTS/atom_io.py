"""I/O helpers for the ATOMS station: read, write, name generation."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


def safe_filename(text: str) -> str:
    """Make a filesystem-safe, readable stem from free text."""
    safe = re.sub(r"[^\w\s-]", "", text.strip()).strip()
    safe = re.sub(r"[-\s]+", "_", safe)
    return safe[:80].strip("_")


def paper_uuid(path: Path) -> str:
    """Stable UUID-like identifier derived from the item's relative path."""
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    """Write data atomically using temp-and-rename."""
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


def write_json_record(workspace: Path, paper_uuid: str, data: dict[str, Any]) -> Path:
    title = data.get("title") or "untitled"
    name = safe_filename(title) or paper_uuid[:16]
    path = workspace / "06_JSON_RECORDS" / f"{name}_axiom_api.json"
    data["api"] = "Axiom API"
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))
    return path


def _build_atom_section(data: dict[str, Any]) -> list[str]:
    """Return markdown lines for the atom classification section."""
    lines = [
        "## Atom Classification (Axiom API)",
        "",
        "### Summary",
        "",
        data.get("summary", "_No summary provided._"),
        "",
        "### Atoms",
        "",
    ]

    for i, atom in enumerate(data.get("atoms", []), start=1):
        lines.append(f"#### Atom {i}: {atom.get('name', 'Unnamed')} ({atom.get('nodeType', 'unknown')})")
        lines.append("")
        lines.append(f"- **stage**: {atom.get('stage', '')}")
        lines.append(f"- **nodeType**: {atom.get('nodeType', '')}")
        if "claimClass" in atom:
            lines.append(f"- **claimClass**: {atom.get('claimClass', '')}")
        if "statementTechnical" in atom:
            lines.append(f"- **statementTechnical**: {atom.get('statementTechnical', '')}")
        if "statementPlain" in atom:
            lines.append(f"- **statementPlain**: {atom.get('statementPlain', '')}")
        if "falsificationCondition" in atom:
            lines.append(f"- **falsificationCondition**: {atom.get('falsificationCondition', '')}")
        lines.append(f"- **verificationStatus**: {atom.get('verificationStatus', '')}")
        lines.append(f"- **challengeStatus**: {atom.get('challengeStatus', '')}")
        if atom.get("edges"):
            lines.append("- **edges**:")
            for edge in atom["edges"]:
                lines.append(f"  - {edge.get('type', '')} -> {edge.get('target', '')} (grade: {edge.get('grade', '')}, propagates: {edge.get('propagates', '')})")
        if atom.get("notes"):
            lines.append(f"- **notes**: {atom['notes']}")
        lines.append("")

    return lines


def enrich_markdown_companion(
    workspace: Path,
    paper_uuid: str,
    data: dict[str, Any],
    source_path: Path,
    target_path: Path | None = None,
) -> Path:
    """Append atom classification to the bottom of the source paper.

    If target_path is None, writes to WORKSPACE/01_ALL_PAPERS/<title>.md.
    If target_path is provided, enriches in place at that path (after the
    original has been preserved).

    If the source is already a CKG companion, the result is:
      CKG sections + original source + Atom Classification section.
    """
    title = data.get("title") or safe_filename(source_path.stem)
    name = safe_filename(title) or paper_uuid[:16]
    path = target_path or (workspace / "01_ALL_PAPERS" / f"{name}.md")

    source_text = source_path.read_text(encoding="utf-8").rstrip()

    lines = [source_text, "", "---", ""]
    lines.extend(_build_atom_section(data))
    lines.append("### Source Hash")
    lines.append("")
    lines.append(f"`{paper_uuid}`")
    lines.append("")

    atomic_write(path, "\n".join(lines).encode("utf-8"))
    return path


def preserve_original(workspace: Path, data: dict[str, Any], source_path: Path) -> Path:
    title = data.get("title") or safe_filename(source_path.stem)
    name = safe_filename(title) or "untitled"
    path = workspace / "00_ORIGINAL_UNTOUCHED" / f"{name}_original{source_path.suffix}"
    atomic_write(path, source_path.read_bytes())
    return path
