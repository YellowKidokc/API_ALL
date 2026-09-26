#!/usr/bin/env python3
"""Report whether processed papers carry their original source article with them.

No papers are changed.  The report separates a missing attached source from a
source whose path/hash cannot yet be verified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from organize_and_retake_folders import OUTBOX, parse_metadata, unc_path

MASTER = OUTBOX / "00_ALL_PROCESSED_ARTICLES"
MATRIX = OUTBOX / "02_EVIDENCE_MATRIX"
REPORTS = MATRIX / "00__AUDITS_AND_RECEIPTS"
MARKER = "## Complete preserved source"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_prefix(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()[:240]


def state_for(path: Path) -> dict:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    meta = parse_metadata(text)
    # Parsed frontmatter preserves a Windows UNC path correctly.  Do not
    # collapse its leading double backslash: that would turn a network path
    # into an invalid local-rooted path.
    source_file = str(meta.get("source_file", ""))
    source_hash = str(meta.get("source_sha256", "")).lower()
    has_analysis = "## At a glance" in text
    has_marker = MARKER in text
    attached = text.split(MARKER, 1)[1].strip() if has_marker else ""

    state = "SOURCE_ATTACHMENT_REVIEW"
    reason = "Could not determine attachment state"
    source_path = Path(source_file) if source_file else None
    source_exists = bool(source_path and source_path.exists())
    source_hash_matches = False
    source_text_seen = False
    if source_exists:
        original = source_path.read_bytes()
        actual_hash = sha256_bytes(original)
        source_hash_matches = bool(source_hash and actual_hash == source_hash)
        original_text = original.decode("utf-8", errors="replace")
        prefix = normalized_prefix(original_text)
        source_text_seen = bool(prefix and prefix in re.sub(r"\s+", " ", attached))

    if not has_analysis:
        state, reason = "NO_COMPLETED_ANALYSIS", "No completed analysis section"
    elif not has_marker or not attached:
        state, reason = "ANALYSIS_WITHOUT_ATTACHED_SOURCE", "Analysis is present but the original article is not attached"
    elif source_exists and source_hash_matches and source_text_seen:
        state, reason = "SOURCE_ATTACHED_AND_VERIFIED", "Attached source matches the preserved original source file and hash"
    elif source_exists and source_hash_matches:
        state, reason = "SOURCE_ATTACHED_HASH_VERIFIED", "Source hash matches; attached-text comparison needs review"
    elif not source_file:
        state, reason = "SOURCE_ATTACHED_NO_SOURCE_PATH", "Attached source exists but no original source path is recorded"
    elif not source_exists:
        state, reason = "SOURCE_ATTACHED_SOURCE_PATH_MISSING", "Attached source exists but the recorded original source file is unavailable"
    else:
        state, reason = "SOURCE_ATTACHED_HASH_MISMATCH", "Attached source exists but the recorded source hash does not match the original file"

    return {
        "state": state, "reason": reason, "record": str(path),
        "sha256": sha256_bytes(raw),
        "title": str(meta.get("title", "")).strip('"'),
        "source_file": source_file, "source_sha256": source_hash,
        "has_analysis": has_analysis, "has_source_marker": has_marker,
        "attached_source_characters": len(attached), "source_file_exists": source_exists,
        "source_hash_matches": source_hash_matches, "attached_prefix_matches": source_text_seen,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit original-source attachment for processed records.")
    parser.add_argument("--scope", choices=("master", "matrix"), default="matrix")
    parser.add_argument("--include-waiting", action="store_true")
    args = parser.parse_args()
    root = MASTER if args.scope == "master" else MATRIX
    records = list(root.rglob("*.knowledge.md")) + list(root.rglob("*.epistemic.md"))
    if args.scope == "matrix" and not args.include_waiting:
        records = [path for path in records if "00__WAITING_TO_BE_PROCESSED" not in path.parts]
    results = [state_for(path) for path in sorted(records)]
    summary = Counter(row["state"] for row in results)
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    stem = f"SOURCE_ATTACHMENT_AUDIT_{args.scope.upper()}_{stamp}"
    with open(unc_path(REPORTS / f"{stem}.json"), "w", encoding="utf-8") as handle:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "summary": summary, "records": results}, handle, indent=2, ensure_ascii=False, default=dict)
    with open(unc_path(REPORTS / f"{stem}.csv"), "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]) if results else ["state"])
        writer.writeheader(); writer.writerows(results)
    print(f"Source-attachment audit ({args.scope})")
    for state, count in sorted(summary.items()):
        print(f"{state}: {count}")
    print(f"CSV: {REPORTS / f'{stem}.csv'}")


if __name__ == "__main__":
    main()
