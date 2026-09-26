"""Capture one YouTube transcript into an OpenIntel case source file."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi


def video_id(value: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})", value)
    return match.group(1) if match else value.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    vid = video_id(args.url)
    transcript = YouTubeTranscriptApi().fetch(vid, languages=["en"])
    lines = [
        "# Raw YouTube Transcript",
        "",
        f"**Video ID:** `{vid}`",
        f"**URL:** https://www.youtube.com/watch?v={vid}",
        "**Transcript:** English (caption track returned by YouTube)",
        f"**Segments:** {len(transcript)}",
        "",
        "## Transcript",
        "",
    ]
    for segment in transcript:
        timestamp = int(segment.start)
        minutes, seconds = divmod(timestamp, 60)
        hours, minutes = divmod(minutes, 60)
        stamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
        lines.append(f"[{stamp}] {segment.text}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(transcript)} segments to {args.output}")


if __name__ == "__main__":
    main()
