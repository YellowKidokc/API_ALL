#!/usr/bin/env python3
"""Build rebuildable Domain, Subject/Claim, and Evidence views for the OUTBOX.

The authoritative paper always remains in ``00_ALL_PROCESSED_ARTICLES``.
This program only creates byte-for-byte copies in discovery views and records
each route.  It never moves, rewrites, or promotes a paper.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from organize_and_retake_folders import (
    OUTBOX, clean_title, folder_label, match_domains, parse_metadata, safe_copy,
    unc_path, unique_labels,
)

MASTER = OUTBOX / "00_ALL_PROCESSED_ARTICLES"
DOMAINS = OUTBOX / "01_CATEGORIZED_DOMAINS"
SUBJECTS = OUTBOX / "03_DISCOVERY_FACETS" / "02_PRECISE_SUBJECT"
EVIDENCE = OUTBOX / "02_EVIDENCE_MATRIX" / "00_EVIDENCE_VIEWS"
OPERATIONS = OUTBOX / "04_BROWSE_BY_TOPIC" / "00_PROVENANCE_AND_OPERATIONS"


def evidence_shelves(text: str) -> list[str]:
    """Route by the kind of warrant discussed, not by a truth verdict."""
    lower = text.lower()
    shelves = ["01_Source_Bound_Case_Files"]
    signals = (
        ("02_Formal_and_Mathematical", ("lean", "z3", "theorem", "equation", "formal model", "axiom")),
        ("03_Empirical_and_Testable", ("experiment", "measurement", "data", "prediction", "replication", "empirical")),
        ("04_Logical_and_Philosophical", ("logic", "inference", "contradiction", "necessary", "counterexample", "argument")),
        ("05_Textual_and_Historical", ("scripture", "biblical", "hebrew", "greek", "citation", "source text", "history")),
        ("06_Theological_and_Interpretive", ("theology", "christ", "trinity", "god", "revelation", "logos")),
    )
    for folder, terms in signals:
        if any(term in lower for term in terms):
            shelves.append(folder)
    return shelves


def subject_labels(meta: dict) -> list[str]:
    labels = unique_labels(list(meta.get("subject_tags") or meta.get("tags") or []), limit=8)
    return labels or ["Needs_Subject_Review"]


def domain_labels(meta: dict, title: str, text: str) -> list[str]:
    explicit = unique_labels(list(meta.get("technical_domains") or []), limit=6)
    if explicit:
        return explicit
    # Existing high-resolution domain matcher remains the conservative fallback.
    return [folder_label(Path(item).parts[0]) for item in match_domains(f"{title}\n{text[:8000]}")]


def write_index(record_count: int, receipt_name: str) -> None:
    index = OUTBOX / "00_LIBRARY_START_HERE.md"
    index.write_text(
        "# Evidence Chain Outbox Library\n\n"
        "## The four ways to find a completed paper\n\n"
        "1. **00_ALL_PROCESSED_ARTICLES** — the authoritative completed paper set.\n"
        "2. **01_CATEGORIZED_DOMAINS** — one paper may appear in every justified broad domain.\n"
        "3. **03_DISCOVERY_FACETS/02_PRECISE_SUBJECT** — nuanced subjects and claims.\n"
        "4. **02_EVIDENCE_MATRIX/00_EVIDENCE_VIEWS** — evidence-type views; these do not make a claim proved.\n\n"
        "Every view contains a byte-for-byte copy of its master paper. The master paper remains the "
        "authoritative version; do not edit a routed copy. Candidate and source-boundary labels travel with it.\n\n"
        f"Last rebuild: {datetime.now(timezone.utc).isoformat()}  \n"
        f"Master papers routed: {record_count}  \n"
        f"Routing receipt: `04_BROWSE_BY_TOPIC/00_PROVENANCE_AND_OPERATIONS/{receipt_name}`\n",
        encoding="utf-8",
    )


def main() -> None:
    if not MASTER.exists():
        raise SystemExit(f"Missing master paper shelf: {MASTER}")
    sources = sorted(set(MASTER.rglob("*.knowledge.md")) | set(MASTER.rglob("*.epistemic.md")))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    records: list[dict] = []

    for source in sources:
        raw = source.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        meta = parse_metadata(text)
        title = clean_title(source, str(meta.get("title", "")), text)
        name = source.name
        routes: dict[str, list[str]] = {"domains": [], "subjects": [], "evidence": []}

        for label in domain_labels(meta, title, text):
            destination = DOMAINS / label / name
            safe_copy(source, destination)
            routes["domains"].append(str(destination))
        for label in subject_labels(meta):
            destination = SUBJECTS / label / name
            safe_copy(source, destination)
            routes["subjects"].append(str(destination))
        for label in evidence_shelves(text):
            destination = EVIDENCE / label / name
            safe_copy(source, destination)
            routes["evidence"].append(str(destination))

        records.append({
            "master": str(source), "sha256": hashlib.sha256(raw).hexdigest(),
            "title": title, "candidate_status": meta.get("status", "UNSPECIFIED"), **routes,
        })

    OPERATIONS.mkdir(parents=True, exist_ok=True)
    json_receipt = OPERATIONS / f"UNIFIED_LIBRARY_RECEIPT_{stamp}.json"
    csv_receipt = OPERATIONS / f"UNIFIED_LIBRARY_RECEIPT_{stamp}.csv"
    with open(unc_path(json_receipt), "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)
    with open(unc_path(csv_receipt), "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["master", "sha256", "title", "candidate_status", "domains", "subjects", "evidence"])
        writer.writeheader()
        for record in records:
            writer.writerow({key: "; ".join(value) if isinstance(value, list) else value for key, value in record.items()})

    write_index(len(records), csv_receipt.name)
    print(f"Routed {len(records)} master papers into Domain, Subject/Claim, and Evidence views.")
    print(f"Receipt: {csv_receipt}")


if __name__ == "__main__":
    main()
