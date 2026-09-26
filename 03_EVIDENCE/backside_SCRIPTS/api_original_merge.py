#!/usr/bin/env python3
"""api_original_merge.py — API + ORIGINAL DOCUMENT MERGE.

Created 2026-09-16 (Claude, with David). Status: TESTED.

Finds every API output (companions etc.) in OUTBOX, finds the original article it was made
from (by the source_sha256 the companion records), and writes ONE merged file:
API material on top, the original article unchanged below (article_stack rule).

Never overwrites or moves anything: merged files go to OUTBOX/MERGED_WITH_ORIGINAL/<shelf>/.
Companions whose original cannot be found are listed in the report, not guessed.

  python api_original_merge.py                 # all shelves
  python api_original_merge.py --shelf FOR_SUBSTACK --limit 5
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import article_stack

ROOT = Path(__file__).resolve().parents[1]
OUTBOX = ROOT / "OUTBOX"
MERGED = OUTBOX / "MERGED_WITH_ORIGINAL"
ORIGINAL_DIRS = [ROOT / "PROCESSED_ORIGINALS", OUTBOX / "00_ORIGINALS_PRESERVED", ROOT / "INBOX"]
SHELVES = ["FOR_SUBSTACK", "00_UNTOUCHED", "BY_DOMAIN", "BY_CONTENT_TYPE", "BY_SERIES", "CANONICAL_PROOFS"]
SHA_RE = re.compile(r"source_sha256:\s*[\"']?([0-9a-f]{64})")
TEXT_EXT = {".md", ".txt", ".html", ".htm"}


def index_originals(log) -> dict[str, Path]:
    idx: dict[str, Path] = {}
    for d in ORIGINAL_DIRS:
        if not d.exists():
            continue
        files = [p for p in d.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXT]
        log(f"  hashing {len(files):,} originals in {d.name} …")
        for p in files:
            try:
                sha = article_stack.sha256_bytes(article_stack.original_of(p.read_bytes()))
            except OSError:
                continue
            idx.setdefault(sha, p)
    return idx


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shelf", action="append", help="limit to shelf name(s) under OUTBOX")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args(argv)
    log = print

    originals = index_originals(log)
    log(f"  {len(originals):,} distinct originals indexed")
    rows, merged, missing, already, no_sha = [], 0, 0, 0, 0
    shelves = args.shelf or SHELVES
    n = 0
    for shelf in shelves:
        base = OUTBOX / shelf
        if not base.exists():
            continue
        for comp in sorted(base.rglob("*.md")):
            if args.limit and n >= args.limit:
                break
            n += 1
            raw = comp.read_bytes()
            head = raw[:6000].decode("utf-8", errors="replace")
            m = SHA_RE.search(head)
            rel = comp.relative_to(OUTBOX)
            if article_stack.MARKER_PREFIX in raw:
                already += 1
                rows.append([str(rel), "", "already_has_original", ""])
                continue
            if not m:
                no_sha += 1
                rows.append([str(rel), "", "no_source_sha256_in_file", ""])
                continue
            sha = m.group(1)
            orig = originals.get(sha)
            if not orig:
                missing += 1
                rows.append([str(rel), sha, "original_not_found", ""])
                continue
            original = article_stack.original_of(orig.read_bytes())
            out = MERGED / rel
            article_stack.write_stacked(out, raw.decode("utf-8", errors="replace"), original)
            merged += 1
            rows.append([str(rel), sha, "merged", str(out.relative_to(OUTBOX))])

    MERGED.mkdir(parents=True, exist_ok=True)
    report = MERGED / f"_MERGE_REPORT_{datetime.now():%Y%m%d_%H%M%S}.csv"
    with open(report, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["api_output", "source_sha256", "result", "merged_file"])
        w.writerows(rows)
    log(f"\nmerged {merged} · original not found {missing} · no sha recorded {no_sha} · already merged {already}")
    log(f"output  {MERGED}")
    log(f"report  {report}")


if __name__ == "__main__":
    main()
