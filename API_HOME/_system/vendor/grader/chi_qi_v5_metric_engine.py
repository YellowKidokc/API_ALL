#!/usr/bin/env python3
"""
χ / Qi v5 Statistical Audit Engine — scaffold
=============================================

This is the v5 layer that sits between:
- filetagger_chi_v2.py: fast corpus scanner
- chi_jm_diagnostic_engine_v4_gold.py: deep paper/claim audit
- .chi sidecars: readable audit records
- SQLite: statistical memory
- HTML dashboards: corpus/page/sentence navigation

Core rule:
Every label must have a score.
Every score must have evidence spans.
Every evidence span must have a weight.
Every winner must beat a rival.
Every weakness must produce a symptom.
Every symptom must produce a repair path.

This file is intentionally standard-library first. If openpyxl is present, it can
load David's lexicon workbook. If not, it falls back to built-in seed terms.
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import html
import json
import math
import os
import re
import sqlite3
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ENGINE_VERSION = "chi_qi_v5.0-scaffold"

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-']+|[χΧΩΣΘΛΨΦ][\w_]*")
PARA_RE = re.compile(r"\n\s*\n+")
SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'“‘])")
HTML_TAG_RE = re.compile(r"(?s)<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"(?is)<(script|style).*?>.*?</\1>")
INPUT_EXTS = {".md", ".txt", ".html", ".htm", ".csv", ".tsv", ".json", ".xlsx"}
MAX_XLSX_SHEETS_AS_INPUT = 25
MAX_XLSX_ROWS_PER_SHEET_AS_INPUT = 800
MAX_XLSX_COLS_AS_INPUT = 32
MAX_SENTENCE_AXIOM_TERMS = 500

# Seed terms are deliberately small. The lexicon workbook should be primary.
SEED_COLLECTIONS: Dict[str, List[str]] = {
    "EVIDENCE_TERMS": ["source", "citation", "data", "measurement", "study", "observed", "figure", "table", "reproducible", "peer-reviewed"],
    "BOUNDARY_TERMS": ["does not prove", "not claim", "limited", "scope", "boundary", "candidate", "hypothesis", "analogy", "metaphor", "within the model"],
    "FALSIFY_TERMS": ["kill condition", "falsify", "would fail", "counterexample", "refuted", "death condition", "wrong if"],
    "COHERENCE_TERMS": ["coherence", "integrate", "alignment", "structure", "mechanism", "invariant", "logos", "unify"],
    "DISCOHERENCE_TERMS": ["contradiction", "incoherent", "fragmentation", "drift", "unsupported", "circular", "ad hoc"],
    "FRUITS": ["love", "joy", "peace", "patience", "kindness", "goodness", "faithfulness", "gentleness", "self-control"],
    "ANTI_FRUITS": ["rage", "domination", "coercion", "contempt", "dehumanization", "panic", "manipulation", "despair"],
    "LAW_KEYWORDS": ["gravity", "grace", "motion", "will", "light", "truth", "strong force", "love", "entropy", "justice", "information", "logos", "quantum", "faith", "relativity", "relationship", "weak force", "decay", "coherence", "christ"],
}

MASTER_VARIABLES = {
    "G": ["grace", "mercy", "restore", "redemption", "forgive"],
    "M": ["will", "repentance", "moral", "alignment", "choice"],
    "E": ["truth", "evidence", "source", "measure", "citation"],
    "S": ["entropy", "judgment", "decay", "consequence", "collapse"],
    "T": ["time", "kairos", "sequence", "history", "threshold"],
    "K": ["knowledge", "information", "logos", "signal", "model"],
    "R": ["relationship", "family", "covenant", "binding", "community"],
    "Q": ["quantum", "faith", "observer", "measurement", "uncertainty"],
    "F": ["force", "action", "motion", "will", "moral force"],
    "C": ["coherence", "christ", "integration", "shalom", "kingdom"],
}

STOP_TERMS = {
    "about", "after", "again", "against", "alone", "also", "another", "anything",
    "because", "before", "being", "between", "cannot", "could", "every", "from",
    "have", "into", "must", "only", "other", "rather", "should", "some", "than",
    "that", "their", "there", "these", "thing", "this", "through", "without",
    "with", "within", "would", "your",
}

DOMAIN_TERMS = {
    "theology": ["god", "christ", "jesus", "spirit", "grace", "sin", "salvation", "scripture", "logos"],
    "physics": ["physics", "quantum", "field", "entropy", "relativity", "gravity", "mass", "energy", "measurement"],
    "information_theory": ["information", "signal", "noise", "channel", "shannon", "compression", "encoding"],
    "formal_math": ["equation", "theorem", "proof", "lean", "operator", "function", "variable", "axiom"],
    "history": ["historical", "century", "document", "record", "timeline", "1900", "1919"],
    "epistemology": ["truth", "knowledge", "ground", "regress", "assumption", "falsifiability", "method"],
    "ethics_moral_philosophy": ["good", "evil", "justice", "ought", "virtue", "responsibility", "accountability"],
    "sociology_culture": ["society", "institution", "culture", "community", "family", "civilization"],
    "psychology": ["behavior", "emotion", "anxiety", "habit", "trauma", "identity", "willpower"],
    "ai_methodology": ["ai", "llm", "model", "prompt", "agent", "classification", "corpus"],
}

@dataclass
class SemanticTerm:
    term: str
    collection: str
    bucket: str = ""
    subbucket: str = ""
    polarity: str = "positive"
    weight: float = 1.0
    danger_level: str = "low"
    source_sheet: str = ""

@dataclass
class TextUnit:
    unit_id: str
    file_id: str
    unit_type: str
    ordinal: int
    text: str
    anchor: str
    start_char: int
    end_char: int
    parent_unit_id: Optional[str] = None
    heading: str = ""

@dataclass
class EvidenceSpan:
    span_id: str
    result_id: str
    file_id: str
    unit_id: str
    metric_id: str
    term: str
    normalized_term: str
    lexicon_collection: str
    lexicon_bucket: str
    lexicon_subbucket: str
    polarity: str
    danger_level: str
    term_weight: float
    contribution: float
    matched_text: str
    paragraph_index: int
    sentence_index: int
    start_char: int
    end_char: int
    context_before: str = ""
    context_after: str = ""

@dataclass
class MetricResult:
    result_id: str
    file_id: str
    unit_id: str
    scope: str
    metric_id: str
    metric_family: str
    metric_object: str
    facet: str
    raw_hits: int = 0
    weighted_hits: float = 0.0
    unique_terms: int = 0
    density_per_1000_words: float = 0.0
    distribution_score: float = 0.0
    cooccurrence_score: float = 0.0
    counter_signal_score: float = 0.0
    structural_completeness: float = 0.0
    evidence_support: float = 0.0
    boundary_support: float = 0.0
    formal_support: float = 0.0
    kill_condition_support: float = 0.0
    repair_support: float = 0.0
    rival_metric_id: Optional[str] = None
    rival_score: float = 0.0
    margin: float = 0.0
    score: float = 0.0
    confidence: float = 0.0
    normalized_pct: float = 0.0
    qualifier: str = "absent"
    symptom: str = ""
    symptom_severity: str = "none"
    repair_action: str = ""
    route_trigger: bool = False
    evidence_spans: List[EvidenceSpan] = field(default_factory=list)

def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    try:
        if math.isnan(x):
            return lo
    except Exception:
        return lo
    return max(lo, min(hi, float(x)))

def pct(x: float) -> float:
    return round(clamp(x), 2)

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

def tokens(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def read_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".csv", ".tsv"}:
        return read_csv_text(path, delimiter="\t" if ext == ".tsv" else ",")
    if ext == ".json":
        return read_json_text(path)
    if ext == ".xlsx":
        return read_xlsx_text(path)
    raw = path.read_text(encoding="utf-8", errors="replace")
    if ext in {".html", ".htm"}:
        raw = SCRIPT_STYLE_RE.sub(" ", raw)
        raw = re.sub(r"(?is)</(p|div|section|article|li|h[1-6]|tr)>", "\n", raw)
        raw = HTML_TAG_RE.sub(" ", raw)
        raw = html.unescape(raw)
    return raw.replace("\r\n", "\n").replace("\r", "\n")

def read_csv_text(path: Path, delimiter: str = ",") -> str:
    chunks: List[str] = []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        for row_index, row in enumerate(reader, 1):
            values = [normalize_text(str(v)) for v in row if normalize_text(str(v))]
            if values:
                chunks.append(f"row {row_index}: " + " | ".join(values))
    return "\n".join(chunks)

def flatten_json(value: Any, prefix: str = "") -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            yield from flatten_json(item, key_path)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            yield from flatten_json(item, f"{prefix}[{idx}]")
    elif value is not None:
        text = normalize_text(str(value))
        if text:
            yield f"{prefix}: {text}" if prefix else text

def read_json_text(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return path.read_text(encoding="utf-8", errors="replace")
    return "\n".join(flatten_json(data))

def read_xlsx_text(path: Path) -> str:
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True)
    except Exception:
        return ""
    chunks: List[str] = []
    for sheet_name in wb.sheetnames[:MAX_XLSX_SHEETS_AS_INPUT]:
        ws = wb[sheet_name]
        chunks.append(f"sheet: {sheet_name}")
        for row_index, row in enumerate(ws.iter_rows(max_row=MAX_XLSX_ROWS_PER_SHEET_AS_INPUT, max_col=MAX_XLSX_COLS_AS_INPUT, values_only=True), 1):
            values = [normalize_text(str(v)) for v in row if v is not None and normalize_text(str(v))]
            if values:
                chunks.append(f"{sheet_name} row {row_index}: " + " | ".join(values))
    wb.close()
    return "\n".join(chunks)

def split_paragraphs_with_offsets(text: str, file_id: str) -> List[TextUnit]:
    units: List[TextUnit] = []
    ordinal = 0
    for m in re.finditer(r"\S(?:.*?)(?=\n\s*\n+|\Z)", text, flags=re.DOTALL):
        para = normalize_text(m.group(0))
        if len(para.split()) < 4:
            continue
        ordinal += 1
        units.append(TextUnit(
            unit_id=f"{file_id}::p{ordinal:04d}",
            file_id=file_id,
            unit_type="paragraph",
            ordinal=ordinal,
            text=para,
            anchor=f"p-{ordinal:04d}",
            start_char=m.start(),
            end_char=m.end(),
        ))
    return units

def split_sentences_from_paragraphs(paras: List[TextUnit]) -> List[TextUnit]:
    out: List[TextUnit] = []
    ordinal = 0
    for p in paras:
        offset_cursor = p.start_char
        for piece in SENT_RE.split(p.text):
            sent = normalize_text(piece)
            if len(sent) < 20:
                continue
            ordinal += 1
            # approximate local offset; enough for the first v5 layer
            idx = p.text.find(sent)
            start = p.start_char + max(0, idx)
            out.append(TextUnit(
                unit_id=f"{p.file_id}::s{ordinal:04d}",
                file_id=p.file_id,
                unit_type="sentence",
                ordinal=ordinal,
                text=sent,
                anchor=f"s-{ordinal:04d}",
                start_char=start,
                end_char=start + len(sent),
                parent_unit_id=p.unit_id,
            ))
    return out

class LexiconStore:
    def __init__(self, path: Optional[Path] = None, policy: str = "merge"):
        self.path = str(path) if path else ""
        self.policy = policy
        self.loaded = False
        self.warnings: List[str] = []
        self.terms_by_collection: Dict[str, List[SemanticTerm]] = defaultdict(list)
        self.sheet_names: List[str] = []
        self.checksum: str = ""

    @classmethod
    def load(cls, path: Optional[Path], policy: str = "merge") -> "LexiconStore":
        store = cls(path, policy)
        for collection, terms in SEED_COLLECTIONS.items():
            for t in terms:
                store.terms_by_collection[collection].append(SemanticTerm(term=t, collection=collection, source_sheet="built_in"))
        if not path:
            return store
        if path.suffix.lower() in {".csv", ".tsv"}:
            store._load_table_rows(cls._read_delimited_rows(path), path.name)
            store.loaded = True
            return store
        if path.suffix.lower() == ".json":
            store._load_json_terms(path)
            store.loaded = True
            return store
        try:
            store.checksum = sha256_text(path.read_bytes().hex())
            from openpyxl import load_workbook  # optional runtime dependency
            wb = load_workbook(path, read_only=True, data_only=True)
            store.sheet_names = list(wb.sheetnames)
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                preview_rows = list(ws.iter_rows(max_row=12, values_only=True))
                header_index = cls._find_header_row(preview_rows)
                if header_index is None:
                    continue
                rows = ws.iter_rows(min_row=header_index + 2, values_only=True)
                headers = [str(h).strip() if h is not None else "" for h in preview_rows[header_index]]
                h = {name: i for i, name in enumerate(headers) if name}
                def cell(row, key, default=""):
                    idx = h.get(key)
                    if idx is None or idx >= len(row):
                        return default
                    return row[idx] if row[idx] is not None else default
                for row in rows:
                    if row is None or not any(str(x).strip() for x in row if x is not None):
                        continue
                    for structured_term in cls._structured_terms_from_row(row, h, sheet_name):
                        store.terms_by_collection[structured_term.collection].append(structured_term)
                    collection = str(cell(row, "collection", sheet_name) or sheet_name).strip()
                    term = str(cell(row, "term", "") or "").strip()
                    if not term and "key" in h and "value" in h:
                        term = str(cell(row, "value", "") or cell(row, "key", "") or "").strip()
                    if not term:
                        continue
                    try:
                        weight = float(cell(row, "weight", 1) or 1)
                    except Exception:
                        weight = 1.0
                    store.terms_by_collection[collection].append(SemanticTerm(
                        term=term,
                        collection=collection,
                        bucket=str(cell(row, "bucket", collection) or collection),
                        subbucket=str(cell(row, "subbucket", "") or ""),
                        polarity=str(cell(row, "polarity", "positive") or "positive"),
                        weight=weight,
                        danger_level=str(cell(row, "danger_level", "low") or "low"),
                        source_sheet=sheet_name,
                    ))
            store.loaded = True
        except Exception as exc:
            store.warnings.append(f"lexicon load failed: {exc}")
        return store

    @staticmethod
    def _read_delimited_rows(path: Path) -> List[Dict[str, Any]]:
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
            return list(csv.DictReader(fh, delimiter=delimiter))

    def _load_table_rows(self, rows: List[Dict[str, Any]], source_name: str) -> None:
        for row in rows:
            normalized = {str(k).strip(): v for k, v in row.items() if k is not None}
            h = {k: i for i, k in enumerate(normalized.keys())}
            tuple_row = tuple(normalized.values())
            for structured_term in self._structured_terms_from_row(tuple_row, h, source_name):
                self.terms_by_collection[structured_term.collection].append(structured_term)
            collection = str(normalized.get("collection") or normalized.get("Collection") or source_name).strip()
            term = str(normalized.get("term") or normalized.get("Term") or normalized.get("value") or normalized.get("Value") or normalized.get("key") or normalized.get("Key") or "").strip()
            if not term:
                continue
            try:
                weight = float(normalized.get("weight") or normalized.get("Weight") or 1)
            except Exception:
                weight = 1.0
            self.terms_by_collection[collection].append(SemanticTerm(
                term=term,
                collection=collection,
                bucket=str(normalized.get("bucket") or normalized.get("Bucket") or normalized.get("key") or collection),
                subbucket=str(normalized.get("subbucket") or normalized.get("Subbucket") or ""),
                polarity=str(normalized.get("polarity") or normalized.get("Polarity") or "positive"),
                weight=weight,
                danger_level=str(normalized.get("danger_level") or normalized.get("Danger_Level") or "low"),
                source_sheet=source_name,
            ))

    def _load_json_terms(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
        except Exception as exc:
            self.warnings.append(f"json lexicon load failed: {exc}")
            return
        if isinstance(data, list) and all(isinstance(x, dict) for x in data):
            self._load_table_rows(data, path.name)
            return
        if isinstance(data, dict):
            rows: List[Dict[str, Any]] = []
            for collection, terms in data.items():
                if isinstance(terms, list):
                    for item in terms:
                        if isinstance(item, dict):
                            row = dict(item)
                            row.setdefault("collection", collection)
                            rows.append(row)
                        else:
                            rows.append({"collection": collection, "term": str(item), "bucket": collection})
                elif isinstance(terms, dict):
                    for bucket, values in terms.items():
                        if isinstance(values, list):
                            for item in values:
                                rows.append({"collection": collection, "term": str(item), "bucket": bucket})
                        else:
                            rows.append({"collection": collection, "term": str(values), "bucket": bucket})
            self._load_table_rows(rows, path.name)

    @classmethod
    def load_many(cls, paths: Iterable[Path], policy: str = "merge") -> "LexiconStore":
        paths = [p for p in paths if p]
        if not paths:
            return cls.load(None, policy)
        base = cls.load(paths[0], policy)
        for path in paths[1:]:
            other = cls.load(path, policy)
            for collection, terms in other.terms_by_collection.items():
                base.terms_by_collection[collection].extend(terms)
            base.sheet_names.extend([f"{path.name}:{s}" for s in other.sheet_names])
            base.warnings.extend(other.warnings)
            base.loaded = base.loaded or other.loaded
            base.path = ";".join(x for x in [base.path, other.path] if x)
            base.checksum = sha256_text((base.checksum + other.checksum).encode("utf-8", errors="ignore").hex())
        return base


    @staticmethod
    def _find_header_row(rows: List[Tuple[Any, ...]]) -> Optional[int]:
        preferred = {
            "term", "collection", "value", "key", "Axiom_ID", "Axiom_Name",
            "Core_Statement", "ID", "Name", "Statement", "#", "Axiom Name",
        }
        for idx, row in enumerate(rows[:12]):
            headers = {str(x).strip() for x in row if x is not None}
            if headers & preferred:
                return idx
        return None

    @staticmethod
    def _get_by_any(row: Tuple[Any, ...], h: Dict[str, int], keys: Iterable[str]) -> str:
        lower = {k.lower(): v for k, v in h.items()}
        for key in keys:
            idx = h.get(key)
            if idx is None:
                idx = lower.get(key.lower())
            if idx is not None and idx < len(row) and row[idx] is not None:
                return str(row[idx]).strip()
        return ""

    @classmethod
    def _structured_terms_from_row(cls, row: Tuple[Any, ...], h: Dict[str, int], sheet_name: str) -> List[SemanticTerm]:
        axiom_id = cls._get_by_any(row, h, ["Axiom_ID", "ID"])
        name = cls._get_by_any(row, h, ["Axiom_Name", "Name", "Axiom Name"])
        statement = cls._get_by_any(row, h, ["Core_Statement", "Statement"])
        tier = cls._get_by_any(row, h, ["Tier", "Stage"])
        axiom_type = cls._get_by_any(row, h, ["Type"])
        if not (axiom_id or name or statement):
            return []
        if axiom_id.upper().startswith("LEGEND") or "instruction" in axiom_id.lower():
            return []
        if axiom_id.lower().startswith("stage "):
            return []
        collection = cls._collection_for_structured_type(axiom_type, sheet_name)
        if not collection:
            return []
        bucket = axiom_id or name
        subbucket = " | ".join(x for x in [tier, axiom_type] if x)
        out: List[SemanticTerm] = []
        for term, weight in [(axiom_id, 2.5), (name, 2.0), (statement, 1.5)]:
            term = normalize_text(term)
            if term and len(term) > 1:
                out.append(SemanticTerm(term=term, collection=collection, bucket=bucket, subbucket=subbucket, weight=weight, source_sheet=sheet_name))
        return out

    @staticmethod
    def _collection_for_structured_type(row_type: str, sheet_name: str) -> str:
        normalized = (row_type or "").strip().lower().replace(" ", "_").replace("-", "_")
        if normalized in {"axiom"}:
            return "AXIOM_TERMS"
        if normalized in {"definition"}:
            return "DEFINITION_TERMS"
        if normalized in {"lemma", "logicalnecessity", "logical_necessity"}:
            return "LEMMA_TERMS"
        if normalized in {"theorem"}:
            return "THEOREM_TERMS"
        if normalized in {"property"}:
            return "PROPERTY_TERMS"
        if normalized in {"equation"}:
            return "EQUATION_TERMS"
        if normalized in {"boundarycondition", "boundary_condition"}:
            return "BOUNDARY_CONDITION_TERMS"
        if normalized in {"assumption", "pre_assumption", "preassumption"}:
            return "ASSUMPTION_TERMS"
        if normalized in {"claim"}:
            return "CLAIM_ROW_TERMS"
        if normalized in {"law"}:
            return "STRUCTURED_LAW_TERMS"
        if normalized in {"fruit"}:
            return "STRUCTURED_FRUIT_TERMS"
        if "axiom" in sheet_name.lower() and not row_type:
            return "AXIOM_TERMS"
        return ""

    def terms(self, collections: Iterable[str]) -> List[SemanticTerm]:
        out: List[SemanticTerm] = []
        for c in collections:
            out.extend(self.terms_by_collection.get(c, []))
        return out

    def grouped_vector(self, file_id: str, text: str, collection: str, prefix: str, family: str, limit: int = 25) -> Dict[str, float]:
        unit = TextUnit(file_id=file_id, unit_id=file_id, unit_type="file", ordinal=0, text=text, anchor="", start_char=0, end_char=len(text))
        grouped: Dict[str, List[SemanticTerm]] = defaultdict(list)
        for term in self.terms_by_collection.get(collection, []):
            grouped[term.bucket or term.term].append(term)
        raw: Dict[str, float] = {}
        for bucket, terms in grouped.items():
            result = build_metric_from_terms(file_id, unit, f"{prefix}.{bucket}.score", family, bucket, "score", terms, [], [])
            if result.score > 0:
                raw[bucket] = result.score
        ranked = dict(sorted(raw.items(), key=lambda kv: kv[1], reverse=True)[:limit])
        return normalize_vector(ranked)

    def collection_counts(self) -> Dict[str, int]:
        return {k: len(v) for k, v in sorted(self.terms_by_collection.items())}

def danger_modifier(level: str) -> float:
    return {"low": 1.0, "medium": 1.15, "high": 1.35, "critical": 1.65}.get((level or "").lower(), 1.0)

def polarity_modifier(polarity: str) -> float:
    return -1.0 if (polarity or "").lower() in {"negative", "counter"} else 1.0

def term_matches(text: str, term: str) -> List[Tuple[int, int, str]]:
    if not term:
        return []
    pattern = re.escape(term.lower())
    low = text.lower()
    matches = []
    if " " in term:
        start = 0
        while True:
            i = low.find(term.lower(), start)
            if i < 0:
                break
            matches.append((i, i + len(term), text[i:i+len(term)]))
            start = i + len(term)
    else:
        for m in re.finditer(rf"\b{pattern}\b", low):
            matches.append((m.start(), m.end(), text[m.start():m.end()]))
    return matches

def make_result_id(file_id: str, unit_id: str, metric_id: str) -> str:
    return hashlib.sha1(f"{file_id}|{unit_id}|{metric_id}".encode()).hexdigest()[:20]

def build_metric_from_terms(
    file_id: str,
    unit: TextUnit,
    metric_id: str,
    family: str,
    obj: str,
    facet: str,
    terms: List[SemanticTerm],
    support_terms: List[SemanticTerm],
    counter_terms: List[SemanticTerm],
) -> MetricResult:
    result_id = make_result_id(file_id, unit.unit_id, metric_id)
    word_count = max(1, len(tokens(unit.text)))
    spans: List[EvidenceSpan] = []
    unique = set()
    weighted = 0.0
    for st in terms:
        for start, end, matched in term_matches(unit.text, st.term):
            contrib = max(0.25, st.weight) * danger_modifier(st.danger_level) * abs(polarity_modifier(st.polarity))
            weighted += contrib
            unique.add(st.term.lower())
            spans.append(EvidenceSpan(
                span_id=hashlib.sha1(f"{result_id}|{st.term}|{start}|{end}".encode()).hexdigest()[:20],
                result_id=result_id,
                file_id=file_id,
                unit_id=unit.unit_id,
                metric_id=metric_id,
                term=st.term,
                normalized_term=st.term.lower(),
                lexicon_collection=st.collection,
                lexicon_bucket=st.bucket or st.collection,
                lexicon_subbucket=st.subbucket,
                polarity=st.polarity,
                danger_level=st.danger_level,
                term_weight=st.weight,
                contribution=round(contrib, 4),
                matched_text=matched,
                paragraph_index=unit.ordinal if unit.unit_type == "paragraph" else 0,
                sentence_index=unit.ordinal if unit.unit_type == "sentence" else 0,
                start_char=unit.start_char + start,
                end_char=unit.start_char + end,
            ))
    support_score = min(100.0, len({s.term.lower() for s in support_terms if term_matches(unit.text, s.term)}) * 14)
    counter_score = min(100.0, len({s.term.lower() for s in counter_terms if term_matches(unit.text, s.term)}) * 16)
    density = 1000.0 * weighted / word_count
    marker_strength = min(100.0, weighted * 12)
    distribution = 100.0 if spans else 0.0
    score = pct(0.35 * marker_strength + 0.20 * min(100, density * 10) + 0.20 * support_score + 0.15 * distribution - 0.20 * counter_score)
    confidence = pct(0.55 * score + 0.25 * min(100, len(unique) * 20) + 0.20 * (100 - counter_score))
    qualifier = "dominant" if score >= 85 else "strong" if score >= 65 else "moderate" if score >= 35 else "weak" if score >= 10 else "absent"
    symptom = "No meaningful signal detected." if score < 10 else f"{obj} signal is {qualifier} at {unit.unit_type} level."
    if counter_score > 40:
        symptom += " Counter-signal pressure is high; inspect contradiction or mixed category."
    repair = "No immediate repair required; preserve and compare to rivals."
    if score < 35:
        repair = "Add clearer terms, evidence spans, or downgrade this label."
    if counter_score > 40:
        repair = "Split claim or add boundary language before promoting."
    return MetricResult(
        result_id=result_id,
        file_id=file_id,
        unit_id=unit.unit_id,
        scope=unit.unit_type,
        metric_id=metric_id,
        metric_family=family,
        metric_object=obj,
        facet=facet,
        raw_hits=len(spans),
        weighted_hits=round(weighted, 4),
        unique_terms=len(unique),
        density_per_1000_words=round(density, 4),
        distribution_score=distribution,
        cooccurrence_score=support_score,
        counter_signal_score=counter_score,
        evidence_support=support_score if family in {"evidence", "domain", "law"} else 0,
        boundary_support=support_score if "boundary" in metric_id else 0,
        score=score,
        confidence=confidence,
        qualifier=qualifier,
        symptom=symptom,
        symptom_severity="high" if counter_score > 60 else "medium" if score < 35 and len(spans) else "low",
        repair_action=repair,
        route_trigger=bool(score >= 70 or counter_score >= 50 or (score >= 45 and confidence < 55)),
        evidence_spans=spans,
    )

def normalize_vector(raw: Dict[str, float]) -> Dict[str, float]:
    positives = {k: max(0.0, float(v)) for k, v in raw.items() if float(v) > 0}
    total = sum(positives.values())
    if total <= 0:
        return {k: 0.0 for k in raw}
    return {k: round(v / total * 100.0, 2) for k, v in positives.items()}

def extract_profiles(file_id: str, text: str, lex: LexiconStore) -> Dict[str, Dict[str, float]]:
    full_unit = TextUnit(file_id=file_id, unit_id=file_id, unit_type="file", ordinal=0, text=text, anchor="", start_char=0, end_char=len(text))
    raw_domains = {}
    for d, terms in DOMAIN_TERMS.items():
        sts = [SemanticTerm(term=t, collection="DOMAIN_KEYWORDS", bucket=d) for t in terms]
        res = build_metric_from_terms(file_id, full_unit, f"domain.{d}.score", "domain", d, "score", sts, [], [])
        raw_domains[d] = res.score
    raw_chi = {}
    for var, terms in MASTER_VARIABLES.items():
        sts = [SemanticTerm(term=t, collection="ME_VARS", bucket=var) for t in terms]
        res = build_metric_from_terms(file_id, full_unit, f"me.{var.lower()}.score", "master_equation", var, "score", sts, [], [])
        raw_chi[var] = res.score
    return {
        "domain_vector": normalize_vector(raw_domains),
        "chi_vector": normalize_vector(raw_chi),
        "axiom_vector": lex.grouped_vector(file_id, text, "AXIOM_TERMS", "axiom", "axiom"),
        "definition_vector": lex.grouped_vector(file_id, text, "DEFINITION_TERMS", "definition", "definition"),
        "lemma_vector": lex.grouped_vector(file_id, text, "LEMMA_TERMS", "lemma", "lemma"),
        "theorem_vector": lex.grouped_vector(file_id, text, "THEOREM_TERMS", "theorem", "theorem"),
        "property_vector": lex.grouped_vector(file_id, text, "PROPERTY_TERMS", "property", "property"),
        "equation_vector": lex.grouped_vector(file_id, text, "EQUATION_TERMS", "equation", "equation"),
        "boundary_condition_vector": lex.grouped_vector(file_id, text, "BOUNDARY_CONDITION_TERMS", "boundary_condition", "boundary_condition"),
        "assumption_vector": lex.grouped_vector(file_id, text, "ASSUMPTION_TERMS", "assumption", "assumption"),
        "fruit_vector": lex.grouped_vector(file_id, text, "FRUITS", "fruit", "fruit"),
        "anti_fruit_vector": lex.grouped_vector(file_id, text, "ANTI_FRUITS", "anti_fruit", "anti_fruit"),
        "law_vector": lex.grouped_vector(file_id, text, "LAW_KEYWORDS", "law", "law"),
        "structured_law_vector": lex.grouped_vector(file_id, text, "STRUCTURED_LAW_TERMS", "structured_law", "law"),
    }

def write_chi_sidecar(path: Path, report: Dict[str, Any], out_path: Path) -> None:
    text = ["---", "template_version: chi_qi_v5.0", f"file_id: {report['identity']['file_id']}", f"source_path: {json.dumps(str(path))}", "---", ""]
    text.append("# χ / Qi v5 File Intelligence Sidecar\n")
    text.append("## Identity\n")
    text.append("```json\n" + json.dumps(report["identity"], indent=2) + "\n```\n")
    text.append("## Lexicon\n")
    text.append("```json\n" + json.dumps(report["lexicon"], indent=2) + "\n```\n")
    text.append("## Profiles\n")
    text.append("```json\n" + json.dumps(report["profiles"], indent=2) + "\n```\n")
    text.append("## Top Metric Results\n")
    text.append("```json\n" + json.dumps(report["metric_results"][:25], indent=2) + "\n```\n")
    text.append("## Routing\n")
    text.append("```json\n" + json.dumps(report["routing"], indent=2) + "\n```\n")
    out_path.write_text("\n".join(text), encoding="utf-8")

def init_db(db_path: Path, schema_path: Optional[Path] = None) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    if schema_path and schema_path.exists():
        con.executescript(schema_path.read_text(encoding="utf-8"))
    return con

def top_terms_for_text(file_id: str, text: str, terms: List[SemanticTerm], limit: int) -> List[SemanticTerm]:
    if limit <= 0 or not terms:
        return []
    unit = TextUnit(file_id=file_id, unit_id=file_id, unit_type="file", ordinal=0, text=text, anchor="", start_char=0, end_char=len(text))
    scored: List[Tuple[float, SemanticTerm]] = []
    seen = set()
    for term in terms:
        key = (term.collection, term.bucket, term.term)
        if key in seen:
            continue
        seen.add(key)
        result = build_metric_from_terms(file_id, unit, f"candidate.{term.collection}.{term.bucket}", term.collection.lower(), term.bucket, "score", [term], [], [])
        if result.raw_hits:
            scored.append((result.score * max(1.0, term.weight), term))
    return [term for _, term in sorted(scored, key=lambda kv: kv[0], reverse=True)[:limit]]

def process_file(path: Path, lex: LexiconStore, out_dir: Path, deep_axiom_spans: int = 0) -> Dict[str, Any]:
    raw = read_text(path)
    file_id = sha256_text(str(path) + raw[:1000])[:16]
    paras = split_paragraphs_with_offsets(raw, file_id)
    sents = split_sentences_from_paragraphs(paras)
    profiles = extract_profiles(file_id, raw, lex)

    metric_results: List[MetricResult] = []
    # Sentence-level evidence / boundary / falsification / coherence examples.
    metric_specs = [
        ("axiom.general.score", "axiom", "axiom", "score", ["AXIOM_TERMS"], ["EVIDENCE_TERMS", "BOUNDARY_TERMS"], []),
        ("law.general.score", "law", "law", "score", ["LAW_KEYWORDS"], ["EVIDENCE_TERMS"], []),
        ("evidence.general.score", "evidence", "evidence", "score", ["EVIDENCE_TERMS"], ["BOUNDARY_TERMS"], []),
        ("boundary.general.score", "boundary", "boundary", "score", ["BOUNDARY_TERMS"], ["EVIDENCE_TERMS"], []),
        ("falsification.general.score", "falsification", "falsification", "score", ["FALSIFY_TERMS"], ["EVIDENCE_TERMS"], []),
        ("coherence.general.score", "coherence", "coherence", "score", ["COHERENCE_TERMS"], ["EVIDENCE_TERMS", "FALSIFY_TERMS"], ["DISCOHERENCE_TERMS"]),
        ("fruit.general.score", "fruit", "fruit", "score", ["FRUITS"], ["BOUNDARY_TERMS"], ["ANTI_FRUITS"]),
        ("anti_fruit.general.score", "anti_fruit", "anti_fruit", "score", ["ANTI_FRUITS"], [], ["FRUITS"]),
    ]
    units = sents[:300] if sents else paras[:300]
    deep_axiom_terms = top_terms_for_text(file_id, raw, lex.terms(["AXIOM_TERMS"]), deep_axiom_spans)
    for unit in units:
        for metric_id, fam, obj, facet, cols, support_cols, counter_cols in metric_specs:
            terms = lex.terms(cols)
            if fam == "axiom" and deep_axiom_terms:
                terms = deep_axiom_terms
            elif fam == "axiom" and len(terms) > MAX_SENTENCE_AXIOM_TERMS:
                continue
            support = lex.terms(support_cols)
            counter = lex.terms(counter_cols)
            result = build_metric_from_terms(file_id, unit, metric_id, fam, obj, facet, terms, support, counter)
            if result.raw_hits or result.score >= 10:
                metric_results.append(result)

    high_risk = [r for r in metric_results if r.route_trigger or r.counter_signal_score > 50]
    identity = {
        "file_id": file_id,
        "source_path": str(path),
        "title": path.stem,
        "content_type": path.suffix.lower().lstrip(".") or "text",
        "extension": path.suffix.lower(),
        "word_count": len(tokens(raw)),
        "paragraph_count": len(paras),
        "sentence_count": len(sents),
        "hash_sha256": sha256_text(raw),
    }
    lexicon_block = {
        "loaded": lex.loaded,
        "path": lex.path,
        "policy": lex.policy,
        "checksum": lex.checksum,
        "sheets_loaded": lex.sheet_names,
        "role": "canonical_measurement_language",
        "warnings": lex.warnings,
        "collection_counts": lex.collection_counts(),
    }
    report = {
        "template_version": "chi_qi_v5.0",
        "identity": identity,
        "lexicon": lexicon_block,
        "profiles": profiles,
        "metric_results": [
            {k: v for k, v in asdict(r).items() if k != "evidence_spans"} | {
                "evidence_spans": [asdict(s) for s in r.evidence_spans[:5]]
            }
            for r in sorted(metric_results, key=lambda x: (x.score, x.confidence), reverse=True)[:100]
        ],
        "routing": {
            "pass_1_complete": True,
            "pass_2_deep_audit_recommended": bool(high_risk or max((r.score for r in metric_results), default=0) >= 70),
            "pass_3_llm_review_recommended": False,
            "reasons": sorted(set([r.symptom for r in high_risk[:10]])),
            "deep_axiom_spans_requested": deep_axiom_spans,
            "deep_axiom_terms_used": len(deep_axiom_terms),
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_chi_sidecar(path, report, out_dir / f"{path.name}.chi")
    (out_dir / f"{path.stem}.chi_v5.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report

def top_vector_item(vector: Dict[str, float]) -> Tuple[str, float]:
    if not vector:
        return "", 0.0
    key, value = max(vector.items(), key=lambda kv: kv[1])
    return key, value

def write_batch_summary_csv(reports: List[Dict[str, Any]], out_path: Path) -> None:
    fields = [
        "file_id", "path", "extension", "word_count", "top_domain", "top_domain_score",
        "top_chi", "top_chi_score", "top_axiom", "top_axiom_score", "top_fruit",
        "top_fruit_score", "top_law", "top_law_score", "deep_audit_recommended",
        "deep_axiom_terms_used",
    ]
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for report in reports:
            identity = report.get("identity", {})
            profiles = report.get("profiles", {})
            top_domain, top_domain_score = top_vector_item(profiles.get("domain_vector", {}))
            top_chi, top_chi_score = top_vector_item(profiles.get("chi_vector", {}))
            top_axiom, top_axiom_score = top_vector_item(profiles.get("axiom_vector", {}))
            top_fruit, top_fruit_score = top_vector_item(profiles.get("fruit_vector", {}))
            top_law, top_law_score = top_vector_item(profiles.get("law_vector", {}))
            writer.writerow({
                "file_id": identity.get("file_id", ""),
                "path": identity.get("source_path", ""),
                "extension": identity.get("extension", ""),
                "word_count": identity.get("word_count", 0),
                "top_domain": top_domain,
                "top_domain_score": top_domain_score,
                "top_chi": top_chi,
                "top_chi_score": top_chi_score,
                "top_axiom": top_axiom,
                "top_axiom_score": top_axiom_score,
                "top_fruit": top_fruit,
                "top_fruit_score": top_fruit_score,
                "top_law": top_law,
                "top_law_score": top_law_score,
                "deep_audit_recommended": report.get("routing", {}).get("pass_2_deep_audit_recommended", False),
                "deep_axiom_terms_used": report.get("routing", {}).get("deep_axiom_terms_used", 0),
            })

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="χ / Qi v5 Statistical Audit scaffold")
    p.add_argument("--input", required=True, help="Input file or folder")
    p.add_argument("--out", required=True, help="Output folder")
    p.add_argument("--lexicon", action="append", default=[], help="Optional workbook lexicon/control file. Repeat for axioms, fruits, and metric catalogs.")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--max-files", type=int, default=0)
    p.add_argument("--deep-axiom-spans", type=int, default=0, help="Enable sentence-level axiom citations for the top N axiom terms matched in each file.")
    args = p.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    lex_paths = [Path(x).expanduser().resolve() for x in args.lexicon]
    lex = LexiconStore.load_many(lex_paths)

    if input_path.is_file():
        files = [input_path]
    else:
        globber = input_path.rglob("*") if args.recursive else input_path.glob("*")
        files = [x for x in globber if x.suffix.lower() in INPUT_EXTS]
    if args.max_files:
        files = files[:args.max_files]

    reports = []
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f}")
        reports.append(process_file(f, lex, out_dir, deep_axiom_spans=args.deep_axiom_spans))

    summary = {
        "engine_version": ENGINE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(reports),
        "lexicon_loaded": lex.loaded,
        "reports": [{"file_id": r["identity"]["file_id"], "path": r["identity"]["source_path"], "profiles": r["profiles"], "routing": r["routing"]} for r in reports],
    }
    (out_dir / "chi_qi_v5_batch_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_batch_summary_csv(reports, out_dir / "chi_qi_v5_batch_summary.csv")
    print(f"Done: {out_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
