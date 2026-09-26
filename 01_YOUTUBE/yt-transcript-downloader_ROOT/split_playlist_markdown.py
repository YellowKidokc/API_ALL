#!/usr/bin/env python3
"""
Split a combined YTBSD playlist markdown export into one markdown file per video.

The original combined playlist file is never modified. By default this writes
files beside the source file in a folder named after the source stem.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


SECTION_RE = re.compile(r"(?m)^## (?P<number>\d+)\. (?P<title>.+?)\s*$")
META_RE = re.compile(r"^\*\*(?P<key>[^*]+):\*\*\s*(?P<value>.*)$", re.MULTILINE)
UNSAFE_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
SPACE_RE = re.compile(r"\s+")


@dataclass
class VideoSection:
    number: int
    title: str
    video_id: str
    url: str
    language: str
    filename: str
    path: str
    chars: int
    words: int


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", b"", 0, 1, f"Could not decode {path}")


def slugify(value: str, max_len: int = 90) -> str:
    value = UNSAFE_FILENAME_RE.sub(" ", value)
    value = value.replace("'", "")
    value = value.replace("&", " and ")
    value = re.sub(r"[^A-Za-z0-9._ -]+", " ", value)
    value = SPACE_RE.sub(" ", value).strip(" ._-")
    value = value.lower().replace(" ", "-")
    value = re.sub(r"-{2,}", "-", value)
    return (value[:max_len].strip(" ._-") or "untitled")


def extract_metadata(section: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for match in META_RE.finditer(section):
        key = match.group("key").strip().lower()
        metadata[key] = match.group("value").strip()
    return metadata


def playlist_title(text: str, source: Path) -> str:
    first_heading = re.search(r"(?m)^# (.+?)\s*$", text)
    return first_heading.group(1).strip() if first_heading else source.stem


def split_sections(text: str) -> list[tuple[re.Match[str], str]]:
    matches = list(SECTION_RE.finditer(text))
    sections: list[tuple[re.Match[str], str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match, text[start:end].strip() + "\n"))
    return sections


def write_video_file(output_dir: Path, match: re.Match[str], section: str) -> VideoSection:
    number = int(match.group("number"))
    title = match.group("title").strip()
    metadata = extract_metadata(section)
    video_id = metadata.get("video id", "")
    url = metadata.get("url", "")
    language = metadata.get("transcript language", "")
    id_suffix = f"_{slugify(video_id, 24)}" if video_id else ""
    filename = f"{number:03d}_{slugify(title)}{id_suffix}.md"
    target = output_dir / filename
    target.write_text(section, encoding="utf-8", newline="\n")
    return VideoSection(
        number=number,
        title=title,
        video_id=video_id,
        url=url,
        language=language,
        filename=filename,
        path=str(target),
        chars=len(section),
        words=len(re.findall(r"\S+", section)),
    )


def write_index(output_dir: Path, title: str, source: Path, videos: list[VideoSection]) -> None:
    index_path = output_dir / "_index.md"
    lines = [
        f"# {title}",
        "",
        f"**Source:** `{source}`",
        f"**Videos:** {len(videos)}",
        "",
        "## Files",
        "",
    ]
    for video in videos:
        url_part = f" - {video.url}" if video.url else ""
        lines.append(f"{video.number}. [{video.title}]({video.filename}){url_part}")
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    manifest_path = output_dir / "_manifest.json"
    manifest = {
        "source": str(source),
        "playlist_title": title,
        "video_count": len(videos),
        "videos": [asdict(video) for video in videos],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    csv_path = output_dir / "_manifest.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(videos[0]).keys()))
        writer.writeheader()
        for video in videos:
            writer.writerow(asdict(video))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a combined YTBSD playlist markdown file into individual video markdown files."
    )
    parser.add_argument("input", type=Path, help="Combined playlist markdown file.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Output directory. Defaults to subtitles/<source-stem>_split.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow writing into an existing output directory.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    source = args.input.resolve()
    if not source.exists():
        print(f"Input file not found: {source}", file=sys.stderr)
        return 2
    if not source.is_file():
        print(f"Input path is not a file: {source}", file=sys.stderr)
        return 2

    output_dir = args.output_dir or source.with_name(f"{source.stem}_split")
    output_dir = output_dir.resolve()
    if output_dir.exists() and not args.overwrite:
        print(f"Output directory already exists: {output_dir}", file=sys.stderr)
        print("Use --overwrite or choose a different --output-dir.", file=sys.stderr)
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)

    text = read_text(source)
    sections = split_sections(text)
    if not sections:
        print("No video sections found. Expected headings like: ## 1. Video title", file=sys.stderr)
        return 1

    title = playlist_title(text, source)
    videos = [write_video_file(output_dir, match, section) for match, section in sections]
    write_index(output_dir, title, source, videos)

    print(f"Split {len(videos)} videos")
    print(f"Output: {output_dir}")
    print(f"Index:  {output_dir / '_index.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
