#!/usr/bin/env python3
"""
chi_evaluator_7q.py — Master Equation + 7Q Full Method + Fruits Lexicon
POF 2828 | 2026-06-18 | David Lowe / Claude
"""

from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Literal

import openpyxl
from openpyxl import load_workbook


# ============================================================
# 1. LOAD 7Q WORKBOOK SHEETS
# ============================================================

def load_workbook_sheets(path: Path) -> dict[str, dict]:
    """Load all sheets from 7Q Full Method.xlsx as dicts (row-wise)."""
    wb = load_workbook(path, data_only=True, read_only=True)
    sheets = {}
    for name in wb.sheetnames:
        ws = wb[name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
        data = []
        for row in rows[1:]:
            if any(cell is not None and str(cell).strip() for cell in row):
                data.append({headers[i]: row[i] for i in range(len(headers)) if i < len(row)})
        sheets[name] = data
    return sheets


def load_enum_lookup(sheets: dict) -> dict[str, dict[str, str]]:
    """Load 'Enums & Dropdowns' sheet → mapping: q_field → enum_value → display_label."""
    rows = sheets.get("Enums & Dropdowns", [])
    lookup = {}
    for row in rows:
        q = row.get("Question", "").strip()
        field = row.get("Field Name", "").strip()
        enum = row.get("Enum Value", "").strip()
        label = row.get("Display Label / Description", "").strip()
        if field and enum:
            key = f"{q}::{field}" if q else field
            lookup.setdefault(key, {})[enum] = label
    return lookup


def load_truth_score_tables(sheets: dict) -> dict[str, dict]:
    """Load the Truth Score sheet's decision tables."""
    rows = sheets.get("Truth Score", [])
    tables = {"S": {}, "E": {}, "L": {}, "D": {}, "P": {}, "C": {}, "confidence": []}
    mode = None
    for row in rows:
        text = str(row.get("A", "")).strip()
        if text in ("S — SURVIVABILITY COMPUTATION", "E — EVIDENCE COMPUTATION",
                    "L — LOGIC COMPUTATION", "D — DEPENDENCIES COMPUTATION",
                    "P — PREDICTIONS COMPUTATION", "C — COHERENCE COMPUTATION"):
            mode = text[0]
            continue
        if "Condition" in text and "Score" in text:
            continue
        if mode and "Condition" in str(row.get("Condition", "")) and "Score" in str(row.get("Score", "")):
            continue
        if mode and row.get("Condition") and row.get("Score") is not None:
            tables[mode][str(row["Condition"]).strip()] = float(row["Score"]) if isinstance(row["Score"], (int, float)) else 0.0
        if "T Range" in text:
            mode = "confidence"
            continue
        if mode == "confidence" and row.get("T Range"):
            label = str(row.get("Label", "")).strip()
            if label:
                tables["confidence"].append({
                    "range": str(row["T Range"]).strip(),
                    "label": label,
                    "meaning": str(row.get("Meaning", "")).strip()
                })
    return tables


def load_evidence_protocol(sheets: dict) -> dict[str, Any]:
    """Load Evidence Protocol sheet → PS/ED/EC component weights and formulas."""
    rows = sheets.get("Evidence Protocol", [])
    protocol = {
        "PS": {"components": {}, "weight": 0},
        "ED": {"components": {}, "weight": 0},
        "EC": {"components": {}, "weight": 0}
    }
    for row in rows:
        text = str(row.get("A", "")).strip()
        if "Phenomenon Strength" in text:
            protocol["PS"]["weight"] = float(row.get("D", row.get("C", 0)) or 0)
        if "Explanatory Depth" in text:
            protocol["ED"]["weight"] = float(row.get("D", row.get("C", 0)) or 0)
        if "Experiential Coherence" in text:
            protocol["EC"]["weight"] = float(row.get("D", row.get("C", 0)) or 0)
        if "Components" in text and "PS" in str(row.get("A", "")):
            comps = [c for c in str(row.get("D", "")).split("+") if c.strip()]
            for comp in comps:
                if "(" in comp:
                    name = comp.split("(")[0].strip()
                    weight = float(comp.split("(")[1].split(")")[0])
                    protocol["PS"]["components"][name] = weight
        if "Components" in text and "ED" in str(row.get("A", "")):
            comps = [c for c in str(row.get("D", "")).split("+") if c.strip()]
            for comp in comps:
                if "(" in comp:
                    name = comp.split("(")[0].strip()
                    weight = float(comp.split("(")[1].split(")")[0])
                    protocol["ED"]["components"][name] = weight
        if "Components" in text and "EC" in str(row.get("A", "")):
            comps = [c for c in str(row.get("D", "")).split("+") if c.strip()]
            for comp in comps:
                if "(" in comp:
                    name = comp.split("(")[0].strip()
                    weight = float(comp.split("(")[1].split(")")[0])
                    protocol["EC"]["components"][name] = weight
    return protocol


# ============================================================
# 2. LOAD FRUITS LEXICON
# ============================================================

FRUIT_TERMS = set()
ANTI_FRUIT_TERMS = set()
GROUNDING_TERMS = set()
CONTRADICTION_TERMS = set()
PROPAGANDA_TERMS = set()
JARGON_TERMS = set()


def load_lexicon_from_workbook(path: Path) -> None:
    """Load Fruit, Anti-Fruit, Grounding, Contradiction, Propaganda, Jargon from the workbook."""
    wb = load_workbook(path, data_only=True, read_only=True)

    for sheet_name, target_set in [
        ("Fruit", FRUIT_TERMS),
        ("Anti-Fruit", ANTI_FRUIT_TERMS),
        ("Grounding", GROUNDING_TERMS),
        ("Contradiction", CONTRADICTION_TERMS),
        ("Propaganda", PROPAGANDA_TERMS),
        ("Jargon", JARGON_TERMS),
    ]:
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        for row in ws.iter_rows(values_only=True):
            if row and row[0]:
                term = str(row[0]).strip().lower()
                if term and not term.startswith("term") and not term.startswith("anti-fruit"):
                    target_set.add(term)


def load_7q_workbook(path: Path) -> dict[str, Any]:
    """Load all 7Q data from the workbook."""
    sheets = load_workbook_sheets(path)
    load_lexicon_from_workbook(path)
    return {
        "sheets": sheets,
        "enums": load_enum_lookup(sheets),
        "truth_tables": load_truth_score_tables(sheets),
        "evidence_protocol": load_evidence_protocol(sheets),
        "lexicon": {
            "fruit": FRUIT_TERMS,
            "anti_fruit": ANTI_FRUIT_TERMS,
            "grounding": GROUNDING_TERMS,
            "contradiction": CONTRADICTION_TERMS,
            "propaganda": PROPAGANDA_TERMS,
            "jargon": JARGON_TERMS,
        }
    }


# ============================================================
# 3. TERM SCORING ENGINE
# ============================================================

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z][a-z']+", text.lower())


def count_terms(text: str, term_set: set[str]) -> int:
    tokens = tokenize(text)
    return sum(1 for t in tokens if t in term_set)


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def score_channel(text: str, lexicon: dict[str, set[str]]) -> dict[str, float]:
    """Score a single sentence/paragraph across all term categories."""
    tokens = tokenize(text)
    token_count = max(1, len(tokens))

    fruit = count_terms(text, lexicon.get("fruit", set()))
    anti = count_terms(text, lexicon.get("anti_fruit", set()))
    ground = count_terms(text, lexicon.get("grounding", set()))
    contra = count_terms(text, lexicon.get("contradiction", set()))
    prop = count_terms(text, lexicon.get("propaganda", set()))
    jargon = count_terms(text, lexicon.get("jargon", set()))

    # Normalize per token
    f = clamp01(fruit / (max(1, token_count / 35.0)))
    a = clamp01(anti / (max(1, token_count / 35.0)))
    g = clamp01(ground / (max(1, token_count / 40.0)))
    c = clamp01(contra / (max(1, token_count / 50.0)))
    p = clamp01(prop / (max(1, token_count / 30.0)))
    j = clamp01(jargon / (max(1, token_count / 40.0)))

    # Coherence = (fruit + ground) / (anti + contra + 1e-6) clamped
    coherence = clamp01((fruit + ground + 0.1) / (anti + contra + 1e-6))

    # Truth = coherence * 0.34 + ground * 0.23 + fruit * 0.23 - anti * 0.14 - contra * 0.12
    truth = clamp01(coherence * 0.34 + g * 0.23 + f * 0.23 - a * 0.14 - c * 0.12)

    return {
        "truth": round(truth, 4),
        "coherence": round(coherence, 4),
        "fruit": round(f, 4),
        "anti_fruit": round(a, 4),
        "grounding": round(g, 4),
        "contradiction": round(c, 4),
        "propaganda": round(p, 4),
        "jargon": round(j, 4),
        "tokens": token_count,
    }


def score_sentence(sentence: str, lexicon: dict[str, set[str]]) -> dict[str, float]:
    """Score a single sentence for all metrics."""
    return score_channel(sentence, lexicon)


# ============================================================
# 4. 10‑CHANNEL MASTER EQUATION TENSOR
# ============================================================

CHANNEL_NAMES = {
    "G": "Gravity / Belonging",
    "M": "Mass / Meaning",
    "E": "Entropy / Engagement",
    "S": "Spacetime / Structure",
    "T": "Time / Eternity",
    "K": "Knowledge / Logos",
    "R": "Relationship",
    "Q": "Quantum / Observer",
    "F": "Faith / Coupling",
    "C": "Christ / Coherence",
}


def sentence_tensor(scores: dict[str, float]) -> dict[str, float]:
    """Convert sentence scores to a 10‑channel vector."""
    f = scores["fruit"]
    a = scores["anti_fruit"]
    g = scores["grounding"]
    c = scores["contradiction"]
    coh = scores["coherence"]
    # Each channel is a blend of positive and negative terms
    base = clamp01((f + g + coh) / (a + c + 1e-6))
    return {
        "G": base * 0.8 + f * 0.2,
        "M": base * 0.7 + g * 0.3,
        "E": coh * 0.6 + (1 - a) * 0.4,
        "S": base * 0.5 + coh * 0.5,
        "T": g * 0.6 + coh * 0.4,
        "K": base * 0.9 + f * 0.1,
        "R": base * 0.7 + (1 - a) * 0.3,
        "Q": coh * 0.5 + (1 - c) * 0.5,
        "F": base * 0.8 + g * 0.2,
        "C": coh * 0.9 + (1 - a) * 0.1,
    }


def aggregate_tensor(sentence_tensors: list[dict[str, float]]) -> dict[str, float]:
    """Mean of all sentence tensors."""
    if not sentence_tensors:
        return {k: 0.0 for k in CHANNEL_NAMES}
    agg = {k: 0.0 for k in CHANNEL_NAMES}
    for st in sentence_tensors:
        for k in agg:
            agg[k] += st.get(k, 0.0)
    n = len(sentence_tensors)
    return {k: round(v / n, 4) for k, v in agg.items()}


def compute_chi(tensor: dict[str, float]) -> float:
    """χ = product of all 10 channel scores."""
    prod = 1.0
    for v in tensor.values():
        prod *= clamp01(v)
    return round(prod, 6)


# ============================================================
# 5. 7Q TRUTH SCORE DERIVATION
# ============================================================

def derive_S(branch_status: str, adversarial_tested: bool) -> float:
    mapping = {
        "alive": 1.0 if adversarial_tested else 0.6,
        "problematic": 0.3,
        "dead": 0.0,
        "untested": 0.4,
    }
    return mapping.get(branch_status, 0.5)


def derive_E(evidence_tier: str, replication: str) -> float:
    if evidence_tier == "tier_1":
        if replication == "replicated":
            return 1.0
        if replication == "partial":
            return 0.8
        return 0.9
    if evidence_tier == "tier_2":
        if replication == "replicated":
            return 0.7
        return 0.4
    if evidence_tier == "tier_3":
        return 0.2
    return 0.0


def derive_L(evidence_type: list[str], precision: str) -> float:
    score = 0.3
    if "mathematical" in evidence_type:
        score = 1.0
    elif "logical" in evidence_type:
        score = 0.8
    if precision in ("mathematical", "precise"):
        score = min(1.0, score + 0.2)
    return round(score, 4)


def derive_D(chain_terminus: str, fragility: str) -> float:
    if chain_terminus == "axiom":
        if fragility == "survive_independently":
            return 1.0
        if fragility == "degrade_gracefully":
            return 0.8
        return 0.6
    if chain_terminus == "brute_fact":
        return 0.5
    if chain_terminus == "circularity":
        return 0.1
    if chain_terminus == "open":
        return 0.0
    return 0.5


def derive_P(confirmed: int, untested: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((confirmed + 0.5 * untested) / total, 4)


def derive_C(isomorphism_status: str) -> float:
    mapping = {
        "ISO-confirmed": 1.0,
        "ISO-parallel": 0.6,
        "ISO-analogy": 0.3,
        "none": 0.0,
    }
    return mapping.get(isomorphism_status, 0.0)


def compute_truth_score(
    S: float,
    E: float,
    L: float,
    D: float,
    P: float,
    C: float
) -> tuple[float, str]:
    T = round((S + E + L + D + P + C) / 6.0, 4)
    if T >= 0.85:
        label = "ESTABLISHED"
    elif T >= 0.65:
        label = "WELL SUPPORTED"
    elif T >= 0.40:
        label = "TENTATIVE"
    elif T >= 0.15:
        label = "SPECULATIVE"
    else:
        label = "UNSUPPORTED"
    return T, label


# ============================================================
# 6. EVIDENCE PROTOCOL — PS/ED/EC/CF/E_final
# ============================================================

def evidence_score(
    reproducibility: float,
    effect_size: float,
    measurement_quality: float,
    mechanism_clarity: float,
    constraint_consistency: float,
    scope: float,
    internal_consistency: float,
    longitudinal_stability: float,
    behavioral_transformation: float,
    intersubjective_pattern: float
) -> dict[str, float]:
    """Compute PS, ED, EC, CF, E_final from the Evidence Protocol."""
    PS = (reproducibility * 0.4 + effect_size * 0.3 + measurement_quality * 0.3)
    ED = (mechanism_clarity * 0.4 + constraint_consistency * 0.3 + scope * 0.3)
    EC = (internal_consistency * 0.25 + longitudinal_stability * 0.25 +
          behavioral_transformation * 0.25 + intersubjective_pattern * 0.25)

    PS = clamp01(PS)
    ED = clamp01(ED)
    EC = clamp01(EC)

    CF = (0.5 + 0.5 * ED) * (0.5 + 0.5 * EC)
    E_final = PS * CF

    # Why‑Penalty: if ED < 0.3, cap E_final at 0.5
    if ED < 0.3:
        E_final = min(E_final, 0.5)

    return {
        "PS": round(PS, 4),
        "ED": round(ED, 4),
        "EC": round(EC, 4),
        "CF": round(CF, 4),
        "E_final": round(E_final, 4),
    }


# ============================================================
# 7. MAIN EVALUATOR
# ============================================================

def split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"])', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def evaluate_text(
    text: str,
    lexicon: dict[str, set[str]],
    evidence_fields: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Master evaluator: takes text, returns full 7Q + χ report."""
    sentences = split_sentences(text)
    if not sentences:
        sentences = [text]

    sentence_scores = []
    sentence_tensors = []

    for sent in sentences:
        sc = score_sentence(sent, lexicon)
        sentence_scores.append(sc)
        sentence_tensors.append(sentence_tensor(sc))

    # Document-level aggregates
    agg_scores = {
        k: round(sum(s[k] for s in sentence_scores) / len(sentence_scores), 4)
        for k in sentence_scores[0].keys()
    }

    tensor = aggregate_tensor(sentence_tensors)
    chi = compute_chi(tensor)

    # Derive 7Q variables (using placeholder defaults for fields not present in raw text)
    S = derive_S("alive", True)
    E = derive_E("tier_2", "replicated")
    L = derive_L(["logical"], "detailed")
    D = derive_D("brute_fact", "survive_independently")
    P = derive_P(3, 1, 4)
    C = derive_C("ISO-parallel")

    T, confidence_label = compute_truth_score(S, E, L, D, P, C)

    # Gradient direction (linear regression slope on cumulative χ)
    cum_chi = []
    running = 1.0
    for st in sentence_tensors:
        running *= clamp01(st.get("C", 0.5))
        cum_chi.append(running)

    if len(cum_chi) > 1:
        xs = list(range(len(cum_chi)))
        mean_x = sum(xs) / len(xs)
        mean_y = sum(cum_chi) / len(cum_chi)
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, cum_chi))
        denominator = sum((x - mean_x) ** 2 for x in xs)
        slope = numerator / denominator if denominator != 0 else 0
        gradient = "positive" if slope > 0.01 else ("negative" if slope < -0.01 else "neutral")
    else:
        gradient = "neutral"

    # Dominant/weakest channels
    sorted_channels = sorted(tensor.items(), key=lambda kv: kv[1])
    weakest_channel = sorted_channels[0][0] if sorted_channels else "N/A"
    strongest_channel = sorted_channels[-1][0] if sorted_channels else "N/A"

    return {
        "document_score": {
            "χ": chi,
            "truth_score_T": T,
            "confidence_label": confidence_label,
            "gradient_direction": gradient,
            "S": S,
            "E": E,
            "L": L,
            "D": D,
            "P": P,
            "C": C,
            "channel_scores": tensor,
            "dominant_law": "Gravity ↔ Grace",  # placeholder — can be improved
            "weakest_channel": f"{weakest_channel} ({CHANNEL_NAMES.get(weakest_channel, '')})",
            "strongest_channel": f"{strongest_channel} ({CHANNEL_NAMES.get(strongest_channel, '')})",
            "sentence_count": len(sentences),
        },
        "sentence_breakdown": sentence_scores,
        "sentence_tensors": sentence_tensors,
    }


# ============================================================
# 8. CLI
# ============================================================

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="χ-Evaluator + 7Q Full Method")
    parser.add_argument("--input", "-i", required=True, help="Text file or direct text to evaluate")
    parser.add_argument("--workbook", "-w", default="7Q Full Method.xlsx", help="Path to 7Q Full Method.xlsx")
    parser.add_argument("--output", "-o", default=None, help="Output JSON file (if not provided, prints to stdout)")
    args = parser.parse_args()

    wb_path = Path(args.workbook)
    if not wb_path.exists():
        print(f"ERROR: Workbook not found: {wb_path}", file=sys.stderr)
        return 1

    data = load_7q_workbook(wb_path)
    lexicon = data["lexicon"]

    # Read input
    input_path = Path(args.input)
    if input_path.exists():
        text = input_path.read_text(encoding="utf-8", errors="ignore")
    else:
        text = args.input

    result = evaluate_text(text, lexicon)

    output = args.output
    if output:
        Path(output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())