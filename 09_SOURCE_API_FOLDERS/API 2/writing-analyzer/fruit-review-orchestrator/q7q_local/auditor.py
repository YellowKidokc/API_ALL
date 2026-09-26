"""7Q audit layer: vulnerability flags and small penalties."""

from __future__ import annotations

from .core import SevenQState


def audit_state(state: SevenQState, cfg) -> SevenQState:
    if state.ed_score < cfg.get("why_penalty_threshold", 0.3):
        state = state.with_flag("why_penalty")

    if state.ec_score < 0.1:
        state = state.with_flag("no_lived")

    if not state.kill_conditions:
        state = state.with_flag("unfalsifiable")

    if not state.axiom_deps and not state.dependencies:
        state = state.with_flag("ungrounded")

    if state.precision == "vague":
        state = state.with_flag("undefined")

    if "select" in (state.claim_text + " " + state.assertion).lower() and "evidence" in state.claim_text.lower():
        state = state.with_flag("select_bias")

    if "only" in (state.claim_text + " " + state.assertion).lower() and (
        "support" in state.claim_text.lower() or "confirm" in state.claim_text.lower()
    ):
        state = state.with_flag("confirm_bias")

    # Small confidence penalty for explicit flags
    penalty_map = {"why_penalty": 0.08, "no_lived": 0.05, "unfalsifiable": 0.10, "ungrounded": 0.08}
    for flag in state.flags:
        state.t_score = max(0.0, state.t_score - penalty_map.get(flag, 0.0))
    return state

