#!/usr/bin/env python3
"""Create a non-destructive workspace for records whose original-source link is stale.

The master record stays in OUTBOX.  This creates a copy of the analysis record
and a matching locator card, both carrying the original paths and expected hash.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from organize_and_retake_folders import OUTBOX, safe_copy, unc_path

MASTER = OUTBOX / "00_ALL_PROCESSED_ARTICLES"
PROCESS = OUTBOX / "00__IN_PROCESS__SOURCE_REATTACHMENT"
ANSWERS = PROCESS / "01_ANALYSIS_RECORDS_AWAITING_SOURCE_LINK"
LOCATORS = PROCESS / "02_ORIGINAL_PAPERS_TO_LOCATE"
RECEIPTS = PROCESS / "00_RECEIPTS"


def load_latest_master_audit() -> list[dict]:
    audits = sorted(
        (OUTBOX / "02_EVIDENCE_MATRIX" / "00__AUDITS_AND_RECEIPTS").glob("SOURCE_ATTACHMENT_AUDIT_MASTER_*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not audits:
        raise SystemExit("Run audit_source_attachment.py --scope master first.")
    return json.loads(audits[0].read_text(encoding="utf-8"))["records"]


def main() -> None:
    eligible = [row for row in load_latest_master_audit() if row["state"] == "SOURCE_ATTACHED_SOURCE_PATH_MISSING"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    receipt = []
    ANSWERS.mkdir(parents=True, exist_ok=True)
    LOCATORS.mkdir(parents=True, exist_ok=True)
    for row in eligible:
        master = Path(row["record"])
        if not master.exists():
            continue
        # Flat master shelf normally makes this the original filename; a hash
        # suffix prevents an accidental collision without overwriting anything.
        name = master.name
        answer_copy = ANSWERS / name
        if answer_copy.exists() and hashlib.sha256(answer_copy.read_bytes()).hexdigest() != row["sha256"]:
            answer_copy = ANSWERS / f"{master.stem}__{row['sha256'][:8]}{master.suffix}"
        safe_copy(master, answer_copy)

        card = LOCATORS / f"{answer_copy.name}.source-to-locate.md"
        card.write_text(
            "---\n"
            "record_kind: original_source_locator\n"
            "status: AWAITING_SOURCE_RELINK\n"
            f"record_sha256: {row['sha256']}\n"
            f"expected_source_sha256: {row['source_sha256']}\n"
            "---\n\n"
            "# Original Paper To Locate\n\n"
            f"- **Analysis copy in process:** `{answer_copy}`\n"
            f"- **Original master location:** `{master}`\n"
            f"- **Recorded prior source location:** `{row['source_file']}`\n"
            f"- **Expected original SHA-256:** `{row['source_sha256']}`\n"
            f"- **Title currently recorded:** {row['title'] or 'UNRESOLVED'}\n\n"
            "The analysis record includes a preserved-source section, but the recorded original file is no longer "
            "available at its prior location. Find the original file, verify its SHA-256, update the source link, "
            "then return the corrected record to its original master location.\n",
            encoding="utf-8",
        )
        receipt.append({"master": str(master), "analysis_copy": str(answer_copy), "locator_card": str(card),
                        "expected_source": row["source_file"], "expected_source_sha256": row["source_sha256"]})

    RECEIPTS.mkdir(parents=True, exist_ok=True)
    report = RECEIPTS / f"SOURCE_REATTACHMENT_STAGING_{stamp}.csv"
    with open(unc_path(report), "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["master", "analysis_copy", "locator_card", "expected_source", "expected_source_sha256"])
        writer.writeheader(); writer.writerows(receipt)
    print(f"Staged {len(receipt)} analysis/source-locator pairs.")
    print(f"Receipt: {report}")


if __name__ == "__main__":
    main()
