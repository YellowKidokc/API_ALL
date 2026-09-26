"""Migration 2026-09-22: Desktop\\APIs\\APIs (junk, left untouched) -> Desktop\\APIs\\MAIN (baseline).
Copies only. Never deletes or modifies anything in the junk folder. Writes a receipt of every copy."""
import hashlib, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

J = Path(r"\\192.168.2.50\h_hp\Desktop\APIs\APIs")
M = Path(r"\\192.168.2.50\h_hp\Desktop\APIs\MAIN")
APIS = ["CKG_EVIDENCE", "PYTHON", "LEAN4", "STORIES"]
INBOX = ["00_WAITING_NOT_PROCESSED", "01_PRIORITY", "02_SERIES", "03_GENERAL", "04_DUPLICATES"]
OUTBOX = ["01_ALL_PAPERS", "02_BY_GENERAL", "03_BY_SERIES", "04_BY_DOMAIN", "05_BY_CONTENT_TYPE", "06_BY_LAW"]
receipt = {"started": datetime.now(timezone.utc).isoformat(), "copied": [], "skipped_same": [], "conflicts": [],
           "notes": []}


def h(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cp(src, dst):
    src, dst = Path(src), Path(dst)
    if not src.exists():
        receipt["notes"].append(f"missing source: {src}")
        return
    if src.is_dir():
        for f in sorted(src.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and f.name != "queue.lock":
                cp(f, dst / f.relative_to(src))
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    sh = h(src)
    if dst.exists():
        if h(dst) == sh:
            receipt["skipped_same"].append(str(dst))
        else:
            receipt["conflicts"].append({"src": str(src), "dst": str(dst)})
        return
    shutil.copy2(src, dst)
    if h(dst) != sh:
        raise SystemExit(f"hash mismatch after copy: {dst}")
    receipt["copied"].append({"src": str(src), "dst": str(dst), "sha256": sh})


# 1. skeleton
for d in ["_BACKSIDE/CONFIG", "_BACKSIDE/TEMPLATES", "_BACKSIDE/REGISTRY", "_BACKSIDE/MIGRATION", "SCRIPTS/ckg",
          "SCRIPTS/series", "LIBRARY/CLAIM", "LIBRARY/EVIDENCE", "LIBRARY/PROOF", "LIBRARY/PROCESS",
          "SYSTEM_DOCS/SPECS", "SYSTEM_DOCS/REGISTRIES", "SYSTEM_DOCS/PROTOCOLS", "SYSTEM_DOCS/SESSION_LOGS"]:
    (M / d).mkdir(parents=True, exist_ok=True)
for api in APIS:
    (M / "_BACKSIDE" / api).mkdir(parents=True, exist_ok=True)
    for lane in INBOX:
        (M / api / "INBOX" / lane).mkdir(parents=True, exist_ok=True)
    for lane in OUTBOX:
        (M / api / "OUTBOX" / lane).mkdir(parents=True, exist_ok=True)

# 2. code — pick the newest workbench copy, record both hashes
wb_candidates = [J / "workbench", J / "CKG_EVIDENCE/_BACKSIDE/workbench", J / "STATIONS/CKG_EVIDENCE/_BACKSIDE/workbench"]
for f in ["ckg.py", "providers.py", "series_tools.py", "__init__.py"]:
    versions = {str(c / f): h(c / f) for c in wb_candidates if (c / f).exists()}
    receipt["notes"].append({"workbench_file": f, "versions": versions})
    newest = max((c / f for c in wb_candidates if (c / f).exists()), key=lambda p: p.stat().st_mtime)
    cp(newest, M / "SCRIPTS/ckg" / f)
cp(J / "CKG_EVIDENCE/STATIONS/SCRIPTS/paper_grader.py", M / "SCRIPTS/paper_grader.py")
cp(J / "OUTBOX/04_BY_SERIES/SCRIPTS", M / "SCRIPTS/series")
cp(J / "SYSTEM/TESTS/test_ckg.py", M / "_BACKSIDE/CKG_EVIDENCE/TESTS/test_ckg.py")

# 3. config + template check (policy hash must match existing STATE so finished papers are not re-billed)
cp(J / "CKG_EVIDENCE/_BACKSIDE/CONFIG/ckg.json", M / "_BACKSIDE/CONFIG/ckg.json")
tpl = M / "_BACKSIDE/TEMPLATES/CKG_ATOM_MASTER_TEMPLATE_v3.1_BLANK.md"
cp(J / "templates/CKG_ATOM_MASTER_TEMPLATE.md", tpl)
cfg = json.loads((M / "_BACKSIDE/CONFIG/ckg.json").read_text(encoding="utf-8"))
policy = hashlib.sha256(("ckg-runner/3.1.1" + tpl.read_text(encoding="utf-8") + "deepseek" + cfg["model"]).encode()).hexdigest()
state_policies = {p.name for p in (J / "SYSTEM/STATE/CKG").glob("*/*") if p.is_dir()}
receipt["policy_hash"] = policy
receipt["policy_matches_existing_state"] = policy in state_policies

# 4. CKG data (union of the three older layouts; identical files skipped, differing files logged)
B = M / "_BACKSIDE/CKG_EVIDENCE"
for src in [J / "SYSTEM/STATE/CKG", J / "CKG_EVIDENCE/_BACKSIDE/STATE/CKG"]:
    cp(src, B / "STATE/CKG")
for src in [J / "SYSTEM/ORIGINALS", J / "CKG_EVIDENCE/OUTBOX/08_ORIGINAL_PAPERS", J / "STATIONS/CKG_EVIDENCE/OUTBOX/08_ORIGINAL_PAPERS"]:
    cp(src, B / "SYSTEM/ORIGINALS")
for src in [J / "SYSTEM/RECORDS", J / "CKG_EVIDENCE/OUTBOX/06_JSON_RECORDS", J / "STATIONS/CKG_EVIDENCE/OUTBOX/06_JSON_RECORDS"]:
    cp(src, B / "SYSTEM/RECORDS")
cp(J / "NEEDS_ATTENTION", B / "NEEDS_ATTENTION")
cp(J / "OUTBOX/05_SESSION_REPORTS", B / "SESSION_REPORTS")
for src in [J / "LIBRARY", J / "CKG_EVIDENCE/OUTBOX/05_CLAIMS_EVIDENCE_AND_PROOFS", J / "STATIONS/CKG_EVIDENCE/OUTBOX/05_CLAIMS_EVIDENCE_AND_PROOFS"]:
    cp(src, M / "LIBRARY")
cp(J / "OUTBOX/01_ALL_PAPERS", M / "CKG_EVIDENCE/OUTBOX/01_ALL_PAPERS")
cp(J / "OUTBOX/00_MASTER_INDEX.csv", M / "CKG_EVIDENCE/OUTBOX/00_MASTER_INDEX.csv")
for f in ["00_COMPLETE_SERIES_READER.md", "00_SERIES_MANIFEST.json"]:
    cp(J / "OUTBOX/04_BY_SERIES/Numbers in God" / f, M / "CKG_EVIDENCE/OUTBOX/03_BY_SERIES/Numbers in God" / f)

# 5. live inbox — copy each unique file once (by hash)
seen = {}
for src_root in [J / "INBOX", J / "CKG_EVIDENCE/INBOX", J / "STATIONS/CKG_EVIDENCE/INBOX"]:
    for f in sorted(src_root.rglob("*")) if src_root.exists() else []:
        if not f.is_file():
            continue
        s = h(f)
        if s in seen:
            receipt["skipped_same"].append(f"inbox duplicate of {seen[s]}: {f}")
            continue
        seen[s] = str(f)
        cp(f, M / "CKG_EVIDENCE/INBOX" / f.relative_to(src_root))

# 6. station notes
for api in ["LEAN4", "STORIES"]:
    for f in ["FOLDER_LAYOUT.txt", "STATION_STATUS.txt"]:
        if (J / api / f).exists():
            cp(J / api / f, M / "_BACKSIDE" / api / f)

receipt["finished"] = datetime.now(timezone.utc).isoformat()
out = M / "_BACKSIDE/MIGRATION/MIGRATION_RECEIPT_2026-09-22.json"
out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(f"copied {len(receipt['copied'])} · identical skipped {len(receipt['skipped_same'])} · "
      f"conflicts {len(receipt['conflicts'])} · policy matches existing state: {receipt['policy_matches_existing_state']}")
for c in receipt["conflicts"]:
    print("CONFLICT", c)
for n in receipt["notes"]:
    print("NOTE", n)
