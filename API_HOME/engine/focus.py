"""Compose additive focus instructions without changing a station's normal task."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Iterable

HEADER = "## EXTRA FOCUS FROM DAVID:"
REQUIRED = ("Focus adds attention; it never replaces or narrows the normal job. "
            "Return the full normal output, then add `## Focus findings` and answer "
            "each point with sentence IDs, timestamps, or other source citations.")

def _markdown_points(path: Path | None) -> list[str]:
    if not path or not path.is_file(): return []
    return [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]

def _channel_points(path: Path | None) -> list[str]:
    if not path or not path.is_file(): return []
    if path.suffix.lower() != ".json": return _markdown_points(path)
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    value = obj.get("focus", obj.get("ask", obj)) if isinstance(obj, dict) else obj
    if isinstance(value, str): return [value.strip()] if value.strip() else []
    return [str(x).strip() for x in value if str(x).strip()] if isinstance(value, list) else []

def compose(station_dir: Path, item_dir: Path | None = None, run_focus: str = "",
            channel_focus: Path | None = None) -> tuple[str, str]:
    points: list[str] = []
    points.extend(_markdown_points(station_dir / "FOCUS.md"))
    if item_dir: points.extend(_markdown_points(item_dir / "01_NOTES" / "FOCUS.md"))
    points.extend(_channel_points(channel_focus))
    if run_focus.strip() and run_focus.strip() != "0": points.append(run_focus.strip())
    # Stable de-duplication makes checkpoint hashes predictable.
    points = list(dict.fromkeys(points))
    text = "" if not points else f"{HEADER}\n\n{REQUIRED}\n\n" + "\n".join(f"- {p.lstrip('- ').strip()}" for p in points)
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()

def append(prompt: str, focus_text: str) -> str:
    return prompt.rstrip() + ("\n\n" + focus_text if focus_text else "") + "\n"
