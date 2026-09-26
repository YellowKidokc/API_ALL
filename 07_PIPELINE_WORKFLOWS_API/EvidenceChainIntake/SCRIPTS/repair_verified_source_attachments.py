#!/usr/bin/env python3
"""Replace stale source projections with exact verified originals, with backups."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from organize_and_retake_folders import OUTBOX, safe_copy, unc_path

INTAKE = Path(__file__).resolve().parent.parent
MASTER = OUTBOX / "00_ALL_PROCESSED_ARTICLES"
ORIGINALS = INTAKE / "SCRIPTS" / "ORIGINALS"
AUDITS = OUTBOX / "02_EVIDENCE_MATRIX" / "00__AUDITS_AND_RECEIPTS"
BACKUPS = OUTBOX / "00__BACKUPS__SOURCE_PROJECTION_BEFORE_REATTACHMENT"
RECEIPTS = OUTBOX / "00__IN_PROCESS__SOURCE_REATTACHMENT" / "00_RECEIPTS"
MARKER = "## Complete preserved source"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_title(text: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return match.group(1).strip() if match else ""


def latest_targets() -> list[dict]:
    reports = sorted(AUDITS.glob("SOURCE_ATTACHMENT_AUDIT_MASTER_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not reports:
        raise SystemExit("Run audit_source_attachment.py --scope master first.")
    rows = json.loads(reports[0].read_text(encoding="utf-8"))["records"]
    return [row for row in rows if row["state"] == "SOURCE_ATTACHED_SOURCE_PATH_MISSING"]


def set_frontmatter(text: str, key: str, value: str) -> str:
    quoted = json.dumps(value, ensure_ascii=False)
    pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
    if re.search(pattern, text):
        return re.sub(pattern, f"{key}: {quoted}", text, count=1)
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("Expected YAML frontmatter")
    return text[:end] + f"\n{key}: {quoted}" + text[end:]


def repair_record(record: str, original: str, archive_path: Path, timestamp: str) -> str:
    if MARKER not in record:
        raise ValueError("Missing preserved-source marker")
    prefix = record.split(MARKER, 1)[0].rstrip()
    title = source_title(original)
    if re.search(r'(?m)^title:\s*["\']?(?:ckg_evaluation:|untitled)?["\']?\s*$', prefix, re.I) and title:
        prefix = set_frontmatter(prefix, "title", title)
    prefix = set_frontmatter(prefix, "source_file", str(archive_path))
    prefix = set_frontmatter(prefix, "source_relinked_at", timestamp)
    prefix = set_frontmatter(prefix, "source_attachment_status", "verified_exact_original")
    return (
        f"{prefix}\n\n{MARKER}\n\n"
        "<!-- BEGIN EXACT SOURCE PROJECTION; verified against source_sha256 -->\n\n"
        f"{original.rstrip()}\n\n"
        "<!-- END EXACT SOURCE PROJECTION -->\n"
    )


def main() -> None:
    targets = latest_targets()
    source_index = {digest(path): path for path in ORIGINALS.rglob("*") if path.is_file()}
    missing = [row for row in targets if row["source_sha256"] not in source_index]
    if missing:
        raise SystemExit(f"Refusing repair: {len(missing)} expected original(s) are unavailable.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_root = BACKUPS / stamp
    receipt = []
    for row in targets:
        master = Path(row["record"])
        original_path = source_index[row["source_sha256"]]
        backup = backup_root / master.name
        safe_copy(master, backup)
        old_hash = digest(master)
        original_text = original_path.read_text(encoding="utf-8", errors="replace")
        repaired = repair_record(master.read_text(encoding="utf-8", errors="replace"), original_text, original_path, datetime.now(timezone.utc).isoformat())
        master.write_text(repaired, encoding="utf-8")
        receipt.append({
            "master": str(master), "backup": str(backup), "verified_original": str(original_path),
            "source_sha256": row["source_sha256"], "old_record_sha256": old_hash,
            "new_record_sha256": digest(master),
        })
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    report = RECEIPTS / f"VERIFIED_SOURCE_REATTACHMENT_{stamp}.csv"
    with open(unc_path(report), "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(receipt[0]) if receipt else ["master"])
        writer.writeheader(); writer.writerows(receipt)
    print(f"Repaired {len(receipt)} master records using exact verified originals.")
    print(f"Backup: {backup_root}")
    print(f"Receipt: {report}")


if __name__ == "__main__":
    main()
