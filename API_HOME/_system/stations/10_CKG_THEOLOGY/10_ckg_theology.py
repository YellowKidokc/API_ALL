"""10_CKG_THEOLOGY: theology triage on each video, run right after the CKG index (03).

One whole-transcript call per video (API-10.1). The model proposes; engine/triage.py enforces the rules
(default CLEAN, timestamps, three-flag cap with Warrant / Doctrine tier / Opponent priority, rows 16-17 exempt,
church history = verify, row 15 needs comments, platform probes are notes only).

Reads, when they exist:
  * the CKG index for the same video (03_YT_INDEX output, yt_indexed/<Channel>/_API/*.index.json)
  * comments: <transcript>.comments.json or <transcript>.info.json beside the transcript
    (--fetch-comments downloads them with yt-dlp when it is installed)
Writes the youtube_deep_analysis_v1 document (argument_layer + youtube_specific_probes + theology_rubric),
the 17-line table with the kept expansions underneath, and one Excel sheet per part.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine import triage  # noqa: E402
from engine.comments import comments, fetch_comments  # noqa: E402
from engine.output import markdown_to_html, page  # noqa: E402
from engine.paths import configured, external  # noqa: E402
from engine.station import ItemResult, Station  # noqa: E402

LABEL = "10_CKG_THEOLOGY"
HERE = Path(__file__).resolve().parent


def args(p):
    p.add_argument("--fetch-comments", action="store_true", help="download comments with yt-dlp first (needs yt-dlp)")


def platform_names() -> list[str]:
    text = (HERE / "PLATFORM_PROBES.md").read_text(encoding="utf-8")
    return [line.split("|")[0].strip() for line in text.splitlines() if "|" in line and not line.startswith("#")]


def ckg_index(item) -> dict | None:
    if not configured("yt_indexed"):
        return None
    folder = external("yt_indexed") / item.meta.get("channel", "") / "_API"
    if not folder.is_dir():
        return None
    for f in folder.glob("*.index.json"):
        text = f.read_text(encoding="utf-8", errors="replace")
        if item.id in text[:5000] or f.name.startswith(item.title[:40]):
            try:
                return json.loads(text)
            except ValueError:
                return None
    return None


def process(ctx):
    item = ctx.item
    if ctx.args.fetch_comments:
        fetch_comments(item, ctx)
    rubric = triage.load_rubric((HERE / "RUBRIC.md").read_text(encoding="utf-8"))
    names = platform_names()
    index = ckg_index(item)
    audience = comments(item)
    ctx.step(f"inputs: transcript, CKG index {'found' if index else 'not found (run 03 first for best results)'}, "
             f"{len(audience)} comment(s)")
    prompt = ((HERE / "PROMPT.md").read_text(encoding="utf-8")
              + "\n\nRUBRIC (row | probe | the one question | expands when):\n"
              + "\n".join(f"{r['row']} | {r['probe']} | {r['question']} | {r['expands_when']}" for r in rubric)
              + "\n\nPLATFORM PROBES:\n" + (HERE / "PLATFORM_PROBES.md").read_text(encoding="utf-8")
              + f"\n\nITEM: {item.id}\nCHANNEL: {item.meta.get('channel', '')}\nVIDEO: {item.title}\nURL: {item.meta.get('url', '')}"
              + (f"\n\nCKG INDEX FOR THIS VIDEO (station 03):\n{json.dumps(index, ensure_ascii=False)[:60000]}" if index else "")
              + ("\n\nCOMMENTS (most liked first):\n" + "\n".join(audience) if audience else "\n\nCOMMENTS: none acquired")
              + f"\n\nTRANSCRIPT:\n{ctx.text}")
    extra = f"index={bool(index)};comments={len(audience)}"
    reply = ctx.cached("triage", lambda: ctx.call_json("theology_triage", prompt), extra=extra)
    if not isinstance(reply, dict):
        return None
    ruled = triage.enforce(reply, rubric, comments_available=bool(audience))
    for line in ruled["log"]:
        ctx.step(f"rule: {line}")
    ctx.step(f"verdicts: {len(ruled['flags'])} FLAG, {len(ruled['claims'])} CLAIM, {len(ruled['unknown'])} ??")
    layer = triage.claims_into_graph(reply.get("argument_layer") or {}, ruled["rows"])
    meta = item.meta
    doc = {"type": "youtube_deep_analysis_v1", "source_platform": "youtube", "channel": meta.get("channel"),
           "source_family": meta.get("channel"), "speaker": reply.get("speaker", ""), "video_sequence": meta.get("series_order"),
           "date": meta.get("upload_date", ""), "original_title": item.title, "video_id": item.id, "url": meta.get("url"),
           "transcript_language": meta.get("language", ""), "classification": ["youtube_deep_dive", "theology"],
           "keywords": reply.get("keywords", []), "anomalies_detected": reply.get("anomalies_detected", []),
           "synthesis_hooks": reply.get("synthesis_hooks", []),
           "claim_atoms": [c.get("text") for c in layer.get("claims", [])],
           "source_reliability": reply.get("source_reliability", ""), "word_count": len(ctx.text.split()),
           "analyzed_at": ctx.receipts[-1]["finished_at"] if ctx.receipts else "",
           "argument_layer": layer, "youtube_specific_probes": triage.platform_notes(reply, names),
           "theology_rubric": {"rows": ruled["rows"], "collapse_question": reply.get("collapse_question", ""),
                               "steers_around": bool(reply.get("steers_around")), "rules_applied": ruled["log"],
                               "flags": ruled["flags"], "claims": ruled["claims"], "unknown_for_channel_pass": ruled["unknown"]},
           "inputs": {"ckg_index": bool(index), "comments": len(audience)}}
    md = render(item, doc)
    sheets = {"rubric": ruled["rows"],
              "platform": [{"probe": k, "note": v} for k, v in doc["youtube_specific_probes"].items()]}
    for part in ("claims", "premises", "hidden_premises", "inference_edges", "adversarial_tests"):
        sheets[part] = layer.get(part, []) or []
    return ItemResult(doc, page(f"Theology triage: {item.title}", markdown_to_html(md)), sheets, md,
                      {"theology_flags": len(ruled["flags"]), "theology_claims": len(ruled["claims"])})


def render(item, doc) -> str:
    tr = doc["theology_rubric"]
    out = [f"# Theology triage: {item.title}", "", f"*{doc.get('channel') or ''} · {doc.get('url') or ''}*", "",
           f"**Collapse question:** {tr['collapse_question']}" + (" *(the speaker steers around it)*" if tr["steers_around"] else ""), "",
           "| # | probe | verdict | ≤12 words |", "|---|---|---|---|"]
    out += [f"| {r['row']} | {r['probe']} | {r['verdict']}{' (verify)' if r['verify'] and r['verdict'] != 'CLEAN' else ''} | "
            f"{r['line']}{' [' + r['timestamp'] + ']' if r['timestamp'] and r['verdict'] not in ('CLEAN', '??') else ''} |"
            for r in tr["rows"]]
    expanded = [r for r in tr["rows"] if r["verdict"] in ("FLAG", "CLAIM") and r["expansion"]]
    if expanded:
        out += [""]
        for r in expanded:
            out += [f"## {r['row']}. {r['probe']} ({r['verdict']})", "", r["expansion"], ""]
    wc = (doc["argument_layer"] or {}).get("win_condition") or {}
    if wc:
        out += ["## Win condition", "", f"- **Would win:** {wc.get('what_would_win', '')}",
                f"- **Would defeat:** {wc.get('what_would_defeat', '')}", ""]
    hp = [h for h in (doc["argument_layer"] or {}).get("hidden_premises", []) if h.get("load_bearing")]
    if hp:
        out += ["## Load-bearing hidden premises", ""] + [f"- {h.get('id')}: {h.get('text')} ({h.get('reason', '')})" for h in hp] + [""]
    out += ["## Platform notes", ""] + [f"- {k}: {v}" for k, v in doc["youtube_specific_probes"].items()]
    if tr["rules_applied"]:
        out += ["", "## Rules applied", ""] + [f"- {x}" for x in tr["rules_applied"]]
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(Station(LABEL, kind="videos", extra_args=args,
                             prompt_files=["RUBRIC.md", "PLATFORM_PROBES.md"]).run(process))
