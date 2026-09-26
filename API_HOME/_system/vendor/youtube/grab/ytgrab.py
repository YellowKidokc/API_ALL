"""
ytgrab.py — non-interactive entry point for YTBSD.

One URL or twenty. No menu, no prompts. Same pipeline underneath.

    python ytgrab.py https://www.youtube.com/watch?v=dxfw1iehEA8
    python ytgrab.py URL1 URL2 URL3
    python ytgrab.py --file urls.txt
    python ytgrab.py --clipboard
    python ytgrab.py https://www.youtube.com/@chasehughesofficial

Differences from the ytbsd.py wizard, all deliberate:
  1. Direct connection is tried FIRST for every video. Only failures fall
     through to a proxy. The wizard's collaborative queue never tries
     direct, which is why one video burned ~250 proxy attempts.
  2. Webshare rotating residential proxies are the fallback when
     credentials are present. The free-proxy swarm is the last resort.
  3. Thread count scales to the WORK, not to the proxy list. The wizard
     defaulted to len(proxies) — 300 threads at 1 video.
  4. Markdown output keeps [MM:SS] timestamps per segment, so a line is
     citable. The wizard flattens segments into one prose blob.
  5. Channel fetches default to /videos only. The /shorts tab falls into
     a 200-proxy retry grind when it fails, which is the observed hang.
     Pass --shorts if you actually want them.

WEBSHARE SETUP — credentials come from the environment, never from a file
in this repo (this is a git repo; a committed secret is a leaked secret):

    setx WEBSHARE_USER "your-proxy-username"
    setx WEBSHARE_PASS "your-proxy-password"

Open a NEW terminal after setx — it doesn't affect the current one. Buy a
"Residential" package, NOT "Proxy Server" and NOT "Static Residential";
static defeats the rotation, which is the whole point. The username goes
in WITHOUT any -rotate suffix — WebshareProxyConfig appends that itself.

Untested — written against the source, not run. Findings from the first
run should come straight back here.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime

# A status glyph must not make an otherwise successful lookup fail when a
# Windows terminal is using a legacy code page.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(errors="replace")

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

import ytbsd
from ytbsd import (
    PROXY_FILE,
    SCRIPT_DIR,
    ProxyPool,
    NoTranscriptError,
    check_transcript_availability,
    extract_video_id,
    fetch_content_with_timeout,
    get_video_ids_from_url,
    normalize_channel_url,
    sanitize_filename,
)

DEFAULT_OUT = os.path.join(SCRIPT_DIR, "subtitles")

# Cap threads so a small job doesn't spin up hundreds of workers.
MAX_AUTO_THREADS = 64
THREADS_PER_VIDEO = 4

# Webshare rotates server-side, so retries are the mechanism that gets a
# fresh IP. The library's own default for residential pools is 10.
WEBSHARE_RETRIES = 10


# ---------------------------------------------------------------------------
# URL shape detection
# ---------------------------------------------------------------------------

def detect_mode(url: str) -> str:
    """Return 'single', 'playlist', or 'channel' from the URL's shape alone."""
    u = url.strip()

    # Bare 11-char video ID
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", u):
        return "single"

    lowered = u.lower()

    # A watch URL carrying a list= is still one video unless it's a pure
    # playlist link. Treat /playlist?list= as playlist, watch?v=...&list= as single.
    if "/playlist" in lowered or lowered.startswith("list="):
        return "playlist"
    if "v=" in lowered or "youtu.be/" in lowered or "/shorts/" in lowered:
        return "single"
    if "@" in u or "/channel/" in lowered or "/c/" in lowered or "/user/" in lowered:
        return "channel"
    if "list=" in lowered:
        return "playlist"

    # Unknown shape — let yt-dlp decide, treat as single.
    return "single"


def read_urls(args) -> list[str]:
    urls: list[str] = list(args.urls)

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)

    if args.clipboard:
        try:
            import tkinter

            root = tkinter.Tk()
            root.withdraw()
            clip = root.clipboard_get()
            root.destroy()
        except Exception as e:
            print(f"Could not read clipboard: {e}")
            clip = ""
        for line in clip.splitlines():
            line = line.strip()
            if line:
                urls.append(line)

    # De-dupe, preserve order
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


# ---------------------------------------------------------------------------
# Resolution: URLs -> flat video list
# ---------------------------------------------------------------------------

def resolve(urls: list[str], proxy_pool: ProxyPool, want_shorts: bool) -> list[dict]:
    """Expand every URL into video dicts. Mixed shapes are fine."""
    videos: list[dict] = []
    seen_ids = set()

    for url in urls:
        mode = detect_mode(url)

        if mode == "single":
            url = f"https://www.youtube.com/watch?v={extract_video_id(url)}"
            targets = [(url, "single")]
        elif mode == "channel":
            base = normalize_channel_url(url)
            targets = [(base + "/videos", "channel")]
            if want_shorts:
                targets.append((base + "/shorts", "channel"))
        else:
            targets = [(url, "playlist")]

        for target_url, target_mode in targets:
            try:
                found, source_name, _type = get_video_ids_from_url(
                    target_url, target_mode, proxy_pool
                )
            except Exception as e:
                print(f"  ! could not resolve {target_url}: {str(e).splitlines()[0][:80]}")
                continue

            for v in found:
                if v.get("id") and v["id"] not in seen_ids:
                    seen_ids.add(v["id"])
                    # Remember where this video came from so the writer can
                    # file it under its channel instead of one flat heap.
                    # For a channel or playlist that is the source name; for a
                    # lone video the source name is the video's own title,
                    # which would make a folder per video, so use the uploader.
                    if target_mode == "single":
                        v["source_folder"] = v.get("uploader") or "Single Videos"
                    else:
                        v["source_folder"] = source_name or "Unsorted"
                    videos.append(v)

    return videos


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------

def _result(video: dict, text=None, fetched=None, lang=None, method=None) -> dict:
    return {
        "id": video["id"],
        "title": video["title"],
        # Carried through so the writer still knows which channel this came
        # from - this dict is rebuilt from scratch, not the original.
        "source_folder": video.get("source_folder", ""),
        "transcript": text,
        "fetched_transcript": fetched,
        "language": lang,
        "method": method,
        "error_detail": None,
    }


def _pick_transcript(transcript_list):
    """English first, then an English translation, then anything."""
    try:
        t = transcript_list.find_transcript(["en"])
        kind = "auto-generated" if t.is_generated else "manual"
        return t, f"English ({kind})"
    except Exception:
        pass

    for t in transcript_list:
        if t.is_translatable:
            codes = [l.get("language_code", "") for l in t.translation_languages]
            if "en" in codes:
                return t.translate("en"), f"Translated from {t.language}"

    available = list(transcript_list)
    if available:
        return available[0], f"{available[0].language} (no English available)"

    raise NoTranscriptError("No transcript available in any language")


# ---------------------------------------------------------------------------
# Pass 1 — direct, no proxies
# ---------------------------------------------------------------------------

def try_direct(video: dict) -> dict | None:
    """
    Attempt a transcript with no proxy. Returns a result dict on success,
    None if it should be retried through a proxy.

    A definitive "no transcript" also returns a result — no point burning
    proxy budget on a video that has no captions.
    """
    try:
        transcript_obj, lang_info = check_transcript_availability(video["id"], proxy=None)
    except NoTranscriptError:
        return _result(video, method="no_transcript")
    except Exception:
        return None

    try:
        text, fetched = fetch_content_with_timeout(transcript_obj)
    except Exception:
        return None

    return _result(video, text, fetched, lang_info, "direct")


# ---------------------------------------------------------------------------
# Pass 2 — Webshare rotating residential
# ---------------------------------------------------------------------------

def get_webshare_config(locations: list[str] | None = None) -> WebshareProxyConfig | None:
    """Build a Webshare config from the environment, or None if unset."""
    user = os.environ.get("WEBSHARE_USER", "").strip()
    password = os.environ.get("WEBSHARE_PASS", "").strip()
    if not user or not password:
        return None
    return WebshareProxyConfig(
        proxy_username=user,
        proxy_password=password,
        filter_ip_locations=locations or None,
        retries_when_blocked=WEBSHARE_RETRIES,
    )


def try_webshare(video: dict, config: WebshareProxyConfig) -> dict | None:
    """
    Attempt a transcript through Webshare's rotating pool. The library
    handles rotation and retry-on-block internally, so this is one call,
    not a swarm.
    """
    api = YouTubeTranscriptApi(proxy_config=config)
    try:
        transcript_list = api.list(video["id"])
        transcript_obj, lang_info = _pick_transcript(transcript_list)
    except NoTranscriptError:
        return _result(video, method="no_transcript")
    except Exception:
        return None

    try:
        text, fetched = fetch_content_with_timeout(transcript_obj)
    except Exception:
        return None

    return _result(video, text, fetched, lang_info, "webshare")


# ---------------------------------------------------------------------------
# Timestamped markdown
# ---------------------------------------------------------------------------

def stamp(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def transcript_block(video: dict) -> str:
    """Timestamped lines if we have segments, flat text otherwise."""
    fetched = video.get("fetched_transcript")
    if fetched:
        return "\n".join(f"[{stamp(seg.start)}] {seg.text}" for seg in fetched)
    return video.get("transcript") or "*No transcript available for this video.*"


_TAB_SUFFIXES = (" - Videos", " - Shorts", " - Streams", " - Live", " - Playlists")


def channel_folder_name(raw: str) -> str:
    """Folder name for a channel, without the tab suffix YouTube adds.

    Enumerating a channel goes through its /videos tab, and yt-dlp titles
    that page "Name - Videos". Left alone the same creator ends up with a
    "Name - Videos" folder and a "Name - Shorts" folder.
    """
    name = (raw or "").strip()
    for suffix in _TAB_SUFFIXES:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
            break
    return name


def write_markdown(video: dict, out_dir: str) -> str:
    # Everything used to land in one flat directory, so a 200-video channel
    # became 200 loose files with no sign of where they came from. Each video
    # now goes in a folder named for its channel or playlist.
    folder = sanitize_filename(channel_folder_name(video.get("source_folder", ""))) or "Unsorted"
    target_dir = os.path.join(out_dir, folder)
    os.makedirs(target_dir, exist_ok=True)
    name = sanitize_filename(video["title"]) or video["id"]
    path = os.path.join(target_dir, f"{name}.md")

    lines = [
        f"# {video['title']}",
        "",
        f"**Video ID:** `{video['id']}`",
        f"**URL:** https://www.youtube.com/watch?v={video['id']}",
        f"**Transcript Language:** {video.get('language') or 'unknown'}",
        f"**Retrieved via:** {video.get('method') or 'unknown'}",
        f"**Captured:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
        "## Transcript",
        "",
        transcript_block(video),
        "",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        description="Grab YouTube transcripts. One URL or many. No prompts."
    )
    p.add_argument("urls", nargs="*", help="Video, playlist, or channel URLs (or bare video IDs)")
    p.add_argument("--file", help="Text file with one URL per line")
    p.add_argument("--clipboard", action="store_true", help="Read URLs from the clipboard")
    p.add_argument("--out", default=DEFAULT_OUT, help=f"Output directory (default: {DEFAULT_OUT})")
    p.add_argument("--threads", type=int, default=0, help="Override auto thread count")
    p.add_argument("--shorts", action="store_true", help="Also pull a channel's /shorts tab")
    p.add_argument("--no-webshare", action="store_true", help="Skip Webshare even if configured")
    p.add_argument("--locations", default="", help="Comma-separated Webshare country codes, e.g. US,CA")
    p.add_argument("--free-proxies", action="store_true",
                   help="Allow the free-proxy swarm as a last resort (off by default)")
    p.add_argument("--no-timestamps", action="store_true", help="Flat prose instead of [MM:SS] lines")
    p.add_argument("--limit", type=int, default=0,
                   help="Fetch at most N videos this session, then stop (for huge channels)")
    p.add_argument("--direct-giveup", type=int, default=8,
                   help="Abandon the direct pass after N straight failures (0 disables)")
    p.add_argument("--skip-direct", action="store_true",
                   help="Go straight to Webshare; skip the direct pass entirely")
    p.add_argument("--status", action="store_true",
                   help="Report what is saved and what is still missing, then exit")
    args = p.parse_args()

    urls = read_urls(args)
    if not urls:
        p.error("no URLs given (pass them as arguments, --file, or --clipboard)")

    # Webshare first-class; free proxies only if explicitly allowed.
    locations = [c.strip() for c in args.locations.split(",") if c.strip()]
    webshare = None if args.no_webshare else get_webshare_config(locations)

    if webshare:
        print("Webshare credentials found — rotating residential enabled.")
    elif not args.no_webshare:
        print("No WEBSHARE_USER / WEBSHARE_PASS in environment — direct only.")

    # Only fetch the free list if it's actually going to be used.
    if args.free_proxies and not os.path.exists(PROXY_FILE):
        ytbsd.download_fresh_proxies(PROXY_FILE)
    # Merely having proxies.txt on disk must not activate the swarm.  Both URL
    # resolution and transcript fetching use it only after explicit opt-in.
    proxy_pool = (
        ProxyPool(PROXY_FILE, validate=False)
        if args.free_proxies and os.path.exists(PROXY_FILE)
        else None
    )

    print(f"\nResolving {len(urls)} URL(s)...")
    videos = resolve(urls, proxy_pool, want_shorts=args.shorts)
    if not videos:
        print("Nothing to download.")
        return
    print(f"Resolved to {len(videos)} video(s)")

    # Skip videos already saved by a previous run. Re-fetching them wastes
    # requests and is what trips YouTube's rate limit on channel re-runs.
    # Failed runs still write a placeholder marked "Retrieved via:** failed",
    # so those are retried rather than treated as done.
    def already_saved(v: dict) -> bool:
        name = sanitize_filename(v["title"]) or v["id"]
        folder = sanitize_filename(channel_folder_name(v.get("source_folder", ""))) or "Unsorted"
        # Check the channel folder first, then the old flat location, so a
        # library downloaded before per-channel folders existed is still
        # recognised and does not get fetched all over again.
        candidates = [
            os.path.join(args.out, folder, f"{name}.md"),
            os.path.join(args.out, f"{name}.md"),
        ]
        for path in candidates:
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8", errors="replace") as f:
                if "**Retrieved via:** failed" not in f.read(2000):
                    return True
        return False

    # One pass over the folder: a big channel means thousands of stat calls.
    saved_flags = {v["id"]: already_saved(v) for v in videos}
    skipped = [v for v in videos if saved_flags[v["id"]]]
    videos = [v for v in videos if not saved_flags[v["id"]]]

    if args.status:
        print(f"\nStatus of {args.out}")
        print(f"  complete:       {len(skipped)}")
        print(f"  still to fetch: {len(videos)}")
        for v in videos[:20]:
            print(f"    - {v['title'][:70]}")
        if len(videos) > 20:
            print(f"    ... and {len(videos) - 20} more")
        return

    if skipped:
        print(f"Skipping {len(skipped)} already saved in {args.out}")
    if not videos:
        print("Everything is already downloaded.")
        return
    if args.limit and len(videos) > args.limit:
        print(f"{len(videos)} left to fetch; this session takes {args.limit}")
        videos = videos[:args.limit]
    print(f"{len(videos)} to fetch now\n")

    # --- Pass 1: direct, no proxies ---
    print("Pass 1: direct connection..." if not args.skip_direct
          else "Pass 1: skipped (--skip-direct)")
    done: list[dict] = []
    pending: list[dict] = []
    written: list[str] = []

    def save(result: dict) -> None:
        """Write one transcript the moment it is captured.

        Nothing waits for a final batch write, so a long channel run can be
        stopped, crash, or span several days without losing what it already
        fetched. Failure placeholders are written too: already_saved() treats
        them as unfinished, so the next run retries them.
        """
        if args.no_timestamps:
            result["fetched_transcript"] = None
        written.append(write_markdown(result, args.out))
    misses = 0
    abandoned = False
    for index, v in enumerate(videos):
        if args.skip_direct or abandoned:
            pending.append(v)
            continue
        result = try_direct(v)
        if result is None:
            pending.append(v)
            misses += 1
            print(f"  . {v['title'][:60]} -> needs proxy")
            # Once YouTube rate-limits the IP, every further direct attempt
            # just burns a timeout and deepens the block. Hand the rest to
            # Webshare instead of walking thousands of certain failures.
            if args.direct_giveup and misses >= args.direct_giveup:
                abandoned = True
                remaining = len(videos) - index - 1
                print(f"  ! {misses} straight failures - this IP looks rate-limited.")
                if remaining:
                    print(f"    Sending the remaining {remaining} straight to the proxy passes.")
        else:
            done.append(result)
            save(result)
            misses = 0
            tag = "no transcript" if result["method"] == "no_transcript" else "ok"
            print(f"  + {v['title'][:60]} -> {tag}")

    # --- Pass 2: Webshare rotating residential ---
    if pending and webshare:
        print(f"\nPass 2: {len(pending)} video(s) via Webshare...")
        still_pending = []
        for v in pending:
            result = try_webshare(v, webshare)
            if result is None:
                still_pending.append(v)
                print(f"  . {v['title'][:60]} -> still blocked")
            else:
                done.append(result)
                save(result)
                tag = "no transcript" if result["method"] == "no_transcript" else "ok"
                print(f"  + {v['title'][:60]} -> {tag}")
        pending = still_pending

    # --- Pass 3: free-proxy swarm, opt-in only ---
    if pending and args.free_proxies and proxy_pool:
        if args.threads > 0:
            threads = args.threads
        else:
            threads = max(1, min(
                len(pending) * THREADS_PER_VIDEO,
                len(proxy_pool.proxies) or 1,
                MAX_AUTO_THREADS,
            ))
        print(f"\nPass 3: {len(pending)} video(s) via free proxies, {threads} thread(s)...")
        swarm_results, _success, _interrupted = ytbsd.download_transcripts_parallel(
            pending,
            source_name="ytgrab",
            source_type="mixed",
            num_threads=threads,
            output_config={"format": "markdown", "split": False, "max_words": None},
        )
        done.extend(swarm_results)
        for result in swarm_results:
            save(result)
        pending = []

    for v in pending:
        failure = _result(v, method="failed")
        done.append(failure)
        save(failure)

    # Every file was written as it was captured; nothing left to flush.
    print()
    ok = sum(1 for d in done if d.get("transcript"))
    print("=" * 60)
    print(f"  {ok}/{len(done)} transcripts captured")
    print(f"  Output: {args.out}")
    for path in written[:10]:
        print(f"    - {os.path.basename(path)}")
    if len(written) > 10:
        print(f"    ... and {len(written) - 10} more")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Everything captured so far is already saved.")
        print("Run the same command again to resume; finished videos are skipped.")
        sys.exit(1)
