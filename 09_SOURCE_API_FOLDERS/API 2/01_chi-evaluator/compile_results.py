import json, glob, os, re

results = {}
for f in glob.glob(r"X:\06_ENGINES\01_chi-evaluator\OUTBOX\run_*\*deepseek*.json"):
    try:
        d = json.load(open(f, encoding="utf-8"))
        fname = os.path.basename(f)
        m = re.search(r"(\d{4})-(\w+)", fname)
        if not m:
            continue
        year = int(m.group(1))
        pres = m.group(2)
        ev = d.get("evaluation", d)
        chi = ev.get("static_chi", 0)
        verdict = ev.get("verdict", "?")
        fruit = ev.get("fruit_output", {}).get("fruit_score", 0)
        fruits = ev.get("fruit_output", {}).get("dominant_fruits", [])[:2]
        if year not in results or chi > results[year].get("chi", 0):
            results[year] = {"pres": pres, "chi": chi, "verdict": verdict, "fruit": fruit, "fruits": fruits}
    except:
        pass

print(f"{len(results)} unique years")
for y in sorted(results.keys()):
    r = results[y]
    fr = ", ".join(r["fruits"][:2]) if r["fruits"] else ""
    print(f"{y}  {r['pres']:12s}  chi={r['chi']:.6f}  fruit={r['fruit']:.3f}  {r['verdict']:22s}  {fr}")
