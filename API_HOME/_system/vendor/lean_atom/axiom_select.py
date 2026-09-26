"""
axiom_select.py - From the harvest manifest, pick the files that declare axioms,
find the Lake project each came from, and set aside Mathlib test copies.

    python axiom_select.py <ALL_LEAN4 folder>      -> writes axiom_files.json next to this script
"""

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
MATHLIB = os.environ.get("ONE_MENU_PATH_MATHLIB_CACHE", "")


def project_of(path):
    d = os.path.dirname(path)
    for _ in range(12):
        if os.path.exists(os.path.join(d, "lean-toolchain")) and (
                os.path.exists(os.path.join(d, "lakefile.lean")) or os.path.exists(os.path.join(d, "lakefile.toml"))):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent
    return None


def mathlib_names():
    names = set()
    for sub in ("MathlibTest", "Mathlib", "Archive"):
        for dp, _, fn in os.walk(os.path.join(MATHLIB, sub)):
            names.update(f.lower() for f in fn if f.endswith(".lean"))
    return names


def base(name):
    name = re.sub(r"__v\d+(?=\.lean$)", "", name)
    return re.sub(r"^[0-9A-F]{6}_", "", name).lower()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    harvest = sys.argv[1]
    rows = json.load(open(os.path.join(harvest, "MANIFEST.json"), encoding="utf-8"))["files"]
    lib = mathlib_names()
    out, dropped = [], 0
    for r in rows:
        if not r["axioms"]:
            continue
        origins = [o for o in r["origins"] if os.path.exists(o)] or r["origins"]
        proj = next((p for p in (project_of(o) for o in origins) if p), None)
        try:
            text = open(origins[0], encoding="utf-8", errors="replace").read()
        except OSError:
            text = ""
        reason = ("mathlib_test_guard_msgs" if "#guard_msgs" in text
                  else "same_name_as_mathlib_file" if base(r["file"]) in lib else None)
        dropped += bool(reason)
        out.append({"file": r["file"], "sha256": r["sha256"], "origins": origins, "project": proj,
                    "axioms": r["axioms"], "theorems": r["theorems"], "sorry": r["sorry_lines"],
                    "version_rank": r["version_rank"], "versions_of_name": r["versions_of_name"],
                    "copies": r["copies"], "newest": r["newest_copy_date"], "library_reason": reason})
    json.dump(out, open(HERE / "axiom_files.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    keep = [o for o in out if not o["library_reason"]]
    print(f"{len(out)} files declare axioms | {dropped} Mathlib test copies set aside | "
          f"{len(keep)} to compile ({sum(o['axioms'] for o in keep)} axiom declarations), "
          f"{sum(1 for o in keep if o['project'])} inside their own Lake project")


if __name__ == "__main__":
    main()
