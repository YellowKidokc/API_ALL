"""stats_engine.py -- Stage 2 of the Fruits of the Spirit grading pipeline.

Reads grading_out/<paper>.lexicon.json (Stage 1 output), computes ~100
statistics, and writes grading_out/<paper>.stats.json. No API calls.

Each statistic is {key, value, unit, note, in_report}. The <=25 most
decision-relevant stats are marked in_report and printed to the console as a
tidy table. The output also carries a per-sentence "series" block for later
charting.

Inputs:
  --paper   Path to the original paper (used to locate <paper>.lexicon.json),
            or a path to the .lexicon.json directly.
Output:
  grading_out/<paper>.stats.json
"""

import argparse
import hashlib
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

STATION_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = STATION_DIR / "grading_out"
WEIGHTS_PATH = Path(__file__).resolve().parent / "weights.json"


def load_weights():
    """Load scripts/weights.json (the tuning file). Fail loudly if missing."""
    if not WEIGHTS_PATH.exists():
        sys.exit(f"ERROR: tuning file not found: {WEIGHTS_PATH}\n"
                 "weights.json holds the category weights and tunables; restore it.")
    with open(WEIGHTS_PATH, encoding="utf-8") as f:
        return json.load(f)

CATEGORIES = ["fruit", "anti_fruit", "grounding", "contradiction", "jargon", "propaganda", "archetype"]
FRUIT_AXES = [
    "love", "joy", "peace", "patience", "kindness",
    "goodness", "faithfulness", "gentleness", "self_control",
]
CLAIM_KEYS = ["weak", "moderate", "strong", "forbidden"]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def shannon_entropy(counts):
    total = sum(counts)
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return round(h, 4)


def percentile(sorted_vals, pct):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * pct / 100.0
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return round(sorted_vals[int(k)], 4)
    return round(sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f), 4)


def main():
    ap = argparse.ArgumentParser(description="Stage 2: statistics engine (no API).")
    ap.add_argument("--paper", required=True,
                    help="Path to the paper, or to its .lexicon.json.")
    args = ap.parse_args()

    p = Path(args.paper)
    lex_path = p if p.suffix == ".json" else OUT_DIR / f"{p.stem}.lexicon.json"
    if not lex_path.exists() and not p.suffix == ".json":
        lex_path = OUT_DIR / f"{p.name}.lexicon.json"
    with open(lex_path, encoding="utf-8") as f:
        lex = json.load(f)

    tuning = load_weights()
    weights = tuning["category_weights"]
    axis_weights = tuning.get("fruit_axis_weights", {})
    z_threshold = float(tuning.get("spike_z_threshold", 2.0))
    weights_sha = hashlib.sha256(WEIGHTS_PATH.read_bytes()).hexdigest()

    sentences = lex["sentences"]
    n_sent = len(sentences)
    words_per = [s["word_count"] for s in sentences]
    total_words = sum(words_per) or 1

    stats = []

    def add(key, value, unit, note, in_report=False):
        # in_report flags are assigned from the weights.json whitelist below;
        # the parameter marks intent at the call site.
        stats.append({"key": key, "value": value, "unit": unit,
                      "note": note, "in_report": False})

    # --- volume -----------------------------------------------------------
    add("volume.sentences", n_sent, "count", "Sentence count from Stage 1 splitter", True)
    add("volume.words", sum(words_per), "count", "Total word count", True)
    add("volume.paragraphs", lex.get("paragraph_count", 0), "count", "Blank-line separated blocks")
    add("volume.sentence_len.avg", round(statistics.fmean(words_per), 2) if words_per else 0,
        "words", "Mean sentence length", True)
    add("volume.sentence_len.median", statistics.median(words_per) if words_per else 0, "words", "Median sentence length")
    add("volume.sentence_len.stdev", round(statistics.pstdev(words_per), 2) if len(words_per) > 1 else 0,
        "words", "Population stdev of sentence length")
    add("volume.sentence_len.min", min(words_per) if words_per else 0, "words", "Shortest sentence")
    add("volume.sentence_len.max", max(words_per) if words_per else 0, "words", "Longest sentence")

    # --- per-category volume + density ------------------------------------
    cat_hits = {c: [s["categories"][c]["hits"] for s in sentences] for c in CATEGORIES}
    cat_totals = {c: sum(cat_hits[c]) for c in CATEGORIES}
    cat_uniques = {c: len({t for s in sentences for t in s["categories"][c]["matched_terms"]})
                   for c in CATEGORIES}
    gate_density = {"fruit", "anti_fruit", "grounding", "propaganda"}
    for c in CATEGORIES:
        add(f"{c}.hits", cat_totals[c], "count", f"Total {c} lexicon hits")
        add(f"{c}.unique_terms", cat_uniques[c], "count", f"Distinct {c} terms matched")
        add(f"{c}.density_per_100w", round(cat_totals[c] / total_words * 100, 3),
            "hits/100 words", f"{c} density", c in gate_density)
        add(f"{c}.weighted_score", round(cat_totals[c] * weights.get(c, 0.0), 3),
            "weighted", f"{c} hits x weight {weights.get(c, 0.0)}")

    # --- Truth Engine v2.0 TRUTH formula ----------------------------------
    truth_pos = cat_totals["fruit"] * weights.get("fruit", 1.0) + \
        cat_totals["grounding"] * weights.get("grounding", 2.0)
    truth_neg = sum(cat_totals[c] * weights.get(c, 0.0)
                    for c in ("anti_fruit", "contradiction", "jargon", "propaganda"))
    truth = truth_pos + truth_neg
    add("truth.score", round(truth, 3), "weighted",
        "TRUTH = (fruit x1.0 + grounding x2.0) + (anti_fruit x-1.5 + contradiction x-0.5 "
        "+ jargon x-0.3 + propaganda x-2.0)", True)
    add("truth.positive_component", round(truth_pos, 3), "weighted", "fruit + grounding contribution")
    add("truth.negative_component", round(truth_neg, 3), "weighted", "anti-fruit + contradiction + jargon + propaganda contribution")
    add("truth.per_100_words", round(truth / total_words * 100, 3), "weighted/100 words",
        "TRUTH score normalized by length")

    # --- fruit axes ---------------------------------------------------------
    axis_totals = {a: sum(s["fruit_axes"].get(a, 0) for s in sentences) for a in FRUIT_AXES}
    axis_sum = sum(axis_totals.values()) or 1
    for a in FRUIT_AXES:
        add(f"fruit_axis.{a}.total", axis_totals[a], "count", f"Attributed {a} hits", True)
    for a in FRUIT_AXES:
        add(f"fruit_axis.{a}.share", round(axis_totals[a] / axis_sum, 4), "share",
            f"Share of attributed fruit hits for {a}")
    ranked = sorted(FRUIT_AXES, key=lambda a: axis_totals[a], reverse=True)
    add("fruit_axis.strongest", ranked[0], "axis", f"Strongest fruit axis ({axis_totals[ranked[0]]} hits)")
    add("fruit_axis.weakest", ranked[-1], "axis", f"Weakest fruit axis ({axis_totals[ranked[-1]]} hits)")
    add("fruit_axis.entropy", shannon_entropy(list(axis_totals.values())), "bits",
        "Shannon entropy across the nine fruit axes")
    add("fruit_axis.attributed_hits", sum(axis_totals.values()), "count",
        "Fruit hits attributable to a canonical axis")
    add("fruit_axis.unattributed_hits", cat_totals["fruit"] - sum(axis_totals.values()), "count",
        "Fruit hits with no axis mapping")
    add("fruit_axis.weighted_total",
        round(sum(axis_totals[a] * float(axis_weights.get(a, 1.0)) for a in FRUIT_AXES), 3),
        "weighted", "Fruit-axis totals weighted by weights.json fruit_axis_weights")

    # --- anti-fruit profile ---------------------------------------------------
    anti_axis_totals = {}
    for s in sentences:
        for a, n in s["anti_fruit_axes"].items():
            anti_axis_totals[a] = anti_axis_totals.get(a, 0) + n
    add("anti_fruit.axis_hits", sum(anti_axis_totals.values()), "count",
        "Anti-fruit hits attributable to an axis label")
    add("anti_fruit.axis_distinct", len(anti_axis_totals), "count", "Distinct anti-fruit axes hit")
    top_anti = sorted(anti_axis_totals.items(), key=lambda kv: kv[1], reverse=True)[:5]
    add("anti_fruit.top_axes", [{"axis": a, "hits": n} for a, n in top_anti], "list",
        "Top anti-fruit axes by hits")
    for a, n in top_anti:
        add(f"anti_fruit.axis.{a}.total", n, "count", f"Anti-fruit axis '{a}' hits")

    # --- claim strength -------------------------------------------------------
    cs_totals = {k: sum(s["claim_strength"][k] for s in sentences) for k in CLAIM_KEYS}
    cs_sum = sum(cs_totals.values()) or 1
    for k in CLAIM_KEYS:
        add(f"claim_strength.{k}.count", cs_totals[k], "count", f"CLAIM_STRENGTH {k} hits")
        add(f"claim_strength.{k}.share", round(cs_totals[k] / cs_sum, 4), "share",
            f"Share of claim-strength hits that are {k}")
    weak_n, strong_n = cs_totals["weak"], cs_totals["strong"]
    add("claim_strength.strong_to_weak_ratio",
        round(strong_n / weak_n, 4) if weak_n else (None if strong_n == 0 else "inf"),
        "ratio", "strong_claim : weak_inference", True)
    add("claim_strength.forbidden_share", round(cs_totals["forbidden"] / cs_sum, 4), "share",
        "forbidden_unless_formal share of claim-strength hits")

    # --- hedges vs absolutes ----------------------------------------------------
    hedge_n = sum(s["hedges"] for s in sentences)
    abs_n = sum(s["absolutes"] for s in sentences)
    add("hedge.count", hedge_n, "count", "Hedge term hits (LEXICON_V2 HEDGE_TERMS)")
    add("absolute.count", abs_n, "count", "Absolute term hits (LEXICON_V2 ABSOLUTE_TERMS)")
    add("hedge.density_per_100w", round(hedge_n / total_words * 100, 3), "hits/100 words", "Hedge density")
    add("absolute.density_per_100w", round(abs_n / total_words * 100, 3), "hits/100 words", "Absolute density")
    add("hedge_to_absolute_ratio",
        round(hedge_n / abs_n, 4) if abs_n else (None if hedge_n == 0 else "inf"),
        "ratio", "hedges : absolutes; high = calibrated, low = overclaiming", True)

    # --- grounding to claim ------------------------------------------------------
    total_claims = sum(cs_totals.values())
    add("grounding_to_claim_ratio",
        round(cat_totals["grounding"] / total_claims, 4) if total_claims else None,
        "ratio", "grounding hits : claim-strength hits (evidence per claim signal)", True)

    # --- per-third drift -----------------------------------------------------------
    third = max(1, n_sent // 3)
    thirds = [sentences[:third], sentences[third:2 * third], sentences[2 * third:]]
    for c in ("fruit", "anti_fruit", "grounding"):
        densities = []
        for i, part in enumerate(thirds):
            w = sum(s["word_count"] for s in part) or 1
            h = sum(s["categories"][c]["hits"] for s in part)
            d = round(h / w * 100, 3)
            densities.append(d)
            add(f"drift.{c}.third{i + 1}_density", d, "hits/100 words",
                f"{c} density in document third {i + 1}")
        add(f"drift.{c}.delta_third3_minus_third1", round(densities[2] - densities[0], 3),
            "hits/100 words", f"{c} density drift from first to last third")

    # --- spike detection ------------------------------------------------------------
    for c in CATEGORIES:
        xs = cat_hits[c]
        if len(xs) < 2:
            mean, sd = (xs[0] if xs else 0), 0.0
        else:
            mean, sd = statistics.fmean(xs), statistics.pstdev(xs)
        scored = []
        for s in sentences:
            x = s["categories"][c]["hits"]
            z = (x - mean) / sd if sd > 0 else 0.0
            scored.append((z, s))
        add(f"spikes.{c}.count_z_gt_2", sum(1 for z, _ in scored if z > z_threshold), "count",
            f"Sentences with {c} z-score > {z_threshold} (weights.json spike_z_threshold)")
        top = sorted(scored, key=lambda zs: zs[0], reverse=True)[:5]
        add(f"spikes.{c}.top5",
            [{"sentence_idx": s["idx"], "z": round(z, 3), "hits": s["categories"][c]["hits"],
              "excerpt": s["text"][:90]} for z, s in top if z > 0],
            "list", f"Top 5 {c} spikes by per-sentence z-score",
            c in ("fruit", "anti_fruit", "grounding", "propaganda"))

    # --- distribution shape --------------------------------------------------------
    sent_scores = [round(sum(s["categories"][c]["weighted_score"] for c in CATEGORIES), 4)
                   for s in sentences]
    sorted_scores = sorted(sent_scores)
    sorted_lens = sorted(words_per)
    add("dist.sentence_score.p25", percentile(sorted_scores, 25), "weighted", "25th percentile per-sentence weighted score")
    add("dist.sentence_score.p50", percentile(sorted_scores, 50), "weighted", "Median per-sentence weighted score")
    add("dist.sentence_score.p75", percentile(sorted_scores, 75), "weighted", "75th percentile per-sentence weighted score")
    add("dist.sentence_score.p90", percentile(sorted_scores, 90), "weighted", "90th percentile per-sentence weighted score")
    add("dist.sentence_len.p25", percentile(sorted_lens, 25), "words", "25th percentile sentence length")
    add("dist.sentence_len.p75", percentile(sorted_lens, 75), "words", "75th percentile sentence length")
    add("dist.sentence_len.p90", percentile(sorted_lens, 90), "words", "90th percentile sentence length")
    if len(words_per) > 2 and statistics.pstdev(words_per) > 0:
        m, sd = statistics.fmean(words_per), statistics.pstdev(words_per)
        skew = statistics.fmean([((w - m) / sd) ** 3 for w in words_per])
    else:
        skew = 0.0
    add("dist.sentence_len.skewness", round(skew, 4), "skew", "Fisher moment skewness of sentence lengths")
    add("dist.sentence_score.entropy", shannon_entropy(
        [max(0.0, sc - min(sorted_scores)) + 1e-9 for sc in sent_scores]), "bits",
        "Entropy of per-sentence weighted-score mass (shifted non-negative)")
    add("dist.claim_strength.entropy", shannon_entropy(list(cs_totals.values())), "bits",
        "Entropy across claim-strength classes")

    # --- series block for charting ---------------------------------------------------
    series = {
        "sentence_idx": [s["idx"] for s in sentences],
        "word_count": words_per,
        "weighted_total": sent_scores,
        "hedges": [s["hedges"] for s in sentences],
        "absolutes": [s["absolutes"] for s in sentences],
        **{f"claim_{k}": [s["claim_strength"][k] for s in sentences] for k in CLAIM_KEYS},
        **{c: cat_hits[c] for c in CATEGORIES},
    }

    # in_report whitelist from weights.json is authoritative
    whitelist = set(tuning.get("in_report_whitelist", []))
    for st in stats:
        st["in_report"] = st["key"] in whitelist

    in_report_n = sum(1 for st in stats if st["in_report"])
    out_path = OUT_DIR / f"{lex['paper_name']}.stats.json"
    payload = {
        "paper": lex["paper"],
        "paper_name": lex["paper_name"],
        "generated_at": now_iso(),
        "stage": "stats_engine_v1",
        "source_lexicon_json": str(lex_path),
        "weights_file": str(WEIGHTS_PATH),
        "weights_sha256": weights_sha,
        "stat_count": len(stats),
        "in_report_count": in_report_n,
        "stats": stats,
        "series": series,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    # --- console table of in_report stats --------------------------------------------
    rows = [st for st in stats if st["in_report"]]
    kw = max(len(st["key"]) for st in rows)
    print(f"\n=== IN-REPORT STATS ({len(rows)} of {len(stats)}) — {lex['paper_name']} ===")
    print(f"{'key'.ljust(kw)}  {'value'.rjust(12)}  unit")
    print("-" * (kw + 28))
    for st in rows:
        v = st["value"]
        if isinstance(v, list):
            v = f"[{len(v)} items]"
        elif v is None:
            v = "n/a"
        print(f"{st['key'].ljust(kw)}  {str(v).rjust(12)}  {st['unit']}")
    print(f"\n[stats] {len(stats)} stats ({in_report_n} in_report) -> {out_path}")


if __name__ == "__main__":
    main()
