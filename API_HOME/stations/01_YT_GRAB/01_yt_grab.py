"""01_YT_GRAB: download transcripts with the vendored ytgrab into yt_subtitles (the ONE download location).

After a grab, when run interactively, it asks two questions about the channel it just grabbed:
  * what should the AI look for in this channel's videos?  -> yt_focus/<Channel>.json {"ask": ...}
    (08, 09, 03 and 04 all add it to their prompts for every video of that channel)
  * auto-process new videos from this channel?             -> adds it to WATCH_CHANNELS.txt (station 06)
"""
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.legacy import main  # noqa: E402
from engine.paths import API_HOME, PathConfigurationError, external  # noqa: E402

WATCH = API_HOME / "vendor" / "youtube" / "deepseek_home" / "WATCH_CHANNELS.txt"


def newest_channels(root: Path, since: float) -> list[str]:
    return [p.name for p in root.iterdir() if p.is_dir() and p.stat().st_mtime >= since]


def after_grab(since: float) -> None:
    try:
        subs = external("yt_subtitles")
        focus_dir = external("yt_focus", create=True)
    except PathConfigurationError:
        return
    for channel in newest_channels(subs, since):
        print(f"\nChannel grabbed: {channel}")
        path = focus_dir / f"{channel}.json"
        current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if current.get("ask"):
            print(f"  saved focus: {current['ask']}")
        ask = input("  What should the AI look for in this channel's videos? (Enter = nothing / keep) ").strip()
        if ask:
            current.update({"ask": ask, "saved": date.today().isoformat()})
            path.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  saved -> {path}")
        watched = WATCH.read_text(encoding="utf-8").splitlines() if WATCH.exists() else []
        if channel not in [w.strip() for w in watched]:
            if input("  Auto-process new videos from this channel (station 06)? [y/N] ").strip().lower().startswith("y"):
                with WATCH.open("a", encoding="utf-8") as f:
                    f.write(f"\n{channel}\n")
                print("  added to WATCH_CHANNELS.txt")


if __name__ == "__main__":
    started = time.time()
    code = main("01_YT_GRAB")
    if code == 0 and sys.stdin.isatty() and "--dry-run" not in sys.argv:
        after_grab(started - 5)
    raise SystemExit(code)
