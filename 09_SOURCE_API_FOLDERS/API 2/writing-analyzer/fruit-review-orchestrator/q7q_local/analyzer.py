"""7Q analysis layer (forward, reverse, evidence modes)."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .core import DEATH_TYPES, SevenQState, QMode


def generate_negation(text: str) -> str:
    t = text.strip()
    if not t:
        return "not claim"
    return f"not ({t[:180]})"


def compute_ps_score(text: str, evidence_items: List[Dict[str, Any]]) -> float:
    words = len(text.lower().split())
    if words < 1:
        return 0.0
    anchors = ["data", "experiment", "study", "proof", "source", "cite", "evidence", "simulation", "model", "observation"]
    hits = sum(1 for a in anchors if a in text.lower())
    ps = min(1.0, 0.2 + (hits / max(len(anchors), 1)) + min(len(evidence_items) * 0.05, 0.4))
    return round(ps, 3)


def compute_ed_score(text: str, evidence_items: List[Dict[str, Any]]) -> float:
    if not text:
        return 0.0
    c = 0.0
    c += 0.25 if any(x in text.lower() for x in ["because", "therefore", "hence", "thus"]) else 0.0
    c += 0.25 if any(x in text.lower() for x in ["because of", "due to", "causes", "mechanism"]) else 0.0
    c += 0.20 if evidence_items else 0.0
    if "if" in text.lower() and ("then" in text.lower() or "implies" in text.lower()):
        c += 0.15
    return min(1.0, c)


def compute_ec_score(text: str, evidence_items: List[Dict[str, Any]]) -> float:
    # EC currently tracks explicit phenomenology and coherence language.
    cues = ["observed", "experienced", "felt", "measured", "felt", "sense", "reported"]
    c = 0.0
    lower = text.lower()
    c += min(len([x for x in cues if x in lower]) * 0.08, 0.4)
    if evidence_items:
        c += 0.25
    return min(1.0, c)


def extract_dependencies(text: str) -> List[str]:
    keys = ["assume", "requires", "depends on", "given", "if", "provided that", "unless"]
    return [k for k in keys if k in text.lower()]


def determine_terminus(deps: List[str], assumptions: List[str]) -> str:
    if not deps and not assumptions:
        return "unknown"
    if any("axiom" in a.lower() for a in assumptions):
        return "axiom"
    if any("empirical" in d.lower() for d in deps):
        return "empirical"
    if any("data" in a.lower() for a in assumptions):
        return "brute_fact"
    if len(deps) > 4:
        return "fragile_chain"
    return "theoretical"


def determine_fragility(chain_terminus: str, dependencies: List[str]) -> str:
    if chain_terminus in {"axiom", "brute_fact"}:
        return "survive_independently"
    if chain_terminus in {"empirical", "theoretical"} and len(dependencies) <= 2:
        return "degrade_gracefully"
    if chain_terminus == "fragile_chain":
        return "fragile"
    return "unknown"


def extract_predictions(text: str) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: List[str] = []
    for line in lines:
        if any(k in line.lower() for k in ["if", "then", "will", "predict", "expect", "should observe"]):
            out.append(line)
    return out


def extract_kill_conditions(text: str) -> List[str]:
    keys = [
        "if false", "if not", "impossible", "cannot hold", "breaks if", "collapse if",
        "falsified", "disconfirmed", "inconsistent", "contradiction", "counterexample"
    ]
    lower = text.lower()
    return [k for k in keys if k in lower]


def detect_death_type(statement: str) -> str:
    s = statement.lower()
    if any(x in s for x in ["contradiction", "inconsistent"]):
        return DEATH_TYPES[2]
    if any(x in s for x in ["infinite", "regress"]):
        return DEATH_TYPES[1]
    if "falsified" in s or "counterexample" in s:
        return DEATH_TYPES[4]
    if "impossible" in s:
        return DEATH_TYPES[0]
    return DEATH_TYPES[4]


def compute_q0_score(state: SevenQState) -> float:
    low = (state.claim_text + " " + state.assertion).lower()
    if any(x in low for x in ["investigate", "explore", "examine", "question"]):
        return 1.0
    if any(x in low for x in ["prove", "demonstrate", "must be"]):
        return 0.3
    return 0.6


def compute_q1_score(state: SevenQState) -> float:
    score = 0.0
    if state.claim_text:
        score += 0.3
    if state.subclaims:
        score += 0.2
    if state.claim_type != "descriptive":
        score += 0.2
    if state.precision in {"mathematical", "precise"}:
        score += 0.3
    return min(1.0, score)


def compute_q2_score(state: SevenQState) -> float:
    score = 0.0
    if state.primary_domain:
        score += 0.3
    if state.additional_domains:
        score += 0.2 * min(3, len(state.additional_domains)) / 3
    if state.scale and state.scale != "metaphysical":
        score += 0.2
    score += {"ISO_CONFIRMED": 0.3, "ISO_PARALLEL": 0.2, "ISO_ANALOGY": 0.1}.get(state.iso_status, 0.0)
    return min(1.0, score)


def compute_q3_score(state: SevenQState) -> float:
    score = 0.0
    if state.assertion:
        score += 0.2
    if state.negation:
        score += 0.2
    precision_weights = {"vague": 0.1, "basic": 0.3, "detailed": 0.5, "mathematical": 0.7, "precise": 1.0}
    certainty_weights = {"proven": 1.0, "derived": 0.8, "well_supported": 0.6, "tentative": 0.4, "speculative": 0.2, "unknown": 0.3}
    score += precision_weights.get(state.precision, 0.2) * 0.3
    score += certainty_weights.get(state.certainty, 0.3) * 0.3
    return min(1.0, score)


def compute_q4_score(state: SevenQState) -> float:
    return state.e_final


def compute_q5_score(state: SevenQState) -> float:
    score = 0.0
    if state.dependencies:
        score += 0.3 * min(1.0, len(state.dependencies) / 5.0)
    if state.axiom_deps:
        score += 0.2
    if state.chain_terminus == "axiom":
        score += 0.3
    elif state.chain_terminus == "empirical":
        score += 0.25
    elif state.chain_terminus == "brute_fact":
        score += 0.15
    elif state.chain_terminus in {"circular", "infinite"}:
        score = 0.0
    if state.fragility == "survive_independently":
        score += 0.2
    elif state.fragility == "degrade_gracefully":
        score += 0.1
    return min(1.0, score)


def compute_q6_score(state: SevenQState) -> float:
    total = len(state.predictions)
    if total == 0:
        return 0.1
    confirmed = len(state.confirmed_predictions)
    failed = len(state.failed_predictions)
    score = 0.4 * (confirmed / total) + 0.2 * (1 - failed / total)
    if state.cross_domain_force:
        score += 0.3
    return min(1.0, score)


def compute_q7_score(state: SevenQState) -> float:
    score = 0.0
    if state.kill_conditions:
        score += 0.3 * min(1.0, len(state.kill_conditions) / 5.0)
    if state.branch_status == "alive":
        score += 0.3
    elif state.branch_status == "untested":
        score += 0.15
    elif state.branch_status == "problematic":
        score += 0.05
    if state.adversarial_tested:
        score += 0.4
    return min(1.0, score)


def analyze_evidence(state: SevenQState, cfg: Dict[str, Any]) -> SevenQState:
    state.ps_score = compute_ps_score(state.claim_text, state.evidence_items)
    state.ed_score = compute_ed_score(state.claim_text, state.evidence_items)
    state.ec_score = compute_ec_score(state.claim_text, state.evidence_items)
    state.cf_score = (0.5 + 0.5 * state.ed_score) * (0.5 + 0.5 * state.ec_score)
    state.e_final = state.ps_score * state.cf_score

    why_threshold = cfg.get("why_penalty_threshold", 0.3)
    if state.ed_score < why_threshold:
        state.e_final *= (0.5 + state.ed_score)
        state.why_penalty_applied = True
        state = state.with_flag("why_penalty")
    return state


def analyze_dependencies(state: SevenQState) -> SevenQState:
    state.dependencies = extract_dependencies((state.claim_text + " " + state.assertion).lower())
    state.assumptions = []
    state.chain_terminus = determine_terminus(state.dependencies, state.assumptions)
    state.fragility = determine_fragility(state.chain_terminus, state.dependencies)
    return state


def analyze_consequences(state: SevenQState) -> SevenQState:
    predictions = extract_predictions(state.claim_text)
    state.confirmed_predictions = [p for p in predictions if "confirmed" in p.lower() or "observed" in p.lower()]
    state.failed_predictions = [p for p in predictions if "fail" in p.lower() or "false" in p.lower()]
    state.untested_predictions = [p for p in predictions if p not in state.confirmed_predictions + state.failed_predictions]
    state.predictions = [
        {"description": p, "status": "confirmed" if p in state.confirmed_predictions else "failed" if p in state.failed_predictions else "untested"}
        for p in predictions
    ]
    state.cross_domain_force = len(state.additional_domains) > 1
    return state


def analyze_falsification(state: SevenQState) -> SevenQState:
    kills = extract_kill_conditions((state.claim_text + " " + state.assertion).lower())
    state.kill_conditions = [{"description": k, "type": detect_death_type(k), "severity": "fatal"} for k in kills]
    if state.kill_conditions and len(state.kill_conditions) >= 3:
        state.branch_status = "alive" if not state.failed_predictions else "problematic"
    elif state.kill_conditions:
        state.branch_status = "untested"
    state.adversarial_tested = "adversarial" in (state.claim_text + " " + state.assertion).lower()
    return state


def analyze_forward(state: SevenQState, cfg: Dict[str, Any]) -> SevenQState:
    state.posture = "investigating"
    state.q_scores["Q0"] = compute_q0_score(state)
    state.q_scores["Q1"] = compute_q1_score(state)
    state.q_scores["Q2"] = compute_q2_score(state)
    state.negation = generate_negation(state.assertion or state.claim_text)
    state.q_scores["Q3"] = compute_q3_score(state)
    state = analyze_evidence(state, cfg)
    state.q_scores["Q4"] = state.e_final
    state = analyze_dependencies(state)
    state.q_scores["Q5"] = compute_q5_score(state)
    state = analyze_consequences(state)
    state.q_scores["Q6"] = compute_q6_score(state)
    state = analyze_falsification(state)
    state.q_scores["Q7"] = compute_q7_score(state)
    return state


def analyze_reverse(state: SevenQState, cfg: Dict[str, Any]) -> SevenQState:
    state.run_mode = QMode.REVERSE
    state = analyze_falsification(state)
    state.q_scores["Q7"] = compute_q7_score(state)
    state = analyze_consequences(state)
    state.q_scores["Q6"] = compute_q6_score(state)
    state = analyze_dependencies(state)
    state.q_scores["Q5"] = compute_q5_score(state)
    state = analyze_evidence(state, cfg)
    state.q_scores["Q4"] = state.e_final
    state.negation = generate_negation(state.assertion or state.claim_text)
    state.q_scores["Q3"] = compute_q3_score(state)
    state.q_scores["Q2"] = compute_q2_score(state)
    state.q_scores["Q1"] = compute_q1_score(state)
    state.q_scores["Q0"] = compute_q0_score(state)
    return state


def analyze_evidence_mode(state: SevenQState, cfg: Dict[str, Any]) -> SevenQState:
    state.run_mode = QMode.EVIDENCE
    state = analyze_evidence(state, cfg)
    state.q_scores["Q4"] = state.e_final
    return state

