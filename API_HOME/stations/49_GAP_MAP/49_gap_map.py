"""49_GAP_MAP: where David's own work on a topic needs to expand, contract, fill a hole, or cite someone.

Needs a 48_TOPIC_SYNTHESIS run for the same topic, and David's own work: papers created with
`47_NEW_PAPER --own`, and/or the files under the own_work path.

  ONE_MENU.bat 49 --topic resurrection   (--min 3: relevance threshold for David's own files; --candidates 6)
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine import bridge  # noqa: E402
from engine.output import markdown_to_html, page  # noqa: E402
from engine.station import Context, ItemResult, Station  # noqa: E402
from engine.text import numbered, segment  # noqa: E402

LABEL = "49_GAP_MAP"
HERE = Path(__file__).resolve().parent


def args(p):
    p.add_argument("--topic")
    p.add_argument("--min", dest="minimum", type=int, default=3, help="relevance threshold for David's own sources (default 3)")
    p.add_argument("--candidates", type=int, default=6, help="closest matches sent with each comparison (default 6)")


def main() -> int:
    station = Station(LABEL, kind="own", extra_args=args)
    a = station.args
    if not a.topic:
        print("49_GAP_MAP: --topic is required")
        return 2
    started = time.monotonic()
    root = bridge.topic_folder(a.topic)
    ctx = Context(station, None)
    ctx.who, ctx.cache_root = a.topic[:18], root / "_cache"
    run = bridge.latest_topic_run(a.topic, "48_TOPIC_SYNTHESIS")
    if not run:
        print(f"49_GAP_MAP: no finished 48_TOPIC_SYNTHESIS for '{a.topic}'. Run: ONE_MENU.bat 48 --topic \"{a.topic}\"")
        return 2
    synthesis = json.loads((run / "48_TOPIC_SYNTHESIS.json").read_text(encoding="utf-8"))
    ctx.step(f"using synthesis {run.name}: {len(synthesis['best_arguments'])} best argument(s), {len(synthesis['arguments'])} extracted")
    own = bridge.relevance(bridge.own_sources(), a.topic, a.minimum)
    if a.limit:
        own = own[: a.limit]
    ctx.step(f"David's own sources on '{a.topic}': {len(own)}")
    for s, score, method in own:
        ctx.step(f"   {score:>2} ({method}) {s.key} {s.title[:60]}")
    if a.dry_run:
        return 0
    if not own:
        print("No own work found. Mark papers with `47_NEW_PAPER --own`, or set own_work in paths.json (RELOCATE.bat).")
        return 2

    # 1. David's claims
    own_prompt = (HERE / "OWN_CLAIMS.md").read_text(encoding="utf-8")
    claims = []

    def extract(entry):
        src, _, _ = entry
        sub = Context(station, src.item)
        sub.who, sub.cache_root = src.key[:18], root / "_cache"
        paragraphs, sentences = segment(src.text())
        prompt = f"{own_prompt}\n\nTOPIC: {a.topic}\nITEM: {src.key}\nTITLE: {src.title}\n\n{numbered(paragraphs, sentences)}"
        data = sub.cached(f"own-{src.key.replace(':', '_')}", lambda: sub.call_json("own_claims", prompt), extra=src.source_hash + a.topic)
        found = [{**c, "own_key": src.key, "own_title": src.title, "citation": src.citation()} for c in (data or {}).get("claims", [])] if isinstance(data, dict) else []
        sub.step(f"{len(found)} claim(s)")
        return found, sub
    for found, sub in ctx.parallel(extract, own, width=a.workers):
        claims += found
        ctx.receipts += sub.receipts
        ctx.calls += sub.calls
        ctx.steps += sub.steps
        ctx.warnings += [f"own source: {e}" for e in sub.errors]
    for i, c in enumerate(claims, 1):
        c["id"] = f"DL-{i:03d}"
    ctx.step(f"{len(claims)} claim(s) from David's work")

    # 2. local pre-match
    best = synthesis["best_arguments"]
    external_args = synthesis["arguments"]
    for i, e in enumerate(external_args, 1):
        e["id"] = f"EX-{i:03d}"
    claim_vecs = [bridge.bag(c.get("claim", "") + " " + c.get("quote", "")) for c in claims]
    arg_vecs = [bridge.bag(bridge.argument_text(e)) for e in external_args]

    def nearest(vec, pool_vecs, pool, k):
        scored = sorted(((bridge.cosine(vec, v), i) for i, v in enumerate(pool_vecs)), reverse=True)[:k]
        return [dict(pool[i], similarity=round(s, 3)) for s, i in scored if s > 0]

    # 3. coverage per best argument
    cov_prompt = (HERE / "COVERAGE.md").read_text(encoding="utf-8")

    def coverage(entry):
        c, s = entry["cluster"], entry["synthesis"] or {}
        vec = bridge.bag(" ".join([s.get("strongest_form", ""), c.get("representative", "")] + list(map(str, s.get("steps", [])))))
        cands = nearest(vec, claim_vecs, claims, a.candidates)
        brief = {"id": c["id"], "title": s.get("title"), "strongest_form": s.get("strongest_form") or c.get("representative"),
                 "steps": s.get("steps"), "objections": [o.get("objection") for o in s.get("objections", [])]}
        prompt = f"{cov_prompt}\n\nTOPIC: {a.topic}\nBEST ARGUMENT:\n{json.dumps(brief, ensure_ascii=False)}\n\nCANDIDATES (David's claims):\n" + \
                 json.dumps([{k: x.get(k) for k in ("id", "claim", "quote", "support", "similarity")} for x in cands], ensure_ascii=False)
        r = ctx.cached(f"cov-{c['id']}", lambda: ctx.call_json("gap_match", prompt), extra=prompt)
        return {"argument": c["id"], "title": s.get("title") or c.get("representative"), "breadth": c.get("breadth"),
                "mean_strength": c.get("mean_strength"), "candidates": [x["id"] for x in cands], **(r if isinstance(r, dict) else {})}
    ctx.step(f"coverage: {len(best)} best argument(s) against David's claims, in parallel")
    coverage_rows = ctx.parallel(coverage, best, width=a.workers)

    # 4. prior art per David claim
    pa_prompt = (HERE / "PRIOR_ART.md").read_text(encoding="utf-8")
    by_ex = {e["id"]: e for e in external_args}

    def prior(claim):
        cands = nearest(bridge.bag(claim.get("claim", "") + " " + claim.get("quote", "")), arg_vecs, external_args, a.candidates)
        prompt = f"{pa_prompt}\n\nTOPIC: {a.topic}\nDAVID'S CLAIM ({claim['id']}): {claim.get('claim')}\nQUOTE: {claim.get('quote')}\n\nCANDIDATES:\n" + \
                 json.dumps([{"id": x["id"], "claim": x.get("claim"), "source_key": x.get("source_key"), "quote_or_ts": x.get("quote_or_ts"),
                              "attributed_to": x.get("attributed_to"), "similarity": x["similarity"]} for x in cands], ensure_ascii=False)
        r = ctx.cached(f"prior-{claim['id']}", lambda: ctx.call_json("prior_art", prompt), extra=prompt) if cands else \
            {"status": "original", "matches": [], "cite_suggestion": "", "unverified_literature": [], "note": "no candidate in the corpus"}
        r = r if isinstance(r, dict) else {}
        matches = [dict(m, citation=by_ex.get(m.get("id"), {}).get("citation"), source_title=by_ex.get(m.get("id"), {}).get("source_title"),
                        quote_or_ts=by_ex.get(m.get("id"), {}).get("quote_or_ts")) for m in r.get("matches", []) if m.get("id") in by_ex]
        return {"claim_id": claim["id"], "claim": claim.get("claim"), "own_title": claim.get("own_title"), "quote": claim.get("quote"),
                **r, "matches": matches, "corpus_size": len(synthesis.get("sources_used", []))}
    ctx.step(f"prior art: {len(claims)} claim(s) against {len(external_args)} extracted argument(s), in parallel")
    prior_rows = ctx.parallel(prior, claims, width=a.workers)

    # 5. report
    data = {"topic": a.topic, "synthesis_run": run.name, "own_sources": [{"key": s.key, "title": s.title, "relevance": sc} for s, sc, _ in own],
            "own_claims": claims, "coverage": coverage_rows, "prior_art": prior_rows}
    md = render(data)
    result = ItemResult(data, page(f"Gap map: {a.topic}", markdown_to_html(md)),
                        {"coverage": [{k: v for k, v in r.items() if k != "focus_findings"} for r in coverage_rows],
                         "prior_art": [{k: v for k, v in r.items() if k != "focus_findings"} for r in prior_rows], "own_claims": claims}, md)
    ok = station.write(ctx, result, started, folder=root)
    report = root / "03_REPORT"
    report.mkdir(parents=True, exist_ok=True)
    (report / "gap_map.md").write_text(md, encoding="utf-8")
    (report / "gap_map.html").write_text(result.html, encoding="utf-8")
    print(f"49_GAP_MAP: report -> {report / 'gap_map.md'}")
    return 0 if ok else 1


def render(d: dict) -> str:
    cov, pa = d["coverage"], d["prior_art"]
    out = [f"# Gap map: {d['topic']}", "",
           f"*David's work: {len(d['own_sources'])} source(s), {len(d['own_claims'])} claim(s) · compared with synthesis {d['synthesis_run']}. "
           "AI proposal; citations are built from the source records; anything marked verify is a lead, not a citation.*", "",
           "## EXPAND: strong arguments your work does not make yet", ""]
    for r in sorted((r for r in cov if r.get("coverage") in ("missing", "partial")), key=lambda r: (r.get("coverage") != "missing", -(r.get("breadth") or 0))):
        out += [f"- **{r.get('title')}** ({r['argument']}, {r.get('coverage')}, made by {r.get('breadth')} source(s)): {r.get('expand', '')}"]
    out += ["", "## HOLES: objections your work leaves unanswered", ""]
    holes = [(r.get("title"), o) for r in cov for o in r.get("objections_unanswered", []) or []]
    out += [f"- {o}  *(against: {t})*" for t, o in holes] or ["- none reported"]
    out += ["", "## CONTRACT: claims the corpus argues against", ""]
    out += [f"- {r['claim_id']} {r.get('claim')} — {r.get('cite_suggestion', '')}" for r in pa if r.get("status") == "contradicted"] or ["- none"]
    out += ["", "## CITE: someone in your corpus made this before", "", "| your claim | where you make it | cite |", "|---|---|---|"]
    for r in pa:
        if r.get("status") in ("prior_art", "parallel"):
            cites = "<br>".join(f"{m.get('citation')} ({m.get('how_close', '')})" for m in r.get("matches", []) if m.get("citation"))
            out.append(f"| {r['claim_id']} {r.get('claim')} ({r.get('status')}) | {r.get('own_title')} | {cites or r.get('cite_suggestion', '')} |")
    leads = [(r["claim_id"], x) for r in pa for x in r.get("unverified_literature", []) or []]
    if leads:
        out += ["", "**Leads from general knowledge (verify before citing):**"] + [f"- {cid}: {x.get('who')} — {x.get('what')}" for cid, x in leads]
    out += ["", f"## ORIGINAL: no match in a corpus of {pa[0]['corpus_size'] if pa else 0} source(s)", ""]
    out += [f"- {r['claim_id']} {r.get('claim')}" for r in pa if r.get("status") == "original"] or ["- none"]
    out += ["", "## Covered well", ""] + ([f"- {r.get('title')} ({r['argument']})" for r in cov if r.get("coverage") == "covered"] or ["- none"])
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(main())
