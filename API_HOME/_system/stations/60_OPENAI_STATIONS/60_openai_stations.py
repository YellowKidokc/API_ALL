"""60_OPENAI_STATIONS: the 23 api_call prompts, bundled so one whole-document call answers several.

  ONE_MENU.bat 60                              every default bundle, every paper
  python .../60_openai_stations.py --bundle grading --bundle claims
  python .../60_openai_stations.py --stations 05,17,21
  python .../60_openai_stations.py --list      show stations and bundles
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.output import markdown_to_html, page  # noqa: E402
from engine.station import ItemResult, Station  # noqa: E402

LABEL = "60_OPENAI_STATIONS"
HERE = Path(__file__).resolve().parent
CONF = json.loads((HERE / "bundles.json").read_text(encoding="utf-8"))
PROMPTS = {d.name[:2]: d for d in sorted((HERE / "prompts").iterdir()) if d.is_dir()}
BUNDLE_TEMPLATE = """You are running several analysis stations over the SAME document in one pass. Each station below has its own
instructions. Do every station completely and independently, exactly as its instructions say; do not shorten one because
others are present. Return ONE JSON object whose keys are exactly: {keys}. The value for each key is that station's full
output: a JSON object when the station asks for JSON, otherwise a markdown string.
KEYS: {keys}

{blocks}

DOCUMENT:
{document}"""


def args(p):
    p.add_argument("--bundle", action="append", default=[], help="bundle name(s) from bundles.json")
    p.add_argument("--stations", default="", help="comma-separated station numbers, e.g. 05,17")
    p.add_argument("--list", action="store_true", help="list stations and bundles and exit")


def plan(station) -> list[tuple[str, list[str], bool]]:
    a = station.args
    bundles = CONF["bundles"]
    if a.stations:
        wanted = [s.strip().zfill(2) for s in a.stations.split(",") if s.strip()]
        return [("custom", wanted, False)]
    names = a.bundle or list(bundles)
    return [(n, bundles[n]["stations"], bool(bundles[n].get("after"))) for n in names]


def chunks(stations: list[str], cap: int) -> list[list[str]]:
    weights, default = CONF.get("weights", {}), CONF.get("default_weight", 1500)
    out, current, load = [], [], 0
    for s in stations:
        w = weights.get(s, default)
        if current and load + w > cap:
            out.append(current)
            current, load = [], 0
        current.append(s)
        load += w
    return out + ([current] if current else [])


def key(nn: str) -> str:
    return PROMPTS[nn].name


def process(ctx):
    station = ctx.station
    cap = int(station.settings.get("output_token_cap", 8000))
    jobs, after = [], []
    for name, members, is_after in plan(station):
        for part in chunks([m for m in members if m in PROMPTS], cap):
            (after if is_after else jobs).append((name, part))
    ctx.step(f"{len(jobs)} bundled call(s) now" + (f", {len(after)} after them" if after else "") + ": " +
             "; ".join(f"{n}[{','.join(p)}]" for n, p in jobs + after))
    results: dict[str, object] = {}

    def run(job, context: str = ""):
        name, part = job
        keys = [key(nn) for nn in part]
        blocks = "\n\n".join(f"### STATION {key(nn)}\n{(PROMPTS[nn] / 'prompt.txt').read_text(encoding='utf-8')}" for nn in part)
        prompt = BUNDLE_TEMPLATE.format(keys=", ".join(keys), blocks=blocks, document=ctx.text) + context
        task = f"oa_bundle_{name}" if name != "custom" else f"oa_{part[0]}"
        data = ctx.cached(f"bundle-{'-'.join(part)}", lambda: ctx.call_json(task, prompt, max_tokens=cap), extra=hashlib.sha256(context.encode()).hexdigest()[:16])
        if ctx.calls:
            ctx.calls[-1]["answers_goals"] = [f"API-60.{nn}" for nn in part]
        got = {}
        for k in keys:
            if isinstance(data, dict) and k in data:
                got[k] = data[k]
            else:
                ctx.warnings.append(f"{k}: missing from the bundle reply")
        ctx.step(f"bundle {name}: {len(got)}/{len(keys)} station output(s) back")
        return got

    for got in ctx.parallel(run, jobs, width=len(jobs) or 1):
        results.update(got)
    for job in after:
        context = "\n\nOUTPUTS OF THE OTHER STATIONS (reference context):\n" + json.dumps(results, ensure_ascii=False)[:120000]
        results.update(run(job, context))
    if not results:
        return None
    md = ["# api_call stations", ""]
    for k, v in results.items():
        md += [f"## {k}", "", v if isinstance(v, str) else "```json\n" + json.dumps(v, indent=2, ensure_ascii=False)[:20000] + "\n```", ""]
    md = "\n".join(md)
    rows = [{"station": k, "type": "markdown" if isinstance(v, str) else "json", "size": len(json.dumps(v))} for k, v in results.items()]
    return ItemResult(results, page(f"api_call stations: {ctx.item.title}", markdown_to_html(md)), {"stations": rows}, md)


def main() -> int:
    station = Station(LABEL, extra_args=args, prompt_files=["bundles.json", "prompts/*/prompt.txt"])
    if station.args.list:
        for nn, d in PROMPTS.items():
            print(f"  {nn}  {d.name}")
        for name, b in CONF["bundles"].items():
            print(f"  bundle {name:<14} {' '.join(b['stations'])}  {b.get('why', '')}")
        return 0
    return station.run(process)


if __name__ == "__main__":
    raise SystemExit(main())
