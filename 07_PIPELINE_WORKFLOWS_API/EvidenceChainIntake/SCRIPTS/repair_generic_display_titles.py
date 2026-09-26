#!/usr/bin/env python3
"""Replace only generic displayed headings when a verified title already exists."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from organize_and_retake_folders import OUTBOX, parse_metadata, safe_copy

MASTER = OUTBOX / "00_ALL_PROCESSED_ARTICLES"
BACKUPS = OUTBOX / "00__BACKUPS__DISPLAY_TITLE_FIX"


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    changed = 0
    for path in sorted(MASTER.glob("*.knowledge.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = parse_metadata(text)
        title = str(meta.get("title", "")).strip()
        heading = re.search(r"(?m)^#\s+(.+?)\s*$", text)
        if not heading or not title:
            continue
        if heading.group(1).strip().lower() not in {"ckg_evaluation:", "untitled"}:
            continue
        if title.lower() in {"ckg_evaluation:", "untitled"}:
            continue
        safe_copy(path, BACKUPS / stamp / path.name)
        text = text[:heading.start(1)] + title + text[heading.end(1):]
        path.write_text(text, encoding="utf-8")
        changed += 1
    print(f"Corrected {changed} generic display heading(s).")
    print(f"Backup: {BACKUPS / stamp}")


if __name__ == "__main__":
    main()
