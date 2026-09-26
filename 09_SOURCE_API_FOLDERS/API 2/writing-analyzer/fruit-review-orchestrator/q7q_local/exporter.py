"""7Q export layer."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .core import EXPORTS_DIR, SYSTEM_NAME, SYSTEM_VERSION, SevenQState


def _safe_claim_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "claim"


def export_json(state: SevenQState, output_path: Optional[Path] = None) -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        claim_tag = _safe_claim_id(state.claim_id)
        output_path = EXPORTS_DIR / f"7Q_{ts}_{claim_tag}.json"

    data = {
        "schema": "seven_questions.v2",
        "system": {"id": "7Q_ENGINE", "name": SYSTEM_NAME, "version": SYSTEM_VERSION},
        "claim": {"id": state.claim_id, "text": state.claim_text, "title": state.paper_title},
        "subclaims": state.subclaims,
        "domain": {
            "primary": state.primary_domain, "additional": state.additional_domains,
            "scale": state.scale, "iso_status": state.iso_status,
        },
        "assertion": {
            "statement": state.assertion or state.claim_text[:500],
            "type": state.claim_type,
            "precision": state.precision,
            "certainty": state.certainty,
            "scope": state.scope,
            "negation": state.negation,
        },
        "evidence": {
            "items": state.evidence_items, "tier": state.evidence_tier, "types": state.evidence_type,
            "replication": state.replication_status, "ps": state.ps_score, "ed": state.ed_score,
            "ec": state.ec_score, "cf": state.cf_score, "e_final": state.e_final, "why_penalty": state.why_penalty_applied
        },
        "dependencies": {
            "items": state.dependencies, "axioms": state.axiom_deps, "assumptions": state.assumptions,
            "terminus": state.chain_terminus, "fragility": state.fragility,
        },
        "consequences": {
            "predictions": state.predictions, "confirmed": state.confirmed_predictions,
            "untested": state.untested_predictions, "failed": state.failed_predictions,
            "cross_domain_force": state.cross_domain_force
        },
        "falsification": {
            "kill_conditions": state.kill_conditions, "branch_status": state.branch_status,
            "cascade_scope": state.cascade_scope, "adversarial_tested": state.adversarial_tested
        },
        "scores": {
            "q0": state.q_scores.get("Q0", 0.0), "q1": state.q_scores.get("Q1", 0.0),
            "q2": state.q_scores.get("Q2", 0.0), "q3": state.q_scores.get("Q3", 0.0),
            "q4": state.q_scores.get("Q4", 0.0), "q5": state.q_scores.get("Q5", 0.0),
            "q6": state.q_scores.get("Q6", 0.0), "q7": state.q_scores.get("Q7", 0.0),
            "t_score": state.t_score, "tier": state.tier, "confidence_class": state.confidence_class,
        },
        "chi": {
            "enabled": bool(state.chi_result),
            "static": state.chi_static,
            "gradient": state.chi_gradient,
            "log_gradient": state.chi_log_gradient,
            "gradient_direction": state.chi_gradient_direction,
            "verdict": state.chi_verdict,
            "claim_type": state.chi_result.get("claim_type", ""),
            "compressed_claim": state.chi_result.get("compressed_claim", ""),
            "zero_channels": state.chi_result.get("zero_channels", []),
            "weakest_channels": state.chi_result.get("weakest_channels", []),
            "strongest_channels": state.chi_result.get("strongest_channels", []),
            "channel_results": state.chi_result.get("channel_results", []),
            "pressure_results": state.chi_result.get("pressure_results", []),
            "fruit_output": state.chi_result.get("fruit_output", {}),
            "trace": {
                "tau": state.chi_result.get("tau", []),
                "chi_trace": state.chi_result.get("chi_trace", []),
            },
        },
        "audit": {"flags": state.flags, "errors": state.errors, "warnings": state.warnings},
        "metadata": {"run_mode": state.run_mode.value if hasattr(state.run_mode, "value") else str(state.run_mode),
                     "timestamp": state.run_timestamp, "source_path": state.paper_path},
    }
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def export_markdown(state: SevenQState, output_path: Optional[Path] = None) -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        claim_tag = _safe_claim_id(state.claim_id)
        output_path = EXPORTS_DIR / f"7Q_{ts}_{claim_tag}.md"

    lines = [
        "# 7Q Analysis Report",
        f"Claim: {state.paper_title or 'Untitled'}",
        "",
        f"T-Score: {state.t_score:.3f} | Tier: {state.tier} | Confidence: {state.confidence_class}",
        f"Run mode: {state.run_mode.value if hasattr(state.run_mode, 'value') else state.run_mode}",
        f"Timestamp: {state.run_timestamp}",
        "",
        "## Scores",
        "| Question | Score |",
        "|---|---|",
    ]
    for q in ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7"]:
        lines.append(f"| {q} | {state.q_scores.get(q, 0.0):.3f} |")
    lines.append(f"| **T-Score** | **{state.t_score:.3f}** |")
    lines += [
        "",
        "## Domain",
        f"- Primary: {state.primary_domain}",
        f"- Additional: {', '.join(state.additional_domains) if state.additional_domains else 'None'}",
        f"- Scale: {state.scale}",
        f"- ISO Status: {state.iso_status}",
        "",
        "## Evidence",
        f"- PS: {state.ps_score:.3f}",
        f"- ED: {state.ed_score:.3f}",
        f"- EC: {state.ec_score:.3f}",
        f"- CF: {state.cf_score:.3f}",
        f"- E_final: {state.e_final:.3f}",
        "",
        "## Kill Conditions",
    ]
    if state.kill_conditions:
        for i, k in enumerate(state.kill_conditions, start=1):
            lines.append(f"{i}. {k.get('description')} ({k.get('type')})")
    else:
        lines.append("- None identified")
    if state.flags:
        lines += ["", "## Flags", *[f"- {f}" for f in state.flags]]

    if state.chi_result:
        fruit_output = state.chi_result.get("fruit_output", {})
        fruit_tendency = fruit_output.get("notes", "")
        fruit_score = fruit_output.get("fruit_score", 0.0)
        chi_gradient = state.chi_gradient
        channel_results = state.chi_result.get("channel_results", [])
        lines += [
            "",
            "## χ-Evaluator",
            f"- Static χ: {state.chi_static:.3f}",
            f"- Gradient: {chi_gradient:.6f}",
            f"- Log-Gradient: {state.chi_log_gradient:.6f}",
            f"- Direction: {state.chi_gradient_direction}",
            f"- Verdict: {state.chi_verdict}",
            f"- Fruit output: {fruit_tendency}",
            f"- Fruit score: {fruit_score:.3f}",
            f"- Compressed claim: {state.chi_result.get('compressed_claim', '')}",
        ]
        if channel_results:
            lines += ["", "### χ channel detail"]
            lines += ["| Channel | v_pos | v_neg | effective | gradient | confidence | failure |", "|---|---|---|---|---|---|---|"]
            for c in channel_results:
                lines.append(
                    "| {c} | {vp:.3f} | {vn:.3f} | {e:.3f} | {gd} | {cf:.2f} | {fm} |".format(
                        c=c.get("channel", ""),
                        vp=float(c.get("v_pos", 0.0)),
                        vn=float(c.get("v_neg", 0.0)),
                        e=float(c.get("effective_score", 0.0)),
                        gd=c.get("gradient_direction", 0),
                        cf=float(c.get("confidence", 0.0)),
                        fm=(c.get("failure_mode", "") or "")
                    )
                )

        weak = state.chi_result.get("weakest_channels", [])
        strong = state.chi_result.get("strongest_channels", [])
        if weak:
            lines.append(f"- Weakest channels: {', '.join(weak)}")
        if strong:
            lines.append(f"- Strongest channels: {', '.join(strong)}")
        zero = state.chi_result.get("zero_channels", [])
        if zero:
            lines.append(f"- Zero channels: {', '.join(zero)}")

        pressure_results = state.chi_result.get("pressure_results", [])
        if pressure_results:
            lines += ["", "### Pressure"]
            for p in pressure_results:
                lines.append(f"- {p.get('pressure_state', '')}: {p.get('chi', 0.0)} ({p.get('notes', '')})")

        fruit_output = state.chi_result.get("fruit_output", {})
        if fruit_output.get("dominant_fruits") or fruit_output.get("dominant_antifruits"):
            lines += ["", "### Fruit"]
            if fruit_output.get("dominant_fruits"):
                lines.append(f"- Dominant fruits: {', '.join(fruit_output.get('dominant_fruits', []))}")
            if fruit_output.get("dominant_antifruits"):
                lines.append(f"- Dominant anti-fruits: {', '.join(fruit_output.get('dominant_antifruits', []))}")

    output_path.write_text("\\n".join(lines), encoding="utf-8")
    return output_path
