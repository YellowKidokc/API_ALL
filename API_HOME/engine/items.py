"""Items: the things stations run on. Two kinds share one folder shape.

  paper   <papers_root>/<PAPER_ID>_<slug>/paper.json      (created by station 47 NEW_PAPER)
  video   <yt_work>/<Channel>/<VIDEO_ID>_<slug>/video.json (created on first use from a transcript)

Both have 00_SOURCE (read-only copy + sha256), 01_NOTES (FOCUS.md), 02_RUNS/NN_STATION/<date>/,
03_REPORT, so every station, the tagger, the synthesis layer and the report combiner treat
papers and videos the same way.
"""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .output import sha256_file
from .paths import PathConfigurationError, configured, external, inside
from .text import strip_front_matter

META_FILES = {"paper": "paper.json", "video": "video.json"}
TEXT_EXT = {".md", ".txt", ".html", ".htm", ".tex"}


def slugify(text: str, limit: int = 60) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:limit] or "untitled"


@dataclass
class Item:
    kind: str
    folder: Path

    @property
    def meta_path(self) -> Path:
        return self.folder / META_FILES[self.kind]

    @property
    def meta(self) -> dict:
        return json.loads(self.meta_path.read_text(encoding="utf-8"))

    def save_meta(self, meta: dict) -> None:
        tmp = self.meta_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.meta_path)

    @property
    def id(self) -> str:
        return str(self.meta["id"])

    @property
    def title(self) -> str:
        return str(self.meta.get("title") or self.id)

    @property
    def source(self) -> Path:
        return self.folder / "00_SOURCE" / self.meta["source_file"]

    @property
    def source_hash(self) -> str:
        return str(self.meta["source_hash"])

    def text(self) -> str:
        raw = self.source.read_text(encoding="utf-8", errors="replace")
        if self.source.suffix.lower() in (".html", ".htm"):
            raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
            raw = re.sub(r"<br\s*/?>|</p>|</h\d>|</li>", "\n\n", raw, flags=re.I)
            raw = re.sub(r"<[^>]+>", " ", raw)
        return strip_front_matter(raw)

    def label(self) -> str:
        return f"{self.kind}:{self.id} {self.title[:50]}"


def load(folder: Path) -> Item | None:
    for kind, name in META_FILES.items():
        if (folder / name).is_file():
            return Item(kind, folder)
    return None


def _template_copy(destination: Path) -> None:
    shutil.copytree(inside("templates", "PAPER_FOLDER"), destination)
    readme = destination / "README.md"
    if readme.exists():
        readme.unlink()


def _copy_source(source: Path, destination: Path) -> str:
    digest = sha256_file(source)
    target = destination / "00_SOURCE" / source.name
    if target.exists():
        target.chmod(0o644)
    shutil.copy2(source, target)
    target.chmod(0o444)
    (destination / "00_SOURCE" / "sha256.txt").write_text(f"{digest}  {source.name}\n", encoding="utf-8")
    return digest


def create_paper(source: Path, *, title: str | None = None, paper_id: str | None = None, series: str = "",
                 own: bool = False) -> Item:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    root = external("papers_root", create=True)
    digest = sha256_file(source)
    for existing in root.glob("*/paper.json"):
        meta = json.loads(existing.read_text(encoding="utf-8"))
        if meta.get("source_hash") == digest:
            print(f"Already have this paper: {existing.parent}")
            return Item("paper", existing.parent)
    title = title or _title_from(source)
    paper_id = paper_id or digest[:12].upper()
    destination = root / f"{paper_id}_{slugify(title)}"
    if destination.exists():
        raise FileExistsError(f"Paper folder already exists: {destination}")
    _template_copy(destination)
    _copy_source(source, destination)
    meta = {"id": paper_id, "kind": "paper", "title": title, "series": series, "status": "new", "own_work": own,
            "source_hash": digest, "source_file": source.name, "original_path": str(source),
            "created_at": datetime.now(timezone.utc).isoformat(), "stations_run": [], "headline_scores": {}, "tags": {}}
    item = Item("paper", destination)
    item.save_meta(meta)
    return item


def _title_from(source: Path) -> str:
    try:
        head = source.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return source.stem
    match = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", head, re.M) or re.search(r"^#\s+(.+)$", head, re.M)
    return match.group(1).strip() if match else source.stem


def _video_id(text: str, fallback: str) -> str:
    match = (re.search(r"\*\*Video ID:\*\*\s*`?([A-Za-z0-9_-]{6,})`?", text)
             or re.search(r"video_id:\s*[\"']?([A-Za-z0-9_-]{6,})", text)
             or re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", text))
    return match.group(1) if match else fallback


def ensure_video(transcript: Path) -> Item:
    """Video item folder for a transcript .md (from ytgrab: '# title', '**Video ID:**', '## Transcript')."""
    transcript = transcript.resolve()
    text = transcript.read_text(encoding="utf-8", errors="replace")
    channel = transcript.parent.name if transcript.parent.name != "_originals" else transcript.parent.parent.name
    title = _title_from(transcript)
    vid = _video_id(text, sha256_file(transcript)[:11])
    root = external("yt_work", create=True) / channel
    folder = root / f"{vid}_{slugify(title, 50)}"
    digest = sha256_file(transcript)
    if (folder / "video.json").exists():
        item = Item("video", folder)
        meta = item.meta
        if meta.get("source_hash") != digest:
            meta["source_hash"] = _copy_source(transcript, folder)
            meta["source_file"] = transcript.name
            item.save_meta(meta)
        return item
    root.mkdir(parents=True, exist_ok=True)
    _template_copy(folder)
    _copy_source(transcript, folder)
    url = re.search(r"\*\*URL:\*\*\s*<?(\S+?)>?\s*$", text, re.M)
    item = Item("video", folder)
    item.save_meta({"id": vid, "kind": "video", "title": title, "channel": channel, "series": channel,
                    "url": url.group(1) if url else f"https://www.youtube.com/watch?v={vid}",
                    "source_hash": digest, "source_file": transcript.name, "original_path": str(transcript),
                    "created_at": datetime.now(timezone.utc).isoformat(), "stations_run": [], "tags": {}})
    return item


def _transcripts(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*.md") if "_originals" not in p.parts and not p.name.startswith("_"))


def discover(selectors: list[str], kind: str = "papers", limit: int | None = None,
             channel: str | None = None) -> list[Item]:
    """Resolve menu selectors into items.

    selectors: item folders, transcript files, channel folders, or source files (papers are
    created on the fly only by station 47). With no selectors: every paper in papers_root
    and/or every transcript under yt_subtitles (optionally one --channel)."""
    items: list[Item] = []
    for raw in selectors:
        path = Path(raw).expanduser()
        if not path.is_absolute() and not path.exists():
            for key in ("papers_root", "yt_subtitles", "yt_work"):
                if configured(key) and (external(key) / raw).exists():
                    path = external(key) / raw
                    break
        loaded = load(path) if path.is_dir() else None
        if loaded:
            items.append(loaded)
        elif path.is_dir():
            items.extend(ensure_video(t) for t in _transcripts(path))
        elif path.is_file() and path.suffix.lower() in TEXT_EXT:
            items.append(ensure_video(path))
        else:
            raise FileNotFoundError(f"No item at {raw}")
    if not selectors:
        if kind in ("papers", "both"):
            try:
                items.extend(Item("paper", p.parent) for p in sorted(external("papers_root").glob("*/paper.json")))
            except PathConfigurationError as exc:
                if kind == "papers":
                    raise
                print(f"(papers skipped: {exc})")
        if kind in ("videos", "both"):
            try:
                base = external("yt_subtitles")
                folder = base / channel if channel else base
                items.extend(ensure_video(t) for t in _transcripts(folder)[: limit or None])
            except PathConfigurationError as exc:
                if kind == "videos":
                    raise
                print(f"(videos skipped: {exc})")
    return items[:limit] if limit else items


def all_items(kind: str = "both") -> list[Item]:
    """Every existing item folder (no creation). Used by the tagger search, synthesis and percentiles."""
    found: list[Item] = []
    if kind in ("papers", "both") and configured("papers_root"):
        found.extend(Item("paper", p.parent) for p in sorted(external("papers_root").glob("*/paper.json")))
    if kind in ("videos", "both") and configured("yt_work"):
        found.extend(Item("video", p.parent) for p in sorted(external("yt_work").glob("*/*/video.json")))
    return found
