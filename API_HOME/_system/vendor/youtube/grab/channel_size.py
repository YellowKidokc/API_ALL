#!/usr/bin/env python3
"""Print "<video count>|<safe folder name>" for a channel or playlist URL.

Used by GRAB_CHANNEL.bat to decide whether a download is a one-sitting job or
a multi-night one. Counting is cheap: titles only, no transcripts.
"""
from __future__ import annotations

import re
import sys

import yt_dlp


def main() -> int:
    if len(sys.argv) < 2:
        print("0|unknown")
        return 2
    url = sys.argv[1]
    if "/@" in url and not re.search(r"/(videos|shorts|streams|playlists)/?$", url):
        url = url.rstrip("/") + "/videos"
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
    info = None
    last = ""
    # Not every handle exposes /videos; fall back to the URL as given.
    for candidate in dict.fromkeys([url, sys.argv[1]]):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(candidate, download=False)
            break
        except Exception as exc:
            last = str(exc)
    if info is None:
        print(f"0|error: {last}"[:200])
        return 1
    entries = [e for e in (info.get("entries") or []) if e]
    name = info.get("title") or info.get("uploader") or "channel"
    name = re.sub(r"\s*-\s*(Videos|Shorts|Streams)$", "", str(name)).strip()
    name = re.sub(r'[<>:"/\|?*]', " ", name)
    print(f"{len(entries)}|{re.sub(r'\s+', ' ', name).strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
