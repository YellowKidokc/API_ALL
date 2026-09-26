"""FOCUS: David's extra requests, written on paper next to the call.

Three levels are gathered and appended to every prompt a station sends, under
## EXTRA FOCUS FROM DAVID:
  standing   stations/NN_NAME/FOCUS.md                (every run of that station)
  per item   <paper>/01_NOTES/FOCUS.md, or focus/<Channel>.json for YouTube
  per run    the answer to menu question 3 / --focus (several lines allowed)

Focus adds attention; it never removes the station's normal job. Empty files add
nothing and lines starting with # are comments. Saved focus lives in
config/focus_library.json and can be picked by number in the menu.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .paths import inside

HEADER = "## EXTRA FOCUS FROM DAVID:"
REQUIRED = ("Focus adds attention; it never replaces or narrows the normal job. Return the full normal output, "
            "then add a `## Focus findings` section (or a \"focus_findings\" field when the reply is JSON) that "
            "answers each point below, citing sentence ids, paragraph ids or timestamps.")


def points_from_markdown(path: Path | None) -> list[str]:
    if not path or not path.is_file():
        return []
    return [line.strip().lstrip("-*").strip() for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def points_from_channel(path: Path | None) -> list[str]:
    """focus/<Channel>.json as written by lens_pass.py --pick: {"lenses": [...], "ask": "..."}."""
    if not path or not path.is_file():
        return []
    if path.suffix.lower() != ".json":
        return points_from_markdown(path)
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    out: list[str] = []
    if isinstance(obj, dict):
        for key in ("focus", "ask"):
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                out.append(value.strip())
            elif isinstance(value, list):
                out.extend(str(x).strip() for x in value if str(x).strip())
    elif isinstance(obj, list):
        out.extend(str(x).strip() for x in obj if str(x).strip())
    return out


def library() -> list[dict]:
    path = inside("config", "focus_library.json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def save_to_library(name: str, points: list[str]) -> int:
    path = inside("config", "focus_library.json")
    items = library()
    items.append({"number": max([x["number"] for x in items] + [0]) + 1, "name": name, "points": points})
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return items[-1]["number"]


def resolve_run_focus(raw: str | list[str]) -> list[str]:
    """Menu answer -> focus points. '0' = none; a number = saved focus; anything else is David's words.
    Several answers can be separated by new lines or ';;'."""
    entries = raw if isinstance(raw, list) else str(raw).replace(";;", "\n").splitlines()
    saved = {str(x["number"]): x for x in library()}
    points: list[str] = []
    for entry in (e.strip() for e in entries):
        if not entry or entry == "0":
            continue
        numbers = entry.replace(",", " ").split()
        if all(n in saved for n in numbers):
            for n in numbers:
                points.extend(saved[n]["points"])
        else:
            points.append(entry)
    return points


def compose(station_dir: Path, item_dir: Path | None = None, run_focus: str | list[str] = "",
            channel_focus: Path | None = None) -> tuple[str, str]:
    """Return (focus block, sha256 of the block). Empty focus -> ('', hash of '')."""
    points: list[str] = []
    points.extend(points_from_markdown(station_dir / "FOCUS.md"))
    if item_dir:
        points.extend(points_from_markdown(item_dir / "01_NOTES" / "FOCUS.md"))
    points.extend(points_from_channel(channel_focus))
    points.extend(resolve_run_focus(run_focus))
    points = list(dict.fromkeys(p for p in points if p))
    text = "" if not points else f"{HEADER}\n\n{REQUIRED}\n\n" + "\n".join(f"- {p}" for p in points)
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def append(prompt: str, focus_text: str) -> str:
    return prompt.rstrip() + ("\n\n" + focus_text if focus_text else "") + "\n"
