#!/usr/bin/env python3
"""Audit Evidence Matrix records and optionally stage unfinished copies.

Without ``--stage-waiting`` this is read-only with respect to papers.  Staging
moves only Matrix copies lacking a completed analysis receipt; master/source
copies are never moved or changed.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from organize_and_retake_folders import OUTBOX, parse_metadata, unc_path

MASTER = OUTBOX / "00_ALL_PROCESSED_ARTICLES"
MATRIX = OUTBOX / "02_EVIDENCE_MATRIX"
REPORTS = MATRIX / "00__AUDITS_AND_RECEIPTS"
WAITING = MATRIX / "00__WAITING_TO_BE_PROCESSED"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_state(text: str, meta: dict, is_master_match: bool) -> tuple[str, str]:
    """Return a conservative state and the evidence for that state."""
    generation = str(meta.get("generation_id", "")).upper()
    semantic_time = "semantic_analyzed_at:" in text
    semantic_provider = "semantic_provider:" in text
    unanswered = bool(re.search(r"(?i)\[open\]|\bnot run\b|not assessed", text))
    has_analysis = all(f"## {heading}" in text for heading in (
        "At a glance", "Evidence chain", "What this does not establish",
    ))

    if not is_master_match:
        return "IDENTITY_REVIEW", "No byte-identical counterpart in current master shelf"
    if generation.startswith("G2"):
        return "GENERATION_2", "Explicit G2 metadata"
    if semantic_time and semantic_provider and has_analysis and not unanswered:
        return "GENERATION_1_ANALYZED", "Analysis receipt metadata present; no G2 label"
    if unanswered or not semantic_time:
        return "SOURCE_OR_TEMPLATE_ONLY", "No completed semantic receipt or unresolved template markers"
    return "LEGACY_REVIEW", "Partially processed or ambiguous legacy record"


def waiting_destination(source: Path, file_hash: str) -> Path:
    """Keep the old Matrix topic as context and avoid filename collisions."""
    topic = source.parent.name
    candidate = WAITING / topic / source.name
    if candidate.exists() and digest(candidate) != file_hash:
        candidate = WAITING / topic / f"{source.stem}__{file_hash[:8]}{source.suffix}"
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Evidence Matrix generation state.")
    parser.add_argument("--stage-waiting", action="store_true",
                        help="Move only unfinished Matrix copies into 00__WAITING_TO_BE_PROCESSED.")
    parser.add_argument("--include-waiting", action="store_true",
                        help="Also inspect records already in 00__WAITING_TO_BE_PROCESSED.")
    args = parser.parse_args()
    masters = list(MASTER.rglob("*.knowledge.md")) + list(MASTER.rglob("*.epistemic.md"))
    master_hashes = {digest(path): path for path in masters}
    records = list(MATRIX.rglob("*.knowledge.md")) + list(MATRIX.rglob("*.epistemic.md"))
    if not args.include_waiting:
        records = [path for path in records if WAITING not in path.parents]
    results = []
    for path in sorted(records):
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        meta = parse_metadata(text)
        file_hash = hashlib.sha256(raw).hexdigest()
        state, reason = audit_state(text, meta, file_hash in master_hashes)
        title = str(meta.get("title", "")).strip('"')
        results.append({
            "state": state,
            "reason": reason,
            "matrix_record": str(path),
            "master_record": str(master_hashes.get(file_hash, "")),
            "sha256": file_hash,
            "generation_id": meta.get("generation_id", ""),
            "semantic_provider": re.search(r'(?m)^semantic_provider:\s*"?([^\n"]+)', text).group(1).strip() if "semantic_provider:" in text else "",
            "semantic_analyzed_at": re.search(r'(?m)^semantic_analyzed_at:\s*"?([^\n"]+)', text).group(1).strip() if "semantic_analyzed_at:" in text else "",
            "title": title,
            "generic_title": title.lower() in {"", "ckg_evaluation:", "untitled"},
        })

        if args.stage_waiting and state == "SOURCE_OR_TEMPLATE_ONLY":
            destination = waiting_destination(path, file_hash)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.move(unc_path(path), unc_path(destination))
            results[-1]["staged_waiting_copy"] = str(destination)
        else:
            results[-1]["staged_waiting_copy"] = ""

    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    summary = Counter(item["state"] for item in results)
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "summary": summary, "records": results}
    json_path = REPORTS / f"GENERATION_STATE_AUDIT_{stamp}.json"
    csv_path = REPORTS / f"GENERATION_STATE_AUDIT_{stamp}.csv"
    with open(unc_path(json_path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, default=dict)
    with open(unc_path(csv_path), "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]) if results else ["state"])
        writer.writeheader()
        writer.writerows(results)
    print("Generation-state audit")
    for state, count in sorted(summary.items()):
        print(f"{state}: {count}")
    if args.stage_waiting:
        print(f"Staged waiting copies: {sum(bool(item['staged_waiting_copy']) for item in results)}")
    print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()
