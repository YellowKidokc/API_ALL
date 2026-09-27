"""Re-lay ALL_LEAN4 from its manifest with case-insensitive version names."""
import json, os, sys, csv, hashlib
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
D = os.environ.get("ONE_MENU_PATH_LEAN_HARVEST", "")
m = json.load(open(os.path.join(D, "MANIFEST.json"), encoding="utf-8"))
rows = m["files"]
groups = defaultdict(list)
for r in rows:
    base = r["file"].split("__v")[0] if "__v" in r["file"] else r["file"][:-5]
    base = base[:-5] if base.endswith(".lean") else base
    groups[base.lower()].append(r)
fixed = 0
for key, rs in groups.items():
    rs.sort(key=lambda r: r["newest_copy_date"], reverse=True)
    stem = os.path.splitext(os.path.basename(rs[0]["origins"][0]))[0]
    for i, r in enumerate(rs, 1):
        want = f"{stem}.lean" if i == 1 else f"{stem}__v{i}.lean"
        dest = os.path.join(D, want)
        data = None
        for o in r["origins"]:
            try:
                data = open(o, "rb").read(); break
            except OSError:
                continue
        if data is None or hashlib.sha256(data).hexdigest() != r["sha256"]:
            print("  ! cannot recover", want); continue
        if not (os.path.exists(dest) and open(dest, "rb").read() == data):
            open(dest, "wb").write(data); fixed += 1
        r["file"], r["version_rank"], r["versions_of_name"] = want, i, len(rs)
json.dump(m, open(os.path.join(D, "MANIFEST.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
with open(os.path.join(D, "MANIFEST.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=[k for k in rows[0] if k != "origins"] + ["origins"])
    w.writeheader()
    for r in rows: w.writerow({**r, "origins": " | ".join(r["origins"])})
on_disk = {n.lower() for n in os.listdir(D) if n.endswith(".lean")}
listed = {r["file"].lower() for r in rows}
stale = sorted(on_disk - listed)
print("rewritten:", fixed, "| manifest rows:", len(rows), "| lean on disk:", len(on_disk), "| stale names:", stale[:10])
