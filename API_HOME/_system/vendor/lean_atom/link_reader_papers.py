import os  # ONE_MENU
"""
link_reader_papers.py - Add `reader_papers` links to proof pills and axiom pills
by matching source SHA-256 against the One Page Paper LEAN4 master list.
Read-only on the paper pipeline; only our pills are updated. Safe to re-run.

    python link_reader_papers.py
"""

import csv
import glob
import json
import sys
from pathlib import Path

import yaml

MASTER = os.path.join(os.environ.get("ONE_MENU_PATH_PIPELINE_API_ROOT", ""), "LEAN4", "OUTBOX", "03_MASTER_LIST", "MASTER_LIST.csv")
PROOF = os.path.join(os.environ.get("ONE_MENU_PATH_APIS_ROOT", ""), "CLAIMS_PROOFS_EVIDENCE", "PROOF")
AXIOMS = os.path.join(os.environ.get("ONE_MENU_PATH_APIS_ROOT", ""), "LEAN4", "AXIOMS")
AXIOM_FILES = Path(__file__).parent / "axiom_files.json"


class _D(yaml.SafeDumper):
    pass


_D.add_representer(str, lambda d, v: d.represent_scalar("tag:yaml.org,2002:str", v, style="|" if "\n" in v else None))


def papers_by_hash():
    out = {}
    for r in csv.DictReader(open(MASTER, encoding="utf-8-sig")):
        if r.get("paper_status") == "DRAFT_READY":
            out[r["source_sha256"].lower()] = {
                "paper": r.get("combined_paper") or r.get("reader_paper"),
                "paper_uuid": r.get("paper_uuid"),
                "status": "DRAFT_READY - AI reader paper, not a verification receipt",
            }
    return out


def update(path, papers):
    pill = yaml.safe_load(open(path, encoding="utf-8"))
    changed = pill.get("reader_papers") != papers
    if changed:
        pill["reader_papers"] = papers
        Path(path).write_text(yaml.dump(pill, Dumper=_D, sort_keys=False, allow_unicode=True, width=110),
                              encoding="utf-8")
    return changed


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    by_hash = papers_by_hash()
    print(f"{len(by_hash)} finished reader papers in the master list")

    n = linked = 0
    for p in glob.glob(PROOF + r"\**\*.pill.yaml", recursive=True):
        pill = yaml.safe_load(open(p, encoding="utf-8"))
        h = ((pill.get("veins") or {}).get("source") or {}).get("file_sha256")
        hit = by_hash.get((h or "").lower())
        n += 1
        if hit:
            linked += 1
            update(p, [hit])
    print(f"proof pills: {linked} of {n} have a reader paper")

    files = {a["file"]: a["sha256"].lower() for a in json.load(open(AXIOM_FILES, encoding="utf-8"))}
    n = linked = 0
    for p in glob.glob(AXIOMS + r"\pills\**\*.pill.yaml", recursive=True):
        pill = yaml.safe_load(open(p, encoding="utf-8"))
        hits = []
        for f in (pill.get("facts") or {}).get("appears_in", []):
            hit = by_hash.get(files.get(f["file"], ""))
            if hit and hit not in hits:
                hits.append({**hit, "file": f["file"]})
        n += 1
        if hits:
            linked += 1
            update(p, hits)
    print(f"axiom pills: {linked} of {n} have a reader paper")


if __name__ == "__main__":
    main()
