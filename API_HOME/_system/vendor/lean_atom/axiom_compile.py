"""
axiom_compile.py - Compile every axiom-declaring harvested Lean file and record,
per theorem, which axioms it actually rests on (#print axioms).

Input : axiom_files.json (from the harvest manifest)
Output: <out>/compile/<file>.json   one result per file
        <out>/00_COMPILE_SUMMARY.json

Each file is built inside its own Lake project with that project's toolchain
when it came from one; otherwise in the main project's environment (recorded
as env = fallback). Sources are never modified: a temporary copy with
`#print axioms` lines appended is compiled from the scratch folder.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lean_atom.scanner.extractor import LeanExtractor  # noqa: E402

MAIN_ENV = os.environ.get("ONE_MENU_PATH_LEAN_ROOT", "")
PRINT_RE = re.compile(r"'([^']+)' (?:depends on axioms: \[(.*?)\]|does not depend on any axioms)", re.S)
ERR_RE = re.compile(r"^(?:.*?):(\d+):\d+: error", re.M)
STANDARD = {"propext", "Classical.choice", "Quot.sound"}


def run(cmd, cwd, timeout):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        return p.returncode, p.stdout + "\n" + p.stderr
    except subprocess.TimeoutExpired as e:
        return -1, f"TIMEOUT after {timeout}s\n{(e.stdout or '')}"
    except FileNotFoundError as e:
        return -2, str(e)


def compile_one(item, out_dir, scratch, timeout):
    name = item["file"]
    src = next((o for o in item["origins"] if os.path.exists(o)), None)
    result = {"file": name, "sha256": item["sha256"], "source_used": src,
              "project": item["project"], "env": "own_project" if item["project"] else "fallback_main_env",
              "checked_at": datetime.now(timezone.utc).isoformat()}
    if not src:
        result.update(status="SOURCE_MISSING")
        return result
    text = open(src, encoding="utf-8", errors="replace").read()
    decls = LeanExtractor.extract_declarations(text, name)
    theorems = [d for d in decls if d["declaration_kind"] in ("theorem", "lemma")]
    axioms = [d for d in decls if d["declaration_kind"] == "axiom"]
    n_lines = text.count("\n") + 1
    probe = text + "\n\n" + "\n".join(f"#print axioms {t['fully_qualified_name']}" for t in theorems) + "\n"

    root = item["project"] or MAIN_ENV
    tmp = Path(scratch) / f"probe_{item['sha256'][:12]}.lean"
    tmp.write_text(probe, encoding="utf-8")
    code, output = run(["lake", "env", "lean", str(tmp)], root, timeout)
    env_note = None
    if item["project"] and code != 0 and not ERR_RE.search(output):
        # The file's own project could not even start (missing package, bad
        # lakefile). Record that, then try the main project's environment.
        env_note = next((ln for ln in output.splitlines() if "error" in ln.lower()), output[:300]).strip()
        root = MAIN_ENV
        result["env"] = "fallback_main_env_after_project_error"
        code, output = run(["lake", "env", "lean", str(tmp)], root, timeout)
    try:
        toolchain = open(os.path.join(root, "lean-toolchain")).read().strip()
    except OSError:
        toolchain = None

    err_lines = [int(m.group(1)) for m in ERR_RE.finditer(output)]
    source_errors = [l for l in err_lines if l <= n_lines]
    deps = {}
    for m in PRINT_RE.finditer(output):
        listed = [a.strip() for a in (m.group(2) or "").replace("\n", " ").split(",") if a.strip()]
        deps[m.group(1)] = listed
    if code == -1:
        status = "TIMEOUT"
    elif code == -2:
        status = "TOOLCHAIN_MISSING"
    elif source_errors:
        status = "FAILED"
    elif code != 0 and not err_lines:
        status = "ENV_ERROR"          # Lean never got to the file
    elif code != 0:
        status = "PASSED_WITH_PROBE_ERRORS"   # source fine; some #print lines could not resolve
    else:
        status = "PASSED"
    first_error = next((ln for ln in output.splitlines() if "error" in ln.lower()), None)
    result.update(
        status=status, exit_code=code, toolchain=toolchain,
        command=f"lake env lean <probe of {name}>  (cwd {root})",
        theorem_count=len(theorems), axiom_count=len(axioms),
        axioms=[{"name": a["fully_qualified_name"], "statement": a["formal_statement"],
                 "lines": [a["start_line"], a["end_line"]]} for a in axioms],
        theorems=[{"name": t["fully_qualified_name"],
                   "axioms_used": deps.get(t["fully_qualified_name"]),
                   "uses_sorry": "sorryAx" in (deps.get(t["fully_qualified_name"]) or []),
                   "custom_axioms": [a for a in (deps.get(t["fully_qualified_name"]) or []) if a not in STANDARD and a != "sorryAx"]}
                  for t in theorems],
        first_error=first_error[:400] if first_error else None,
        own_project_env_error=env_note,
        probe_resolved=sum(1 for t in theorems if t["fully_qualified_name"] in deps),
    )
    tmp.unlink(missing_ok=True)
    (Path(out_dir) / "compile").mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "compile" / (name[:-5] + ".json")).write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out_dir = sys.argv[1]
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    items = [i for i in json.load(open(Path(__file__).parent / "axiom_files.json", encoding="utf-8"))
             if not i.get("library_reason")]
    scratch = tempfile.mkdtemp(prefix="axiom_probe_")
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(compile_one, it, out_dir, scratch, 900): it for it in items}
        for n, f in enumerate(futs, 1):
            it = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = {"file": it["file"], "status": "ERROR", "error": str(e)}
            results.append(r)
            print(f"  [{n}/{len(items)}] {r['status']:<17} {r['file']}  "
                  f"({r.get('axiom_count', '?')} axioms, {r.get('theorem_count', '?')} theorems)", flush=True)
    summary = {"generated_at": datetime.now(timezone.utc).isoformat(), "files": len(results),
               "status_counts": {}, "results": [{k: r.get(k) for k in ("file", "status", "env", "toolchain",
                                                                    "axiom_count", "theorem_count", "first_error")}
                                                for r in results]}
    for r in results:
        summary["status_counts"][r["status"]] = summary["status_counts"].get(r["status"], 0) + 1
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "00_COMPILE_SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False),
                                                            encoding="utf-8")
    print("\n", summary["status_counts"])


if __name__ == "__main__":
    main()
