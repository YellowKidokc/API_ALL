#!/usr/bin/env python3
"""Hash and classify every Markdown file in OUTBOX without moving anything."""
from __future__ import annotations

import csv, hashlib, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from organize_and_retake_folders import OUTBOX, unc_path

MASTER = OUTBOX / "00_ALL_PROCESSED_ARTICLES"
LOGS = Path(__file__).resolve().parent / "LOGS"
CKG = ("At a glance", "Central claim", "Best concise argument", "System or model", "Evidence chain", "Best evidence and sources", "Strongest objection and negative controls", "What survives", "What this does not establish", "Corrections and revisions", "Implications", "Formal or testable path", "Open questions and next actions", "Recommended classification and relationships")

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def content_kind(text: str) -> str:
    headings = [h for h in re.findall(r"(?m)^##\s+(.+?)\s*$", text) if h in CKG]
    if headings == list(CKG) and "## Complete preserved source" in text:
        return "CKG_CASE_FILE"
    if headings:
        return "CKG_PARTIAL"
    if len(text.split()) >= 250:
        return "LEGACY_CONTENT_CANDIDATE"
    return "OPERATIONAL_OR_SHORT_NOTE"

def main() -> None:
    files = sorted(OUTBOX.rglob("*.md"))
    master_hashes = {digest(p) for p in MASTER.rglob("*.md")} if MASTER.exists() else set()
    rows = []
    operational_words = {"backup", "receipt", "audit", "logs", "tools", "waiting", "in_process", "original_structure"}
    for path in files:
        raw = path.read_bytes(); text = raw.decode("utf-8", errors="replace"); h = hashlib.sha256(raw).hexdigest()
        relative = path.relative_to(OUTBOX)
        path_words = " ".join(part.lower() for part in relative.parts)
        if path.is_relative_to(MASTER):
            bucket = content_kind(text)
        elif h in master_hashes:
            bucket = "ROUTED_DUPLICATE_OF_MASTER"
        elif any(word in path_words for word in operational_words):
            bucket = "OPERATIONAL_OR_SHORT_NOTE"
        else:
            bucket = content_kind(text)
        rows.append({"bucket": bucket, "sha256": h, "words": len(text.split()), "path": str(path)})
    summary = Counter(row["bucket"] for row in rows)
    unique = len({row["sha256"] for row in rows})
    LOGS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report = LOGS / f"ENTIRE_OUTBOX_AUDIT_{stamp}.csv"
    with open(unc_path(report), "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["bucket", "sha256", "words", "path"])
        writer.writeheader(); writer.writerows(rows)
    print(f"Markdown files: {len(rows)}; unique content hashes: {unique}")
    for bucket, count in sorted(summary.items()): print(f"{bucket}: {count}")
    print(f"CSV: {report}")

if __name__ == "__main__": main()
