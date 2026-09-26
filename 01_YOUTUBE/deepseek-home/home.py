"""DeepSeek home base: every call = HOME + GLOSSARY + STATE + TASK + INPUT.

Usage:
  python home.py chat "a question for DeepSeek"
  python home.py summary  path\to\transcript.md
  python home.py claims   path\to\transcript.md   (chunked, ~1200 words, 150 overlap)
  add --dry-run to build and save the request without calling the API
  add --model deepseek-reasoner for harder jobs

Saved per call: requests/<id>.md (exact payload), outputs/<id>.md (reply),
log.jsonl (one line per call), and a line in outputs/INDEX.md.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
CHUNK_WORDS = {"claims": 1200}
OVERLAP_WORDS = 150


def read_clean(name):
    """Read a home file, dropping <!-- notes --> meant for David, not DeepSeek."""
    p = HERE / name
    if not p.exists():
        return ""
    return re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8"), flags=re.S).strip()


def chunk_lines(lines, size, overlap):
    """Split timestamped lines into ~size-word chunks sharing ~overlap words."""
    chunks, start = [], 0
    while start < len(lines):
        words, end = 0, start
        while end < len(lines) and words < size:
            words += len(lines[end].split())
            end += 1
        chunks.append(lines[start:end])
        if end >= len(lines):
            break
        back, k = 0, end
        while k > start + 1 and back < overlap:
            k -= 1
            back += len(lines[k].split())
        start = k
    return chunks


def split_input(task, text):
    """Return (title, [input pieces]); title carries the video ID when present."""
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), "")
    vid = re.search(r"\*\*Video ID:\*\*\s*`([^`]+)`", text)
    if vid:
        title = f"{title} [video ID: {vid.group(1)}]"
    if task not in CHUNK_WORDS:
        return title, [text]
    body = text.split("## Transcript", 1)[-1]
    lines = [l for l in body.splitlines() if l.strip()]
    pieces = chunk_lines(lines, CHUNK_WORDS[task], OVERLAP_WORDS)
    return title, ["\n".join(p) for p in pieces]


# David's live CKG argument template; only its argument-first front half is sent
ARG_TEMPLATE = pathlib.Path(r"D:\GitHub\nerve\source\html\atoms\Template\CKGARGUMENT_TEMPLATE_V1.md")
INCLUDES = {"index": ["DEBATE_MAP.md", "@argument-template", "templates/STORY_TEMPLATE_V1.md"],
            "synthesize": ["DEBATE_MAP.md"]}


def argument_template():
    """Front half of the CKG argument template: overview through 'Where to investigate'."""
    if not ARG_TEMPLATE.exists():
        return ""
    t = ARG_TEMPLATE.read_text(encoding="utf-8")
    start = t.find("## Argument overview")
    end = t.find('<a id="framework-overview">')
    if start < 0:
        return ""
    body = re.sub(r"<!--.*?-->", "", t[start:end if end > start else None], flags=re.S).strip()
    return ("# CKG ARGUMENT TEMPLATE V1 (front half; the JSON in TASK is the output "
            "format, this shows what each part means)\n\n" + body)


def build(task, piece, title, part, total):
    sections = [read_clean("HOME.md"), read_clean("GLOSSARY.md"),
                read_clean("STATE.md")]
    sections += [argument_template() if f == "@argument-template" else read_clean(f)
                 for f in INCLUDES.get(task, [])]
    sections.append(read_clean(f"tasks/{task}.md"))
    head = f"# INPUT"
    if title:
        head += f"\nsource: {title}"
    if total > 1:
        head += f"\nchunk: {part} of {total}"
    sections.append(f"{head}\n\n{piece}")
    return "\n\n---\n\n".join(s for s in sections if s)


def slug(s):
    s = re.sub(r"\s*\[video ID:.*", "", s)
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")[:50] or "chat"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", help="name of a file in tasks/ (chat, summary, claims)")
    ap.add_argument("input", help="a file path, or plain text for chat")
    ap.add_argument("--model", default="deepseek-chat")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not (HERE / "tasks" / f"{args.task}.md").exists():
        ap.error(f"no task file tasks/{args.task}.md")
    src = pathlib.Path(args.input)
    text = src.read_text(encoding="utf-8") if src.is_file() else args.input
    title, pieces = split_input(args.task, text)

    client = None
    if not args.dry_run:
        import openai
        client = openai.OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
                               base_url="https://api.deepseek.com")

    for d in ("requests", "outputs"):
        (HERE / d).mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    replies = []
    for i, piece in enumerate(pieces, 1):
        prompt = build(args.task, piece, title, i, len(pieces))
        cid = f"{stamp}_{args.task}_{slug(title or text[:40])}"
        if len(pieces) > 1:
            cid += f"_part{i:02d}"
        (HERE / "requests" / f"{cid}.md").write_text(prompt, encoding="utf-8")
        print(f"[{i}/{len(pieces)}] {cid}  ({len(prompt.split())} words sent)")
        if args.dry_run:
            continue

        resp = client.chat.completions.create(
            model=args.model, temperature=0.3,
            messages=[{"role": "user", "content": prompt}])
        reply = resp.choices[0].message.content
        replies.append(reply)
        (HERE / "outputs" / f"{cid}.md").write_text(reply, encoding="utf-8")
        with open(HERE / "log.jsonl", "a", encoding="utf-8") as log:
            log.write(json.dumps({
                "id": cid, "time": stamp, "task": args.task, "model": args.model,
                "source": title or "chat", "part": i, "parts": len(pieces),
                "tokens_in": resp.usage.prompt_tokens,
                "tokens_out": resp.usage.completion_tokens}) + "\n")

    if replies:
        name = f"{stamp}_{args.task}_{slug(title or text[:40])}"
        with open(HERE / "outputs" / "INDEX.md", "a", encoding="utf-8") as st:
            st.write(f"- {stamp[:8]} | {args.task} | {title or 'chat'} | "
                     f"outputs/{name}*.md ({len(replies)} part(s))\n")
        if len(pieces) == 1:
            print("\n" + replies[0])
        print(f"\n[done: {len(replies)} reply(ies) in {HERE / 'outputs'}]")


if __name__ == "__main__":
    main()
