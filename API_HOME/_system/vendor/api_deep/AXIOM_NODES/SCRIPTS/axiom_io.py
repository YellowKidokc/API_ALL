"""I/O helpers for the AXIOM_NODES station."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


def safe_filename(text: str) -> str:
    safe = re.sub(r"[^\w\s-]", "", text.strip()).strip()
    safe = re.sub(r"[-\s]+", "_", safe)
    return safe[:80].strip("_")


def paper_uuid(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
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
    path = workspace / "06_JSON_RECORDS" / f"{name}_axiom_nodes_api.json"
    data["api"] = "Axiom Nodes API"
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))
    return path


def enrich_markdown_companion(
    workspace: Path,
    paper_uuid: str,
    data: dict[str, Any],
    source_path: Path,
    target_path: Path | None = None,
) -> Path:
    title = data.get("title") or safe_filename(source_path.stem)
    name = safe_filename(title) or paper_uuid[:16]
    path = target_path or (workspace / "01_ALL_PAPERS" / f"{name}.md")

    source_text = source_path.read_text(encoding="utf-8").rstrip()

    lines = [source_text, "", "---", ""]
    lines.append("## Axiom Node Mapping (Axiom Nodes API)")
    lines.append("")
    lines.append("### Summary")
    lines.append("")
    lines.append(data.get("summary", "_No summary provided._"))
    lines.append("")
    lines.append(f"**Primary mode:** {data.get('primary_mode', 'UNKNOWN')}")
    lines.append("")
    lines.append("### Mapped Nodes")
    lines.append("")

    for node in data.get("axiom_nodes", []):
        lines.append(f"- **{node.get('node_id', '')}** — {node.get('name', '')}")
        lines.append(f"  - mode: {node.get('mode', '')}")
        lines.append(f"  - alignment: {node.get('alignment', '')}")
        lines.append(f"  - confidence: {node.get('confidence', '')}")
        if node.get("evidence_quote"):
            lines.append(f"  - evidence: {node['evidence_quote']}")
        if node.get("notes"):
            lines.append(f"  - notes: {node['notes']}")
        lines.append("")

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
