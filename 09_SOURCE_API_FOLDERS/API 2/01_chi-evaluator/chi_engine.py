"""
chi_engine.py
=============
Core math and data structures for the χ-Evaluator v2.
No API dependencies — pure Python math.
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import asdict, dataclass, field
from typing import Literal

CHANNELS: dict[str, str] = {
    "G":     "External input / dependency honesty",
    "M":     "Alignment / reference standard",
    "E":     "Truth / signal fidelity",
    "S_eff": "Entropy / disorder cost",
    "T":     "Temporal persistence",
    "K":     "Compression / wisdom density",
    "R":     "Phase transition / justified regime change",
    "Q":     "Free will / invitation vs coercion",
    "F":     "Cross-context binding",
    "C":     "Integration / whole-system coherence",
}

CHANNEL_ORDER = list(CHANNELS.keys())

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

FRUITS     = ["Love", "Joy", "Peace", "Patience", "Kindness",
               "Goodness", "Faithfulness", "Gentleness", "Self-Control"]
ANTIFRUITS = ["Hatred", "Despair", "Anxiety", "Impatience", "Cruelty",
               "Corruption", "Betrayal", "Harshness", "Addiction"]

FATAL_FAILURE_MODES = {
    "coercion", "contradiction", "self-sealing",
    "unfalsifiable", "circular validation", "circular",
}


def clamp01(x) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v) or math.isinf(v):
        return 0.0
    return max(0.0, min(1.0, v))


def chi_product(scores: list[float]) -> float:
    result = 1.0
    for s in scores:
        result *= clamp01(s)
    return round(result, 8)


def tanh_fruit_score(chi: float, beta: float = 4.0, chi_c: float = 0.30) -> float:
    raw = math.tanh(beta * (chi - chi_c))
    return round((raw + 1.0) / 2.0, 6)


def simple_slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom


@dataclass
class ChannelResult:
    channel: str
    name: str
    v_pos: float
    v_neg: float
    effective_score: float
    gradient_direction: int
    confidence: float
    reasoning: str
    evidence: str = ""
    failure_mode: str = ""
    repair_path: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ChannelResult":
        ch = d.get("channel", "G")
        vp = clamp01(d.get("v_pos", 0.0))
        vn = clamp01(d.get("v_neg", 0.0))
        return cls(
            channel=ch,
            name=CHANNELS.get(ch, ch),
            v_pos=vp,
            v_neg=vn,
            effective_score=round(vp * (1.0 - vn), 6),
            gradient_direction=max(-1, min(1, int(d.get("gradient_direction", 0)))),
            confidence=clamp01(d.get("confidence", 0.5)),
            reasoning=str(d.get("reasoning", "")),
            evidence=str(d.get("evidence", "")),
            failure_mode=str(d.get("failure_mode", "")),
            repair_path=str(d.get("repair_path", "")),
        )


@dataclass
class PressureResult:
    pressure_state: str
    chi: float
    notes: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "PressureResult":
        return cls(
            pressure_state=str(d.get("pressure_state", "")),
            chi=clamp01(d.get("chi", 0.0)),
            notes=str(d.get("notes", "")),
        )


@dataclass
class FruitOutput:
    dominant_fruits: list[str] = field(default_factory=list)
    dominant_antifruits: list[str] = field(default_factory=list)
    fruit_score: float = 0.5
    notes: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "FruitOutput":
        return cls(
            dominant_fruits=list(d.get("dominant_fruits", [])),
            dominant_antifruits=list(d.get("dominant_antifruits", [])),
            fruit_score=clamp01(d.get("fruit_score", 0.5)),
            notes=str(d.get("notes", "")),
        )


@dataclass
class ChiEvaluation:
    claim: str
    claim_type: str
    compressed_claim: str
    channel_results: list[ChannelResult]
    pressure_results: list[PressureResult] = field(default_factory=list)
    fruit_output: FruitOutput = field(default_factory=FruitOutput)
    final_report: str = ""
    static_chi: float = 0.0
    gradient: str = "neutral"
    zero_channels: list[str] = field(default_factory=list)
    weakest_channels: list[str] = field(default_factory=list)
    strongest_channels: list[str] = field(default_factory=list)
    verdict: str = "fragile"

    @property
    def geo_mean(self) -> float:
        """Geometric mean of channel scores — computed via log-sum to avoid underflow."""
        scores = [c.effective_score for c in self.channel_results]
        if not scores:
            return 0.0
        log_sum = sum(math.log(max(s, 1e-10)) for s in scores)
        return round(math.exp(log_sum / len(scores)), 6)

    def compute(self) -> "ChiEvaluation":
        scores = [c.effective_score for c in self.channel_results]
        self.static_chi = chi_product(scores)

        self.zero_channels = [
            c.channel for c in self.channel_results
            if c.effective_score <= 0.000001
        ]

        by_score = sorted(self.channel_results, key=lambda c: c.effective_score)
        self.weakest_channels  = [c.channel for c in by_score[:3]]
        self.strongest_channels = [c.channel for c in by_score[-3:]][::-1]

        self.gradient = self._infer_gradient()
        self.verdict  = self._infer_verdict()

        # Fruit score from geometric mean (more intuitive scale than raw product)
        gm = self.geo_mean
        self.fruit_output.fruit_score = tanh_fruit_score(gm)

        # Auto-populate fruits if model didn't return them
        if not self.fruit_output.dominant_fruits and not self.fruit_output.dominant_antifruits:
            if gm >= 0.60:
                self.fruit_output.dominant_fruits = ["Peace", "Goodness", "Faithfulness"]
            elif gm >= 0.45:
                self.fruit_output.dominant_fruits = ["Patience", "Kindness"]
                self.fruit_output.dominant_antifruits = ["Anxiety"]
            else:
                self.fruit_output.dominant_antifruits = ["Anxiety", "Despair", "Corruption"]

        return self

    def _infer_gradient(self) -> str:
        if self.pressure_results and len(self.pressure_results) >= 3:
            chis = [max(1e-9, p.chi) for p in self.pressure_results]
            logs = [math.log(x) for x in chis]
            slope = simple_slope(list(range(len(logs))), logs)
            if slope > 0.05:
                return "positive"
            if slope < -0.05:
                return "negative"
            return "neutral"

        directions = [c.gradient_direction for c in self.channel_results]
        total = sum(directions)
        if any(c.effective_score < 0.05 and c.gradient_direction < 0
               for c in self.channel_results):
            return "unstable"
        if total >= 3:
            return "positive"
        if total <= -3:
            return "negative"
        return "neutral"

    def _infer_verdict(self) -> str:
        if self.zero_channels:
            modes = {
                c.failure_mode.lower().strip()
                for c in self.channel_results
                if c.channel in self.zero_channels
            }
            if modes & FATAL_FAILURE_MODES:
                return "collapsed"
            return "repairable"

        ch = {c.channel: c for c in self.channel_results}

        # Propaganda signature: high signal, low freedom/compression/time
        if (ch.get("E") and ch["E"].effective_score > 0.70 and (
            (ch.get("Q") and ch["Q"].effective_score < 0.25) or
            (ch.get("K") and ch["K"].effective_score < 0.25) or
            (ch.get("T") and ch["T"].effective_score < 0.25)
        )):
            return "high-signal deception"

        # Verdicts scaled to geometric mean (per-channel average, 0–1)
        gm = self.geo_mean
        if gm >= 0.72 and self.gradient in {"positive", "neutral"}:
            return "coherent"
        if 0.55 <= gm < 0.72:
            return "partially coherent"
        if 0.35 <= gm < 0.55:
            return "fragile"
        return "collapsed" if self.gradient == "negative" else "repairable"

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    def to_markdown(self, model_label: str = "") -> str:
        header = f"# χ-Evaluator Report"
        if model_label:
            header += f" — {model_label}"

        verdict_line = f"**Verdict:** {self.verdict.upper()}"
        chi_line     = (f"**χ product:** {self.static_chi:.6f}   |   "
                        f"**χ geo-mean:** {self.geo_mean:.4f}   |   "
                        f"**Gradient:** {self.gradient}")
        fruit_line   = f"**Fruit score:** {self.fruit_output.fruit_score:.3f}"

        channel_rows = ["| Channel | Score | Gradient | Failure mode |",
                        "|---------|-------|----------|--------------|"]
        for c in self.channel_results:
            arrow = {1: "↑", 0: "→", -1: "↓"}.get(c.gradient_direction, "?")
            channel_rows.append(
                f"| {c.channel} — {c.name} | {c.effective_score:.3f} | {arrow} | {c.failure_mode or '—'} |"
            )

        pressure_rows = ["| Pressure | χ | Notes |", "|----------|---|-------|"]
        for p in self.pressure_results:
            pressure_rows.append(f"| {p.pressure_state} | {p.chi:.4f} | {p.notes} |")

        fruits_line     = f"**Fruits:**     {', '.join(self.fruit_output.dominant_fruits) or 'none'}"
        antifruits_line = f"**Anti-Fruits:** {', '.join(self.fruit_output.dominant_antifruits) or 'none'}"

        sections = [
            header,
            "",
            f"**Claim:** {self.claim}",
            f"**Type:** {self.claim_type}",
            f"**Compressed:** {self.compressed_claim}",
            "",
            verdict_line,
            chi_line,
            fruit_line,
            "",
            "## Channel Scores",
            *channel_rows,
            "",
            f"**Zero channels:** {', '.join(self.zero_channels) or 'none'}",
            f"**Weakest:** {', '.join(self.weakest_channels)}",
            f"**Strongest:** {', '.join(self.strongest_channels)}",
            "",
            "## Pressure Results",
            *pressure_rows,
            "",
            "## Fruit Output",
            fruits_line,
            antifruits_line,
            f"{self.fruit_output.notes}",
            "",
            "## Final Report",
            self.final_report,
        ]
        return "\n".join(sections)


def _normalize_channel_dict(code: str, raw: dict) -> dict:
    """Normalize a single channel dict regardless of which key names the model used."""
    # Support both 'reasoning' and 'rationale' for the text field
    reasoning = (raw.get("reasoning") or raw.get("rationale")
                 or raw.get("explanation") or raw.get("notes") or "")
    return {
        "channel":            code,
        "v_pos":              raw.get("v_pos", 0.5),
        "v_neg":              raw.get("v_neg", 0.1),
        "effective_score":    raw.get("effective_score", 0.0),
        "gradient_direction": raw.get("gradient_direction", 0),
        "confidence":         raw.get("confidence", 0.5),
        "reasoning":          reasoning,
        "evidence":           raw.get("evidence", ""),
        "failure_mode":       raw.get("failure_mode", ""),
        "repair_path":        raw.get("repair_path", ""),
    }


def _extract_channels(d: dict) -> list[dict]:
    """
    Handle all observed JSON shapes from models:
    1. Full list:  {"channel_results": [{"channel": "G", ...}]}
    2. O3 flat:    {"G": {...}, "M": {...}, ...}
    3. DS nested:  {"channels": {"G": {...}}} or {"scores": {"G": {...}}}
    """
    # Shape 1 — preferred
    if "channel_results" in d and isinstance(d["channel_results"], list):
        return d["channel_results"]

    # Shape 3 — named sub-object (any of several key names)
    for key in ("channels", "scores", "channel_scores", "results"):
        if key in d and isinstance(d[key], dict):
            src = d[key]
            found = [_normalize_channel_dict(k, v) for k, v in src.items()
                     if k in CHANNEL_ORDER and isinstance(v, dict)]
            if found:
                return found

    # Shape 2 — flat top-level channel codes
    flat = {k: v for k, v in d.items()
            if k in CHANNEL_ORDER and isinstance(v, dict)}
    if flat:
        return [_normalize_channel_dict(k, flat[k]) for k in CHANNEL_ORDER if k in flat]

    return []


def parse_model_json(raw_json: str) -> "ChiEvaluation | None":
    """Parse model-returned JSON into a ChiEvaluation. Returns None on failure."""
    import re

    try:
        d = json.loads(raw_json)
    except json.JSONDecodeError:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_json, re.DOTALL)
        if m:
            try:
                d = json.loads(m.group(1))
            except json.JSONDecodeError:
                return None
        else:
            return None

    try:
        raw_channels = _extract_channels(d)
        if not raw_channels:
            print(f"    [parse error] no channel data found — keys: {list(d.keys())[:10]}")
            return None

        channels = [ChannelResult.from_dict(c) for c in raw_channels]

        # Pressure results — may be list or dict; handle key variations across models
        raw_pressure = d.get("pressure_results") or d.get("pressure_states") or []
        if isinstance(raw_pressure, dict):
            raw_pressure = [
                {
                    "pressure_state": k,
                    "chi": v.get("chi", v.get("coherence", v.get("score", 0.5))),
                    "notes": v.get("notes", v.get("note", "")),
                }
                for k, v in raw_pressure.items()
                if isinstance(v, dict)
            ]
        pressure = [PressureResult.from_dict(p) for p in raw_pressure]

        # Fruit output
        raw_fruit = d.get("fruit_output") or d.get("fruit") or {}
        fruit = FruitOutput.from_dict(raw_fruit)

        ev = ChiEvaluation(
            claim=str(d.get("claim", "")),
            claim_type=str(d.get("claim_type", "mixed")),
            compressed_claim=str(d.get("compressed_claim", d.get("claim", ""))),
            channel_results=channels,
            pressure_results=pressure,
            fruit_output=fruit,
            final_report=str(d.get("final_report", d.get("summary", d.get("verdict_note", "")))),
        )
        return ev.compute()
    except Exception as e:
        print(f"    [parse error] {e}")
        return None
