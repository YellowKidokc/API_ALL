"""
chi_evaluator/core/equation.py
Master Equation v2 — Product with gradient, statistics, Monte Carlo

χ = G · M · E · S_eff · T · K · R · Q · F · C

Each channel: v_eff = v_pos * (1 - v_neg)

Gradient: d/dτ ln χ = Σ (1/v_i)(dv_i/dτ)

Statistics: Monte Carlo, sensitivity, distributions, deception detection

POF 2828 | 2026-06-18
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Literal, Optional, Callable
from collections import Counter, defaultdict
import json

# ============================================================
# 1. CHANNEL DEFINITIONS
# ============================================================

CHANNEL_NAMES = {
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

CHANNEL_ORDER = ["G", "M", "E", "S_eff", "T", "K", "R", "Q", "F", "C"]

FAILURE_MODES = [
    "self_sealing",          # G failure
    "circular",              # M failure
    "unfalsifiable",         # E failure
    "contradictory",         # S_eff failure
    "urgency_dependent",     # T failure
    "compression_loss",      # K failure
    "unjustified_transition",# R failure
    "coercive",              # Q failure
    "tribal",                # F failure
    "compartmentalized",     # C failure
]

# ============================================================
# 2. CORE DATACLASSES
# ============================================================

@dataclass
class ChannelScore:
    """Score for one channel with positive/negative decomposition."""
    channel: str
    v_pos: float
    v_neg: float
    confidence: float
    gradient_direction: int  # -1, 0, +1
    reasoning: str = ""
    evidence: str = ""
    failure_mode: str = ""

    @property
    def effective(self) -> float:
        """v_eff = v_pos * (1 - v_neg)"""
        return max(0.0, min(1.0, self.v_pos * (1.0 - self.v_neg)))

    @property
    def is_zero(self) -> bool:
        return self.effective < 0.000001

    @property
    def is_weak(self) -> bool:
        return 0.000001 <= self.effective < 0.25

    @property
    def is_strong(self) -> bool:
        return self.effective >= 0.75

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "name": CHANNEL_NAMES.get(self.channel, self.channel),
            "v_pos": round(self.v_pos, 6),
            "v_neg": round(self.v_neg, 6),
            "effective": round(self.effective, 6),
            "confidence": round(self.confidence, 6),
            "gradient_direction": self.gradient_direction,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "failure_mode": self.failure_mode,
        }


@dataclass
class PressureState:
    """Score under a specific pressure state."""
    name: str  # static, compression, objection, time, translation, evidence, implementation, fruit, falsification, misuse
    channel_scores: list[ChannelScore]
    notes: str = ""

    @property
    def chi(self) -> float:
        """Product of all effective scores."""
        result = 1.0
        for cs in self.channel_scores:
            result *= cs.effective
        return result

    @property
    def log_chi(self) -> float:
        return math.log(max(self.chi, 1e-12))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "chi": round(self.chi, 8),
            "log_chi": round(self.log_chi, 6),
            "notes": self.notes,
            "channels": [cs.to_dict() for cs in self.channel_scores],
        }


@dataclass
class FruitOutput:
    """Fruit/anti-Fruit mapping via tanh phase transition."""
    fruit_scores: dict[str, float] = field(default_factory=dict)
    anti_fruit_scores: dict[str, float] = field(default_factory=dict)
    dominant_fruits: list[str] = field(default_factory=list)
    dominant_antifruits: list[str] = field(default_factory=list)
    fruit_score: float = 0.5
    beta: float = 4.0
    chi_c: float = 0.30

    def compute(self, chi: float) -> FruitOutput:
        """Compute fruit output from chi using tanh transition."""
        raw = math.tanh(self.beta * (chi - self.chi_c))
        self.fruit_score = round((raw + 1.0) / 2.0, 6)
        return self

    def to_dict(self) -> dict:
        return {
            "fruit_score": self.fruit_score,
            "dominant_fruits": self.dominant_fruits,
            "dominant_antifruits": self.dominant_antifruits,
            "beta": self.beta,
            "chi_c": self.chi_c,
            "fruit_scores": {k: round(v, 4) for k, v in self.fruit_scores.items()},
            "anti_fruit_scores": {k: round(v, 4) for k, v in self.anti_fruit_scores.items()},
        }


@dataclass
class ChiEvaluation:
    """Complete evaluation of a claim."""
    claim: str
    claim_type: str  # analytic, empirical, moral, theological, speculative, narrative, policy, mixed
    compressed_claim: str
    pressure_states: list[PressureState] = field(default_factory=list)
    fruit_output: FruitOutput = field(default_factory=FruitOutput)
    final_report: str = ""

    @property
    def static_chi(self) -> float:
        """χ at the static (first) pressure state."""
        return self.pressure_states[0].chi if self.pressure_states else 0.0

    @property
    def gradient(self) -> float:
        """Log-gradient across pressure states."""
        if len(self.pressure_states) < 2:
            return 0.0
        xs = list(range(len(self.pressure_states)))
        ys = [ps.log_chi for ps in self.pressure_states]
        return simple_slope(xs, ys)

    @property
    def gradient_label(self) -> Literal["positive", "neutral", "negative", "unstable"]:
        if any(ps.chi < 0.01 and i > 0 for i, ps in enumerate(self.pressure_states)):
            return "unstable"
        g = self.gradient
        if g > 0.05:
            return "positive"
        if g < -0.05:
            return "negative"
        return "neutral"

    @property
    def zero_channels(self) -> list[str]:
        """Channels that are zero at static state."""
        if not self.pressure_states:
            return []
        return [cs.channel for cs in self.pressure_states[0].channel_scores if cs.is_zero]

    @property
    def weakest_channels(self) -> list[str]:
        """Bottom 3 channels at static state."""
        if not self.pressure_states:
            return []
        sorted_scores = sorted(self.pressure_states[0].channel_scores, key=lambda cs: cs.effective)
        return [cs.channel for cs in sorted_scores[:3]]

    @property
    def strongest_channels(self) -> list[str]:
        """Top 3 channels at static state."""
        if not self.pressure_states:
            return []
        sorted_scores = sorted(self.pressure_states[0].channel_scores, key=lambda cs: cs.effective, reverse=True)
        return [cs.channel for cs in sorted_scores[:3]]

    @property
    def verdict(self) -> Literal["coherent", "partially coherent", "fragile", "high-signal deception", "collapsed", "repairable"]:
        if self.zero_channels:
            # Check if zero is fatal or repairable
            fatal_modes = {"coercive", "self_sealing", "unfalsifiable", "circular", "contradictory"}
            zero_scores = [cs for cs in self.pressure_states[0].channel_scores if cs.is_zero]
            modes = {cs.failure_mode for cs in zero_scores}
            if modes & fatal_modes:
                return "collapsed"
            return "repairable"

        # Check for deception signature: strong E but weak Q, K, or T
        channels_by_id = {cs.channel: cs for cs in self.pressure_states[0].channel_scores}
        if (channels_by_id.get("E", ChannelScore("E",0,0,0,0)).effective > 0.70 and
            (channels_by_id.get("Q", ChannelScore("Q",0,0,0,0)).effective < 0.25 or
             channels_by_id.get("K", ChannelScore("K",0,0,0,0)).effective < 0.25 or
             channels_by_id.get("T", ChannelScore("T",0,0,0,0)).effective < 0.25)):
            return "high-signal deception"

        chi = self.static_chi
        gradient = self.gradient_label
        if chi > 0.50 and gradient in {"positive", "neutral"}:
            return "coherent"
        if 0.10 <= chi <= 0.50:
            return "partially coherent"
        if 0.01 <= chi < 0.10:
            return "fragile"
        return "collapsed" if gradient == "negative" else "repairable"

    def to_dict(self) -> dict:
        return {
            "claim": self.claim,
            "claim_type": self.claim_type,
            "compressed_claim": self.compressed_claim,
            "static_chi": round(self.static_chi, 8),
            "gradient": round(self.gradient, 6),
            "gradient_label": self.gradient_label,
            "verdict": self.verdict,
            "zero_channels": self.zero_channels,
            "weakest_channels": self.weakest_channels,
            "strongest_channels": self.strongest_channels,
            "pressure_states": [ps.to_dict() for ps in self.pressure_states],
            "fruit_output": self.fruit_output.to_dict(),
            "final_report": self.final_report,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ============================================================
# 3. STATISTICS ENGINE
# ============================================================

@dataclass
class ChiStatistics:
    """Overwhelming statistics from a set of evaluations."""
    evaluations: list[ChiEvaluation]

    # Per-channel
    channel_stats: dict[str, dict] = field(default_factory=dict)
    channel_correlation: dict[str, dict] = field(default_factory=dict)

    # Global
    chi_distribution: list[float] = field(default_factory=list)
    gradient_distribution: list[float] = field(default_factory=list)

    # Monte Carlo
    monte_carlo_results: list[dict] = field(default_factory=list)
    monte_carlo_ci: tuple[float, float] = (0.0, 0.0)

    # Fruit
    fruit_distribution: list[float] = field(default_factory=list)
    fruit_correlation: float = 0.0

    # Deception
    deception_count: int = 0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0

    # Pressure
    pressure_sensitivity: dict[str, float] = field(default_factory=dict)

    def compute(self) -> ChiStatistics:
        """Compute all statistics from evaluations."""
        if not self.evaluations:
            return self

        # --- Channel Statistics ---
        channel_scores: dict[str, list[float]] = {ch: [] for ch in CHANNEL_ORDER}
        for ev in self.evaluations:
            if not ev.pressure_states:
                continue
            for cs in ev.pressure_states[0].channel_scores:
                channel_scores[cs.channel].append(cs.effective)

        self.channel_stats = {}
        for ch, scores in channel_scores.items():
            if scores:
                self.channel_stats[ch] = {
                    "mean": round(statistics.mean(scores), 4),
                    "median": round(statistics.median(scores), 4),
                    "std": round(statistics.stdev(scores) if len(scores) > 1 else 0, 4),
                    "min": round(min(scores), 4),
                    "max": round(max(scores), 4),
                    "count": len(scores),
                    "zero_count": sum(1 for s in scores if s < 0.000001),
                    "weak_count": sum(1 for s in scores if 0.000001 <= s < 0.25),
                    "strong_count": sum(1 for s in scores if s >= 0.75),
                }

        # --- Channel Correlation ---
        self.channel_correlation = {}
        for ch1 in CHANNEL_ORDER:
            self.channel_correlation[ch1] = {}
            for ch2 in CHANNEL_ORDER:
                if ch1 == ch2:
                    self.channel_correlation[ch1][ch2] = 1.0
                    continue
                scores1 = channel_scores.get(ch1, [])
                scores2 = channel_scores.get(ch2, [])
                if len(scores1) >= 2 and len(scores2) >= 2:
                    try:
                        corr = statistics.correlation(scores1, scores2)
                        self.channel_correlation[ch1][ch2] = round(corr, 4)
                    except statistics.StatisticsError:
                        self.channel_correlation[ch1][ch2] = 0.0
                else:
                    self.channel_correlation[ch1][ch2] = 0.0

        # --- Global Distributions ---
        self.chi_distribution = [ev.static_chi for ev in self.evaluations]
        self.gradient_distribution = [ev.gradient for ev in self.evaluations]

        # --- Fruit Statistics ---
        self.fruit_distribution = [ev.fruit_output.fruit_score for ev in self.evaluations]
        if self.chi_distribution and self.fruit_distribution:
            try:
                self.fruit_correlation = statistics.correlation(self.chi_distribution, self.fruit_distribution)
            except statistics.StatisticsError:
                self.fruit_correlation = 0.0

        # --- Deception Detection ---
        self.deception_count = sum(1 for ev in self.evaluations if ev.verdict == "high-signal deception")
        # For false positive rate: count claims that are "coherent" but have negative gradient
        coherent_with_negative = sum(1 for ev in self.evaluations if ev.verdict == "coherent" and ev.gradient_label == "negative")
        coherent_count = sum(1 for ev in self.evaluations if ev.verdict == "coherent")
        self.false_positive_rate = coherent_with_negative / max(1, coherent_count)
        # For false negative rate: count "collapsed" claims that have positive gradient
        collapsed_with_positive = sum(1 for ev in self.evaluations if ev.verdict == "collapsed" and ev.gradient_label == "positive")
        collapsed_count = sum(1 for ev in self.evaluations if ev.verdict == "collapsed")
        self.false_negative_rate = collapsed_with_positive / max(1, collapsed_count)

        # --- Pressure Sensitivity ---
        self.pressure_sensitivity = {}
        if self.evaluations and len(self.evaluations[0].pressure_states) >= 2:
            for ev in self.evaluations:
                for i, ps in enumerate(ev.pressure_states[1:], 1):
                    state_name = ps.name
                    delta = ps.chi - ev.pressure_states[0].chi
                    if state_name not in self.pressure_sensitivity:
                        self.pressure_sensitivity[state_name] = []
                    self.pressure_sensitivity[state_name].append(delta)
            for state, deltas in self.pressure_sensitivity.items():
                self.pressure_sensitivity[state] = {
                    "mean_delta": round(statistics.mean(deltas), 6),
                    "median_delta": round(statistics.median(deltas), 6),
                    "std_delta": round(statistics.stdev(deltas) if len(deltas) > 1 else 0, 6),
                    "kill_count": sum(1 for d in deltas if d < -0.1),
                    "improve_count": sum(1 for d in deltas if d > 0.1),
                }

        return self

    # --- Monte Carlo ---

    def monte_carlo(
        self,
        n_samples: int = 10000,
        noise_std: float = 0.05,
        seed: Optional[int] = None,
    ) -> ChiStatistics:
        """
        Run Monte Carlo simulation: randomize channel scores and recompute χ.
        This gives confidence intervals and probability distributions.
        """
        if seed is not None:
            random.seed(seed)

        results = []
        for _ in range(n_samples):
            # Pick a random evaluation as base
            base_ev = random.choice(self.evaluations)
            if not base_ev.pressure_states:
                continue

            base_scores = base_ev.pressure_states[0].channel_scores

            # Add noise to each channel
            noisy_scores = []
            for cs in base_scores:
                v_pos_noisy = max(0.0, min(1.0, cs.v_pos + random.gauss(0, noise_std)))
                v_neg_noisy = max(0.0, min(1.0, cs.v_neg + random.gauss(0, noise_std)))
                noisy_scores.append(ChannelScore(
                    channel=cs.channel,
                    v_pos=v_pos_noisy,
                    v_neg=v_neg_noisy,
                    confidence=cs.confidence,
                    gradient_direction=cs.gradient_direction,
                    reasoning=cs.reasoning,
                    evidence=cs.evidence,
                    failure_mode=cs.failure_mode,
                ))

            # Compute chi
            chi = 1.0
            for cs in noisy_scores:
                chi *= cs.effective

            results.append({
                "chi": chi,
                "zero_count": sum(1 for cs in noisy_scores if cs.is_zero),
                "weak_count": sum(1 for cs in noisy_scores if cs.is_weak),
                "strong_count": sum(1 for cs in noisy_scores if cs.is_strong),
            })

        self.monte_carlo_results = results

        if results:
            chis = [r["chi"] for r in results]
            sorted_chis = sorted(chis)
            self.monte_carlo_ci = (
                round(sorted_chis[int(0.025 * len(sorted_chis))], 6),
                round(sorted_chis[int(0.975 * len(sorted_chis))], 6),
            )

        return self

    def to_dict(self) -> dict:
        return {
            "channel_stats": self.channel_stats,
            "channel_correlation": self.channel_correlation,
            "chi_distribution": {
                "mean": round(statistics.mean(self.chi_distribution), 4) if self.chi_distribution else 0,
                "median": round(statistics.median(self.chi_distribution), 4) if self.chi_distribution else 0,
                "std": round(statistics.stdev(self.chi_distribution), 4) if len(self.chi_distribution) > 1 else 0,
                "min": round(min(self.chi_distribution), 4) if self.chi_distribution else 0,
                "max": round(max(self.chi_distribution), 4) if self.chi_distribution else 0,
                "count": len(self.chi_distribution),
                "buckets": dict(Counter([round(c, 2) for c in self.chi_distribution])),
            },
            "gradient_distribution": {
                "positive": sum(1 for g in self.gradient_distribution if g > 0.05),
                "neutral": sum(1 for g in self.gradient_distribution if -0.05 <= g <= 0.05),
                "negative": sum(1 for g in self.gradient_distribution if g < -0.05),
                "unstable": sum(1 for ev in self.evaluations if ev.gradient_label == "unstable"),
            },
            "fruit_distribution": {
                "mean": round(statistics.mean(self.fruit_distribution), 4) if self.fruit_distribution else 0,
                "median": round(statistics.median(self.fruit_distribution), 4) if self.fruit_distribution else 0,
                "std": round(statistics.stdev(self.fruit_distribution), 4) if len(self.fruit_distribution) > 1 else 0,
            },
            "fruit_correlation": round(self.fruit_correlation, 4),
            "deception": {
                "count": self.deception_count,
                "false_positive_rate": round(self.false_positive_rate, 4),
                "false_negative_rate": round(self.false_negative_rate, 4),
            },
            "pressure_sensitivity": self.pressure_sensitivity,
            "monte_carlo": {
                "samples": len(self.monte_carlo_results),
                "confidence_interval_95": self.monte_carlo_ci,
                "mean_chi": round(statistics.mean([r["chi"] for r in self.monte_carlo_results]), 6) if self.monte_carlo_results else 0,
                "median_chi": round(statistics.median([r["chi"] for r in self.monte_carlo_results]), 6) if self.monte_carlo_results else 0,
                "prob_chi_gt_05": round(sum(1 for r in self.monte_carlo_results if r["chi"] > 0.5) / max(1, len(self.monte_carlo_results)), 4),
                "prob_zero_channel": round(sum(1 for r in self.monte_carlo_results if r["zero_count"] > 0) / max(1, len(self.monte_carlo_results)), 4),
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ============================================================
# 4. HELPERS
# ============================================================

def simple_slope(xs: list[float], ys: list[float]) -> float:
    """Compute slope of linear regression."""
    if len(xs) < 2:
        return 0.0
    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom


def build_channel_score(
    channel: str,
    v_pos: float = 0.5,
    v_neg: float = 0.0,
    confidence: float = 0.5,
    gradient_direction: int = 0,
    reasoning: str = "",
    evidence: str = "",
    failure_mode: str = "",
) -> ChannelScore:
    """Factory for ChannelScore with clamping."""
    return ChannelScore(
        channel=channel,
        v_pos=max(0.0, min(1.0, v_pos)),
        v_neg=max(0.0, min(1.0, v_neg)),
        confidence=max(0.0, min(1.0, confidence)),
        gradient_direction=max(-1, min(1, gradient_direction)),
        reasoning=reasoning,
        evidence=evidence,
        failure_mode=failure_mode,
    )


def pressure_states_from_dict(data: dict) -> list[PressureState]:
    """Build PressureState list from dictionary."""
    states = []
    for key, scores in data.items():
        channel_scores = []
        for ch, vals in scores.items():
            if ch in CHANNEL_ORDER:
                channel_scores.append(ChannelScore(
                    channel=ch,
                    v_pos=vals.get("v_pos", 0.5),
                    v_neg=vals.get("v_neg", 0.0),
                    confidence=vals.get("confidence", 0.5),
                    gradient_direction=vals.get("gradient_direction", 0),
                    reasoning=vals.get("reasoning", ""),
                    evidence=vals.get("evidence", ""),
                    failure_mode=vals.get("failure_mode", ""),
                ))
        states.append(PressureState(name=key, channel_scores=channel_scores, notes=data.get("notes", "")))
    return states


# ============================================================
# 5. DEMO
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("χ-Evaluator v2 — Master Equation Python Engine")
    print("=" * 70)

    # Sample claim
    claim = "Truth does not require falsehood, but falsehood requires truth."

    # Build channel scores for static state
    static_scores = [
        build_channel_score("G", v_pos=0.80, v_neg=0.05, confidence=0.80, gradient_direction=1,
                           reasoning="Acknowledges dependency asymmetry"),
        build_channel_score("M", v_pos=0.90, v_neg=0.05, confidence=0.85, gradient_direction=1,
                           reasoning="Aligns with logical priority"),
        build_channel_score("E", v_pos=0.95, v_neg=0.02, confidence=0.90, gradient_direction=1,
                           reasoning="Clear and compressible signal"),
        build_channel_score("S_eff", v_pos=0.90, v_neg=0.03, confidence=0.85, gradient_direction=1,
                           reasoning="Reduces disorder"),
        build_channel_score("T", v_pos=0.88, v_neg=0.04, confidence=0.80, gradient_direction=1,
                           reasoning="Not urgency-dependent"),
        build_channel_score("K", v_pos=0.96, v_neg=0.02, confidence=0.90, gradient_direction=1,
                           reasoning="Compresses to one sentence"),
        build_channel_score("R", v_pos=0.70, v_neg=0.10, confidence=0.70, gradient_direction=0,
                           reasoning="Reframes without over-force"),
        build_channel_score("Q", v_pos=0.95, v_neg=0.01, confidence=0.90, gradient_direction=1,
                           reasoning="Invites inspection"),
        build_channel_score("F", v_pos=0.85, v_neg=0.05, confidence=0.80, gradient_direction=1,
                           reasoning="Applies across domains"),
        build_channel_score("C", v_pos=0.92, v_neg=0.03, confidence=0.85, gradient_direction=1,
                           reasoning="Integrates with larger framework"),
    ]

    # Pressure states
    pressure_states = [
        PressureState("static", static_scores, "Initial assessment"),
        PressureState("compression", [
            build_channel_score("G", 0.85, 0.03, 0.85, 1, "Improves under compression"),
            build_channel_score("M", 0.92, 0.03, 0.88, 1, "Becomes cleaner"),
            build_channel_score("E", 0.97, 0.01, 0.92, 1, "Signal strengthens"),
            build_channel_score("S_eff", 0.92, 0.02, 0.87, 1, "Disorder further reduced"),
            build_channel_score("T", 0.90, 0.03, 0.82, 1, "Still not urgency-dependent"),
            build_channel_score("K", 0.98, 0.01, 0.92, 1, "Compresses perfectly"),
            build_channel_score("R", 0.75, 0.08, 0.72, 1, "Transition more justified"),
            build_channel_score("Q", 0.97, 0.01, 0.92, 1, "Remains invitational"),
            build_channel_score("F", 0.88, 0.04, 0.82, 1, "Cross-domain holds"),
            build_channel_score("C", 0.94, 0.02, 0.87, 1, "Integration improves"),
        ], "Improves under compression"),
        PressureState("strongest_objection", [
            build_channel_score("G", 0.70, 0.10, 0.75, 0, "Objection weakens dependency"),
            build_channel_score("M", 0.80, 0.10, 0.78, 0, "Alignment challenged"),
            build_channel_score("E", 0.85, 0.08, 0.80, 0, "Signal survives"),
            build_channel_score("S_eff", 0.80, 0.10, 0.75, 0, "Some disorder reintroduced"),
            build_channel_score("T", 0.85, 0.06, 0.78, 0, "Still stable"),
            build_channel_score("K", 0.92, 0.04, 0.85, 1, "Compression survives"),
            build_channel_score("R", 0.60, 0.15, 0.65, -1, "Transition challenged"),
            build_channel_score("Q", 0.88, 0.05, 0.82, 0, "Still invitational"),
            build_channel_score("F", 0.75, 0.10, 0.72, 0, "Cross-domain challenged"),
            build_channel_score("C", 0.85, 0.08, 0.78, 0, "Integration holds"),
        ], "Survives strongest objection with minor weakening"),
    ]

    # Fruit output
    fruit = FruitOutput(
        dominant_fruits=["Peace", "Goodness", "Self-Control"],
        dominant_antifruits=[],
        beta=4.0,
        chi_c=0.30,
    )

    # Build evaluation
    ev = ChiEvaluation(
        claim=claim,
        claim_type="analytic",
        compressed_claim=claim,
        pressure_states=pressure_states,
        fruit_output=fruit,
        final_report="The claim is structurally coherent and improves under pressure.",
    )

    # Compute fruit
    ev.fruit_output.compute(ev.static_chi)

    # Print results
    print("\n" + "=" * 70)
    print("EVALUATION RESULT")
    print("=" * 70)
    print(ev.to_json(indent=2))

    # Build statistics from a set of evaluations
    stats = ChiStatistics(evaluations=[ev]).compute()

    print("\n" + "=" * 70)
    print("STATISTICS")
    print("=" * 70)
    print(stats.to_json(indent=2))

    # Monte Carlo
    stats.monte_carlo(n_samples=1000, seed=42)
    print("\n" + "=" * 70)
    print("MONTE CARLO RESULTS")
    print("=" * 70)
    print(json.dumps(stats.monte_carlo_results[:5], indent=2))
    print(f"... {len(stats.monte_carlo_results) - 5} more samples")
    print(f"95% CI: {stats.monte_carlo_ci}")
    print(f"P(χ > 0.5): {stats.monte_carlo_results[0]['prob_chi_gt_05']:.4f}" if stats.monte_carlo_results else "")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)