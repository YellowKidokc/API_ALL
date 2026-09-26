"""7Q scoring layer."""

from __future__ import annotations

from typing import Dict

from .core import SevenQState

from .analyzer import compute_q0_score as _q0
from .analyzer import compute_q4_score, compute_q5_score, compute_q6_score, compute_q7_score


def compute_scores(state: SevenQState, cfg: Dict) -> SevenQState:
    state.q_scores["Q0"] = state.q_scores.get("Q0", _q0(state))
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7"]:
        state.q_scores.setdefault(q, 0.5)

    qs = [state.q_scores[q] for q in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7"]]
    if qs:
        state.t_score = sum(qs) / len(qs)
    state.tier = determine_tier(state.t_score)
    state.confidence_class = determine_confidence(state.t_score)
    return state


def determine_tier(score: float) -> str:
    if score >= 0.85:
        return "NEAR_CANONICAL"
    if score >= 0.70:
        return "STRONG"
    if score >= 0.55:
        return "PROVISIONAL"
    if score >= 0.40:
        return "WEAK"
    return "INSUFFICIENT"


def determine_confidence(score: float) -> str:
    if score >= 0.85:
        return "ESTABLISHED"
    if score >= 0.65:
        return "WELL_SUPPORTED"
    if score >= 0.40:
        return "TENTATIVE"
    if score >= 0.15:
        return "SPECULATIVE"
    return "UNSUPPORTED"

