"""
clean_library.py — Turn the whole subtitles/ library into readable Obsidian notes.

Run it as often as you like. Every run walks every channel folder, skips files
it already cleaned (checked by size + modified time, so thousands of skips take
seconds), and only works on new or changed transcripts.

  subtitles/<Channel>/*.md|.srt|.vtt   ->   obsidian_transcripts/<Channel>/<Title>.md

Each note gets YAML front matter (channel, video_id, url, ...), paragraphs
instead of one-line-per-caption, and clickable [mm:ss] links that jump to that
moment on YouTube.

Cleaning (all local Python, nothing leaves the machine)
-------------------------------------------------------
  always       paragraphs, [mm:ss] links, [Music]/[Applause] tags removed,
               um/uh removed, stutter repeats ("the the the") collapsed,
               "i" -> "I", sentence starts capitalised.
  --punctuate  auto-captions with no punctuation also go through a small
               local punctuation + capitalisation model (ONNX, CPU is fine):
                   pip install punctuators
               First use downloads the model (~210 MB) from Hugging Face:
               1-800-BAD-CODE/punct_cap_seg_en.
               Transcripts that are already punctuated are left alone.

A later --punctuate run upgrades notes that were cleaned without it.

Archiving originals
-------------------
  --archive    for every channel whose files are all cleaned, write
               _archive_zips/<Channel>__ORIGINAL-raw-transcripts__<date>.zip
               (with a MANIFEST.txt inside) and verify it. Originals are NOT
               deleted — check the zip, then store/delete them yourself.

Usage
-----
    python clean_library.py --dry-run             # what would be done
    python clean_library.py                       # clean the whole library
    python clean_library.py --punctuate           # + local punctuation model
    python clean_library.py --channel "Tom Bilyeu" --punctuate --limit 3
    python clean_library.py --archive

Stdlib only, except --punctuate (needs the "punctuators" package).
"""

import argparse
import json
import os
import re
import sys
import zipfile
from datetime import datetime

from transcript_polish import (MD_META, MD_SECTION, build_paragraphs, count_words,
                               fmt_stamp, parse_md_body, parse_srt, split_combined_md)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.join(SCRIPT_DIR, "subtitles")
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "obsidian_transcripts")
DEFAULT_ZIPS = os.path.join(SCRIPT_DIR, "_archive_zips")
STATE_NAME = ".clean_state.json"
EXTS = (".md", ".srt", ".vtt")
LOOSE_FOLDER = "_Unsorted"          # files sitting directly in subtitles/

PUNCT_MODEL = "pcs_en"   # punctuators name for Hugging Face 1-800-BAD-CODE/punct_cap_seg_en
PUNCT_RATIO_OK = 0.02               # >= 2 sentence marks per 100 words = already punctuated
MODE_RANK = {"basic": 0, "punctuated": 1}

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
TRANSCRIPT_HEAD = re.compile(r"^#{2,3}\s+Transcript\s*$", re.M)

TAGS = re.compile(r"\[(?:music|applause|laughter|laughs|inaudible|silence|cheering|__)[^\]]*\]", re.I)
FILLER = re.compile(r"(?<![\w'])(?:u+m+|u+h+m*|e+r+m+|hmm+|mm+)(?![\w'])[,.]?\s*", re.I)
STUTTER = re.compile(r"\b(\w+)(?:\s+\1\b)+", re.I)
KEEP_DOUBLE = {"that", "had", "is", "do", "very", "no", "bye", "ha", "so"}
LONE_I = re.compile(r"(?<![\w'])i(?=(?:['’](?:m|ve|ll|d|s)\b)|(?![\w'’]))")
SENT_START = re.compile(r"(^|[.!?]\s+)([a-z])")


# ---------------------------------------------------------------------------
# Reading sources
# ---------------------------------------------------------------------------

def safe_name(title):
    name = re.sub(r'[<>:"/\\|?*#^\[\]]', "", title)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:120] or "untitled"


def front_matter(raw):
    m = FRONT_MATTER.match(raw)
    if not m:
        return {}, raw
    meta = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep:
            meta[k.strip()] = v.strip().strip('"')
    return meta, raw[m.end():]


def read_videos(path):
    """Source file -> list of {title, video_id, url, language, segments}."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".srt", ".vtt"):
        return [{"title": os.path.splitext(os.path.basename(path))[0],
                 "video_id": "", "url": "", "language": "", "segments": parse_srt(path)}]

    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        raw = fh.read()

    if MD_SECTION.search(raw):                       # combined channel/playlist dump
        videos = split_combined_md(raw)
        for v in videos:
            v["segments"] = parse_md_body(v.pop("body"))
        return videos

    fm, rest = front_matter(raw)
    meta = {k: v.strip("` ") for k, v in MD_META.findall(rest)}
    title = fm.get("title")
    if not title:
        t = re.search(r"^#\s+(.+)$", rest, re.M)
        title = t.group(1).strip() if t else os.path.splitext(os.path.basename(path))[0]
    head = TRANSCRIPT_HEAD.search(rest)
    body = rest[head.end():] if head else ""
    return [{
        "title": title,
        "video_id": fm.get("video_id") or meta.get("Video ID", ""),
        "url": fm.get("url") or meta.get("URL", ""),
        "language": fm.get("transcript_language") or meta.get("Transcript Language", ""),
        "segments": parse_md_body(body.strip()),
    }]


def is_index_file(name):
    return bool(re.search(r"\b000 Index\.md$", name))


def list_sources(src_root, only_channel=None):
    """Yield (channel, abs_path, rel_path) for every transcript in the library."""
    for entry in sorted(os.listdir(src_root)):
        full = os.path.join(src_root, entry)
        if os.path.isdir(full):
            if entry.startswith((".", "_")) or (only_channel and entry != only_channel):
                continue
            for f in sorted(os.listdir(full)):
                if f.lower().endswith(EXTS) and not is_index_file(f):
                    yield entry, os.path.join(full, f), f"{entry}/{f}"
        elif entry.lower().endswith(EXTS) and not only_channel:
            yield LOOSE_FOLDER, full, entry


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def is_unpunctuated(text):
    words = len(text.split())
    return words > 50 and len(re.findall(r"[.!?]", text)) / words < PUNCT_RATIO_OK


def _unstutter(m):
    word = m.group(1)
    repeats = len(m.group(0).split())
    return m.group(0) if word.lower() in KEEP_DOUBLE and repeats == 2 else word


def rule_clean(text):
    t = TAGS.sub(" ", text)
    t = FILLER.sub("", t)
    t = STUTTER.sub(_unstutter, t)
    t = re.sub(r"\s+([,.!?])", r"\1", t)
    t = re.sub(r"([,.!?])\1+", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" ,")
    return t


def capitalise(text):
    t = LONE_I.sub("I", text)
    return SENT_START.sub(lambda m: m.group(1) + m.group(2).upper(), t)


_punct_model = None


def punctuate(texts):
    """Run the local punctuation/truecase model over a list of paragraphs."""
    global _punct_model
    if _punct_model is None:
        from punctuators.models import PunctCapSegModelONNX
        print(f"  loading punctuation model {PUNCT_MODEL} ...")
        _punct_model = PunctCapSegModelONNX.from_pretrained(PUNCT_MODEL)
    counts = [len(t.split()) for t in texts]
    if not sum(counts):
        return texts
    # Punctuate the transcript as one piece so sentences can run across the
    # paragraph breaks, then deal the words back out paragraph by paragraph.
    out = _punct_model.infer(texts=[" ".join(texts).lower()], apply_sbd=False)[0]
    words = (out if isinstance(out, str) else " ".join(out)).split()
    if len(words) != sum(counts):
        # Model changed the word count; fall back to one paragraph at a time.
        res = _punct_model.infer(texts=[t.lower() or " " for t in texts], apply_sbd=False)
        return [(r if isinstance(r, str) else " ".join(r)).strip() for r in res]
    paras, pos = [], 0
    for n in counts:
        paras.append(words[pos:pos + n])
        pos += n
    return [" ".join(p) for p in end_on_sentences(paras)]


def end_on_sentences(paras, max_shift=40):
    """Move each paragraph break forward to the next sentence end (same list length)."""
    for i in range(len(paras) - 1):
        cur, nxt = paras[i], paras[i + 1]
        if not cur or cur[-1].endswith((".", "!", "?")):
            continue
        for j, w in enumerate(nxt[:max_shift]):
            if w.endswith((".", "!", "?")):
                cur.extend(nxt[:j + 1])
                del nxt[:j + 1]
                break
    return paras


def clean_texts(paras, use_model):
    """Returns (cleaned paragraph texts, whether the model was used)."""
    texts = [rule_clean(p["text"]) for p in paras]
    used = False
    if use_model and is_unpunctuated(" ".join(texts)):
        texts = punctuate(texts)
        used = True
    return [capitalise(t) for t in texts], used


# ---------------------------------------------------------------------------
# Writing notes
# ---------------------------------------------------------------------------

def stamp_link(seconds, url):
    if seconds is None:
        return ""
    label = fmt_stamp(seconds)
    if not url:
        return f"[{label}]"
    return f"[{label}]({url}{'&' if '?' in url else '?'}t={int(seconds)}s)"


def render_note(video, channel, rel_src, paras, texts, mode):
    url = video["url"] or (f"https://www.youtube.com/watch?v={video['video_id']}"
                           if video["video_id"] else "")
    q = lambda s: json.dumps(s or "", ensure_ascii=False)
    lines = [
        "---",
        f"title: {q(video['title'])}",
        f"channel: {q(channel)}",
        f"video_id: {q(video['video_id'])}",
        f"url: {q(url)}",
        f"transcript_language: {q(video['language'])}",
        f"source_file: {q(rel_src)}",
        f"cleaned: {mode}",
        f"cleaned_on: {datetime.now():%Y-%m-%d}",
        f"words: {count_words(' '.join(texts))}",
        "tags: [youtube, transcript]",
        "---",
        "",
        f"# {video['title']}",
        "",
        f"**Channel:** [[{channel}]]" + (f" · [Watch on YouTube]({url})" if url else ""),
        "",
        "## Transcript",
        "",
    ]
    for p, t in zip(paras, texts):
        if not t:
            continue
        link = stamp_link(p["start"], url)
        lines += [f"{link} {t}" if link else t, ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Archive
# ---------------------------------------------------------------------------

def archive_channels(src_root, zip_root, state):
    os.makedirs(zip_root, exist_ok=True)
    today = f"{datetime.now():%Y-%m-%d}"
    by_channel = {}
    for channel, path, rel in list_sources(src_root):
        by_channel.setdefault(channel, []).append((path, rel))
    for channel, files in sorted(by_channel.items()):
        pending = [rel for _, rel in files if rel not in state]
        if pending:
            print(f"  skip  {channel}: {len(pending)} file(s) not cleaned yet")
            continue
        zpath = os.path.join(zip_root, f"{safe_name(channel)}__ORIGINAL-raw-transcripts__{today}.zip")
        manifest = [f"Original raw transcripts for channel: {channel}",
                    f"Archived: {datetime.now():%Y-%m-%d %H:%M}",
                    f"Cleaned copies live in: obsidian_transcripts/{channel}/",
                    f"Files: {len(files)}", ""]
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for path, rel in files:
                z.write(path, arcname=f"{channel}/{os.path.basename(path)}")
                manifest.append(os.path.basename(path))
            z.writestr("MANIFEST.txt", "\n".join(manifest) + "\n")
        with zipfile.ZipFile(zpath) as z:
            bad = z.testzip()
            count = len(z.namelist()) - 1
        status = "OK" if bad is None and count == len(files) else f"PROBLEM (bad={bad}, count={count})"
        print(f"  zip   {channel}: {len(files)} files -> {os.path.basename(zpath)}  [{status}]")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def save_state(state, out_root, state_path):
    os.makedirs(out_root, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--src", default=DEFAULT_SRC)
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--channel", help="only this channel folder")
    p.add_argument("--punctuate", action="store_true",
                   help="local punctuation model for unpunctuated auto-captions")
    p.add_argument("--limit", type=int, help="process at most N files this run (for testing)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="redo everything, ignore the skip list")
    p.add_argument("--archive", action="store_true", help="zip originals of fully cleaned channels")
    p.add_argument("--zips", default=DEFAULT_ZIPS)
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    src_root, out_root = os.path.abspath(args.src), os.path.abspath(args.out)
    state_path = os.path.join(out_root, STATE_NAME)
    try:
        with open(state_path, encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        state = {}

    if args.archive:
        archive_channels(src_root, os.path.abspath(args.zips), state)
        return

    mode = "punctuated" if args.punctuate else "basic"
    if args.punctuate and not args.dry_run:
        try:
            import punctuators  # noqa: F401
        except ImportError:
            sys.exit("--punctuate needs the model package:  pip install punctuators")

    sources = list(list_sources(src_root, args.channel))
    todo = []
    for channel, path, rel in sources:
        st = os.stat(path)
        prev = state.get(rel)
        if (not args.force and prev and prev["size"] == st.st_size
                and abs(prev["mtime"] - st.st_mtime) < 1
                and MODE_RANK.get(prev["mode"], -1) >= MODE_RANK[mode]
                and all(os.path.exists(os.path.join(out_root, o)) for o in prev["outputs"])):
            continue
        todo.append((channel, path, rel, st))
    print(f"{len(sources)} transcripts in library, {len(sources) - len(todo)} already done, "
          f"{len(todo)} to process ({mode}).")

    # Single-video files first, so a combined channel dump only fills in the gaps.
    todo.sort(key=lambda t: os.path.basename(t[1]).startswith(("channel_", "playlist_")))
    if args.limit:
        todo = todo[:args.limit]
    # Videos already covered by files we are NOT redoing. A file being redone
    # must not count its own earlier output as a duplicate of itself.
    redo = {rel for _, _, rel, _ in todo}
    seen_ids = {vid for rel, s in state.items() if rel not in redo for vid in s.get("video_ids", [])}

    model_words = 0
    stats = {"notes": 0, "dupes": 0, "empty": 0}
    try:
        for n, (channel, path, rel, st) in enumerate(todo, 1):
            try:
                videos = read_videos(path)
            except Exception as e:
                print(f"  ! could not read {rel}: {e}")
                continue
            outputs, ids = [], []
            combined = len(videos) > 1 or os.path.basename(path).startswith(("channel_", "playlist_"))
            for v in videos:
                if combined and v["video_id"] and v["video_id"] in seen_ids:
                    stats["dupes"] += 1
                    continue
                paras = build_paragraphs(v["segments"])
                if not paras:
                    stats["empty"] += 1
                    continue
                if args.dry_run:
                    texts = [x["text"] for x in paras]
                    if args.punctuate and is_unpunctuated(" ".join(texts)):
                        model_words += count_words(" ".join(texts))
                else:
                    texts, used = clean_texts(paras, args.punctuate)
                    if used:
                        model_words += count_words(" ".join(texts))
                name = safe_name(v["title"]) if combined else safe_name(os.path.splitext(os.path.basename(path))[0])
                out_rel = f"{channel}/{name}.md"
                if out_rel in outputs:
                    out_rel = f"{channel}/{name} ({v['video_id'] or len(outputs)}).md"
                outputs.append(out_rel)
                if v["video_id"]:
                    ids.append(v["video_id"])
                    seen_ids.add(v["video_id"])
                if not args.dry_run:
                    dest = os.path.join(out_root, out_rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, "w", encoding="utf-8") as fh:
                        fh.write(render_note(v, channel, rel, paras, texts, mode))
                stats["notes"] += 1

            if not args.dry_run:
                state[rel] = {"size": st.st_size, "mtime": st.st_mtime, "mode": mode,
                              "outputs": outputs, "video_ids": ids}
                if n % 25 == 0 or n == len(todo):
                    save_state(state, out_root, state_path)
                    print(f"  {n}/{len(todo)} files")
    finally:
        if not args.dry_run and state:
            save_state(state, out_root, state_path)

    print(f"\n{stats['notes']} notes {'would be ' if args.dry_run else ''}written to {out_root}")
    if stats["dupes"]:
        print(f"{stats['dupes']} videos in combined dumps skipped (already have their own file)")
    if stats["empty"]:
        print(f"{stats['empty']} videos had no transcript text")
    if args.punctuate:
        print(f"{model_words:,} words {'would go' if args.dry_run else 'went'} through the punctuation model")


if __name__ == "__main__":
    main()
