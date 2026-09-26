"""09_YT_DEEP: the detailed layer on top of 08. Whole transcript + the 08 summary + DETAIL.md, one call per video."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.focus import points_from_markdown  # noqa: E402
from engine.output import markdown_to_html, page  # noqa: E402
from engine.station import ItemResult, Station, latest_data  # noqa: E402

LABEL = "09_YT_DEEP"


def render(item, d) -> str:
    out = [f"# {item.title}: detailed analysis", ""]
    for a in d.get("arguments", []):
        out += [f"## {a.get('title', 'Argument')}  (strength {a.get('strength', '?')}/10)", ""]
        out += [f"- P{i + 1}: {p}" for i, p in enumerate(a.get("premises", []))]
        out += [f"- unstated: {p}" for p in a.get("unstated_premises", [])]
        out += [f"- **Conclusion**: {a.get('conclusion', '')}", f"- Why this strength: {a.get('strength_reason', '')}",
                f"- Stronger if: {a.get('make_stronger', '')}", ""]
    if d.get("unaddressed_objection"):
        out += ["## Strongest objection not addressed", "", d["unaddressed_objection"], ""]
    if d.get("claims_checked"):
        out += ["## Claims checked", ""] + [f"- [{c.get('timestamp', '')}] {c.get('claim')} (support: {c.get('support')}) {c.get('note', '')}" for c in d["claims_checked"]] + [""]
    if d.get("theophysics_relevance"):
        out += ["## Theophysics relevance", ""] + [f"- **{t.get('theme')}**: {t.get('note')}" for t in d["theophysics_relevance"]] + [""]
    if d.get("focus_findings"):
        out += ["## Focus findings", ""] + [f"- **{f.get('point')}**: {f.get('finding')}" for f in d["focus_findings"]]
    return "\n".join(out)


def process(ctx):
    station = ctx.station
    summary = latest_data(ctx.item, "08_YT_SUMMARY")
    if summary is None:
        ctx.warnings.append("no 08_YT_SUMMARY yet; running without the base layer (run 08 first for best results)")
    detail = points_from_markdown(station.dir / "DETAIL.md")
    body = (station.dir / "PROMPT.md").read_text(encoding="utf-8")
    prompt = (f"{body}\n\nDETAIL:\n" + "\n".join(f"- {d}" for d in detail) +
              f"\n\nBASE-LAYER SUMMARY (station 08):\n{json.dumps(summary, ensure_ascii=False) if summary else '(none)'}"
              f"\n\nITEM: {ctx.item.id}\nVIDEO: {ctx.item.title}\n\nTRANSCRIPT:\n{ctx.text}")
    extra = hashlib.sha256(json.dumps(summary, sort_keys=True).encode()).hexdigest()[:16] if summary else "none"
    data = ctx.cached("deep", lambda: ctx.call_json("yt_deep", prompt), extra=extra)
    if not isinstance(data, dict):
        return None
    md = render(ctx.item, data)
    return ItemResult(data, page(ctx.item.title, markdown_to_html(md)),
                      {"arguments": data.get("arguments", []), "claims": data.get("claims_checked", [])}, md,
                      headline={"yt_mean_argument_strength": round(sum(a.get("strength", 0) for a in data.get("arguments", [])) /
                                                                   max(1, len(data.get("arguments", []))), 2)})


if __name__ == "__main__":
    raise SystemExit(Station(LABEL, prompt_files=["DETAIL.md"], depends_on=["08_YT_SUMMARY"]).run(process))
