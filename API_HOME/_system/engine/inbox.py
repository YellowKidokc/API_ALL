"""One inbox shape for every station that takes files in, and the item folders made from it.

  <inbox>/
    00_PRIORITY/                     runs first; sub-folders are groups too
    01_SERIES/<Series name>/...      a series: the folder name is the series
    02_GROUP/<Group name>/...        same as a series, but not one (e.g. "One pagers"); the folder name is the group
                                     (02_GENERAL is still read, as the same lane)
    (files directly in <inbox> or directly in a lane folder go to the group "Ungrouped")

Order: priority, then series, then group; inside a lane by group name, then file name. The group travels with
every item into its outputs: <outbox>/<lane>/<group>/<item>/, so a group stays together like a series.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .items import Item, _copy_source, _template_copy, slugify
from .output import sha256_file

LANES = (("00_PRIORITY", "priority"), ("01_SERIES", "series"), ("02_GROUP", "group"))
OLD_LANES = (("02_GENERAL", "group"),)   # earlier name of the group lane, still read
SKIP_PARTS = {".git", ".lake", "__pycache__", "_done", "_originals"}


@dataclass
class Entry:
    path: Path
    lane: str      # priority | series | group
    group: str     # the folder name that groups it


def ensure_layout(inbox: Path) -> None:
    for folder, _ in LANES:
        (inbox / folder).mkdir(parents=True, exist_ok=True)


def scan(inbox: Path, extensions: set[str]) -> list[Entry]:
    def files(folder: Path) -> list[Path]:
        return sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in extensions
                      and not SKIP_PARTS & set(p.parts) and not p.name.startswith(("_", ".")))

    out: list[Entry] = []
    lane_dirs = {folder for folder, _ in LANES + OLD_LANES}
    for folder, lane in LANES + OLD_LANES:
        base = inbox / folder
        if not base.is_dir():
            continue
        for f in files(base):
            rel = f.relative_to(base)
            out.append(Entry(f, lane, rel.parts[0] if len(rel.parts) > 1 else "Ungrouped"))
    loose = [f for f in files(inbox) if f.relative_to(inbox).parts[0] not in lane_dirs]
    out.extend(Entry(f, "group", f.relative_to(inbox).parts[0] if len(f.relative_to(inbox).parts) > 1 else "Ungrouped")
               for f in loose)
    rank = {lane: i for i, (_, lane) in enumerate(LANES)}
    out.sort(key=lambda e: (rank[e.lane], e.group.lower(), str(e.path).lower()))
    return out


def ensure_item(entry: Entry, outbox: Path, kind: str) -> Item:
    """Item folder <outbox>/<lane>/<group>/<stem>_<sha8>/ (made once; a changed source is re-copied)."""
    digest = sha256_file(entry.path)
    folder = outbox / entry.lane / entry.group / f"{slugify(entry.path.stem, 60)}_{digest[:8]}"
    meta_name = f"{kind}.json"
    if (folder / meta_name).exists():
        return Item(kind, folder)
    folder.parent.mkdir(parents=True, exist_ok=True)
    _template_copy(folder)
    _copy_source(entry.path, folder)
    item = Item(kind, folder)
    item.save_meta({"id": digest[:12].upper(), "kind": kind, "title": _title(entry.path), "lane": entry.lane,
                    "group": entry.group, "series": entry.group if entry.lane == "series" else "",
                    "source_hash": digest, "source_file": entry.path.name, "original_path": str(entry.path),
                    "created_at": datetime.now(timezone.utc).isoformat(), "stations_run": []})
    return item


def _title(path: Path) -> str:
    if path.suffix.lower() not in (".md", ".txt"):
        return path.stem  # a .lean file's first declaration is not its title
    match = re.search(r"^#\s+(.+)$", path.read_text(encoding="utf-8", errors="replace")[:3000], re.M)
    return match.group(1).strip() if match else path.stem


def load_meta(folder: Path, kind: str) -> dict:
    return json.loads((folder / f"{kind}.json").read_text(encoding="utf-8"))
