"""Tagger (station 44): about 20 tags David edits in config/tags.json, 0-10 per paper and video.

Cheap by design:
  1. local pass (free, same answer every time): keyword density per tag; when the NAS zero-shot
     model is configured (nas_brain/05_MODELS/M22*) and transformers is installed, it is used instead;
  2. only tags that score >= tag_confirm_from locally go to DeepSeek, in ONE whole-item call,
     which returns the 0-10 score, a one-line reason and a quote or timestamp.
Scores live in the catalog SQLite table tag_scores and in paper.json / video.json.

  ONE_MENU.bat find resurrection --min 5     best first, with path and reason
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .paths import configured, external, inside

SCHEMA = """CREATE TABLE IF NOT EXISTS tag_scores (
  item_id TEXT, kind TEXT, tag TEXT, score INTEGER, reason TEXT, quote_or_ts TEXT, path TEXT,
  method TEXT, updated_at TEXT, PRIMARY KEY (item_id, kind, tag))"""


def tags() -> list[dict]:
    raw = json.loads(inside("config", "tags.json").read_text(encoding="utf-8"))
    return [t if isinstance(t, dict) else {"tag": t, "keywords": [t]} for t in raw]


def db() -> sqlite3.Connection:
    path = external("catalog_db", required=False)
    if path == Path():
        path = inside("STATE", "catalog.sqlite")
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute(SCHEMA)
    cols = {r[1] for r in con.execute("PRAGMA table_info(tag_scores)")}
    for col in ("method", "updated_at", "path"):
        if col not in cols:
            con.execute(f"ALTER TABLE tag_scores ADD COLUMN {col} TEXT")
    return con


def _zero_shot():
    """The NAS zero-shot classifier, if available; None otherwise."""
    if not configured("nas_brain"):
        return None
    models = sorted((external("nas_brain") / "05_MODELS").glob("M22*"))
    if not models:
        return None
    try:
        from transformers import pipeline  # type: ignore
        return pipeline("zero-shot-classification", model=str(models[0]))
    except Exception:
        return None


_ZS = None
_ZS_TRIED = False


def local_scores(text: str) -> dict[str, dict]:
    """Deterministic local pass: tag -> {score, reason, quote_or_ts, method}."""
    global _ZS, _ZS_TRIED
    low = text.lower()
    n_words = max(1, len(re.findall(r"\w+", text)))
    out = {}
    if not _ZS_TRIED:
        _ZS, _ZS_TRIED = _zero_shot(), True
    zs = None
    if _ZS is not None:
        try:
            result = _ZS(text[:4000], [t["tag"] for t in tags()], multi_label=True)
            zs = dict(zip(result["labels"], result["scores"]))
        except Exception:
            zs = None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for t in tags():
        hits = 0
        first = ""
        for kw in t.get("keywords", [t["tag"]]):
            pattern = r"\b" + re.escape(kw.lower()) + r"\w*"
            count = len(re.findall(pattern, low))
            hits += count
            if count and not first:
                first = next((ln for ln in lines if re.search(pattern, ln.lower())), "")
        density = hits / n_words * 1000  # hits per 1,000 words
        score = 0 if not hits else min(10, max(1, round(2.5 * math.log2(1 + density))))
        method = "local-keywords"
        if zs is not None:
            score = round(zs.get(t["tag"], 0) * 10)
            method = "local-zero-shot"
        out[t["tag"]] = {"tag": t["tag"], "score": score, "method": method, "quote_or_ts": first[:300],
                         "reason": f"{hits} keyword hit(s), {density:.1f} per 1,000 words" if method == "local-keywords"
                         else "zero-shot model"}
    return out


def save(item, scores: dict[str, dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with db() as con:
        for s in scores.values():
            con.execute("INSERT OR REPLACE INTO tag_scores VALUES (?,?,?,?,?,?,?,?,?)",
                        (item.id, item.kind, s["tag"], int(s["score"]), s.get("reason", ""), s.get("quote_or_ts", ""),
                         str(item.folder), s.get("method", ""), now))
    meta = item.meta
    meta["tags"] = {k: {x: v[x] for x in ("score", "reason", "quote_or_ts", "method")} for k, v in scores.items()}
    item.save_meta(meta)


def tag_local(item) -> dict[str, dict]:
    scores = local_scores(item.text())
    save(item, scores)
    return scores


def find(tag: str, minimum: int = 5) -> list[tuple]:
    with db() as con:
        known = [r[0] for r in con.execute("SELECT DISTINCT tag FROM tag_scores")]
        match = next((k for k in known if k.lower() == tag.lower()), None) or \
            next((k for k in known if tag.lower() in k.lower()), tag)
        return con.execute("SELECT item_id, kind, tag, score, reason, quote_or_ts, path, method FROM tag_scores "
                           "WHERE tag = ? AND score >= ? ORDER BY score DESC, item_id", (match, minimum)).fetchall()


def print_search(tag: str, minimum: int = 5) -> int:
    if not tag:
        print("Usage: ONE_MENU.bat find <tag> [--min 5]")
        return 2
    rows = find(tag, minimum)
    for item_id, kind, name, score, reason, quote, path, method in rows:
        print(f"{score:>2}  {kind:<5} {item_id}  [{name}] ({method})\n    {path}\n    {reason}\n    \"{(quote or '')[:200]}\"")
    print(f"\n{len(rows)} item(s) scoring {minimum}+ for '{tag}'")
    return 0
