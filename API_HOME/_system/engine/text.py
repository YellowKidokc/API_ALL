"""Deterministic text preparation shared by every station: numbered paragraphs
P01.. and sentences S001.. with character offsets. The runner numbers the text,
never the model, so ids are stable across reruns and across stations."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_ABBREV = {"mr", "mrs", "ms", "dr", "prof", "st", "vs", "etc", "e.g", "i.e", "cf", "fig", "eq", "no", "vol", "ch", "v", "jn", "gen", "rev", "matt", "mk", "lk", "rom", "cor", "heb"}
_SENT_END = re.compile(r"([.!?]['\")\]]*)\s+(?=[\"'(\[]?[A-Z0-9])")


@dataclass
class Sentence:
    id: str
    para: str
    text: str
    start: int
    end: int


@dataclass
class Paragraph:
    id: str
    text: str
    start: int
    sentences: list[str]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def strip_front_matter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            return text[end + 4:].lstrip("\n")
    return text


def _split_sentences(block: str) -> list[tuple[int, int]]:
    spans, start = [], 0
    for match in _SENT_END.finditer(block):
        cut = match.end(1)
        word = re.findall(r"([A-Za-z.]+)\.?$", block[start:cut].rstrip(".!?'\")]"))
        if word and word[-1].lower().rstrip(".") in _ABBREV and block[cut - 1] == ".":
            continue
        if block[start:cut].strip():
            spans.append((start, cut))
        start = match.end()
    if block[start:].strip():
        spans.append((start, len(block)))
    return spans


def segment(text: str) -> tuple[list[Paragraph], list[Sentence]]:
    paragraphs: list[Paragraph] = []
    sentences: list[Sentence] = []
    for match in re.finditer(r"[^\n](?:.|\n(?!\s*\n))*", text):
        block = match.group(0)
        if not block.strip() or re.fullmatch(r"\s*(---+|\*\*\*+)\s*", block):
            continue
        pid = f"P{len(paragraphs) + 1:02d}"
        ids = []
        for s, e in _split_sentences(block):
            raw = block[s:e]
            lead = len(raw) - len(raw.lstrip())
            sid = f"S{len(sentences) + 1:03d}"
            sentences.append(Sentence(sid, pid, " ".join(raw.split()), match.start() + s + lead, match.start() + e))
            ids.append(sid)
        paragraphs.append(Paragraph(pid, block.strip(), match.start(), ids))
    return paragraphs, sentences


def numbered(paragraphs: list[Paragraph], sentences: list[Sentence]) -> str:
    """The text as the model sees it: every sentence prefixed with its id."""
    by_id = {s.id: s for s in sentences}
    return "\n\n".join(f"[{p.id}] " + " ".join(f"[{sid}] {by_id[sid].text}" for sid in p.sentences) for p in paragraphs)


def ranges(ids: list[str], size: int) -> list[list[str]]:
    """Output ranges: which sentence ids each parallel call answers for."""
    size = max(1, size)
    return [ids[i:i + size] for i in range(0, len(ids), size)] or [[]]


WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")


def words(text: str) -> list[str]:
    return WORD.findall(text)
