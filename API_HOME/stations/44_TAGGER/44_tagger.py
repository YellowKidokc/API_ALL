"""44_TAGGER: local pass on every item, then one DeepSeek call per item that confirms the candidate tags."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine import tagger  # noqa: E402
from engine.output import page, table  # noqa: E402
from engine.station import ItemResult, Station  # noqa: E402

LABEL = "44_TAGGER"


def process(ctx):
    station = ctx.station
    scores = tagger.local_scores(ctx.text)
    threshold = int(station.settings.get("tag_confirm_from", 3))
    candidates = [t for t, s in scores.items() if s["score"] >= threshold]
    if candidates and station.args.provider != "local":
        body = (station.dir / "PROMPT.md").read_text(encoding="utf-8")
        prompt = f"{body}\n\nTAGS: {' | '.join(candidates)}\nITEM: {ctx.item.id} ({ctx.item.kind}) {ctx.item.title}\n\nTEXT:\n{ctx.text}"
        reply = ctx.cached("confirm", lambda: ctx.call_json("tagger", prompt, focus=False), extra="|".join(candidates))
        for row in (reply or {}).get("tags", []) if isinstance(reply, dict) else []:
            if row.get("tag") in scores:
                scores[row["tag"]] = {"tag": row["tag"], "score": max(0, min(10, int(row.get("score", 0)))),
                                      "reason": row.get("reason", ""), "quote_or_ts": row.get("quote_or_ts", ""),
                                      "method": f"{ctx.args.provider}-confirmed"}
    if ctx.errors:
        return None
    tagger.save(ctx.item, scores)
    rows = sorted(scores.values(), key=lambda r: -r["score"])
    return ItemResult({"tags": rows, "confirmed": candidates}, page(f"Tags: {ctx.item.title}", table(rows, ["tag", "score", "method", "reason", "quote_or_ts"])),
                      {"tags": rows}, headline={f"tag:{r['tag']}": r["score"] for r in rows if r["score"] >= 5})


if __name__ == "__main__":
    raise SystemExit(Station(LABEL, prompt_files=["../../config/tags.json"]).run(process))
