"""
harvest_lean.py - Gather every distinct .lean file from many places into one folder.

Copies only; never moves or deletes a source. Identical files (same SHA-256)
are stored once with all their origins listed. Different files that share a
name are all kept as NAME.lean, NAME__v2.lean, ... (newest first).

Writes <dest>/MANIFEST.csv and <dest>/MANIFEST.json.

    python harvest_lean.py --dest "<folder>" SOURCE [SOURCE ...]
"""

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime

SKIP_DIRS = {".lake", ".git", "node_modules", "lake-packages", "__pycache__", ".pytest_cache",
             # Lean library dependencies, not your proofs (also when copied out of .lake)
             "packages", "batteries", "aesop", "Qq", "proofwidgets", "plausible",
             "LeanSearchClient", "importGraph", "Cli", "Mathlib", "MathlibTest", "Archive",
             "Counterexamples", ".elan", "lean-cache", "$Recycle.Bin", "$RECYCLE.BIN",
             "lean-atom-extractor", "System Volume Information", "Windows", "Program Files",
             "Program Files (x86)", "ProgramData", "AppData"}
SKIP_PREFIXES = ("mathlib", "_EXCLUDED_GENERATED_CACHE")
DECL = re.compile(r"^(?:@\[[^\]]*\]\s*)?(?:(?:private|protected|noncomputable|partial)\s+)*"
                  r"(theorem|lemma|def|structure|inductive|axiom|abbrev|class|instance)\s", re.M)
SORRY = re.compile(r"\bsorry\b")
# Mathlib, Batteries, Aesop, Lean core... all open with this licence header.
# Catches library copies however their folder was renamed.
LIBRARY_HEADER = re.compile(rb"Released under Apache 2\.0 license|Apache License, Version 2\.0", re.I)
COMMENTS = re.compile(r"/-.*?-/|--[^\n]*", re.S)


def lean_files(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS and not d.startswith(SKIP_PREFIXES)]
        for f in fn:
            if f.endswith(".lean"):
                yield os.path.join(dp, f)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--catalog", default=os.environ.get("ONE_MENU_PATH_LEAN_ROOT", ""),
                    help="project whose files count as already cataloged")
    ap.add_argument("sources", nargs="+")
    args = ap.parse_args()

    catalog = set()
    if os.path.isdir(args.catalog):
        for p in lean_files(args.catalog):
            catalog.add(hashlib.sha256(open(p, "rb").read()).hexdigest())

    by_hash = {}
    library_skipped = 0
    for src in args.sources:
        if not os.path.isdir(src):
            print(f"  skip (not found): {src}")
            continue
        n = lib = 0
        for p in lean_files(src):
            try:
                data = open(p, "rb").read()
            except OSError as e:
                print(f"  ! {p}: {e}")
                continue
            if LIBRARY_HEADER.search(data[:1500]):
                lib += 1
                continue
            h = hashlib.sha256(data).hexdigest()
            entry = by_hash.setdefault(h, {"sha256": h, "name": os.path.basename(p), "origins": [],
                                           "mtime": 0, "data": data})
            entry["origins"].append(p)
            entry["mtime"] = max(entry["mtime"], os.path.getmtime(p))
            n += 1
        library_skipped += lib
        print(f"  {n:5d} .lean files  {src}" + (f"   ({lib} library files skipped)" if lib else ""))

    # Different contents that share a file name become versions, newest first.
    by_name = defaultdict(list)
    for e in by_hash.values():
        by_name[e["name"].lower()].append(e)  # Windows names are case-insensitive

    os.makedirs(args.dest, exist_ok=True)
    rows = []
    for name, entries in sorted(by_name.items()):
        entries.sort(key=lambda e: -e["mtime"])
        stem, ext = os.path.splitext(entries[0]["name"])
        for i, e in enumerate(entries, 1):
            out_name = f"{stem}{ext}" if i == 1 else f"{stem}__v{i}{ext}"
            dest = os.path.join(args.dest, out_name)
            if not (os.path.exists(dest) and open(dest, "rb").read() == e["data"]):
                with open(dest, "wb") as fh:
                    fh.write(e["data"])
            text = COMMENTS.sub("", e["data"].decode("utf-8", errors="replace"))
            kinds = defaultdict(int)
            for m in DECL.finditer(text):
                kinds[m.group(1)] += 1
            rows.append({
                "file": out_name,
                "versions_of_name": len(entries),
                "version_rank": i,
                "sha256": e["sha256"],
                "newest_copy_date": datetime.fromtimestamp(e["mtime"]).strftime("%Y-%m-%d %H:%M"),
                "already_cataloged": e["sha256"] in catalog,
                "copies": len(e["origins"]),
                "theorems": kinds["theorem"] + kinds["lemma"],
                "defs": kinds["def"] + kinds["abbrev"],
                "structures": kinds["structure"] + kinds["inductive"] + kinds["class"],
                "axioms": kinds["axiom"],
                "sorry_lines": len(SORRY.findall(text)),
                "origins": e["origins"],
            })

    with open(os.path.join(args.dest, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump({"harvested_at": datetime.now().isoformat(timespec="seconds"),
                   "sources": args.sources, "files": rows}, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(args.dest, "MANIFEST.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[k for k in rows[0] if k != "origins"] + ["origins"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "origins": " | ".join(r["origins"])})

    total_copies = sum(len(e["origins"]) for e in by_hash.values())
    print(f"\n{total_copies} files found -> {len(by_hash)} distinct -> {args.dest}")
    print(f"  library files (Apache-licensed Mathlib etc.) skipped: {library_skipped}")
    print(f"  names with several versions: {sum(1 for v in by_name.values() if len(v) > 1)}")
    print(f"  already cataloged: {sum(r['already_cataloged'] for r in rows)} | new: {sum(not r['already_cataloged'] for r in rows)}")
    print(f"  files with sorry: {sum(1 for r in rows if r['sorry_lines'])} | declared axioms: {sum(r['axioms'] for r in rows)}")


if __name__ == "__main__":
    main()
