"""08_YT_SUMMARY: base layer. The whole transcript + QUESTIONS.md in one call per video; 30+ videos at once."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.focus import points_from_markdown  # noqa: E402
from engine.output import esc, markdown_to_html, page  # noqa: E402
from engine.station import ItemResult, Station  # noqa: E402

LABEL = "08_YT_SUMMARY"


def render(item, data) -> str:
    lines = [f"# {item.title}", "", data.get("summary", ""), ""]
    for a in data.get("answers", []):
        stamps = ", ".join(a.get("timestamps", []) or [])
        lines += [f"## {a.get('question', '')}", "", str(a.get("answer", "")) + (f"  ({stamps})" if stamps else ""), ""]
    if data.get("people_and_sources"):
        lines += ["## People and sources", ""] + [f"- {p.get('name')} ({p.get('role')}, {p.get('timestamp', '')})" for p in data["people_and_sources"]] + [""]
    if data.get("focus_findings"):
        lines += ["## Focus findings", ""] + [f"- **{f.get('point')}**: {f.get('finding')} {', '.join(f.get('timestamps', []) or [])}" for f in data["focus_findings"]]
    return "\n".join(lines)


def process(ctx):
    station = ctx.station
    questions = points_from_markdown(station.dir / "QUESTIONS.md")
    body = (station.dir / "PROMPT.md").read_text(encoding="utf-8")
    prompt = (f"{body}\n\nQUESTIONS:\n" + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions)) +
              f"\n\nITEM: {ctx.item.id}\nVIDEO: {ctx.item.title}\nURL: {ctx.item.meta.get('url', '')}\n\nTRANSCRIPT:\n{ctx.text}")
    data = ctx.cached("summary", lambda: ctx.call_json("yt_summary", prompt))
    if not isinstance(data, dict):
        return None
    md = render(ctx.item, data)
    rows = [{"question": a.get("question"), "answer": a.get("answer"), "timestamps": a.get("timestamps")} for a in data.get("answers", [])]
    return ItemResult(data, page(ctx.item.title, markdown_to_html(md)), {"answers": rows, "sources": data.get("people_and_sources", [])}, md)


if __name__ == "__main__":
    raise SystemExit(Station(LABEL, prompt_files=["QUESTIONS.md"]).run(process))
