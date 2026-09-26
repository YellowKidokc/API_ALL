#!/usr/bin/env python3
"""Sort Evidence Chain records by CKG layout conformance without moving papers."""

from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from organize_and_retake_folders import OUTBOX, unc_path

MASTER = OUTBOX / "00_ALL_PROCESSED_ARTICLES"
LOGS = Path(__file__).resolve().parent / "LOGS"
HEADINGS = (
    "At a glance", "Central claim", "Best concise argument", "System or model",
    "Evidence chain", "Best evidence and sources", "Strongest objection and negative controls",
    "What survives", "What this does not establish", "Corrections and revisions", "Implications",
    "Formal or testable path", "Open questions and next actions", "Recommended classification and relationships",
)


def state(text: str) -> tuple[str, str]:
    found = [heading for heading in re.findall(r"(?m)^##\s+(.+?)\s*$", text) if heading in HEADINGS]
    expected = list(HEADINGS)
    exact = found == expected
    all_sections = all(f"## {heading}" in text for heading in HEADINGS)
    source = "## Complete preserved source" in text
    unanswered = bool(re.search(r"(?i)\[open\]|\bnot run\b", text))
    if exact and source and not unanswered:
        return "CKG_COMPLETE", "Full CKG heading contract, source attachment, and no unresolved template marker"
    if all_sections and source:
        return "CKG_REVIEW", "CKG sections present but order/marker needs review"
    if any(f"## {heading}" in text for heading in HEADINGS):
        return "CKG_PARTIAL", "Some CKG sections exist but the full contract is incomplete"
    return "OTHER_OR_LEGACY", "Does not use the CKG case-file layout"


def main() -> None:
    records = sorted(list(MASTER.glob("*.knowledge.md")) + list(MASTER.glob("*.epistemic.md")))
    rows = []
    for path in records:
        text = path.read_text(encoding="utf-8", errors="replace")
        label, reason = state(text)
        title = re.search(r'(?m)^title:\s*"?(.+?)"?\s*$', text)
        rows.append({"layout_status": label, "reason": reason, "record": str(path),
                     "title": title.group(1) if title else "UNRESOLVED"})
    summary = Counter(row["layout_status"] for row in rows)
    LOGS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report = LOGS / f"CKG_LAYOUT_AUDIT_{stamp}.csv"
    with open(unc_path(report), "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["layout_status", "reason", "record", "title"])
        writer.writeheader(); writer.writerows(rows)
    print("CKG layout audit")
    for label, count in sorted(summary.items()): print(f"{label}: {count}")
    print(f"CSV: {report}")


if __name__ == "__main__":
    main()
