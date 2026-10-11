"""Pull the station folders out of the nested API containers into the main folder, numbered.

  python pull_up_api_folders.py "<your pipeline-workflows folder>"            preview only (nothing moves)
  python pull_up_api_folders.py "<your pipeline-workflows folder>" --apply    move, and write PULL_UP_LOG.csv
  python pull_up_api_folders.py "<your pipeline-workflows folder>" --undo     put everything back from the log

Default containers (relative to the main folder): API\\API, API\\API 2, API\\API 3. Every station folder inside them
moves to <main>\\NN_<name> (numbered in order, --no-number keeps names). Pipeline plumbing folders (INBOX, OUTBOX,
PROCESSED, ERRORS, RECEIPTS, RETRY, REVIEW, PROCESSING, SCRIPTS, PYTHON, _BACKSIDE ...) stay where they are.
API\\Open-AI-CALL-OBS-Plugin-Final-Claude is renamed to QUICK_CALL_OLD (the new DeepSeek QUICK_CALL lives in API_HOME).

Nothing is overwritten: a name that already exists is reported and skipped. Folders whose scripts point at their
parent folder (..\\ or ../) are flagged, because moving them can break those paths.
"""
import argparse
import csv
import re
import shutil
import sys
from pathlib import Path

CONTAINERS = [r"API\API", r"API\API 2", r"API\API 3"]
QUICK = (r"API\Open-AI-CALL-OBS-Plugin-Final-Claude", "QUICK_CALL_OLD")
PLUMBING = {"inbox", "outbox", "processed", "processing", "errors", "receipts", "retry", "review", "scripts",
            "python", "_backside", "pipeline", "__pycache__", ".git", "logs", "_clean_outputs"}
PARENT_REF = re.compile(r"(\.\.[\\/])|(parents\[\d\])|(%~dp0\.\.)")
LOG = "PULL_UP_LOG.csv"


def rel(p: str) -> Path:
    return Path(*re.split(r"[\\/]", p))


def parent_refs(folder: Path) -> int:
    hits = 0
    for f in folder.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".py", ".bat", ".ps1", ".cmd"):
            try:
                hits += bool(PARENT_REF.search(f.read_text(encoding="utf-8", errors="replace")))
            except OSError:
                pass
    return hits


def plan(root: Path, number: bool) -> list[dict]:
    moves, seen = [], {p.name.lower() for p in root.iterdir()}
    candidates = []
    for c in CONTAINERS:
        box = root / rel(c)
        if not box.is_dir():
            continue
        for d in sorted(p for p in box.iterdir() if p.is_dir()):
            if d.name.lower() in PLUMBING:
                continue
            candidates.append((c, d))
    names: dict[str, int] = {}
    for n, (c, d) in enumerate(candidates, 1):
        twin = names.setdefault(d.name.lower(), n)
        name = f"{n:02d}_{d.name}" if number else d.name
        target = root / name
        status = "move"
        if name.lower() in seen or target.exists():
            status = "SKIP: name already taken"
        seen.add(name.lower())
        moves.append({"from": str(d), "to": str(target), "container": c, "status": status,
                      "parent_refs": parent_refs(d), "twin": f"{twin:02d}" if twin != n else ""})
    quick = root / rel(QUICK[0])
    if quick.is_dir():
        target = root / QUICK[1]
        moves.append({"from": str(quick), "to": str(target), "container": "API", "parent_refs": 0,
                      "twin": "", "status": "SKIP: name already taken" if target.exists() else "move"})
    return moves


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="the main folder, your pipeline-workflows folder")
    ap.add_argument("--apply", action="store_true", help="really move (default: preview)")
    ap.add_argument("--undo", action="store_true", help="move everything in PULL_UP_LOG.csv back")
    ap.add_argument("--no-number", action="store_true", help="keep the names as they are")
    a = ap.parse_args()
    root = Path(a.root)
    if not root.is_dir():
        print(f"No folder {root}")
        return 2
    log = root / LOG
    if a.undo:
        rows = list(csv.DictReader(open(log, encoding="utf-8"))) if log.exists() else []
        for r in reversed(rows):
            if Path(r["to"]).exists() and not Path(r["from"]).exists():
                shutil.move(r["to"], r["from"])
                print(f"back  {r['to']}  ->  {r['from']}")
        log.rename(log.with_suffix(".undone.csv")) if rows else None
        return 0
    moves = plan(root, not a.no_number)
    if not moves:
        print("Nothing to pull up: no station folders found in " + ", ".join(CONTAINERS))
        return 0
    for m in moves:
        flag = f"   ! {m['parent_refs']} script(s) refer to their parent folder" if m["parent_refs"] else ""
        flag += f"   ! same name as {m['twin']}: compare the two before deleting either" if m.get("twin") else ""
        print(f"{'MOVE' if m['status'] == 'move' else m['status']:<26} {m['from']}\n{'':26} -> {m['to']}{flag}")
    todo = [m for m in moves if m["status"] == "move"]
    print(f"\n{len(todo)} to move, {len(moves) - len(todo)} skipped, "
          f"{sum(1 for m in todo if m['parent_refs'])} flagged (check them after the move).")
    if not a.apply:
        print("Preview only. Add --apply to move; --undo puts everything back.")
        return 0
    with open(log, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["from", "to", "container", "status", "parent_refs", "twin"])
        if fh.tell() == 0:
            w.writeheader()
        for m in todo:
            shutil.move(m["from"], m["to"])
            w.writerow(m)
            fh.flush()                     # one for one: the log always matches what moved
            print(f"moved {Path(m['from']).name} -> {Path(m['to']).name}")
    print(f"Done. Log: {log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
