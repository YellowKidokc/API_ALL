"""Bridge layer shared by 48 TOPIC_SYNTHESIS and 49 GAP_MAP.

A Source is anything with text that can hold arguments about a topic: a paper item, a video item,
an EVIDENCE companion (evidence_root/OUTBOX/FOR_SUBSTACK), or one of David's own files (own_work).
Citations are always assembled here from source metadata (title, channel, url, timestamp, path),
never written by a model, so a citation in a report points at something that exists.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .items import Item, all_items, slugify
from .metrics import STOP
from .paths import configured, external
from .tagger import find as tag_find, local_scores, tags

TEXT_EXT = {".md", ".txt", ".html", ".htm", ".tex"}


@dataclass
class Source:
    key: str            # stable id: paper:<id>, video:<id>, evidence:<sha12>, own:<sha12>
    kind: str           # paper | video | evidence | own
    title: str
    text_fn: object     # callable returning the text
    meta: dict = field(default_factory=dict)
    source_hash: str = ""
    item: Item | None = None

    def text(self) -> str:
        return self.text_fn()

    def citation(self, where: str = "") -> str:
        m = self.meta
        if self.kind == "video":
            ts = f" at {where}" if where and re.match(r"^\d{1,2}:\d{2}", where) else ""
            return f"{m.get('channel', 'YouTube')}, \"{self.title}\" (YouTube){ts}. {m.get('url', '')}".strip()
        if self.kind == "evidence":
            return f"\"{self.title}\" (EVIDENCE companion). {m.get('path', '')}"
        if self.kind == "own":
            return f"D. Lowe, \"{self.title}\" (own work). {m.get('path', '')}"
        author = m.get("author") or ""
        return f"{author + ', ' if author else ''}\"{self.title}\"{' (' + m['series'] + ')' if m.get('series') else ''}. {m.get('original_path', '')}"


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _file_source(path: Path, kind: str) -> Source:
    raw = path.read_text(encoding="utf-8", errors="replace")
    title = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", raw[:3000], re.M) or re.search(r"^#\s+(.+)$", raw[:3000], re.M)
    h = _hash_text(raw)
    return Source(f"{kind}:{h[:12]}", kind, title.group(1).strip() if title else path.stem, lambda p=path: p.read_text(encoding="utf-8", errors="replace"),
                  {"path": str(path)}, h)


def item_source(item: Item) -> Source:
    return Source(f"{item.kind}:{item.id}", item.kind, item.title, item.text, item.meta, item.source_hash, item)


def own_sources() -> list[Source]:
    out = [item_source(i) for i in all_items("papers") if i.meta.get("own_work")]
    if configured("own_work"):
        root = external("own_work")
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.suffix.lower() in TEXT_EXT and ".obsidian" not in p.parts)
        seen = {s.source_hash for s in out}
        for f in files:
            s = _file_source(f, "own")
            if s.source_hash not in seen:
                out.append(s)
                seen.add(s.source_hash)
    return out


def external_sources(include_evidence: bool = True, include_own: bool = False) -> list[Source]:
    out = [item_source(i) for i in all_items("both") if include_own or not i.meta.get("own_work")]
    if include_evidence and configured("evidence_root"):
        shelf = external("evidence_root") / "OUTBOX" / "FOR_SUBSTACK"
        if shelf.is_dir():
            out += [_file_source(p, "evidence") for p in sorted(shelf.glob("*.md"))]
    return out


def topic_tag(topic: str) -> str | None:
    names = [t["tag"] for t in tags()]
    low = topic.lower()
    return next((n for n in names if n.lower() == low), None) or next((n for n in names if low in n.lower() or n.lower() in low), None)


def topic_keywords(topic: str) -> list[str]:
    tag = topic_tag(topic)
    keywords = [topic.lower()]
    if tag:
        keywords += [k.lower() for t in tags() if t["tag"] == tag for k in t.get("keywords", [])]
    return list(dict.fromkeys(keywords))


def relevance(sources: list[Source], topic: str, minimum: int) -> list[tuple[Source, int, str]]:
    """Score each source 0-10 for the topic: the tagger's stored score when there is one, else the local pass."""
    tag = topic_tag(topic)
    stored = {}
    if tag:
        for row in tag_find(tag, 0):
            stored[f"{row[1]}:{row[0]}"] = (row[3], row[7] or "tagger")
    out = []
    keywords = topic_keywords(topic)
    for s in sources:
        if s.key in stored:
            score, method = stored[s.key]
        else:
            if tag:
                score, method = local_scores(s.text())[tag]["score"], "local-keywords"
            else:
                low = s.text().lower()
                hits = sum(low.count(k) for k in keywords)
                n = max(1, len(low.split()))
                score = 0 if not hits else min(10, max(1, round(2.5 * math.log2(1 + hits / n * 1000))))
                method = "local-keywords"
        if score >= minimum:
            out.append((s, int(score), method))
    return sorted(out, key=lambda x: -x[1])


def bag(text: str) -> Counter:
    return Counter(w for w in re.findall(r"[a-z][a-z'-]+", text.lower()) if w not in STOP and len(w) > 2)


def cosine(a: Counter, b: Counter) -> float:
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na, nb = math.sqrt(sum(v * v for v in a.values())), math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def argument_text(arg: dict) -> str:
    return " ".join([str(arg.get("claim", ""))] + [str(s) for s in arg.get("steps", []) or []])


def cluster(arguments: list[dict], threshold: float = 0.35) -> list[dict]:
    """Greedy single-pass clustering of extracted arguments across sources (local, deterministic).
    Ranked by breadth (distinct sources) first, then total strength."""
    clusters: list[dict] = []
    for arg in sorted(arguments, key=lambda a: -(a.get("strength") or 0)):
        vec = bag(argument_text(arg))
        best, best_sim = None, 0.0
        for c in clusters:
            sim = cosine(vec, c["centroid"])
            if sim > best_sim:
                best, best_sim = c, sim
        if best and best_sim >= threshold:
            best["members"].append(arg)
            best["centroid"] += vec
        else:
            clusters.append({"members": [arg], "centroid": vec})
    out = []
    for c in clusters:
        sources = sorted({m["source_key"] for m in c["members"]})
        strength = sum(m.get("strength") or 0 for m in c["members"])
        out.append({"id": "", "representative": c["members"][0].get("claim", ""), "members": c["members"], "sources": sources,
                    "breadth": len(sources), "total_strength": strength,
                    "mean_strength": round(strength / len(c["members"]), 2), "terms": [w for w, _ in c["centroid"].most_common(8)]})
    out.sort(key=lambda c: (-c["breadth"], -c["total_strength"]))
    for i, c in enumerate(out, 1):
        c["id"] = f"ARG-{i:03d}"
    return out


def topic_folder(topic: str, root_key: str = "syntheses_root") -> Path:
    return external(root_key, create=True) / slugify(topic)


def latest_topic_run(topic: str, label: str) -> Path | None:
    folder = topic_folder(topic) / "02_RUNS" / label
    if not folder.is_dir():
        return None
    for run in sorted((p for p in folder.iterdir() if p.is_dir() and not p.name.startswith("_")), reverse=True):
        receipt = run / f"{label}.run.json"
        if receipt.exists() and not json.loads(receipt.read_text(encoding="utf-8")).get("errors"):
            return run
    return None
