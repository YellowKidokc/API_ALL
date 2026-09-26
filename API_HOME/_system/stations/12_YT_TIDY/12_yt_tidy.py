"""12_YT_TIDY: every transcript gets one uniform name and an Obsidian-ready note. Local, no API.

  yt_subtitles/<Channel>/Gary Habermas - Chapter 159 - The Historical Jesus - Gary Habermas.md
      ->  yt_markdown/<Channel>/Ch 159 - The Historical Jesus.md
          front matter (channel, number, published, video id, url, keywords, tags), H1 "Ch 159 · The Historical Jesus",
          the transcript underneath

One for one: each note is written the moment it is ready (temp file, then swap), and a state file remembers which
source became which note, so a re-run only does new or changed transcripts. The originals are never touched
unless you ask (--rename-originals shows the renames; add --apply to do them).

--watch: keeps an eye on yt_subtitles. When a channel folder has new transcripts and nothing has arrived for
--quiet-minutes (the download has finished), it converts SRT/VTT/JSON (07), tidies (this station) and, unless
--no-summary, writes the channel summary (13, DeepSeek) for that channel. Then it waits for the next download.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine import ytnames  # noqa: E402
from engine.output import sha256_file  # noqa: E402
from engine.paths import API_HOME, PathConfigurationError, external  # noqa: E402
from engine.text import strip_front_matter  # noqa: E402

LABEL = "12_YT_TIDY"
STATE = "_tidy_state.json"
BUSY = {".part", ".ytdl", ".temp", ".tmp"}      # yt-dlp is still writing
RAW = {".srt", ".vtt", ".json"}                 # 07 converts these first


def parse_args():
    p = argparse.ArgumentParser(prog=LABEL, description="Uniform names + Obsidian notes for YouTube transcripts (local)")
    p.add_argument("items", nargs="*", help="channel folders or names (default: every channel)")
    p.add_argument("--channel", help="one channel folder name")
    p.add_argument("--limit", type=int, help="at most this many transcripts")
    p.add_argument("--redo", action="store_true", help="rewrite notes even when the transcript did not change")
    p.add_argument("--dates", action="store_true", help="look up publish dates with yt-dlp for videos without a number")
    p.add_argument("--rename-originals", action="store_true", help="also give the originals the uniform name (preview)")
    p.add_argument("--apply", action="store_true", help="with --rename-originals: really rename")
    p.add_argument("--watch", action="store_true", help="keep watching yt_subtitles for finished downloads")
    p.add_argument("--quiet-minutes", type=float, default=5, help="--watch: a channel is finished after this long without new files")
    p.add_argument("--interval", type=int, default=60, help="--watch: seconds between looks")
    p.add_argument("--no-summary", action="store_true", help="--watch: tidy only, skip 13_YT_CHANNEL_SUMMARY")
    p.add_argument("--dry-run", action="store_true", help="show what would be written")
    return p.parse_args()


def log(msg: str) -> None:
    print(f"{datetime.now():%H:%M:%S} [12] {msg}", flush=True)


# ------------------------------------------------------------------ reading a ytgrab transcript
def read_source(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    head = raw[:4000]
    title = re.search(r"^#\s+(.+)$", head, re.M)
    vid = (re.search(r"\*\*Video ID:\*\*\s*`?([A-Za-z0-9_-]{6,})`?", head) or re.search(r"video_id:\s*[\"']?([A-Za-z0-9_-]{6,})", head))
    url = re.search(r"\*\*URL:\*\*\s*<?(\S+?)>?\s*$", head, re.M)
    date = re.search(r"(?:upload_date|published):\s*[\"']?(\d{4}-?\d{2}-?\d{2})", head)
    body = raw.split("## Transcript", 1)[1] if "## Transcript" in raw else strip_front_matter(raw)
    body = re.sub(r"^\s*#\s+.+\n", "", body.lstrip("\n"), count=1) if "## Transcript" not in raw else body
    vid_s = vid.group(1) if vid else ""
    return {"title": title.group(1).strip() if title else path.stem, "video_id": vid_s,
            "url": url.group(1) if url else (f"https://www.youtube.com/watch?v={vid_s}" if vid_s else ""),
            "date": date.group(1).replace("-", "") if date else "", "body": body.strip("\n")}


def info_date(path: Path) -> str:
    """upload_date from a yt-dlp .info.json beside the transcript, when there is one."""
    info = path.with_suffix(".info.json")
    if info.is_file():
        try:
            return str(json.loads(info.read_text(encoding="utf-8")).get("upload_date") or "")
        except ValueError:
            return ""
    return ""


def lookup_dates(ids: list[str], cache: dict) -> None:
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        log("--dates: yt-dlp is not installed (pip install yt-dlp); names without a number keep just the title")
        return
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        for vid in ids:
            if vid in cache:
                continue
            try:
                cache[vid] = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False).get("upload_date", "")
                log(f"date {vid} {cache[vid]}")
            except Exception as exc:  # removed, private, network
                cache[vid] = ""
                log(f"date {vid}: {exc}")


# ------------------------------------------------------------------ writing the note
def yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def note(src: dict, name: ytnames.Name, channel: str, source_name: str, keywords: list[str]) -> str:
    tag = re.sub(r"[^a-z0-9]+", "-", channel.lower()).strip("-") or "channel"
    fm = ["---", f"title: {yaml_str(name.title)}", f"channel: {yaml_str(channel)}"]
    if name.number is not None:
        fm.append(f"{'chapter' if name.label == 'Ch' else 'number'}: {name.number}")
    fm += [f"published: {name.date or ''}", f"video_id: {src['video_id']}", f"url: {src['url']}",
           f"keywords: [{', '.join(yaml_str(k) for k in keywords)}]", f"tags: [youtube, {tag}]",
           f"source: {yaml_str(source_name)}", "---", "", f"# {name.h1}", ""]
    if src["url"]:
        fm += [f"[Watch on YouTube]({src['url']})", ""]
    return "\n".join(fm) + "\n## Transcript\n\n" + src["body"].strip() + "\n"


def existing_keywords(path: Path) -> list[str]:
    """13 writes keywords into the note; a re-tidy keeps them."""
    if not path.is_file():
        return []
    match = re.search(r"^keywords:\s*\[(.*)\]\s*$", path.read_text(encoding="utf-8", errors="replace")[:3000], re.M)
    if not match or not match.group(1).strip():
        return []
    try:
        return json.loads(f"[{match.group(1)}]")
    except ValueError:
        return []


def transcripts(folder: Path) -> list[Path]:
    return sorted(p for p in folder.glob("*.md") if not p.name.startswith("_"))


def tidy_channel(folder: Path, args, out_root: Path, budget: list[int]) -> int:
    channel = folder.name
    out = out_root / channel
    out.mkdir(parents=True, exist_ok=True)
    state_path = out / STATE
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"files": {}, "dates": {}}
    files = transcripts(folder)
    if args.dates:
        pending = [read_source(p) for p in files]
        lookup_dates([s["video_id"] for s in pending if s["video_id"] and ytnames.parse(s["title"], channel).number is None],
                     state["dates"])
    taken = {v["note"]: k for k, v in state["files"].items()}
    done = 0
    for path in files:
        if budget[0] <= 0:
            break
        digest = sha256_file(path)
        prior = state["files"].get(path.name)
        if prior and prior.get("sha256") == digest and (out / prior["note"]).exists() and not args.redo:
            continue
        src = read_source(path)
        date = src["date"] or info_date(path) or state["dates"].get(src["video_id"], "")
        name = ytnames.parse(src["title"], channel, date)
        stem = name.file_stem
        if taken.get(f"{stem}.md", path.name) != path.name:     # two videos, same name: keep both
            stem = ytnames.safe(f"{stem} ({src['video_id'] or digest[:8]})")
        target = out / f"{stem}.md"
        if prior and prior["note"] != target.name and (out / prior["note"]).exists() and not args.dry_run:
            (out / prior["note"]).rename(target)                  # the naming rule changed: move, keep keywords
        if args.dry_run:
            log(f"would write {channel}/{target.name}   <-  {path.name}")
        else:
            text = note(src, name, channel, path.name, existing_keywords(target))
            tmp = target.with_suffix(".tmp")
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(target)
            state["files"][path.name] = {"note": target.name, "sha256": digest, "video_id": src["video_id"],
                                         "title": src["title"], "at": datetime.now().isoformat(timespec="seconds")}
            taken[target.name] = path.name
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")  # one for one
            log(f"OK  {channel}/{target.name}")
        done += 1
        budget[0] -= 1
    if args.rename_originals:
        rename_originals(folder, state, args.apply and not args.dry_run, state_path)
    return done


def rename_originals(folder: Path, state: dict, apply: bool, state_path: Path) -> None:
    for old, rec in sorted(state["files"].items()):
        src, dst = folder / old, folder / rec["note"]
        if old == rec["note"] or not src.exists():
            continue
        if dst.exists():
            log(f"skip {old}: {dst.name} already exists")
            continue
        if apply:
            src.rename(dst)
            for side in (".info.json", ".comments.json"):
                if src.with_suffix(side).exists():
                    src.with_suffix(side).rename(dst.with_suffix(side))
            state["files"][dst.name] = state["files"].pop(old)
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
            log(f"renamed  {old}  ->  {dst.name}")
        else:
            log(f"would rename  {old}  ->  {dst.name}")
    if not apply:
        log("preview only: add --apply to rename the originals")


def channels(args, base: Path) -> list[Path]:
    names = list(args.items) + ([args.channel] if args.channel else [])
    if names:
        return [Path(n) if Path(n).is_dir() else base / n for n in names]
    return sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


# ------------------------------------------------------------------ watching
def channel_status(folder: Path, out_root: Path) -> tuple[float, bool, bool]:
    """(seconds since the newest file arrived, still downloading, has work)"""
    newest, busy = 0.0, False
    for p in folder.iterdir():
        if p.is_file():
            newest = max(newest, p.stat().st_mtime)
            busy = busy or p.suffix.lower() in BUSY
    state_path = out_root / folder.name / STATE
    known = json.loads(state_path.read_text(encoding="utf-8"))["files"] if state_path.exists() else {}
    raw = any(p.suffix.lower() in RAW and not p.name.endswith(".info.json") for p in folder.iterdir() if p.is_file())
    work = raw or any(p.name not in known for p in transcripts(folder))
    return time.time() - newest, busy, work


def run_station(args_list: list[str]) -> int:
    log("running: " + " ".join(args_list))
    return subprocess.run([sys.executable, *args_list], cwd=API_HOME).returncode


def watch(args, base: Path, out_root: Path) -> int:
    quiet = args.quiet_minutes * 60
    log(f"watching {base}: a channel is processed once nothing new has arrived for {args.quiet_minutes:g} min (Ctrl+C stops)")
    waiting: set[str] = set()
    try:
        while True:
            for folder in channels(args, base):
                if not folder.is_dir():
                    continue
                idle, busy, work = channel_status(folder, out_root)
                if not work:
                    continue
                if busy or idle < quiet:
                    if folder.name not in waiting:
                        log(f"{folder.name}: downloading, waiting until it is quiet")
                        waiting.add(folder.name)
                    continue
                waiting.discard(folder.name)
                log(f"{folder.name}: download finished, processing")
                run_station([str(API_HOME / "stations" / "07_YT_CONVERT" / "07_yt_convert.py"), "--channel", folder.name])
                tidy_channel(folder, args, out_root, [10 ** 9])
                if not args.no_summary:
                    run_station([str(API_HOME / "engine" / "menu.py"), "13", "--channel", folder.name, "--yes"])
                log(f"{folder.name}: done")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log("stopped")
        return 0


def main() -> int:
    args = parse_args()
    try:
        base = external("yt_subtitles")
        out_root = external("yt_markdown", create=True)
    except PathConfigurationError as exc:
        print(f"{LABEL}: {exc}", file=sys.stderr)
        return 2
    if args.watch:
        return watch(args, base, out_root)
    budget = [args.limit or 10 ** 9]
    total = 0
    for folder in channels(args, base):
        if not folder.is_dir():
            print(f"{LABEL}: no channel folder {folder}", file=sys.stderr)
            continue
        total += tidy_channel(folder, args, out_root, budget)
    log(f"{total} note(s) {'would be ' if args.dry_run else ''}written to {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
