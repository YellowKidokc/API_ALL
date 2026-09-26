"""7Q System core primitives.

This is the core layer for the 7Q engine: system constants, shared state object,
and shared utility helpers used across parser/analyzer/scorer/exporter modules.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---- SECTION 01: CONSTANTS ----
SYSTEM_ID = "7Q_ENGINE"
SYSTEM_NAME = "Seven Questions System"
SYSTEM_VERSION = "2.0.0-minimal"
SYSTEM_DESC = "Runnable 7Q core (forward mode baseline)"

HERE = Path(__file__).resolve().parent
INPUT_DIR = HERE / "_inbox"
OUTPUT_DIR = HERE / "_outbox"
PROCESSED_DIR = HERE / "_processed"
LOGS_DIR = HERE / "_logs"
EXPORTS_DIR = HERE / "_exports"

SEVEN_QUESTIONS = [
    {"id": "Q1", "label": "Identity", "question": "What exactly is being claimed?"},
    {"id": "Q2", "label": "Domain", "question": "Where does this claim live?"},
    {"id": "Q3", "label": "Assertion", "question": "What exactly is being asserted?"},
    {"id": "Q4", "label": "Evidence", "question": "What supports this claim?"},
    {"id": "Q5", "label": "Dependencies", "question": "What must already be true?"},
    {"id": "Q6", "label": "Consequences", "question": "If true, what follows?"},
    {"id": "Q7", "label": "Falsification", "question": "How does this die?"},
]

Q0_POSTURE = {"id": "Q0", "label": "Posture", "question": "Am I investigating or advocating?"}

DOMAINS = [
    "physics", "biology", "chemistry", "theology", "philosophy", "consciousness",
    "information_theory", "mathematics", "history", "psychology", "sociology",
    "economics", "ethics", "law", "medicine", "ecology", "computer_science",
    "linguistics", "theophysics", "universal",
]

DEATH_TYPES = [
    "self_refutation", "infinite_regress", "empirical_contradiction",
    "logical_incoherence", "explanatory_failure"
]

ISO_STATUSES = ["ISO_CONFIRMED", "ISO_PARALLEL", "ISO_ANALOGY", "NONE"]


class QMode(str, Enum):
    FORWARD = "forward"
    REVERSE = "reverse"
    EVIDENCE = "evidence"


@dataclass
class SevenQState:
    """State object that flows through all 7Q stages."""

    claim_id: str = ""
    claim_text: str = ""
    paper_title: str = ""
    paper_path: str = ""

    subclaims: List[Dict[str, Any]] = field(default_factory=list)

    primary_domain: str = ""
    additional_domains: List[str] = field(default_factory=list)
    scale: str = ""
    iso_status: str = "NONE"

    assertion: str = ""
    claim_type: str = ""
    precision: str = "vague"
    certainty: str = "unknown"
    scope: str = "domain_specific"
    negation: str = ""

    evidence_items: List[Dict[str, Any]] = field(default_factory=list)
    evidence_tier: str = ""
    evidence_type: List[str] = field(default_factory=list)
    replication_status: str = "unreplicated"
    ps_score: float = 0.0
    ed_score: float = 0.0
    ec_score: float = 0.0
    cf_score: float = 0.0
    e_final: float = 0.0
    why_penalty_applied: bool = False

    dependencies: List[str] = field(default_factory=list)
    axiom_deps: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    chain_terminus: str = ""
    fragility: str = ""

    predictions: List[Dict[str, Any]] = field(default_factory=list)
    confirmed_predictions: List[str] = field(default_factory=list)
    untested_predictions: List[str] = field(default_factory=list)
    failed_predictions: List[str] = field(default_factory=list)
    cross_domain_force: bool = False

    kill_conditions: List[Dict[str, Any]] = field(default_factory=list)
    branch_status: str = "open"
    cascade_scope: str = ""
    adversarial_tested: bool = False

    posture: str = "investigating"
    posture_score: float = 0.0

    q_scores: Dict[str, float] = field(default_factory=dict)
    t_score: float = 0.0
    tier: str = ""
    confidence_class: str = ""

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    run_mode: QMode = QMode.FORWARD
    run_timestamp: str = ""

    # χ-Evaluator (v2): optional coherence-field diagnostics
    chi_result: Dict[str, Any] = field(default_factory=dict)
    chi_static: float = 0.0
    chi_gradient: float = 0.0
    chi_log_gradient: float = 0.0
    chi_gradient_direction: str = ""
    chi_verdict: str = ""

    def with_error(self, msg: str) -> "SevenQState":
        state = replace(self)
        state.errors.append(msg)
        return state

    def with_warning(self, msg: str) -> "SevenQState":
        state = replace(self)
        state.warnings.append(msg)
        return state

    def with_flag(self, flag: str) -> "SevenQState":
        state = replace(self)
        if flag not in state.flags:
            state.flags.append(flag)
        return state


# ---- SECTION 02: CONFIG ----
def load_config(path: Path | None = None) -> Dict[str, Any]:
    """Load configuration from config.yaml or config.json if available."""
    cfg_path = path or (HERE / "config.yaml")
    if cfg_path.exists():
        if cfg_path.suffix.lower() == ".json":
            return json.loads(cfg_path.read_text(encoding="utf-8-sig"))
        # Keep YAML load optional and lightweight.
        try:
            import yaml
        except Exception:
            yaml = None
        if yaml is not None:
            return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    fallback = HERE / "config.json"
    if fallback.exists():
        return json.loads(fallback.read_text(encoding="utf-8-sig"))

    return {
        "system_id": SYSTEM_ID,
        "system_name": SYSTEM_NAME,
        "system_version": SYSTEM_VERSION,
        "max_chars": 12000,
        "input_extensions": [".md", ".txt", ".json", ".yaml", ".html"],
        "default_mode": QMode.FORWARD.value,
        "evidence_tier_weights": {"tier_1": 1.0, "tier_2": 0.6, "tier_3": 0.2},
        "cross_domain_multipliers": {},
        "why_penalty_threshold": 0.30,
        "score_weights": {"S": 1.0, "E": 1.0, "L": 1.0, "D": 1.0, "P": 1.0, "C": 1.0},
        "chi": {
            "enabled": False,
            "steps": 5,
            "zero_cutoff": 0.05,
            "gradient_log": True,
            "recovery_window": 0.25,
            "channels": {
                "G": {"positive_weight": 1.0, "negative_weight": 1.0},
                "M": {"positive_weight": 1.0, "negative_weight": 1.0},
                "E": {"positive_weight": 1.0, "negative_weight": 1.0},
                "S": {"positive_weight": 1.0, "negative_weight": 1.0},
                "T": {"positive_weight": 1.0, "negative_weight": 1.0},
                "K": {"positive_weight": 1.0, "negative_weight": 1.0},
                "R": {"positive_weight": 1.0, "negative_weight": 1.0},
                "Q": {"positive_weight": 1.0, "negative_weight": 1.0},
                "F": {"positive_weight": 1.0, "negative_weight": 1.0},
                "C": {"positive_weight": 1.0, "negative_weight": 1.0},
            },
            "fruit": {
                "beta": 0.35,
                "chi_threshold": 0.42
            }
        },
    }
