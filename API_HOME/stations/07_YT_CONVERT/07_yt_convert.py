"""07_YT_CONVERT: SRT / VTT / JSON transcripts -> ytgrab-style .md, original kept in <Channel>/_originals.

Local, no API. Looks in yt_subtitles/<Channel>/ for .srt .vtt .json (YouTube json3 or a list of
{start, text}). Each becomes <title>.md with '# title', '**Video ID:**', '## Transcript' and
[mm:ss] lines (the format the whole chain reads); the original moves to _originals/ beside it,
named by title, with the video id in the .md front matter. A file is moved only after its .md
is written, one at a time, so an interrupted run never loses work.

When conversion_station is configured, --use-station runs its Run-Inbox.ps1 instead. (Its
behaviour was not in the gathered files, so it is not changed or reimplemented here.)
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.paths import PathConfigurationError, configured, external  # noqa: E402

EXTS = {".srt", ".vtt", ".json"}


def stamp(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def parse_time(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    parts = [float(p) for p in parts]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def cues_from_text(text: str) -> list[tuple[float, str]]:
    cues, last = [], ""
    for block in re.split(r"\n\s*\n", text.replace("\r", "")):
        m = re.search(r"(\d[\d:.,]+)\s*-->\s*[\d:.,]+", block)
        if not m:
            continue
        lines = block[m.end():].strip().splitlines()
        words = re.sub(r"<[^>]+>", "", " ".join(lines)).strip()
        if words and words != last:
            cues.append((parse_time(m.group(1)), words))
            last = words
    return cues


def cues_from_json(text: str) -> list[tuple[float, str]]:
    data = json.loads(text)
    if isinstance(data, dict) and "events" in data:  # YouTube json3
        out = []
        for ev in data["events"]:
            words = "".join(seg.get("utf8", "") for seg in ev.get("segs", []) or []).strip()
            if words:
                out.append((ev.get("tStartMs", 0) / 1000, words))
        return out
    rows = data if isinstance(data, list) else data.get("transcript") or data.get("segments") or []
    return [(float(r.get("start", r.get("offset", 0))), str(r.get("text", "")).strip()) for r in rows if str(r.get("text", "")).strip()]


def video_id(name: str, text: str) -> str:
    m = re.search(r"\[([A-Za-z0-9_-]{11})\]", name) or re.search(r'"(?:videoId|video_id)"\s*:\s*"([A-Za-z0-9_-]{11})"', text)
    return m.group(1) if m else ""


def convert(path: Path, dry: bool, force: bool) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    cues = cues_from_json(raw) if path.suffix.lower() == ".json" else cues_from_text(raw)
    if not cues:
        return "skip (no cues)"
    vid = video_id(path.name, raw)
    title = re.sub(r"\s*\[[A-Za-z0-9_-]{11}\]\s*", " ", path.stem).replace(".en", "").strip() or path.stem
    out = path.with_name(re.sub(r'[<>:"/\\|?*]', "_", title) + ".md")
    if out.exists() and not force:
        return "skip (md exists)"
    if dry:
        return f"would write {out.name}"
    body = [f"---\nvideo_id: \"{vid}\"\nsource_file: \"{path.name}\"\n---", f"# {title}", ""]
    if vid:
        body += [f"**Video ID:** `{vid}`", f"**URL:** https://www.youtube.com/watch?v={vid}", ""]
    body += ["## Transcript", ""] + [f"[{stamp(t)}] {w}" for t, w in cues]
    tmp = out.with_suffix(".md.tmp")
    tmp.write_text("\n".join(body) + "\n", encoding="utf-8")
    tmp.replace(out)
    originals = path.parent / "_originals"
    originals.mkdir(exist_ok=True)
    shutil.move(str(path), str(originals / (re.sub(r'[<>:"/\\|?*]', "_", title) + path.suffix.lower())))
    return f"wrote {out.name}"


def main() -> int:
    p = argparse.ArgumentParser(prog="07_YT_CONVERT", description=__doc__.splitlines()[0])
    p.add_argument("items", nargs="*", help="files or channel folders (default: all of yt_subtitles)")
    p.add_argument("--channel")
    p.add_argument("--limit", type=int)
    p.add_argument("--redo", action="store_true", help="overwrite an existing .md")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--use-station", action="store_true", help="run the X: conversion station's Run-Inbox.ps1 instead")
    a = p.parse_args()
    if a.use_station:
        if not configured("conversion_station"):
            print("conversion_station is not configured (RELOCATE.bat)")
            return 2
        script = external("conversion_station") / "scripts" / "Run-Inbox.ps1"
        return subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script)]).returncode
    try:
        root = external("yt_subtitles")
    except PathConfigurationError as exc:
        print(exc)
        return 2
    targets = [Path(x) for x in a.items] or [root / a.channel if a.channel else root]
    files = []
    for t in targets:
        files += [t] if t.is_file() else sorted(f for f in t.rglob("*") if f.suffix.lower() in EXTS and "_originals" not in f.parts)
    files = files[: a.limit] if a.limit else files
    print(f"07_YT_CONVERT: {len(files)} file(s) to convert")
    failed = 0
    for f in files:
        try:
            print(f"  {f.name}: {convert(f, a.dry_run, a.redo)}")
        except (OSError, ValueError) as exc:
            failed += 1
            print(f"  ERR {f.name}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
