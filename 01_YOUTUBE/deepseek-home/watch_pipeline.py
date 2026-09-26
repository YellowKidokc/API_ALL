"""Watch the folders and move each video through the pipeline on its own.

Every cycle (default 60 s):
  0. conversion station inbox has files  -> convert in parallel, deliver to subtitles/<Channel>
  1. subtitles/ has new transcripts      -> clean locally into obsidian_transcripts/  (the API-ready folder)
  2. a cleaned note appears              -> DeepSeek indexes that video (this is the only API trigger)
  3. anything was indexed                -> rebuild catalog, overviews, record notes

Usage:
  python watch_pipeline.py            run until Ctrl+C
  python watch_pipeline.py --once     one cycle, then exit
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_catalog  # noqa: E402
import index_video  # noqa: E402
import lens_pass  # noqa: E402

REPO = HERE.parents[1]
SUBS = REPO / "subtitles"
CLEAN_OUT = REPO / "obsidian_transcripts"
VENV_PY = REPO / "venv" / "Scripts" / "python.exe"
STATION = pathlib.Path(r"X:\00_CONVERSION_STATION\Transcripts to Markdown")
LOG_DIR = HERE / "logs"


def log(msg):
    line = f"{dt.datetime.now():%H:%M:%S}  {msg}"
    print(line, flush=True)
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_DIR / f"watch-{dt.date.today():%Y%m%d}.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def convert_station():
    inbox = STATION / "inbox"
    if not inbox.is_dir() or not any(p.is_file() for p in inbox.rglob("*")):
        return
    log("convert: files waiting in the conversion station")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    str(STATION / "scripts" / "Run-Inbox.ps1")], check=False)


def newest_mtime(root):
    return max((p.stat().st_mtime for p in root.rglob("*.md")), default=0)


def clean(state):
    """Run the local cleaner only when subtitles/ changed since the last clean."""
    m = newest_mtime(SUBS)
    if m <= state.get("cleaned_through", 0):
        return
    log("clean: new or changed transcripts, cleaning locally (no API)")
    py = str(VENV_PY) if VENV_PY.exists() else sys.executable
    args = [py, "clean_library.py", "--src", str(SUBS), "--out", str(CLEAN_OUT)]
    try:
        subprocess.run([py, "-c", "import punctuators"], check=True, capture_output=True)
        args.append("--punctuate")
    except subprocess.CalledProcessError:
        pass
    subprocess.run(args, cwd=REPO / "Python Clean Library", check=False)
    state["cleaned_through"] = m


def watched_channels():
    """Only channels listed in WATCH_CHANNELS.txt are sent to the API automatically."""
    f = HERE / "WATCH_CHANNELS.txt"
    if not f.exists():
        return []
    return [l.strip() for l in f.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


def pending(channels):
    """Transcripts in watched channels that have a cleaned note and no index yet."""
    out = []
    for ch in channels:
        for f in sorted((SUBS / ch).glob("*.md")) if (SUBS / ch).is_dir() else []:
            if f.name.startswith("_"):
                continue
            text = f.read_text(encoding="utf-8")
            m = index_video.meta(text, f)
            if index_video.paths_for(m)[1].exists() or not index_video.clean_body(m):
                continue
            if len(text.split("## Transcript", 1)[-1].split()) < index_video.MIN_WORDS:
                continue  # empty download: listed in EMPTY_TRANSCRIPTS.md, never sent to the API
            out.append(f)
    return out


def focus_one(path, client):
    """Apply the channel's saved focus (focus/<Channel>.json) to a newly indexed video."""
    saved = lens_pass.load_focus(path.parent.name)
    if not saved or not (saved["lenses"] or saved.get("ask")):
        return
    try:
        log(lens_pass.run_one(path, client, lens_pass.lenses_for(saved["lenses"], saved.get("ask", ""))))
    except Exception as e:  # a failed focus pass must not stop the watcher
        log(f"FAIL  focus {path.name}: {e}")


def index_ready(client, workers, cap, dry_run):
    """Index up to `cap` videos whose cleaned note exists and that are not indexed yet."""
    files = pending(watched_channels())
    if dry_run:
        log(f"dry run: {len(files)} video(s) ready for the API; this cycle would send {min(len(files), cap)}")
        for f in files[:cap]:
            log(f"  would index: {f.parent.name} / {f.stem}")
        return 0
    files = files[:cap]
    done = 0
    with cf.ThreadPoolExecutor(workers) as pool:
        futs = {pool.submit(index_video.index_one, f, client): f for f in files}
        for fut in cf.as_completed(futs):
            try:
                msg = fut.result()
            except Exception as e:  # keep the watcher alive
                log(f"FAIL  {futs[fut].name}: {e}")
                continue
            if msg.startswith("done"):
                done += 1
                log(msg)
                focus_one(futs[fut], client)
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--max-per-cycle", type=int, default=25, help="API safety cap per cycle")
    ap.add_argument("--dry-run", action="store_true", help="show what would be sent; no API calls")
    args = ap.parse_args()

    import openai
    client = openai.OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
    state = {}
    log(f"watching: {STATION / 'inbox'}  ->  {SUBS}  ->  {CLEAN_OUT} (API trigger)")
    log(f"auto-indexed channels (WATCH_CHANNELS.txt): {', '.join(watched_channels()) or 'none'}")
    while True:
        try:
            convert_station()
            clean(state)
            if index_ready(client, args.workers, args.max_per_cycle, args.dry_run):
                build_catalog.main()
                log("catalog rebuilt")
        except Exception as e:  # a bad cycle must not stop the watcher
            log(f"cycle error: {e}")
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
