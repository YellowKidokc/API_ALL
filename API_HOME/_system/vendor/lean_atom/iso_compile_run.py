import json,sys,tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,".")
import axiom_compile as ac
out=sys.argv[1]; items=json.load(open("iso_files.json",encoding="utf-8")); s=tempfile.mkdtemp()
with ThreadPoolExecutor(3) as p:
    for r in p.map(lambda it: ac.compile_one(it,out,s,900), items):
        th=r.get("theorems") or []
        print(f"{r['status']:<26} {r['env']:<40} thm {r.get('theorem_count')} resolved {r.get('probe_resolved')} custom-axiom-thms {sum(1 for t in th if t['custom_axioms'])} sorry {sum(1 for t in th if t['uses_sorry'])}  {r['file']}  | {(r.get('first_error') or '')[:110]}", flush=True)
