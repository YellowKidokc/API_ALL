#!/usr/bin/env python3
"""Split a combined YTBSD channel/playlist .md into Obsidian-ready chapter notes.

    python split_channel_chapters.py "subtitles/channel_Gary Habermas - Videos_....md"
    python split_channel_chapters.py <file> -o "O:/Vault/YouTube" --overwrite

Output: <out>/<Channel>/<Channel> - Chapter 001 - <Title>.md  +  "<Channel> - 000 Index.md"  +  _manifest.json
The combined source file is never modified.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from split_playlist_markdown import extract_metadata, playlist_title, read_text, split_sections

UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f#^\[\]]')


def safe_name(value: str, max_len: int = 110) -> str:
    value = UNSAFE.sub(" ", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value[:max_len].rstrip(" .") or "Untitled"


def channel_name(text: str, source: Path) -> str:
    title = playlist_title(text, source)
    return re.sub(r"\s+-\s+(Videos|Shorts|Live|Playlists)$", "", title).strip()


def yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def transcript_body(section: str) -> str:
    parts = section.split("### Transcript", 1)
    body = parts[1] if len(parts) == 2 else ""
    return body.strip().removesuffix("---").strip()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--out", type=Path, help="Parent folder (default: beside the source file)")
    ap.add_argument("--prefix", default="Chapter")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args(argv)

    source = args.input.resolve()
    text = read_text(source)
    channel = channel_name(text, source)
    kind = "PLAYLIST" if source.name.lower().startswith("playlist") else "CHANNEL"
    downloaded = re.search(r"\*\*Downloaded:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    stamp = downloaded.group(1) if downloaded else "undated"
    out_dir = (args.out or source.parent).resolve() / f"{kind} - {safe_name(channel)} - {stamp}"
    if out_dir.exists() and any(out_dir.iterdir()) and not args.overwrite:
        print(f"Already exists: {out_dir}  (use --overwrite)", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    sections = split_sections(text)
    if not sections:
        print("No '## N. Title' video sections found.", file=sys.stderr)
        return 1

    rows = []
    for match, section in sections:
        num = int(match.group("number"))
        title = match.group("title").strip()
        meta = extract_metadata(section)
        body = transcript_body(section)
        has_transcript = bool(body) and "no transcript" not in body[:200].lower()
        name = f"{safe_name(channel, 60)} - {args.prefix} {num:03d} - {safe_name(title)}.md"
        note = "\n".join([
            "---",
            "type: youtube_chapter",
            f"channel: {yaml_str(channel)}",
            f"chapter: {num}",
            f"title: {yaml_str(title)}",
            f"video_id: {yaml_str(meta.get('video id', ''))}",
            f"url: {yaml_str(meta.get('url', ''))}",
            f"transcript_language: {yaml_str(meta.get('transcript language', ''))}",
            f"status: {'split' if has_transcript else 'no_transcript'}",
            f"words: {len(body.split())}",
            f"source_file: {yaml_str(source.name)}",
            f"downloaded: {stamp}",
            "tags: [youtube]",
            "---",
            "",
            f"# {args.prefix} {num:03d} — {title}",
            "",
            f"[Watch on YouTube]({meta.get('url', '')}) · [[{safe_name(channel, 60)} - 000 Index|Channel index]]",
            "",
            "## Transcript",
            "",
            body if has_transcript else "_No transcript available._",
            "",
        ])
        (out_dir / name).write_text(note, encoding="utf-8", newline="\n")
        rows.append({"chapter": num, "title": title, "file": name, "video_id": meta.get("video id", ""),
                     "url": meta.get("url", ""), "has_transcript": has_transcript, "words": len(body.split())})

    index = [f"# {channel} — Index", "", f"**Source:** `{source.name}`",
             f"**Videos:** {len(rows)} · **With transcripts:** {sum(r['has_transcript'] for r in rows)}", ""]
    index += [f"{r['chapter']}. [[{r['file'][:-3]}|{r['title']}]]" + ("" if r["has_transcript"] else " _(no transcript)_")
              for r in rows]
    (out_dir / f"{safe_name(channel, 60)} - 000 Index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    (out_dir / "_manifest.json").write_text(json.dumps({"channel": channel, "source": str(source), "videos": rows},
                                                       indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"{len(rows)} chapter notes -> {out_dir}")
    print(f"with transcript: {sum(r['has_transcript'] for r in rows)} · without: {sum(not r['has_transcript'] for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
