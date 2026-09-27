"""13_YT_CHANNEL_SUMMARY: the channel summary folder. One DeepSeek call per video, 30+ at once.

Per video: a three-sentence summary, 2-3 keywords and one value per line of COLUMNS.md.
  yt_summary/<Channel>/<note name> (summary).md  the video's summary note (links to its transcript note)
  yt_summary/<Channel>/_rows/<video id>.json     the row (one for one: saved the moment the video is done)
  yt_summary/<Channel>/<Channel> - summary.xlsx  every row, rebuilt after each video
  yt_summary/<Channel>/<Channel> - summary.tsv   the same, tab-separated
  yt_summary/<Channel>/<Channel> - summary.md    index note: every video, its summary and keywords
The keywords are also written into the transcript note made by 12_YT_TIDY (front matter "keywords:").
"""
import csv
import json
import re
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine import ytnames  # noqa: E402
from engine.comments import comments, fetch_comments  # noqa: E402
from engine.output import markdown_to_html, page, write_xlsx  # noqa: E402
from engine.paths import configured, external  # noqa: E402
from engine.station import ItemResult, Station  # noqa: E402

LABEL = "13_YT_CHANNEL_SUMMARY"
HERE = Path(__file__).resolve().parent
SHEET_LOCK = threading.Lock()


def columns() -> list[tuple[str, str]]:
    out = []
    for line in (HERE / "COLUMNS.md").read_text(encoding="utf-8").splitlines():
        if "|" in line and not line.lstrip().startswith("#"):
            name, ask = line.split("|", 1)
            if name.strip():
                out.append((name.strip(), ask.strip()))
    return out


def tidy_note(item) -> tuple[Path | None, ytnames.Name]:
    """The 12_YT_TIDY note for this video (its name comes from 12's state file, or the naming rule)."""
    channel = item.meta.get("channel", "")
    source = Path(item.meta.get("original_path", "")).name
    name = ytnames.parse(item.title, channel, item.meta.get("upload_date", ""))
    if not configured("yt_markdown"):
        return None, name
    folder = external("yt_markdown") / channel
    state = folder / "_tidy_state.json"
    if state.exists():
        rec = json.loads(state.read_text(encoding="utf-8"))["files"].get(source)
        if rec and (folder / rec["note"]).exists():
            return folder / rec["note"], name
    guess = folder / f"{name.file_stem}.md"
    return (guess if guess.exists() else None), name


def set_keywords(note: Path, keywords: list[str]) -> None:
    text = note.read_text(encoding="utf-8")
    line = "keywords: [" + ", ".join(json.dumps(k, ensure_ascii=False) for k in keywords) + "]"
    new = re.sub(r"^keywords:.*$", lambda _: line, text, count=1, flags=re.M)
    if new != text:
        tmp = note.with_suffix(".tmp")
        tmp.write_text(new, encoding="utf-8")
        tmp.replace(note)


def sort_key(row: dict):
    return (row.get("number") is None, row.get("number") or 0, row.get("published") or "", row.get("title") or "")


def rebuild_sheet(folder: Path, channel: str, cols: list[str]) -> None:
    rows = []
    for f in (folder / "_rows").glob("*.json"):
        try:
            rows.append(json.loads(f.read_text(encoding="utf-8")))
        except ValueError:
            continue
    rows.sort(key=sort_key)
    header = ["number", "title", "published", "summary", "keywords", *cols, "url", "video_id", "note"]
    flat = [{h: (", ".join(r.get(h) or []) if h == "keywords" else r.get(h, r.get("columns", {}).get(h, ""))) for h in header}
            for r in rows]
    for r in flat:
        r["number"] = "" if r["number"] is None else r["number"]
    base = folder / f"{ytnames.safe(channel)} - summary"
    write_xlsx(base.with_suffix(".xlsx"), {"videos": flat})
    with open(base.with_suffix(".tsv"), "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows([{k: str(v).replace("\t", " ").replace("\n", " ") for k, v in r.items()} for r in flat])
    lines = [f"# {channel}: summary", "", f"{len(rows)} video(s). Sheet: `{base.name}.xlsx`", ""]
    for r in rows:
        link = f"[[{r['note'][:-3]}]] · [[{r['note'][:-3]} (summary)|summary]]" if r.get("note") else r.get("title", "")
        lines += [f"## {r.get('h1') or r.get('title')}", "", f"{link} · {', '.join(r.get('keywords') or [])}", "",
                  r.get("summary", ""), ""]
    base.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")


def process(ctx):
    item = ctx.item
    channel = item.meta.get("channel", "")
    cols = columns()
    if ctx.args.fetch_comments:
        fetch_comments(item, ctx)
    audience = comments(item)
    ctx.step(f"inputs: transcript, {len(audience)} comment(s)")
    prompt = ((HERE / "PROMPT.md").read_text(encoding="utf-8")
              + "\n\nCOLUMNS (name | what to put in it):\n" + "\n".join(f"{n} | {a}" for n, a in cols)
              + f"\n\nCHANNEL: {channel}\nVIDEO: {item.title}\nURL: {item.meta.get('url', '')}"
              + ("\n\nCOMMENTS (most liked first):\n" + "\n".join(audience) if audience else "\n\nCOMMENTS: none acquired")
              + f"\n\nTRANSCRIPT:\n{ctx.text}")
    reply = ctx.cached("summary", lambda: ctx.call_json("yt_channel_summary", prompt), extra=f"comments={len(audience)}")
    if not isinstance(reply, dict):
        return None
    keywords = [str(k).strip() for k in (reply.get("keywords") or []) if str(k).strip()][:3]
    values = reply.get("columns") or {}
    if not audience and "audience_response" in values:
        values["audience_response"] = "no comments acquired"   # never a guess about comments nobody read
    note, name = tidy_note(item)
    stem = note.stem if note else name.file_stem
    row = {"video_id": item.id, "title": name.title, "h1": name.h1, "number": name.number, "published": name.date,
           "summary": str(reply.get("summary", "")).strip(), "keywords": keywords,
           "columns": {n: values.get(n, "") for n, _ in cols}, "url": item.meta.get("url", ""),
           "note": f"{stem}.md" if note else ""}
    folder = external("yt_summary", create=True) / channel
    (folder / "_rows").mkdir(parents=True, exist_ok=True)
    md = [f"# {name.h1}", "", f"*{channel}* · [Watch on YouTube]({row['url']})" + (f" · transcript [[{stem}]]" if note else ""), "",
          row["summary"], "", "**Keywords:** " + ", ".join(keywords), ""]
    md += [f"- **{n}:** {row['columns'][n]}" for n, _ in cols]
    with SHEET_LOCK:
        (folder / f"{stem} (summary).md").write_text("\n".join(md) + "\n", encoding="utf-8")
        (folder / "_rows" / f"{item.id}.json").write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")
        rebuild_sheet(folder, channel, [n for n, _ in cols])
    ctx.step(f"summary note + sheet row saved -> {folder}")
    if note:
        set_keywords(note, keywords)
        ctx.step(f"keywords written into {note.name}: {', '.join(keywords)}")
    else:
        ctx.warnings.append("no 12_YT_TIDY note for this video yet; keywords kept in the summary only")
    return ItemResult(row, page(name.h1, markdown_to_html("\n".join(md))), {"row": [{**row, **row["columns"]}]}, "\n".join(md))


def args(p):
    p.add_argument("--fetch-comments", action="store_true", help="download comments with yt-dlp first (needs yt-dlp)")


if __name__ == "__main__":
    raise SystemExit(Station(LABEL, extra_args=args, prompt_files=["COLUMNS.md", "PROMPT.md"]).run(process))
