#!/usr/bin/env python3
"""
NLP deep runner for paper-proof-grader.

This is the comparison lane beside chi_qi_v5_metric_engine.py:
- accepts the same text/CSV/TSV/JSON/XLSX input formats
- writes JSON + CSV batch summaries
- uses optional NLP libraries when available
- falls back to deterministic standard-library extraction when they are not
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from chi_qi_v5_metric_engine import INPUT_EXTS, normalize_text, read_text

try:
    import spacy
    try:
        SPACY_NLP = spacy.load("en_core_web_sm")
        HAS_SPACY = True
        SPACY_ERROR = ""
    except Exception as exc:
        SPACY_NLP = None
        HAS_SPACY = False
        SPACY_ERROR = f"{type(exc).__name__}: {exc}"
except Exception as exc:
    SPACY_NLP = None
    HAS_SPACY = False
    SPACY_ERROR = f"{type(exc).__name__}: {exc}"

STOPWORDS = set("""
the a an and or but if then else for of in on at to from with by about into through
over under after before between this that these those there their them they you your
our ours we us he she it its is are was were be been being have has had do does did
will would should could can may might must shall not no yes only also very just more
most some such each other another any all as than like within without because while
where when what which who whom whose how why
""".split())

DOMAIN_HINTS = {
    "theology": {"god", "christ", "jesus", "spirit", "grace", "sin", "salvation", "scripture", "logos", "trinity"},
    "physics": {"physics", "quantum", "field", "entropy", "relativity", "gravity", "mass", "energy", "measurement"},
    "formal_math": {"equation", "theorem", "proof", "axiom", "lemma", "operator", "function", "variable"},
    "information": {"information", "signal", "noise", "channel", "encoding", "compression", "shannon", "bit"},
    "ethics": {"justice", "mercy", "moral", "good", "evil", "virtue", "responsibility"},
}


@dataclass
class SentenceHit:
    sentence_index: int
    score: float
    text: str
    start_char: int
    end_char: int
    reasons: List[str] = field(default_factory=list)


def tokens(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9_\-']{2,}", text)]


def content_tokens(text: str) -> List[str]:
    return [w for w in tokens(text) if w not in STOPWORDS and len(w) > 3]


def split_sentences(text: str) -> List[tuple[int, int, str]]:
    out: List[tuple[int, int, str]] = []
    pattern = re.compile(r"[^.!?\n]+(?:[.!?]+|\n|$)", re.MULTILINE)
    for m in pattern.finditer(text):
        sent = normalize_text(m.group(0))
        if len(sent) >= 30:
            out.append((m.start(), m.end(), sent))
    return out


def extract_entities(text: str) -> Dict[str, Any]:
    if HAS_SPACY and SPACY_NLP:
        doc = SPACY_NLP(text[:40000])
        labels: Dict[str, List[str]] = {}
        for ent in doc.ents:
            labels.setdefault(ent.label_, [])
            if ent.text not in labels[ent.label_] and len(labels[ent.label_]) < 20:
                labels[ent.label_].append(ent.text)
        return {
            "engine": "spacy",
            "entity_count": len(doc.ents),
            "entity_labels": labels,
        }

    # Fallback: capitalized phrase/entity-ish extraction.
    phrases = re.findall(r"\b(?:[A-Z][a-zA-Z0-9]+(?:\s+|$)){1,5}", text)
    cleaned = [normalize_text(p) for p in phrases]
    cleaned = [p for p in cleaned if len(p) > 2 and p.lower() not in STOPWORDS]
    counts = Counter(cleaned)
    return {
        "engine": "fallback_regex",
        "entity_count": sum(counts.values()),
        "entity_labels": {"CAPITALIZED_PHRASE": [p for p, _ in counts.most_common(20)]},
        "dependency_error": SPACY_ERROR,
    }


def top_terms(text: str, n: int = 25) -> List[Dict[str, Any]]:
    counts = Counter(content_tokens(text))
    return [{"term": term, "count": count} for term, count in counts.most_common(n)]


def topic_labels(text: str, n: int = 5) -> List[Dict[str, Any]]:
    words = set(content_tokens(text))
    scores = []
    for domain, hints in DOMAIN_HINTS.items():
        hits = sorted(words & hints)
        if hits:
            scores.append({"topic": domain, "score": len(hits), "terms": hits[:10]})
    scores.sort(key=lambda x: x["score"], reverse=True)
    if scores:
        return scores[:n]
    return [{"topic": "keyword_cluster", "score": item["count"], "terms": [item["term"]]} for item in top_terms(text, n)]


def key_sentences(text: str, n: int = 5) -> List[SentenceHit]:
    sents = split_sentences(text)
    if not sents:
        return []
    term_counts = Counter(content_tokens(text))
    max_count = max(term_counts.values()) if term_counts else 1
    hits: List[SentenceHit] = []
    for idx, (start, end, sent) in enumerate(sents, 1):
        sent_terms = content_tokens(sent)
        unique = set(sent_terms)
        keyword_score = sum(term_counts[t] / max_count for t in unique)
        domain_hits = sum(len(unique & hints) for hints in DOMAIN_HINTS.values())
        citation_hits = len(re.findall(r"\[\d+\]|\([A-Z][A-Za-z]+,\s*\d{4}\)|\bdoi\b|http", sent, re.I))
        axiom_hits = len(re.findall(r"\b(axiom|definition|theorem|lemma|law|proof|evidence|claim)\b", sent, re.I))
        length_penalty = abs(len(sent_terms) - 28) / 60
        score = max(0.0, keyword_score + domain_hits * 1.4 + citation_hits * 2.0 + axiom_hits * 1.6 - length_penalty)
        reasons = []
        if domain_hits:
            reasons.append(f"domain_hits={domain_hits}")
        if citation_hits:
            reasons.append(f"citations={citation_hits}")
        if axiom_hits:
            reasons.append(f"structure_terms={axiom_hits}")
        hits.append(SentenceHit(idx, round(score, 4), sent[:500], start, end, reasons))
    hits.sort(key=lambda x: x.score, reverse=True)
    return hits[:n]


def analyze_text(text: str, source_path: str, key_sentence_count: int = 5) -> Dict[str, Any]:
    clean = normalize_text(text)
    words = content_tokens(clean)
    entities = extract_entities(clean)
    key = key_sentences(clean, key_sentence_count)
    return {
        "source_path": source_path,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": "nlp_deep_runner",
        "dependencies": {
            "spacy": HAS_SPACY,
            "spacy_error": SPACY_ERROR,
        },
        "word_count": len(tokens(clean)),
        "content_word_count": len(words),
        "top_terms": top_terms(clean),
        "topics": topic_labels(clean),
        "entities": entities,
        "key_sentences": [asdict(x) for x in key],
    }


def iter_input_files(input_path: Path, recursive: bool) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    globber = input_path.rglob("*") if recursive else input_path.glob("*")
    return [p for p in globber if p.is_file() and p.suffix.lower() in INPUT_EXTS]


def write_summary_csv(reports: List[Dict[str, Any]], out_path: Path) -> None:
    fields = [
        "source_path", "word_count", "content_word_count", "top_topic",
        "top_topic_score", "top_terms", "entity_engine", "entity_count",
        "key_sentence_1", "key_sentence_1_index", "key_sentence_1_start",
        "key_sentence_1_end", "spacy_available",
    ]
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for report in reports:
            topics = report.get("topics") or []
            top_topic = topics[0] if topics else {}
            key = (report.get("key_sentences") or [{}])[0]
            writer.writerow({
                "source_path": report.get("source_path", ""),
                "word_count": report.get("word_count", 0),
                "content_word_count": report.get("content_word_count", 0),
                "top_topic": top_topic.get("topic", ""),
                "top_topic_score": top_topic.get("score", 0),
                "top_terms": ", ".join(x["term"] for x in report.get("top_terms", [])[:10]),
                "entity_engine": report.get("entities", {}).get("engine", ""),
                "entity_count": report.get("entities", {}).get("entity_count", 0),
                "key_sentence_1": key.get("text", ""),
                "key_sentence_1_index": key.get("sentence_index", ""),
                "key_sentence_1_start": key.get("start_char", ""),
                "key_sentence_1_end": key.get("end_char", ""),
                "spacy_available": report.get("dependencies", {}).get("spacy", False),
            })


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="NLP deep comparison runner")
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--max-files", type=int, default=0)
    p.add_argument("--key-sentences", type=int, default=5)
    args = p.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    files = iter_input_files(input_path, args.recursive)
    if args.max_files:
        files = files[:args.max_files]

    reports = []
    for idx, file_path in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] {file_path}")
        text = read_text(file_path)
        report = analyze_text(text, str(file_path), key_sentence_count=args.key_sentences)
        reports.append(report)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", file_path.name)
        (out_dir / f"{safe_name}.nlp_deep.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    batch = {
        "engine": "nlp_deep_runner",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(reports),
        "dependencies": {"spacy": HAS_SPACY, "spacy_error": SPACY_ERROR},
        "reports": reports,
    }
    (out_dir / "nlp_deep_batch_summary.json").write_text(json.dumps(batch, indent=2, ensure_ascii=False), encoding="utf-8")
    write_summary_csv(reports, out_dir / "nlp_deep_batch_summary.csv")
    print(f"Done: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
