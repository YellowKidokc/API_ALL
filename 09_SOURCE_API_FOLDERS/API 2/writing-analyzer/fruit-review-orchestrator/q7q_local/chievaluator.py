"""Chi coherence gradient engine v2.

Deterministic evaluator with:
- ten-channel product structure with positive/negative decomposition
- pressure states
- gradient inference
- Fruit output
- structured JSON-ready payload in SevenQState.chi_result
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .core import SevenQState


CHI_CHANNELS = ["G", "M", "E", "S_eff", "T", "K", "R", "Q", "F", "C"]

CHANNEL_LABELS = {
    "G": "External input / dependency honesty",
    "M": "Alignment / reference standard",
    "E": "Truth / signal fidelity",
    "S_eff": "Entropy / disorder cost",
    "T": "Temporal persistence",
    "K": "Compression / wisdom density",
    "R": "Phase transition / justified regime change",
    "Q": "Free will / invitation vs coercion",
    "F": "Cross-context binding",
    "C": "Integration / whole-system coherence",
}

PRESSURE_STATES = [
    "static",
    "compression",
    "strongest_objection",
    "time",
    "translation",
    "evidence",
    "implementation",
    "fruit",
    "falsification",
    "hostile_misuse",
]


@dataclass
class ChiResult:
    channel_results: List[Dict[str, Any]] = field(default_factory=list)
    pressure_results: List[Dict[str, Any]] = field(default_factory=list)
    tau: List[float] = field(default_factory=list)
    channel_traces: Dict[str, List[float]] = field(default_factory=dict)
    chi_trace: List[float] = field(default_factory=list)

    chi_static: float = 0.0
    chi_gradient: float = 0.0
    chi_log_gradient: float = 0.0
    gradient_direction: str = "unstable"
    zero_channels: List[str] = field(default_factory=list)
    weakest_channels: List[str] = field(default_factory=list)
    strongest_channels: List[str] = field(default_factory=list)
    gradient_by_channel: Dict[str, float] = field(default_factory=dict)

    fruit_output: Dict[str, Any] = field(default_factory=dict)
    verdict: str = "repairable"
    final_report: str = ""


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _count_hits(text: str, terms: List[str]) -> int:
    low = text.lower()
    return sum(1 for t in terms if t.lower() in low)


def _effective(v_pos: float, v_neg: float) -> float:
    return _clamp01(v_pos * (1.0 - _clamp01(v_neg)))


def _repair_path(channel: str) -> str:
    plans = {
        "G": "Add explicit external references, datasets, and known counterexamples.",
        "M": "Anchor to a clear external standard instead of self-declared verification.",
        "E": "Separate claims from interpretations; define falsifiable observables.",
        "S_eff": "Resolve contradictions and tighten exception handling.",
        "T": "Show persistence when urgency and recency cues are removed.",
        "K": "Attempt one-sentence compression; preserve meaning under compression.",
        "R": "Justify regime change with explicit failure of the old frame.",
        "Q": "Remove coercive framing; invite audits, objections, and revision.",
        "F": "Test claim in multiple domains and communities.",
        "C": "Integrate missing edge-case constraints and avoid strategic exclusions.",
    }
    return plans.get(channel, "Clarify and strengthen reasoning under pressure.")


def _channel_signature(text: str, state: SevenQState) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, List[str]], Dict[str, str], Dict[str, str], Dict[str, float]]:
    combined = f"{state.claim_text}\n{state.assertion}\n{state.paper_title}".lower()
    words = combined.split()
    wlen = max(len(words), 1)
    pos = {name: 0.0 for name in CHI_CHANNELS}
    neg = {name: 0.0 for name in CHI_CHANNELS}
    reasons: Dict[str, List[str]] = {name: [] for name in CHI_CHANNELS}
    evidence: Dict[str, str] = {name: "" for name in CHI_CHANNELS}
    failure: Dict[str, str] = {name: "" for name in CHI_CHANNELS}
    confidence: Dict[str, float] = {name: 0.0 for name in CHI_CHANNELS}

    # G
    g_pos_terms = ["source", "evidence", "study", "data", "measurement", "experiment", "reference", "counterevidence", "citation"]
    g_neg_terms = ["self-evident", "by definition", "because it is what it is", "axiomatically", "it is true"]
    g_pos = _count_hits(combined, g_pos_terms)
    g_neg = _count_hits(combined, g_neg_terms)
    pos["G"] += min(0.70, 0.10 + 0.04 * g_pos)
    neg["G"] += min(0.70, 0.05 * g_neg)
    reasons["G"].append("credits/penalizes dependence openness")
    if g_pos: evidence["G"] = ", ".join([t for t in g_pos_terms if t in combined][:3])
    if g_neg: failure["G"] = "self-sealing"
    confidence["G"] = _clamp01(0.55 + 0.045 * min(4, g_pos))

    # M
    m_pos_terms = ["definition", "standard", "criterion", "replicates", "compatible", "coheres", "equivalent", "corresponds"]
    m_neg_terms = ["only true if", "cannot be checked", "no one can challenge", "everyone agrees"]
    m_pos = _count_hits(combined, m_pos_terms)
    m_neg = _count_hits(combined, m_neg_terms)
    pos["M"] += min(0.70, 0.12 + 0.04 * m_pos)
    neg["M"] += min(0.70, 0.05 * m_neg)
    reasons["M"].append("external alignment against internal circularity")
    if m_neg: failure["M"] = "circular validation"
    confidence["M"] = _clamp01(0.55 + 0.045 * min(4, m_pos))

    # E
    e_pos_terms = ["if", "then", "therefore", "observable", "falsifiable", "testable", "criterion", "example", "measured"]
    e_neg_terms = ["cannot be falsified", "ambiguous", "you'll see", "it is obvious", "proof without"]
    e_pos = _count_hits(combined, e_pos_terms)
    e_neg = _count_hits(combined, e_neg_terms)
    pos["E"] += min(0.70, 0.12 + 0.035 * e_pos)
    neg["E"] += min(0.70, 0.06 * e_neg)
    reasons["E"].append("signal clarity and anti-ambiguity checks")
    if e_neg: failure["E"] = "unfalsifiable"
    confidence["E"] = _clamp01(0.55 + 0.045 * min(5, e_pos))

    # S_eff
    contradiction_hits = _count_hits(combined, ["contradiction", "inconsistent", "cannot both", "both true and", "false and true"])
    pos["S_eff"] += min(0.70, 0.20 + 0.025 * max(0, 7 - contradiction_hits))
    neg["S_eff"] += min(0.70, 0.06 * contradiction_hits)
    reasons["S_eff"].append("tracks contradiction density and ordering pressure")
    if contradiction_hits: failure["S_eff"] = "contradiction"
    confidence["S_eff"] = _clamp01(0.55 + 0.05 * min(4, max(1, 7 - contradiction_hits)))

    # T
    urgency_hits = _count_hits(combined, ["urgent", "immediately", "right now", "crisis", "panic", "fear"])
    t_pos = _count_hits(combined, ["over time", "historically", "repeatable", "when repeated", "durable"])
    pos["T"] += min(0.70, 0.15 + 0.03 * t_pos)
    neg["T"] += min(0.70, 0.06 * (urgency_hits + (urgency_hits / max(1, wlen / 60))))
    reasons["T"].append("checks dependence on urgency/recency")
    if urgency_hits > 2: failure["T"] = "time dependence"
    confidence["T"] = _clamp01(0.55 + 0.04 * min(5, t_pos))

    # K
    jargon = _count_hits(combined, ["qed", "∴", "∈", "∂", "⟹", "homeomorphism", "axiomatic", "functor"])
    jargon += 0.5 * len(re.findall(r"\b\w+ism\b", combined))
    pos["K"] += min(0.70, 0.12 + (0.05 if len(" ".join(words[:20])) <= 220 else 0.0))
    neg["K"] += min(0.70, 0.03 * (jargon / max(1, wlen / 100)))
    reasons["K"].append("compressibility with low explanatory loss")
    if jargon > 3: failure["K"] = "obfuscation"
    confidence["K"] = _clamp01(0.55 + 0.04 * min(5, max(1, 12 - jargon)))

    # R
    r_pos = _count_hits(combined, ["old model", "fails", "insufficient", "regime change", "boundary", "transition", "new framework"])
    r_neg = _count_hits(combined, ["throw away all", "old ways are evil", "must abandon", "new truth"])
    pos["R"] += min(0.70, 0.12 + 0.03 * r_pos)
    neg["R"] += min(0.70, 0.05 * r_neg)
    reasons["R"].append("justified transition vs abrupt rupture")
    if r_neg: failure["R"] = "unjustified regime change"
    confidence["R"] = _clamp01(0.55 + 0.04 * min(5, r_pos))

    # Q
    q_pos = _count_hits(combined, ["question", "challenge", "inspect", "reproduce", "critic", "objection", "auditable", "test", "disagree"])
    q_neg = _count_hits(combined, ["must", "must not", "if you don't", "traitor", "evil", "disobedience", "only true believers"])
    pos["Q"] += min(0.70, 0.12 + 0.03 * q_pos)
    neg["Q"] += min(0.70, 0.05 * q_neg)
    reasons["Q"].append("measures invitation to dissent and freedom under pressure")
    if q_neg: failure["Q"] = "coercion"
    confidence["Q"] = _clamp01(0.55 + 0.04 * min(5, q_pos))

    # F
    f_pos = _count_hits(combined, ["anyone", "any domain", "across", "different", "multiple", "culture", "context", "framework"])
    f_neg = _count_hits(combined, ["only for", "our group", "in our tradition", "outside"])
    pos["F"] += min(0.70, 0.12 + 0.03 * f_pos)
    neg["F"] += min(0.70, 0.04 * f_neg)
    reasons["F"].append("cross-context survivability check")
    if f_neg: failure["F"] = "local tribalism"
    confidence["F"] = _clamp01(0.55 + 0.04 * min(5, f_pos))

    # C
    c_pos = _count_hits(combined, ["integrates", "connects", "unifies", "reconciles", "resolves", "bridges", "across"])
    c_neg = _count_hits(combined, ["ignore", "does not apply", "irrelevant", "outside scope", "we do not care"])
    pos["C"] += min(0.70, 0.12 + 0.03 * c_pos)
    neg["C"] += min(0.70, 0.04 * c_neg)
    reasons["C"].append("whole-system consistency vs selective consistency")
    if c_neg: failure["C"] = "compartmentalization"
    confidence["C"] = _clamp01(0.55 + 0.04 * min(5, c_pos))

    # bonus from existing state
    if state.precision in {"mathematical", "precise"}:
        pos["K"] += 0.08
        pos["E"] += 0.05
    if state.cross_domain_force:
        pos["F"] += 0.10
    if state.kill_conditions:
        neg["Q"] += 0.08
        neg["S_eff"] += 0.06

    pos = {k: _clamp01(min(1.0, pos[k])) for k in CHI_CHANNELS}
    neg = {k: _clamp01(min(1.0, neg[k])) for k in CHI_CHANNELS}
    eff = {k: _effective(pos[k], neg[k]) for k in CHI_CHANNELS}

    for k in CHI_CHANNELS:
        if not evidence[k]:
            evidence[k] = combined[:110]
        reasons[k].append(f"v_pos={pos[k]:.3f}, v_neg={neg[k]:.3f}, eff={eff[k]:.3f}")
        confidence[k] = _clamp01(confidence[k])

    return pos, neg, eff, reasons, evidence, failure, confidence


def _pressure_factors(label: str, text: str, has_kill_conditions: bool) -> Tuple[Dict[str, float], Dict[str, float], str]:
    low = text.lower()
    word_count = max(1, len(low.split()))
    pos_factors = {k: 1.0 for k in CHI_CHANNELS}
    neg_factors = {k: 1.0 for k in CHI_CHANNELS}
    note = "pressure applied"

    if label == "compression":
        dense = 1.0 if word_count <= 70 else max(0.35, 1.0 - 0.0025 * (word_count - 70))
        pos_factors["K"] *= dense
        pos_factors["M"] *= 0.92 + 0.06 * min(1.0, 120 / word_count)
        pos_factors["E"] *= max(0.6, dense)
        neg_factors["K"] *= 1.10
        note = "compressed form robustness"

    elif label == "strongest_objection":
        if not any(t in low for t in ["strongest objection", "serious objection", "counterargument", "steelman"]):
            pos_factors["Q"] *= 0.58
            pos_factors["S_eff"] *= 0.75
            pos_factors["E"] *= 0.80
            note = "no objection work present"
        else:
            pos_factors["Q"] *= 1.05
            note = "objection coverage found"

    elif label == "time":
        if any(t in low for t in ["urgent", "immediately", "right now", "today", "panic", "crisis"]):
            pos_factors["T"] *= 0.56
            neg_factors["T"] *= 1.35
            note = "time-dependent wording detected"
        else:
            pos_factors["T"] *= 1.08
            note = "durability terms present"

    elif label == "translation":
        jargon = _count_hits(low, ["∴", "∂", "≈", "⇒", "isomorphic", "axiomatic", "homeomorphism"]) + 0.4 * len(re.findall(r"\[[^\]]+\]", low))
        if jargon > 2:
            pos_factors["E"] *= 0.72
            pos_factors["C"] *= 0.80
            neg_factors["E"] *= 1.25
            note = "high translation friction"
        else:
            note = "translation friction low"
        pos_factors["M"] *= max(0.6, 1.0 - jargon * 0.05)

    elif label == "evidence":
        if any(t in low for t in ["no data", "no source", "unverified", "uncorroborated"]):
            pos_factors["G"] *= 0.72
            pos_factors["E"] *= 0.70
            pos_factors["M"] *= 0.85
            neg_factors["G"] *= 1.2
            neg_factors["E"] *= 1.1
            note = "evidence stress exposed"
        else:
            note = "evidence terms stable"

    elif label == "implementation":
        action_markers = _count_hits(low, ["implement", "build", "deploy", "apply", "run", "simulate", "measure", "observe", "predict"])
        if action_markers < 1:
            pos_factors["C"] *= 0.95
            neg_factors["C"] *= 1.08
            note = "implementation evidence sparse"
        else:
            pos_factors["C"] *= 1.06
            pos_factors["K"] *= 1.02
            note = "implementation pathway present"

    elif label == "fruit":
        if _count_hits(low, ["love", "gentleness", "patience", "kindness", "forgiveness", "self-control"]):
            pos_factors["Q"] *= 1.08
            pos_factors["C"] *= 1.08
            pos_factors["F"] *= 1.06
        if _count_hits(low, ["violent", "addicted", "despair", "hate", "humiliate", "exploit"]):
            pos_factors["Q"] *= 0.82
            pos_factors["S_eff"] *= 0.86
            neg_factors["Q"] *= 1.2
            note = "fruit-risk language present"
        else:
            note = "fruit-friendly language present"

    elif label == "falsification":
        if has_kill_conditions:
            pos_factors["Q"] *= 0.75
            pos_factors["C"] *= 0.90
            neg_factors["Q"] *= 1.2
            note = "existing kill conditions weaken coherence"
        else:
            pos_factors["Q"] *= 0.90
            note = "no explicit kill conditions in text"

    elif label == "hostile_misuse":
        if _count_hits(low, ["weapon", "weaponize", "attack", "denounce", "shame", "guilt", "coerce", "fear"]):
            pos_factors["Q"] *= 0.60
            pos_factors["F"] *= 0.85
            pos_factors["S_eff"] *= 0.90
            pos_factors["T"] *= 0.85
            neg_factors["Q"] *= 1.3
            note = "coercion/misuse patterns detected"
        else:
            note = "low hostile misuse risk"

    return pos_factors, neg_factors, note


def _product(values: List[float]) -> float:
    out = 1.0
    for v in values:
        out *= _clamp01(v)
    return out


def _slope(x: List[float], y: List[float]) -> float:
    n = min(len(x), len(y))
    if n < 2:
        return 0.0
    xbar = sum(x[:n]) / n
    ybar = sum(y[:n]) / n
    denom = sum((xi - xbar) ** 2 for xi in x[:n])
    if denom == 0:
        return 0.0
    num = sum((x[i] - xbar) * (y[i] - ybar) for i in range(n))
    return num / denom


def _infer_gradient(direction_series: List[float], static_chi: float, final_chi: float) -> Tuple[str, float, float]:
    if len(direction_series) >= 3:
        logs = [math.log(max(1e-12, c + 1e-12)) for c in direction_series]
        slope = _slope(list(range(len(logs))), logs)
        if slope > 0.04:
            return "positive", slope, slope
        if slope < -0.04:
            return "negative", slope, slope
        if abs(slope) <= 0.001:
            return "unstable", slope, slope
        return "neutral", slope, slope
    diff = final_chi - static_chi
    if diff > 0.02:
        return "positive", diff, 0.0
    if diff < -0.02:
        return "negative", diff, 0.0
    return "neutral", diff, 0.0


def _fruit_vector(text: str) -> Dict[str, float]:
    low = text.lower()
    anti_penalty_weight = 1.35
    positives = {
        "Love": ["love", "benevolent", "kind", "gracious", "compassion"],
        "Joy": ["joy", "delight", "thankful", "hopeful", "celebrate"],
        "Peace": ["peace", "calm", "reconcile", "restful", "serene"],
        "Patience": ["patience", "patient", "thorough", "careful", "steady"],
        "Kindness": ["kind", "kindness", "gentle", "compassion", "merciful"],
        "Goodness": ["good", "help", "constructive", "beneficial", "uplifting"],
        "Faithfulness": ["faithful", "consistent", "reliable", "dependable"],
        "Gentleness": ["gentle", "merciful", "restraint", "soft", "humble"],
        "SelfControl": ["self-control", "self control", "temperance", "discipline", "restraint"],
    }
    negatives = {
        "Love": ["hatred", "violent", "cruel", "abuse"],
        "Joy": ["despair", "anxiety", "grief", "hopeless"],
        "Peace": ["fear", "chaos", "conflict", "violence"],
        "Patience": ["impatient", "impulsive", "rash", "hasty"],
        "Kindness": ["harsh", "abusive", "exploit", "neglect"],
        "Goodness": ["corrupt", "harm", "abuse", "deceit"],
        "Faithfulness": ["betray", "unreliable", "inconsistent", "deceive"],
        "Gentleness": ["harsh", "cruel", "abusive", "humiliate"],
        "SelfControl": ["addict", "compulsive", "obsessive", "reckless"],
    }

    out: Dict[str, float] = {}
    for k, p in positives.items():
        p_hits = _count_hits(low, p)
        n_hits = _count_hits(low, negatives[k]) if k in negatives else 0
        out[k] = _clamp01((p_hits - anti_penalty_weight * n_hits) / 8 + 0.5)
    return out


def _dominant_fruits(fruit_vec: Dict[str, float]) -> Tuple[List[str], List[str], float, str]:
    anti_map = {
        "Love": "Hatred",
        "Joy": "Despair",
        "Peace": "Anxiety",
        "Patience": "Impatience",
        "Kindness": "Cruelty",
        "Goodness": "Corruption",
        "Faithfulness": "Betrayal",
        "Gentleness": "Harshness",
        "SelfControl": "Addiction",
    }
    dominant_fruits = [k for k, v in fruit_vec.items() if v >= 0.65]
    dominant_antifruits = [anti_map[k] for k, v in fruit_vec.items() if v <= 0.35]
    return dominant_fruits, dominant_antifruits, 0.5, "anti-Fruit"  # score assigned later


def run_chi_evaluator(state: SevenQState, cfg: Dict[str, Any]) -> SevenQState:
    chi_cfg = cfg.get("chi", {}) or {}
    if not chi_cfg.get("enabled", False):
        return state

    text = state.claim_text or ""
    base_pos, base_neg, base_eff, reasons, evidence, failure_mode, confidence = _channel_signature(text, state)

    steps = max(2, int(chi_cfg.get("steps", 10)))
    selected = PRESSURE_STATES[:steps]
    if len(selected) < 2:
        selected = [PRESSURE_STATES[0], PRESSURE_STATES[1]]

    tau = [i / (len(selected) - 1) for i in range(len(selected))]
    channel_traces = {k: [] for k in CHI_CHANNELS}
    chi_trace: List[float] = []
    pressure_results: List[Dict[str, Any]] = []

    cumulative_pos = {k: 1.0 for k in CHI_CHANNELS}
    cumulative_neg = {k: 1.0 for k in CHI_CHANNELS}

    for idx, p_state in enumerate(selected):
        note = ""
        if p_state != "static":
            p_factors, n_factors, note = _pressure_factors(p_state, text, bool(state.kill_conditions))
            for k in CHI_CHANNELS:
                cumulative_pos[k] = _clamp01(cumulative_pos[k] * p_factors[k])
                cumulative_neg[k] = _clamp01(cumulative_neg[k] * n_factors[k])
                reasons[k].append(f"pressure={p_state} pos_factor={p_factors[k]:.2f} neg_factor={n_factors[k]:.2f}")

        stage = {}
        for k in CHI_CHANNELS:
            pos_stage = _clamp01(base_pos[k] * cumulative_pos[k])
            neg_stage = _clamp01(base_neg[k] * cumulative_neg[k])
            stage[k] = _effective(pos_stage, neg_stage)
            channel_traces[k].append(stage[k])

        chi_val = _product(list(stage.values()))
        if idx == 0 and state.tier in {"NEAR_CANONICAL", "STRONG"}:
            recover = min(1.0, state.t_score * float(chi_cfg.get("recovery_window", 0.25)))
            chi_val = _clamp01(chi_val + recover * 0.05)
        chi_trace.append(chi_val)
        pressure_results.append({"pressure_state": p_state, "chi": round(chi_val, 8), "notes": note or "applied pressure state"})

    chi_static = round(chi_trace[0], 8)
    chi_end = round(chi_trace[-1], 8)
    chi_slope = _slope(tau, chi_trace)
    log_t = [math.log(max(1e-12, x + 1e-12)) for x in chi_trace]
    log_slope = _slope(tau, log_t)
    gradient_label, gradient, raw_log = _infer_gradient(chi_trace, chi_static, chi_end)

    gradient_by_channel = {}
    for k in CHI_CHANNELS:
        values = channel_traces[k]
        slope_k = _slope(tau, values)
        gradient_by_channel[k] = round(slope_k, 6)

    zero_channels = [k for k, v in base_eff.items() if v <= float(chi_cfg.get("zero_cutoff", 0.05))]
    weak = sorted(CHI_CHANNELS, key=lambda c: base_eff[c])[:3]
    strong = sorted(CHI_CHANNELS, key=lambda c: base_eff[c], reverse=True)[:3]

    # channel-level direction from local slope
    channel_results = []
    for ch in CHI_CHANNELS:
        d = values = gradient_by_channel[ch]
        if d > 0.01:
            g = 1
        elif d < -0.01:
            g = -1
        else:
            g = 0
        channel_results.append({
            "channel": ch,
            "name": CHANNEL_LABELS[ch],
            "v_pos": round(base_pos[ch], 6),
            "v_neg": round(base_neg[ch], 6),
            "effective_score": round(base_eff[ch], 6),
            "gradient_direction": g,
            "confidence": round(confidence[ch], 6),
            "reasoning": "; ".join(reasons[ch]),
            "evidence": evidence[ch],
            "failure_mode": failure_mode[ch],
            "repair_path": _repair_path(ch),
        })

    # verdict logic
    verdict = "repairable"
    if zero_channels:
        fatal = {"coercion", "contradiction", "self-sealing", "unfalsifiable", "circular validation"}
        zero_modes = {failure_mode[k].lower().strip() for k in zero_channels if failure_mode.get(k)}
        if zero_modes.intersection(fatal):
            verdict = "collapsed"
        else:
            verdict = "repairable"
    elif _clamp01(base_eff["E"]) > 0.70 and (_clamp01(base_eff["Q"]) < 0.25 or _clamp01(base_eff["K"]) < 0.25 or _clamp01(base_eff["T"]) < 0.25):
        verdict = "high-signal deception"
    elif gradient_label == "positive" and chi_static > 0.50:
        verdict = "coherent"
    elif chi_static > 0.10:
        verdict = "partially coherent"
    elif gradient_label == "negative":
        verdict = "fragile"
    else:
        verdict = "repairable"

    if chi_static >= 0.75 and gradient_label == "negative":
        verdict = "partially coherent"

    fruit_vec = _fruit_vector(text)
    dominant_fruits, anti_fruits, _, _ = _dominant_fruits(fruit_vec)
    beta = float(chi_cfg.get("fruit", {}).get("beta", 0.35))
    chi_c = float(chi_cfg.get("fruit", {}).get("chi_threshold", 0.42))
    fruit_raw = math.tanh(beta * (chi_end - chi_c))
    fruit_score = round((fruit_raw + 1.0) / 2.0, 6)
    fruit_tendency = "Fruit" if fruit_raw >= 0 else "anti-Fruit"

    repair_path: List[str] = []
    if gradient_label == "negative":
        repair_path = [f"deepen channel {c}" for c in weak]
        repair_path.append("add explicit falsification clauses")
        repair_path.append("state correction path under failure")
    elif gradient_label == "positive":
        repair_path = ["preserve and document pressure stability"]
    else:
        repair_path = ["add targeted pressure tests for ambiguous channels"]

    chi_obj = ChiResult(
        channel_results=channel_results,
        pressure_results=pressure_results,
        tau=tau,
        channel_traces=channel_traces,
        chi_trace=[round(x, 8) for x in chi_trace],
        chi_static=chi_static,
        chi_gradient=round(gradient, 6),
        chi_log_gradient=round(raw_log, 6),
        gradient_direction=gradient_label,
        zero_channels=zero_channels,
        weakest_channels=weak,
        strongest_channels=strong,
        gradient_by_channel=gradient_by_channel,
    )

    chi_obj.fruit_output = {
        "dominant_fruits": dominant_fruits,
        "dominant_antifruits": anti_fruits,
        "fruit_score": fruit_score,
        "notes": f"{fruit_tendency}: mean {fruit_score:.3f}",
    }
    chi_obj.verdict = verdict
    chi_obj.final_report = (
        f"Static χ={chi_static:.3f}, end χ={chi_end:.3f}, gradient={gradient_label}. "
        f"Weakest={', '.join(weak)} strongest={', '.join(strong)}."
    )

    state.chi_result = {
        "enabled": True,
        "claim": text[:2000],
        "claim_type": state.claim_type or "mixed",
        "compressed_claim": " ".join((state.claim_text or "").replace("\n", " ").split())[:220],
        "channel_results": chi_obj.channel_results,
        "pressure_results": chi_obj.pressure_results,
        "static_chi": chi_obj.chi_static,
        "gradient": chi_obj.gradient_direction,
        "zero_channels": chi_obj.zero_channels,
        "weakest_channels": chi_obj.weakest_channels,
        "strongest_channels": chi_obj.strongest_channels,
        "fruit_output": chi_obj.fruit_output,
        "verdict": chi_obj.verdict,
        "final_report": chi_obj.final_report,
        "tau": chi_obj.tau,
        "chi_trace": chi_obj.chi_trace,
        "gradient_by_channel": chi_obj.gradient_by_channel,
        "channels_0": base_eff,
    }

    state.chi_static = chi_obj.chi_static
    state.chi_gradient = chi_obj.chi_gradient
    state.chi_log_gradient = chi_obj.chi_log_gradient
    state.chi_gradient_direction = chi_obj.gradient_direction
    state.chi_verdict = chi_obj.verdict
    return state
