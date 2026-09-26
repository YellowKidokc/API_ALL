"""
synthesize_statements.py
========================
After a chi-evaluation run, makes ONE extra DeepSeek call per claim to
synthesize 4 statement formats from the dual-model evaluation data.
Anchored to the Fruits of the Spirit as the primary communicable output.

Returns a dict with keys: one_liner, formal_scientific, theological_narrative,
cross_model_comparison, claim, run_ts
"""

import json
import time
import math

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

FRUITS     = ["Love","Joy","Peace","Patience","Kindness","Goodness",
              "Faithfulness","Gentleness","Self-Control"]
ANTIFRUITS = ["Hatred","Despair","Anxiety","Impatience","Cruelty",
              "Corruption","Betrayal","Harshness","Addiction"]

CHANNEL_FULL = {
    "G":     "External Input",
    "M":     "Alignment",
    "E":     "Signal Fidelity",
    "S_eff": "Entropy Cost",
    "T":     "Temporal",
    "K":     "Compression",
    "R":     "Phase Transition",
    "Q":     "Free Will",
    "F":     "Cross-Context",
    "C":     "Integration",
}

SYNTHESIS_SYSTEM = """\
You are a Fruit-anchored synthesis engine for the χ-Evaluator v2 (Theophysics Master Equation).

THE MASTER EQUATION: χ = G · M · E · S_eff · T · K · R · Q · F · C
This is a PRODUCT — a zero in any channel collapses coherence entirely.

THE FRUITS FORMULA: Φᵢ(χ) = tanh(β(χ − χ_c)) where β=4.0, χ_c=0.30
Fruit score 0→1: below 0.30 = Anti-Fruits dominate; above 0.70 = Fruits dominate.

FRUITS VECTOR:     Love · Joy · Peace · Patience · Kindness · Goodness · Faithfulness · Gentleness · Self-Control
ANTI-FRUITS VECTOR: Hatred · Despair · Anxiety · Impatience · Cruelty · Corruption · Betrayal · Harshness · Addiction

10 CHANNELS (what each measures):
  G = External dependency honesty      M = Alignment to reference standard
  E = Truth / signal fidelity          S = Entropy / disorder cost
  T = Temporal persistence             K = Compression / wisdom density
  R = Phase transition / regime change Q = Free will / invitation not coercion
  F = Cross-context binding            C = Whole-system integration

You receive the chi-evaluation output from two models (O3 and DeepSeek) for a single claim.
Generate EXACTLY 4 statement formats. Return ONLY valid JSON, no explanation outside JSON.

The statements must be GROUNDED in the data — reflect what the evaluation FOUND, not theological assertions beyond it.
The Fruits section is the primary communicable output. Always name the dominant Fruits with their channel justification."""

def _fmt_channels(channels: list) -> str:
    parts = []
    for c in channels:
        code = c.get("channel", "?")
        score = c.get("effective_score", 0)
        parts.append(f"{code}={score:.2f}")
    return "  ".join(parts)

def _geo_mean(channels: list) -> float:
    scores = [c.get("effective_score", 0) for c in channels]
    if not scores:
        return 0.0
    log_sum = sum(math.log(max(s, 1e-10)) for s in scores)
    return round(math.exp(log_sum / len(scores)), 4)

def _model_summary(ev: dict) -> dict:
    channels = ev.get("channel_results", [])
    fo = ev.get("fruit_output", {})
    return {
        "verdict":     ev.get("verdict", "unknown"),
        "gm":          f"{_geo_mean(channels):.4f}",
        "chi":         f"{ev.get('static_chi', 0):.6f}",
        "gradient":    ev.get("gradient", "neutral"),
        "fruit":       f"{fo.get('fruit_score', 0.5):.3f}",
        "fruits":      ", ".join(fo.get("dominant_fruits", [])) or "none",
        "antifruits":  ", ".join(fo.get("dominant_antifruits", [])) or "none",
        "channels":    _fmt_channels(channels),
        "weakest":     ", ".join(ev.get("weakest_channels", [])),
        "strongest":   ", ".join(ev.get("strongest_channels", [])),
    }

def _build_user_prompt(claim: str, model_evs: dict) -> str:
    labels = list(model_evs.keys())
    m1_label = labels[0] if len(labels) > 0 else "model_1"
    m2_label = labels[1] if len(labels) > 1 else "model_2"

    m1 = _model_summary(model_evs[m1_label]) if m1_label in model_evs else {}
    m2 = _model_summary(model_evs[m2_label]) if m2_label in model_evs else {}

    # Truncate claim for prompt
    claim_short = claim.replace("\n", " ").strip()
    if len(claim_short) > 500:
        claim_short = claim_short[:500] + "…"

    lines = [f'CLAIM: "{claim_short}"', ""]

    if m1:
        lines.append(f"{m1_label.upper()} EVALUATION:")
        lines.append(f"  Verdict: {m1['verdict']}  |  χ̄ geo-mean: {m1['gm']}  |  χ product: {m1['chi']}")
        lines.append(f"  Gradient: {m1['gradient']}  |  Fruit score: {m1['fruit']}")
        lines.append(f"  Dominant Fruits: {m1['fruits']}  |  Anti-Fruits: {m1['antifruits']}")
        lines.append(f"  Channel scores: {m1['channels']}")
        lines.append(f"  Weakest: {m1['weakest']}  |  Strongest: {m1['strongest']}")
        lines.append("")

    if m2:
        lines.append(f"{m2_label.upper()} EVALUATION:")
        lines.append(f"  Verdict: {m2['verdict']}  |  χ̄ geo-mean: {m2['gm']}  |  χ product: {m2['chi']}")
        lines.append(f"  Gradient: {m2['gradient']}  |  Fruit score: {m2['fruit']}")
        lines.append(f"  Dominant Fruits: {m2['fruits']}  |  Anti-Fruits: {m2['antifruits']}")
        lines.append(f"  Channel scores: {m2['channels']}")
        lines.append(f"  Weakest: {m2['weakest']}  |  Strongest: {m2['strongest']}")
        lines.append("")

    lines.append("Generate the 4 statement formats as JSON:")
    lines.append("""{
  "one_liner": "Single shareable sentence ~25 words. Start with the claim in quotes, name the dominant Fruits, give Φ score, verdict, and gradient.",
  "formal_scientific": "2-3 sentences. Use Φᵢ(χ) notation, name channel scores for strongest/weakest, state verdict with geo-mean, note what the weakest channel structurally limits.",
  "theological_narrative": "2-3 sentences in plain theological language. What does this claim tend to produce spiritually? What does the weakness in the lowest channel mean for someone who holds or acts on this claim?",
  "cross_model_comparison": "1-2 sentences. Where do the models agree? Name the channel with the largest score gap and what that disagreement means for how confidently we can assess this claim."
}""")

    return "\n".join(lines)


def synthesize(claim: str, model_evs: dict, cfg: dict) -> dict | None:
    """
    Call DeepSeek to synthesize 4 statement formats.
    model_evs: {model_label: evaluation_dict (from ev.to_json() parsed)}
    Returns parsed statements dict or None on failure.
    """
    try:
        import openai
    except ImportError:
        print("    [synthesis] openai not installed")
        return None

    ds_key = cfg.get("DEEPSEEK_API_KEY", "")
    if not ds_key:
        print("    [synthesis] no DEEPSEEK_API_KEY — skipping")
        return None

    user_prompt = _build_user_prompt(claim, model_evs)

    try:
        client = openai.OpenAI(api_key=ds_key, base_url=DEEPSEEK_BASE_URL)
        t0 = time.time()
        resp = client.chat.completions.create(
            model=cfg.get("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=[
                {"role": "system", "content": SYNTHESIS_SYSTEM},
                {"role": "user",   "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=1200,
            temperature=0.4,
        )
        elapsed = round(time.time() - t0, 2)
        raw = resp.choices[0].message.content
        data = json.loads(raw)

        # Validate keys
        required = ["one_liner", "formal_scientific", "theological_narrative",
                    "cross_model_comparison"]
        for k in required:
            if k not in data:
                data[k] = ""

        data["_elapsed_s"] = elapsed
        data["_tokens_in"]  = resp.usage.prompt_tokens if resp.usage else 0
        data["_tokens_out"] = resp.usage.completion_tokens if resp.usage else 0
        print(f"    [synthesis] done {elapsed}s  ({data['_tokens_out']} tok out)")
        return data

    except Exception as e:
        print(f"    [synthesis] error: {e}")
        return None
