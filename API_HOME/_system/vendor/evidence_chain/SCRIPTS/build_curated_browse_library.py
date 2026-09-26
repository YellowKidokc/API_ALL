#!/usr/bin/env python3
"""Build a non-destructive, reader-facing copy library from processed intake records."""

from __future__ import annotations

import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from organize_and_retake_folders import (
    OUTBOX,
    clean_title,
    match_reader_categories,
    parse_metadata,
    safe_copy,
    unc_path,
)

SOURCE_ROOT = OUTBOX / "00_ALL_PROCESSED_ARTICLES"
CURATED_ROOT = OUTBOX / "04_BROWSE_BY_TOPIC"


def filename_for(title: str, source: Path, digest: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    stem = stem[:96] or "untitled-record"
    suffix = ".epistemic.md" if source.name.endswith(".epistemic.md") else ".knowledge.md"
    return f"{stem}__{digest[:8]}{suffix}"


def shelves_for(meta: dict, title: str, text: str) -> list[str]:
    record_type = str(meta.get("type", "")).lower()
    lower = f"{title}\n{text[:4000]}".lower()
    if record_type == "source_record" or "preservation receipt" in lower or "integration receipt" in lower:
        return ["00_PROVENANCE_AND_OPERATIONS"]
    stated = [re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_")
              for value in meta.get("reader_categories", [])]
    stated = [value for value in stated if value]
    selected = stated[:3] or match_reader_categories(f"{title}\n{meta.get('tags', [])}\n{text[:4000]}")[:3]
    # Evidence is a useful cross-cutting lens, but it should not bury every
    # topic-specific paper in a single 50-file shelf.
    specific = [value for value in selected if value != "Evidence_and_Proof"]
    return specific or selected


def main() -> None:
    if not SOURCE_ROOT.exists():
        raise SystemExit(f"Missing authoritative source root: {SOURCE_ROOT}")
    sources = sorted(list(SOURCE_ROOT.rglob("*.knowledge.md")) + list(SOURCE_ROOT.rglob("*.epistemic.md")))
    records = []
    for source in sources:
        text = source.read_text(encoding="utf-8", errors="replace")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        meta = parse_metadata(text)
        title = clean_title(source, str(meta.get("title", "")), text)
        shelves = shelves_for(meta, title, text)
        name = filename_for(title, source, digest)
        destinations = []
        for shelf in shelves:
            destination = CURATED_ROOT / shelf / name
            safe_copy(source, destination)
            destinations.append(str(destination))
        records.append({
            "source": str(source), "sha256": digest, "title": title,
            "shelves": shelves, "destinations": destinations,
        })

    receipt = CURATED_ROOT / f"CURATION_RECEIPT_{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.csv"
    with open(unc_path(receipt), "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "sha256", "title", "shelves", "destinations"])
        writer.writeheader()
        for record in records:
            writer.writerow({**record, "shelves": "; ".join(record["shelves"]), "destinations": "; ".join(record["destinations"])})
    print(f"Curated {len(records)} source records into {CURATED_ROOT}")
    print(f"Receipt: {receipt}")


if __name__ == "__main__":
    main()
