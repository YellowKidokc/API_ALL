"""48_TOPIC_SYNTHESIS: the best arguments for a topic across papers, videos and EVIDENCE companions.

  ONE_MENU.bat 48 --topic resurrection            (menu asks for the topic)
  ... --min 5 (relevance threshold) --top 20 (clusters to synthesize) --no-evidence --include-own

Output: <syntheses_root>/<topic>/02_RUNS/48_TOPIC_SYNTHESIS/<date>/ (json, md, html, xlsx, receipt, calls/, steps.log)
and <syntheses_root>/<topic>/03_REPORT/best_arguments.md|html (the latest, for reading).
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine import bridge  # noqa: E402
from engine.output import markdown_to_html, page  # noqa: E402
from engine.station import Context, ItemResult, Station  # noqa: E402
from engine.text import segment  # noqa: E402

LABEL = "48_TOPIC_SYNTHESIS"
HERE = Path(__file__).resolve().parent


def args(p):
    p.add_argument("--topic", help="e.g. resurrection")
    p.add_argument("--min", dest="minimum", type=int, default=5, help="relevance threshold 0-10 (default 5)")
    p.add_argument("--top", type=int, default=20, help="how many argument clusters to synthesize (default 20)")
    p.add_argument("--threshold", type=float, default=0.35, help="clustering similarity (default 0.35)")
    p.add_argument("--no-evidence", action="store_true", help="leave out EVIDENCE companions")
    p.add_argument("--include-own", action="store_true", help="include David's own papers as sources")


def main() -> int:
    station = Station(LABEL, kind="both", extra_args=args)
    a = station.args
    if not a.topic:
        print("48_TOPIC_SYNTHESIS: --topic is required (e.g. --topic resurrection)")
        return 2
    started = time.monotonic()
    root = bridge.topic_folder(a.topic)
    main_ctx = Context(station, None)
    main_ctx.who, main_ctx.cache_root = a.topic[:18], root / "_cache"
    step = main_ctx.step
    sources = bridge.external_sources(include_evidence=not a.no_evidence, include_own=a.include_own)
    if a.items:
        wanted = {str(Path(x).resolve()) for x in a.items}
        sources = [s for s in sources if s.item and str(s.item.folder.resolve()) in wanted]
    step(f"topic '{a.topic}': looking through {len(sources)} source(s) (tag: {bridge.topic_tag(a.topic) or 'none, using keywords'})")
    chosen = bridge.relevance(sources, a.topic, a.minimum)
    if a.limit:
        chosen = chosen[: a.limit]
    kinds = {}
    for s, _, _ in chosen:
        kinds[s.kind] = kinds.get(s.kind, 0) + 1
    step(f"{len(chosen)} source(s) score {a.minimum}+: " + ", ".join(f"{v} {k}" for k, v in kinds.items()))
    for s, score, method in chosen[:40]:
        step(f"   {score:>2} ({method}) {s.key} {s.title[:60]}")
    if a.dry_run or not chosen:
        if not chosen:
            print("Nothing scored high enough. Lower --min, or run 44 TAGGER first.")
        return 0

    # 1. extract arguments, one whole-source call each, all in parallel
    extract = (HERE / "EXTRACT.md").read_text(encoding="utf-8")
    arguments, failed = [], []

    def one(entry):
        src, score, _ = entry
        ctx = Context(station, src.item)
        ctx.who, ctx.cache_root = src.key[:18], root / "_cache"
        text = src.text()
        kind_note = "VIDEO TRANSCRIPT (cite timestamps)" if src.kind == "video" else "TEXT (cite exact quotes)"
        prompt = f"{extract}\n\nTOPIC: {a.topic}\nITEM: {src.key}\nSOURCE: {src.title} · {kind_note}\n\n{text}"
        data = ctx.cached(f"extract-{src.key.replace(':', '_')}", lambda: ctx.call_json("extract_arguments", prompt),
                          extra=src.source_hash + a.topic)
        found = []
        for arg in (data or {}).get("arguments", []) if isinstance(data, dict) else []:
            arg.update({"source_key": src.key, "source_title": src.title, "source_kind": src.kind, "relevance": score,
                        "citation": src.citation(str(arg.get("quote_or_ts", "")))})
            found.append(arg)
        ctx.step(f"{len(found)} argument(s) about '{a.topic}'")
        return src, found, ctx

    step(f"extracting arguments: {len(chosen)} parallel call(s), whole source each")
    for src, found, ctx in main_ctx.parallel(one, chosen, width=a.workers):
        arguments += found
        main_ctx.receipts += ctx.receipts
        main_ctx.calls += ctx.calls
        main_ctx.steps += ctx.steps
        if ctx.errors:
            failed.append(src.key)
            main_ctx.warnings += [f"{src.key}: {e}" for e in ctx.errors]
    step(f"{len(arguments)} argument(s) from {len(chosen) - len(failed)} source(s); {len(failed)} source(s) failed (listed in warnings)")
    if not arguments:
        main_ctx.errors.append("no arguments extracted")
        station.write(main_ctx, None, started, folder=root)
        return 1

    # 2. cross-reference locally
    clusters = bridge.cluster(arguments, a.threshold)
    step(f"cross-referenced into {len(clusters)} cluster(s); {sum(1 for c in clusters if c['breadth'] > 1)} made by 2+ sources")
    top = clusters[: a.top]

    # 3. synthesize each top cluster in parallel
    synth = (HERE / "SYNTHESIZE.md").read_text(encoding="utf-8")

    def synthesize(c):
        members = [{k: m.get(k) for k in ("claim", "steps", "kind", "stance", "attributed_to", "quote_or_ts", "strength",
                                          "objections", "replies", "source_key", "source_title")} for m in c["members"][:25]]
        prompt = f"{synth}\n\nTOPIC: {a.topic}\nCLUSTER: {c['id']} ({c['breadth']} source(s))\n\n{json.dumps(members, ensure_ascii=False)}"
        return c["id"], main_ctx.cached(f"synth-{c['id']}", lambda: main_ctx.call_json("synthesize_cluster", prompt),
                                        extra=json.dumps(members, sort_keys=True))
    step(f"synthesizing the top {len(top)} argument(s) in parallel")
    synthesized = dict(main_ctx.parallel(synthesize, top, width=a.workers))

    # 4. overview
    brief = [{"id": c["id"], "breadth": c["breadth"], "mean_strength": c["mean_strength"],
              **{k: (synthesized.get(c["id"]) or {}).get(k) for k in ("title", "one_line", "evidence_strength", "rigor")},
              "top_objection": ((synthesized.get(c["id"]) or {}).get("objections") or [{}])[0].get("objection")} for c in top]
    prompt = f"{(HERE / 'OVERVIEW.md').read_text(encoding='utf-8')}\n\nTOPIC: {a.topic}\nSOURCES: {len(chosen)}\n\n{json.dumps(brief, ensure_ascii=False)}"
    step("writing the overview")
    overview = main_ctx.cached("overview", lambda: main_ctx.call_json("synthesis_overview", prompt), extra=json.dumps(brief, sort_keys=True)) or {}

    # 5. report
    data = {"topic": a.topic, "sources_considered": len(sources), "sources_used": [
                {"key": s.key, "kind": s.kind, "title": s.title, "relevance": sc, "method": m, "citation": s.citation()} for s, sc, m in chosen],
            "failed_sources": failed, "arguments": arguments,
            "clusters": [{k: v for k, v in c.items() if k != "members"} | {"member_count": len(c["members"])} for c in clusters],
            "best_arguments": [{"cluster": c, "synthesis": synthesized.get(c["id"])} for c in top], "overview": overview}
    md = render(data)
    rows = [{"cluster": c["id"], "breadth": c["breadth"], "claim": m.get("claim"), "kind": m.get("kind"), "stance": m.get("stance"),
             "strength": m.get("strength"), "attributed_to": m.get("attributed_to"), "quote_or_ts": m.get("quote_or_ts"),
             "source": m.get("source_title"), "citation": m.get("citation")} for c in clusters for m in c["members"]]
    result = ItemResult(data, page(f"Best arguments: {a.topic}", markdown_to_html(md)),
                        {"arguments": rows, "sources": data["sources_used"], "clusters": data["clusters"]}, md)
    ok = station.write(main_ctx, result, started, folder=root)
    report = root / "03_REPORT"
    report.mkdir(parents=True, exist_ok=True)
    (report / "best_arguments.md").write_text(md, encoding="utf-8")
    (report / "best_arguments.html").write_text(result.html, encoding="utf-8")
    print(f"48_TOPIC_SYNTHESIS: report -> {report / 'best_arguments.md'}")
    return 0 if ok else 1


def render(d: dict) -> str:
    out = [f"# Best arguments: {d['topic']}", "",
           f"*{len(d['sources_used'])} sources used of {d['sources_considered']} considered · {len(d['arguments'])} arguments · "
           f"{len(d['clusters'])} distinct after cross-referencing. AI proposal; every citation below is built from the source record.*", ""]
    ov = d.get("overview") or {}
    if ov.get("overview_markdown"):
        out += ["## Overview", "", ov["overview_markdown"], ""]
    if ov.get("gaps_in_the_field"):
        out += ["## What the corpus does not cover", ""] + [f"- {g}" for g in ov["gaps_in_the_field"]] + [""]
    for n, entry in enumerate(d["best_arguments"], 1):
        c, s = entry["cluster"], entry["synthesis"] or {}
        out += ["---", "", f"## {n}. {s.get('title') or c['representative'][:80]}  ({c['id']})", "",
                f"*Made by {c['breadth']} source(s) · mean strength {c['mean_strength']}/10 · evidence {s.get('evidence_strength', '?')}/5 · rigor {s.get('rigor', '?')}/5*", ""]
        if s.get("one_line"):
            out += [f"> {s['one_line']}", ""]
        if s.get("strongest_form"):
            out += [s["strongest_form"], ""]
        if s.get("steps"):
            out += [f"{i}. {x}" for i, x in enumerate(s["steps"], 1)] + [""]
        if s.get("lineage"):
            out += ["**Who holds it:** " + "; ".join(f"{x.get('who')} ({x.get('relation')})" for x in s["lineage"]), ""]
        if s.get("objections"):
            out += ["**Objections and replies:**"] + [f"- {o.get('objection')} ({o.get('origin', '')}) → {o.get('best_reply')} (reply strength {o.get('reply_strength')}/5)" for o in s["objections"]] + [""]
        out += ["**Sources (cite these):**"] + sorted({f"- {m['citation']}" + (f" — \"{str(m.get('quote_or_ts'))[:140]}\"" if m.get("quote_or_ts") else "") for m in c["members"]}) + [""]
        if s.get("uncertain_citations"):
            out += ["**From general knowledge, verify before citing:** " + "; ".join(f"{x.get('who')}: {x.get('what')}" for x in s["uncertain_citations"]), ""]
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(main())
