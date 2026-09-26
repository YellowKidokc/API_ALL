"""11_CKG_PHYSICS: is this theological event a mirror of a physics process (or the reverse)? Stage by stage, in order.

One whole-source call per item (API-11.1), after the CKG index for videos. engine/mirror.py enforces the levels:
STRUCTURAL needs 3+ cited stages in the same order and a transferring prediction; otherwise it is ANALOGY.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine import mirror  # noqa: E402
from engine.output import markdown_to_html, page  # noqa: E402
from engine.station import ItemResult, Station  # noqa: E402

LABEL = "11_CKG_PHYSICS"
HERE = Path(__file__).resolve().parent


def process(ctx):
    item = ctx.item
    kind = "VIDEO TRANSCRIPT (cite timestamps)" if item.kind == "video" else "TEXT (cite exact quotes)"
    prompt = (f"{(HERE / 'PROMPT.md').read_text(encoding='utf-8')}\n\nITEM: {item.id}\nTITLE: {item.title}\nSOURCE: {kind}\n\n{ctx.text}")
    reply = ctx.cached("mirror", lambda: ctx.call_json("physics_mirror", prompt))
    if not isinstance(reply, dict):
        return None
    mirrors = [mirror.enforce(m) for m in reply.get("mirrors", []) or [] if isinstance(m, dict)]
    for m in mirrors:
        ctx.step(f"mirror '{m.get('title', '')[:50]}': {m['level']} ({m['mapped_stages']}/{m['total_stages']} stages, directional {m['directional']})")
        for line in m["rules_applied"]:
            ctx.step(f"   rule: {line}")
    data = {"mirrors": mirrors, "physics_errors": reply.get("physics_errors", []), "focus_findings": reply.get("focus_findings", [])}
    md = render(item, data)
    stages = [{"mirror": m.get("title"), **s} for m in mirrors for s in m.get("stages", [])]
    summary = [{k: m.get(k) for k in ("title", "direction", "physics_process", "theological_event", "level_claimed", "level",
                                      "directional", "mapped_stages", "total_stages", "prediction", "law_axis", "confidence")} for m in mirrors]
    best = max((mirror.LEVELS.index(m["level"]) for m in mirrors), default=0)
    return ItemResult(data, page(f"Physics mirror: {item.title}", markdown_to_html(md)),
                      {"mirrors": summary, "stages": stages, "physics_errors": data["physics_errors"]}, md,
                      {"physics_mirrors": len(mirrors), "physics_best_level": mirror.LEVELS[best]})


def render(item, d) -> str:
    out = [f"# Physics mirror: {item.title}", ""]
    if not d["mirrors"]:
        out += ["No mirror between a theological event and a physics process was found.", ""]
    for m in d["mirrors"]:
        claimed = f" (claimed {m['level_claimed']})" if m["level_claimed"] != m["level"] else ""
        out += [f"## {m.get('title', '')}: **{m['level']}**{claimed}", "",
                f"*{m.get('direction', '')} · physics: {m.get('physics_process', '')} · theology: {m.get('theological_event', '')} · "
                f"directional: {m['directional']} · {m['mapped_stages']}/{m['total_stages']} stages mapped*", "",
                "| # | physics stage | theological counterpart | match | where |", "|---|---|---|---|---|"]
        out += [f"| {s.get('n')} | {s.get('physics', '')} | {s.get('theology', '')} | {s.get('match', '')} | {s.get('timestamp', '')} |"
                for s in m.get("stages", [])]
        out += ["", f"**Prediction that transfers:** {m.get('prediction') or '(none stated)'}"]
        if m.get("breaks"):
            out += ["", "**Where it breaks:**"] + [f"- {b}" for b in m["breaks"]]
        if m.get("law_axis"):
            out += ["", f"**Law axis:** {m['law_axis']}"]
        if m["rules_applied"]:
            out += ["", "**Rules applied:**"] + [f"- {x}" for x in m["rules_applied"]]
        out += [""]
    if d["physics_errors"]:
        out += ["## Physics the speaker got wrong", ""] + [f"- [{e.get('timestamp', '')}] {e.get('claim')} → {e.get('correction')}" for e in d["physics_errors"]]
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(Station(LABEL, kind="both").run(process))
