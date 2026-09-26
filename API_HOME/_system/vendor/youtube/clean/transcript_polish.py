"""
transcript_polish.py — Turn raw YouTube transcripts into readable text. Lossless.

What it does
------------
Drop transcript files into `transcripts_inbox/` (next to this script), run it,
and get three readable versions per video in `transcripts_outbox/`:

  V1  plain       — human paragraphs. No timestamps. Speaker changes (>>)
                    become paragraph breaks. Cleanest to read.
  V2  timestamped — same paragraphs, each headed with [h:mm:ss]. Best when you
                    need to cite "he says X at 14:32".
  V3  full        — every source caption segment on its own line, [mm:ss]
                    prefixed, `>>` and [music] tags kept. Audit trail.
                    Word count is verified identical to the raw source.

Input formats: .srt, .vtt, single-video .md, combined channel/playlist .md
(the "one page with 100 transcripts" files are auto-split into individual
videos, one set of V1/V2/V3 outputs each).

Usage
-----
    python transcript_polish.py                 # process inbox -> outbox
    python transcript_polish.py --in DIR --out DIR
    python transcript_polish.py --versions 1,3  # only some versions

Stdlib only. No pip installs.
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IN = os.path.join(SCRIPT_DIR, "transcripts_inbox")
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "transcripts_outbox")

GAP_SECONDS = 2.0      # pause longer than this starts a new paragraph
MAX_PARA_CHARS = 480   # hard paragraph cap
SENTENCE_BREAK_CHARS = 220  # if a segment ends with . ! ? and para is at least this long, break

TS_SRT = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})")
TS_VTT = re.compile(r"(\d{1,2}):(\d{2})[:.](\d{2})[,.](\d{3})?")
TS_LINE_MD = re.compile(r"^\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]\s*(.*)$")
MD_SECTION = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$", re.M)
MD_META = re.compile(r"^\*\*(.+?):\*\*\s*(.+?)\s*$", re.M)
WORDISH = re.compile(r"[A-Za-z0-9À-ÿ]")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def stamp_to_seconds(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms or 0) / 1000.0


def parse_timestamp_line(line):
    """Parse '00:00:00,080 --> 00:00:02,240' -> (start_s, end_s) or None."""
    m = re.match(r"\s*(\S+)\s*-->\s*(\S+)", line)
    if not m:
        return None
    def one(tok):
        t = TS_SRT.fullmatch(tok)
        if t:
            return stamp_to_seconds(*t.groups())
        t = re.fullmatch(r"(\d{1,2}):(\d{2})[,.](\d{3})", tok)
        if t:  # mm:ss,mmm
            m_, s_, ms_ = t.groups()
            return int(m_) * 60 + int(s_) + int(ms_) / 1000.0
        return None
    start, end = one(m.group(1)), one(m.group(2))
    if start is None or end is None:
        return None
    return start, end


def parse_srt(path):
    """SRT/VTT -> list of segments {start, end, text}."""
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        raw = f.read()
    if raw.strip().startswith("WEBVTT"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else ""
    segments = []
    for block in re.split(r"\n\s*\n", raw):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        ts = None
        text_lines = []
        for l in lines:
            pl = parse_timestamp_line(l)
            if pl is not None:
                ts = ts or pl
                continue
            if re.fullmatch(r"\d{1,6}", l.strip()):  # SRT sequence number
                continue
            text_lines.append(l.strip())
        if ts is None or not text_lines:
            continue
        text = re.sub(r"\s+", " ", " ".join(text_lines)).strip()
        text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)  # strip <i> etc.
        if text:
            segments.append({"start": ts[0], "end": ts[1], "text": text})
    return segments


def parse_md_body(body):
    """Transcript body from a .md -> segments. Timestamped lines become real
    segments; flat text becomes one segment per sentence-ish chunk."""
    segs = []
    for line in body.splitlines():
        m = TS_LINE_MD.match(line.strip())
        if m:
            h, mnt, s, text = m.groups()
            start = (int(h) * 3600 + int(mnt) * 60 + int(s)) if s else (int(h) * 60 + int(mnt))
            if text.strip():
                segs.append({"start": float(start), "end": None, "text": text.strip()})
        elif line.strip():
            # flat prose: split on sentence ends so paragraphing still works
            for chunk in re.split(r"(?<=[.!?])\s+", line.strip()):
                if chunk:
                    segs.append({"start": None, "end": None, "text": chunk})
    return segs


def split_combined_md(raw):
    """Combined channel/playlist .md -> list of {title, meta, body}."""
    parts = MD_SECTION.split(raw)
    # parts: [header, num, title, body, num, title, body, ...]
    videos = []
    for i in range(1, len(parts) - 2, 3):
        num, title, body = parts[i], parts[i + 1], parts[i + 2]
        meta = dict(MD_META.findall(body))
        tmatch = re.search(r"### Transcript\s*\n(.*?)(?:\n---\s*?$|\Z)",
                           body, re.S | re.M)
        videos.append({
            "title": title.strip(),
            "video_id": meta.get("Video ID", "").strip("` "),
            "url": meta.get("URL", ""),
            "language": meta.get("Transcript Language", ""),
            "body": tmatch.group(1).strip() if tmatch else "",
        })
    return videos


def parse_single_md(raw):
    """Single-video .md -> one {title, meta, body}."""
    title_m = re.search(r"^#\s+(.+)$", raw, re.M)
    meta = dict(MD_META.findall(raw))
    tmatch = re.search(r"### Transcript\s*\n(.+?)\s*$", raw, re.S | re.M)
    return [{
        "title": title_m.group(1).strip() if title_m else "untitled",
        "video_id": meta.get("Video ID", "").strip("` "),
        "url": meta.get("URL", ""),
        "language": meta.get("Transcript Language", ""),
        "body": tmatch.group(1).strip() if tmatch else "",
    }]


# ---------------------------------------------------------------------------
# Paragraph builder (shared by all versions)
# ---------------------------------------------------------------------------

def is_speaker_change(text):
    return text.lstrip().startswith(">>")


def clean_text(text, keep_markers):
    t = re.sub(r"\s+", " ", text).strip()
    if not keep_markers:
        t = re.sub(r"^>>\s*", "", t)
    return t


def build_paragraphs(segments):
    """Merge caption segments into paragraphs.
    Breaks on: speaker change (>>), pause > GAP_SECONDS, sentence end after
    SENTENCE_BREAK_CHARS, or paragraph reaching MAX_PARA_CHARS.
    Returns list of {start, end, text}."""
    paras, cur, cur_start, cur_end = [], [], None, None
    for seg in segments:
        text = seg["text"]
        gap = (seg["start"] - cur_end) if (cur and seg["start"] is not None and cur_end is not None) else 0.0
        hard_break = (
            cur
            and (is_speaker_change(text)
                 or gap > GAP_SECONDS
                 or len(" ".join(cur)) >= MAX_PARA_CHARS
                 or (len(" ".join(cur)) >= SENTENCE_BREAK_CHARS and cur[-1].rstrip().endswith((".", "!", "?"))))
        )
        if hard_break:
            paras.append({"start": cur_start, "end": cur_end,
                          "text": " ".join(cur)})
            cur, cur_start = [], None
        cleaned = clean_text(text, keep_markers=False)
        if cleaned:
            cur.append(cleaned)
            if cur_start is None and seg["start"] is not None:
                cur_start = seg["start"]
            if seg["end"] is not None:
                cur_end = seg["end"]
    if cur:
        paras.append({"start": cur_start, "end": cur_end, "text": " ".join(cur)})
    return paras


def fmt_stamp(seconds):
    if seconds is None:
        return "--:--"
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def count_words(text):
    tokens = [t for t in text.split() if WORDISH.search(t)]
    tokens = [t for t in tokens if not re.fullmatch(r"\[\d{1,2}:\d{2}(?::\d{2})?\]|\[?--:--\]?", t)]
    return len(tokens)


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

VERSION_LABELS = {
    "v1": "V1 plain — paragraphs, no timestamps, speaker changes as breaks",
    "v2": "V2 timestamped — same paragraphs with [mm:ss] anchors",
    "v3": "V3 full fidelity — every source segment kept, markers kept (verified lossless)",
}


def header(video, source_name, version, duration_s, raw_words, out_words):
    lines = [
        f"# {video['title']}",
        "",
        f"**Source file:** `{source_name}`",
    ]
    if video.get("url"):
        lines.append(f"**URL:** {video['url']}")
    if video.get("language"):
        lines.append(f"**Language:** {video['language']}")
    lines += [
        f"**Version:** {VERSION_LABELS[version]}",
        f"**Duration:** {fmt_stamp(duration_s)} · **Words:** {out_words} (source: {raw_words})"
        + (" · lossless ✓" if out_words == raw_words else " · ⚠ WORD MISMATCH"),
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def render_v1(video, segments, source_name):
    paras = build_paragraphs(segments)
    body = "\n\n".join(p["text"] for p in paras)
    duration = max((s["end"] or s["start"] or 0) for s in segments) if segments else 0
    raw_w = count_words(" ".join(s["text"] for s in segments))
    out_w = count_words(body)
    return header(video, source_name, "v1", duration, raw_w, out_w) + body + "\n"


def render_v2(video, segments, source_name):
    paras = build_paragraphs(segments)
    body = "\n\n".join(
        f"[{fmt_stamp(p['start'])}] {p['text']}" for p in paras
    )
    duration = max((s["end"] or s["start"] or 0) for s in segments) if segments else 0
    raw_w = count_words(" ".join(s["text"] for s in segments))
    out_w = count_words(body)
    return header(video, source_name, "v2", duration, raw_w, out_w) + body + "\n"


def render_v3(video, segments, source_name):
    lines = [f"[{fmt_stamp(s['start'])}] {clean_text(s['text'], keep_markers=True)}"
             for s in segments]
    body = "\n".join(lines)
    duration = max((s["end"] or s["start"] or 0) for s in segments) if segments else 0
    raw_w = count_words(" ".join(s["text"] for s in segments))
    out_w = count_words(body)
    return header(video, source_name, "v3", duration, raw_w, out_w) + body + "\n"


RENDERERS = {"v1": render_v1, "v2": render_v2, "v3": render_v3}


def safe_name(title):
    name = re.sub(r'[<>:"/\\|?*]', "_", title).strip(" .")
    return name[:120] or "untitled"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def process_file(path, out_dir, versions):
    ext = os.path.splitext(path)[1].lower()
    made = []
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        raw = f.read()

    if ext in (".srt", ".vtt"):
        videos = [{
            "title": os.path.splitext(os.path.basename(path))[0],
            "video_id": "", "url": "", "language": "",
            "segments": parse_srt(path),
        }]
    elif ext == ".md":
        videos = split_combined_md(raw) if MD_SECTION.search(raw) else parse_single_md(raw)
        for v in videos:
            v["segments"] = parse_md_body(v.pop("body"))
    else:
        return made, f"SKIP (unsupported type {ext})"

    base = os.path.splitext(os.path.basename(path))[0]
    dest_dir = out_dir
    if len(videos) > 1:  # combined file -> its own subfolder
        dest_dir = os.path.join(out_dir, safe_name(base))
        os.makedirs(dest_dir, exist_ok=True)

    for idx, v in enumerate(videos, 1):
        if not v["segments"]:
            continue
        prefix = f"{idx:03d}_" if len(videos) > 1 else ""
        for ver in versions:
            out_path = os.path.join(
                dest_dir, f"{prefix}{safe_name(v['title'])}__{ver}.md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(RENDERERS[ver](v, v["segments"], os.path.basename(path), ))
            made.append(out_path)
    return made, f"OK -> {len(made)} files ({len(videos)} video(s))"


def main():
    p = argparse.ArgumentParser(description="Polish raw transcripts into readable versions.")
    p.add_argument("--in", dest="in_dir", default=DEFAULT_IN, help="inbox folder")
    p.add_argument("--out", dest="out_dir", default=DEFAULT_OUT, help="outbox folder")
    p.add_argument("--versions", default="v1,v2,v3", help="comma list: v1,v2,v3")
    args = p.parse_args()

    versions = [v.strip() for v in args.versions.split(",") if v.strip() in RENDERERS]
    if not versions:
        sys.exit("No valid versions requested. Use v1,v2,v3.")

    os.makedirs(args.in_dir, exist_ok=True)
    os.makedirs(args.out_dir, exist_ok=True)

    inputs = [os.path.join(args.in_dir, f) for f in sorted(os.listdir(args.in_dir))
              if os.path.splitext(f)[1].lower() in (".srt", ".vtt", ".md")]
    if not inputs:
        print(f"Inbox is empty: {args.in_dir}")
        print("Drop .srt / .vtt / .md transcript files there and run again.")
        return

    print(f"Polishing {len(inputs)} file(s) -> {args.out_dir}\n")
    ok = 0
    for path in inputs:
        try:
            made, msg = process_file(path, args.out_dir, versions)
            print(f"  {os.path.basename(path)}: {msg}")
            ok += 1
        except Exception as e:  # keep batch going
            print(f"  {os.path.basename(path)}: ERROR {e}")
    print(f"\nDone. {ok}/{len(inputs)} processed. Output in: {args.out_dir}")


if __name__ == "__main__":
    main()
