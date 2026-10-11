"""41_STORY: pass 1 per paper (parallel) -> pass 2 per series -> pass 3 memorable lines, only when coherent.

--force-lines overrides the gate. Pass 3 runs in groups of 15 paragraphs, in order, each group seeing the
through-line and the lines already written, so later lines don't repeat earlier ones.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.output import markdown_to_html, page  # noqa: E402
from engine.station import Context, ItemResult, Station  # noqa: E402
from engine.text import segment  # noqa: E402

LABEL = "41_STORY"
HERE = Path(__file__).resolve().parent
GROUP = 15


def paras_text(paragraphs) -> str:
    return "\n\n".join(f"[{p.id}] {p.text}" for p in paragraphs)


def pass1(ctx) -> dict | None:
    paragraphs, _ = segment(ctx.text)
    ctx.step(f"pass 1: {len(paragraphs)} paragraphs")
    prompt = f"{(HERE / 'PASS1.md').read_text(encoding='utf-8')}\n\nIDS: {', '.join(p.id for p in paragraphs)}\n\nPAPER:\n{paras_text(paragraphs)}"
    data = ctx.cached("pass1", lambda: ctx.call_json("story_paper", prompt))
    return data if isinstance(data, dict) else None


def main() -> int:
    station = Station(LABEL, prompt_files=["PASS1.md", "PASS2.md", "PASS3.md"],
                      extra_args=lambda p: p.add_argument("--force-lines", action="store_true", help="write lines even when not coherent"))
    items = station.items()
    if station.args.dry_run or not items:
        return station.run(lambda ctx: None, items)
    # Phase A: pass 1 for every paper, in parallel.
    first: dict[str, tuple[dict | None, Context]] = {}

    def a(item):
        ctx = Context(station, item)
        first[item.id] = (pass1(ctx), ctx)
    station.say(f"41_STORY phase A: pass 1 for {len(items)} paper(s)")
    Context(station, None).parallel(a, items, width=station.args.workers)
    # Phase B: pass 2 per series.
    series = defaultdict(list)
    for item in items:
        series[item.meta.get("series") or "(no series)"].append(item)
    series_result: dict[str, dict | None] = {}
    for name, members in series.items():
        if name == "(no series)" or len(members) < 2:
            series_result[name] = None
            station.say(f"41_STORY phase B: series '{name}': {len(members)} paper(s), no series pass")
            continue
        members.sort(key=lambda i: (i.meta.get("series_order") or 0, i.title))
        blocks = []
        for m in members:
            ps, _ = segment(m.text())
            blocks.append({"id": m.id, "title": m.title, "pass1": first[m.id][0],
                           "first_paragraph": ps[0].text[:1500] if ps else "", "last_paragraph": ps[-1].text[:1500] if ps else ""})
        ctx = first[members[0].id][1]
        prompt = f"{(HERE / 'PASS2.md').read_text(encoding='utf-8')}\n\nSERIES: {name}\nORDER: {', '.join(m.id for m in members)}\n\n{json.dumps(blocks, ensure_ascii=False)}"
        station.say(f"41_STORY phase B: series '{name}': {len(members)} papers")
        series_result[name] = ctx.cached(f"pass2-{name}", lambda: ctx.call_json("story_series", prompt),
                                         extra=",".join(m.source_hash[:8] for m in members))

    # Phase C: per paper, lines if gated, then write.
    def c(ctx):
        data1, ctx1 = first[ctx.item.id]
        ctx.receipts, ctx.calls, ctx.steps, ctx.errors = ctx1.receipts, ctx1.calls, ctx1.steps, ctx1.errors
        if data1 is None:
            return None
        sname = ctx.item.meta.get("series") or "(no series)"
        s2 = series_result.get(sname)
        paper_ok = data1.get("verdict") == "COHERENT"
        series_ok = s2 is None or s2.get("verdict") == "COHERENT"
        lines, signature, series_line = [], [], ""
        if (paper_ok and series_ok) or station.args.force_lines:
            paragraphs, _ = segment(ctx.text)
            groups = [paragraphs[i:i + GROUP] for i in range(0, len(paragraphs), GROUP)]
            ctx.step(f"pass 3: gate open ({'forced' if station.args.force_lines and not (paper_ok and series_ok) else 'coherent'}), {len(groups)} group(s)")
            for n, group in enumerate(groups):
                last = n == len(groups) - 1
                prompt = (f"{(HERE / 'PASS3.md').read_text(encoding='utf-8')}\n\nTHROUGH-LINE: {data1.get('through_line', '')}\n"
                          f"PREVIOUS LINES: {json.dumps(lines, ensure_ascii=False)}\nLAST GROUP: {'yes' if last else 'no'}\n"
                          f"IDS: {', '.join(p.id for p in group)}\n\nPARAGRAPHS:\n{paras_text(group)}")
                reply = ctx.cached(f"pass3-{group[0].id}", lambda: ctx.call_json("story_lines", prompt), extra=json.dumps(lines))
                if isinstance(reply, dict):
                    lines += reply.get("lines", [])
                    if last:
                        signature, series_line = reply.get("signature", []), reply.get("series_line", "")
        else:
            ctx.step(f"pass 3: gate closed (paper {data1.get('verdict')}, series {s2.get('verdict') if s2 else 'n/a'}); the fix list is the output")
        data = {"pass1": data1, "series": {"name": sname, "result": s2}, "lines": lines, "signature": signature, "series_line": series_line}
        md = render(ctx.item, data)
        if lines:
            by = {x.get("id"): x.get("line") for x in lines}
            paragraphs, _ = segment(ctx.text)
            copy = "\n\n".join((f"> **{by[p.id]}**\n\n" if by.get(p.id) else "") + p.text for p in paragraphs)
            (ctx.item.folder / "01_NOTES" / f"{ctx.item.id}_LINES.md").write_text(copy, encoding="utf-8")
            ctx.step("wrote the pull-quote copy to 01_NOTES (original untouched)")
        return ItemResult(data, page(f"Story: {ctx.item.title}", markdown_to_html(md)),
                          {"paragraphs": data1.get("paragraphs", []), "lines": lines, "fixes": [{"fix": f} for f in data1.get("fixes", [])]},
                          md, {"story_hook_score": (data1.get("hook") or {}).get("score"), "story_verdict": data1.get("verdict")})

    station.per_item = False
    return station.run(c, items)


def render(item, d) -> str:
    p1 = d["pass1"]
    out = [f"# Story: {item.title}", "", f"**Verdict:** {p1.get('verdict')}   **Hook:** {(p1.get('hook') or {}).get('score')}/5", "",
           f"**Through-line:** {p1.get('through_line', '')}", "", f"**Landing:** {(p1.get('landing') or {}).get('verdict')}: {(p1.get('landing') or {}).get('reason', '')}", ""]
    if p1.get("fixes"):
        out += ["## Fixes", ""] + [f"- {f}" for f in p1["fixes"]] + [""]
    out += ["## Paragraphs", "", "| id | role | serves | reason |", "|---|---|---|---|"]
    out += [f"| {x.get('id')} | {x.get('role')} | {x.get('serves')} | {x.get('reason', '')} |" for x in p1.get("paragraphs", [])]
    if d["series"]["result"]:
        s = d["series"]["result"]
        out += ["", f"## Series: {d['series']['name']} ({s.get('verdict')})", "", s.get("through_line", "")]
    if d["lines"]:
        out += ["", "## Memorable lines", ""] + [f"- {x.get('id')}: {x.get('line')}" for x in d["lines"]]
        out += ["", "**Signature:** " + " / ".join(d["signature"]), f"**Series line:** {d['series_line']}"]
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(main())
