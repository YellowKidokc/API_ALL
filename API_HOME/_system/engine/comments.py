"""YouTube comments for a video, shared by 10_CKG_THEOLOGY (row 15) and 13_YT_CHANNEL_SUMMARY (audience_response).

Read from <transcript>.comments.json or <transcript>.info.json beside the transcript, or the item's
00_SOURCE/comments.json (--fetch-comments downloads them there with yt-dlp when it is installed).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

MAX_COMMENTS = 150


def comment_files(item) -> list[Path]:
    original = Path(item.meta.get("original_path", ""))
    stem = original.with_suffix("")
    return [Path(f"{stem}.comments.json"), Path(f"{stem}.info.json"),
            item.folder / "00_SOURCE" / "comments.json"]


def fetch_comments(item, ctx) -> None:
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        ctx.warnings.append("--fetch-comments: yt-dlp is not installed (pip install yt-dlp)")
        return
    target = item.folder / "00_SOURCE" / "comments.json"
    if target.exists():
        return
    ctx.step("fetching comments with yt-dlp")
    opts = {"skip_download": True, "getcomments": True, "quiet": True,
            "extractor_args": {"youtube": {"max_comments": [str(MAX_COMMENTS), "all", "0"]}}}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(item.meta.get("url", ""), download=False)
        target.write_text(json.dumps({"comments": info.get("comments") or []}, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:  # network, removed video, age gate ...
        ctx.warnings.append(f"comments not fetched: {exc}")


def comments(item) -> list[str]:
    for f in comment_files(item):
        if f.is_file():
            try:
                data = json.loads(f.read_text(encoding="utf-8", errors="replace"))
            except ValueError:
                continue
            rows = data.get("comments", data) if isinstance(data, dict) else data
            out = []
            for c in rows if isinstance(rows, list) else []:
                text = c.get("text") if isinstance(c, dict) else str(c)
                likes = c.get("like_count", 0) if isinstance(c, dict) else 0
                if text:
                    out.append((likes or 0, re.sub(r"\s+", " ", text)[:400]))
            out.sort(key=lambda x: -x[0])
            return [f"({likes} likes) {text}" for likes, text in out[:MAX_COMMENTS]]
    return []
