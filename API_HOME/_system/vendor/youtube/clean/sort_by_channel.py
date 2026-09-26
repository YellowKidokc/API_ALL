"""
sort_by_channel.py — Move loose transcripts in subtitles/ into per-channel folders.

Older runs wrote every transcript into one flat folder. Each .md still has its
**Video ID:** line, so this looks up the uploading channel for that ID through
YouTube's public oEmbed endpoint (no API key, no yt-dlp, no proxy) and moves the
file into subtitles/<Channel Name>/ — the same folder name ytgrab.py uses now,
so the files land next to anything downloaded later.

  channel_<Name> - Videos_<stamp>.md   -> folder named from the file name
  playlist_*.md                        -> left where it is (not one channel)
  anything else with a Video ID        -> oEmbed lookup

Lookups are cached in subtitles/.channel_cache.json, so re-runs are instant.
Videos that are private/deleted (lookup fails) are left in place and listed.

Usage
-----
    python sort_by_channel.py              # dry run: show what would move
    python sort_by_channel.py --apply      # actually move the files
    python sort_by_channel.py --dir PATH   # a different subtitles folder

Stdlib only.
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DIR = os.path.join(SCRIPT_DIR, "subtitles")
CACHE_NAME = ".channel_cache.json"

VIDEO_ID = re.compile(r"^\*\*Video ID:\*\*\s*`?([A-Za-z0-9_-]{11})`?", re.M)
CHANNEL_FILE = re.compile(r"^channel_(.+?)_\d{8}_\d{6}\.md$")
_TAB_SUFFIXES = (" - Videos", " - Shorts", " - Streams", " - Live", " - Playlists")


# Same rules as ytgrab.py / ytbsd.py so folder names match new downloads.
def sanitize_filename(name: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip().rstrip('.')
    return sanitized[:100] if len(sanitized) > 100 else sanitized


def channel_folder_name(raw: str) -> str:
    name = (raw or "").strip()
    for suffix in _TAB_SUFFIXES:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
            break
    return name


def first_video_id(path: str):
    with open(path, encoding="utf-8", errors="replace") as fh:
        head = fh.read(4000)
    m = VIDEO_ID.search(head)
    return m.group(1) if m else None


def lookup_channel(video_id: str):
    """Channel name for a video ID, or None if YouTube won't say (private/deleted)."""
    url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(
        f"https://www.youtube.com/watch?v={video_id}", safe="")
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.load(resp).get("author_name")
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404):
                break                # embedding disabled or video gone — try the page
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    return lookup_channel_from_page(video_id)


OWNER = re.compile(r'"ownerChannelName":"((?:[^"\\]|\\.)*)"')


def lookup_channel_from_page(video_id: str):
    """Fallback for channels that disable embedding (oEmbed answers 401)."""
    req = urllib.request.Request(f"https://www.youtube.com/watch?v={video_id}",
                                 headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None
    m = OWNER.search(html)
    return json.loads(f'"{m.group(1)}"') if m else None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", default=DEFAULT_DIR, help="subtitles folder (default: ./subtitles)")
    p.add_argument("--apply", action="store_true", help="move files (default is a dry run)")
    p.add_argument("--workers", type=int, default=8, help="parallel oEmbed lookups")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    root = os.path.abspath(args.dir)
    cache_path = os.path.join(root, CACHE_NAME)
    try:
        with open(cache_path, encoding="utf-8") as fh:
            cache = json.load(fh)
    except (OSError, ValueError):
        cache = {}

    loose = sorted(f for f in os.listdir(root)
                   if f.lower().endswith(".md") and os.path.isfile(os.path.join(root, f)))
    print(f"{len(loose)} loose .md files in {root}")

    plan = {}          # filename -> channel
    skipped = []       # (filename, reason)
    need_lookup = {}   # filename -> video id

    for f in loose:
        m = CHANNEL_FILE.match(f)
        if m:
            plan[f] = channel_folder_name(m.group(1))
        elif f.startswith("playlist_"):
            skipped.append((f, "playlist file (mixed channels)"))
        else:
            vid = first_video_id(os.path.join(root, f))
            if not vid:
                skipped.append((f, "no Video ID"))
            elif cache.get(vid):          # failed lookups (None) get retried
                plan[f] = cache[vid]
            else:
                need_lookup[f] = vid

    if need_lookup:
        print(f"Looking up {len(need_lookup)} channels via oEmbed "
              f"({len(loose) - len(need_lookup)} already known)...")
        ids = sorted(set(need_lookup.values()))
        done = 0
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for vid, name in zip(ids, pool.map(lookup_channel, ids)):
                cache[vid] = name
                done += 1
                if done % 100 == 0:
                    print(f"  {done}/{len(ids)}")
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, indent=1, ensure_ascii=False)
        for f, vid in need_lookup.items():
            plan[f] = cache.get(vid)

    moves = []
    for f, channel in sorted(plan.items()):
        folder = sanitize_filename(channel or "")
        if not folder:
            skipped.append((f, "channel lookup failed (private/deleted?)"))
            continue
        dest = os.path.join(root, folder, f)
        if os.path.exists(dest):
            skipped.append((f, f"already exists in '{folder}'"))
            continue
        moves.append((f, folder))

    counts = Counter(folder for _, folder in moves)
    print(f"\n{len(moves)} files -> {len(counts)} channel folders:")
    for folder, n in counts.most_common():
        print(f"  {n:5d}  {folder}")

    if skipped:
        print(f"\n{len(skipped)} left in place:")
        for f, why in skipped:
            print(f"  - {f}  [{why}]")

    if not args.apply:
        print("\nDry run — nothing moved. Re-run with --apply to move the files.")
        return

    for f, folder in moves:
        os.makedirs(os.path.join(root, folder), exist_ok=True)
        shutil.move(os.path.join(root, f), os.path.join(root, folder, f))
    print(f"\nMoved {len(moves)} files.")


if __name__ == "__main__":
    sys.exit(main())
