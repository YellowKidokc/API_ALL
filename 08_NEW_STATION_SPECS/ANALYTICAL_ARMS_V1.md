# ANALYTICAL ARMS V1: Fruits + Master Equation + Axiom Nodes + Coherence, always run together

David, 2026-09-25: these four are the analytical arms. They never run alone. One run per paper produces one combined
report: **Fruits of the Spirit 1-2 pages (the flagship)**, then about one page each for master equation, axiom nodes and coherence.
Fruits must show, sentence by sentence, where the text spikes toward love and where it spikes away from it.
David will supply the final page format. Until then, the layout below is a placeholder.

Built from what already exists (all in this folder):
- Fruits rubric v0.3.0: `05_API_DEEP_STATIONS\FRUITS\...\scripts\rubric\fruits_rubric_v0.3.0.json` (9 fruits, each with
  mechanism / anti-fruit / counterfeit; 7 gates; 8 stress tests; veto conditions; invariants), its canonical spec
  `Fruits_of_the_Spirit_Epistemic_Rating_System_Canonical.md`, and runner `fruits_grade.py`.
- Truth Engine v2.0 workbook: `\\192.168.2.50\h_hp\Desktop\Folders\ALL EXCEL\Fruits Template (1) (1).xlsx`
  (lexicon sheets: Fruit 278 terms, Anti-Fruit 298, Grounding 103, Contradiction 39, Propaganda 72, Jargon 56, AAVE 591,
  plus Weights, Archetypes and Characterizations).
- Lexicon workbook: `\\192.168.2.50\h_hp\Desktop\Folders\Folders\Master EXCEL (1)\lexicons_master_enhanced.xlsx`
  (FRUITS_LEX and ANTI_FRUITS keyed **per fruit**, SEMANTIC_BUCKETS, ME_VARS, HEDGE/ABSOLUTE/NEGATION terms).
- Axiom nodes runner `05_API_DEEP_STATIONS\AXIOM_NODES` (191 nodes from AXIOMS_PART1_MODE_CLASSIFICATION.md).
- Coherence prompt `05_API_DEEP_STATIONS\COHERENCE_SCORE\PROMPT.md`.
- Master equation V2 spec `08_NEW_STATION_SPECS\MASTER_EQUATION_STATION_V2.md`.

---

## Pipeline (one paper)

```
0 PREP (local)        split into numbered paragraphs P01.. and sentences S001..; keep offsets; hash the source
1 LEXICON (local)     every word of every sentence against the lexicons -> per-sentence, per-fruit hit counts
2 SENTENCE (API)      every sentence scored on all 9 fruits, whole paper in every call -> per-sentence vector  [output ranges, parallel]
3 AGGREGATE (local)   rolling curves, spikes, paragraph/section roll-ups, lexicon-vs-meaning gap
4 ARMS (API, parallel) Fruits verdict (rubric v0.3.0)  |  Master equation x2  |  Axiom nodes  |  Coherence
5 REPORT (local)      render the combined report (Markdown + XLSX in the Truth Engine layout); original untouched
```

Stages 1 and 3 have no API cost and give the same result every time. Every stage saves its JSON, so a rerun reuses finished stages
when the source hash, prompt version and model are unchanged.

---

## Stage 1: word level (local, deterministic)

For each sentence, count lexicon hits per fruit (FRUITS_LEX / FRUIT_BLEND positive), per anti-fruit (ANTI_FRUITS,
ANTI_FRUIT_MAP), and for grounding, contradiction, propaganda, jargon, hedge, absolute and negation. Record **which words**
hit, so the report can show the exact trigger words. Apply the Truth Engine Weights sheet for the legacy TRUTH score.

Handle negation and quotation locally with a simple rule: a hit inside a negation window ("not", "never", "no ... ") or
inside quotation marks is recorded but flagged `negated` / `quoted`. It is not counted as the author's own stance.

**This is a signal, not a verdict.** Rubric invariant: *"Vocabulary is not character evidence."* Word hits are shown as
the trace underneath. They never set a fruit score on their own.

## Stage 2: sentence level (API, the nuance)

For every sentence, the model returns 9 integers from **-2 to +2**, one per fruit:
`-2` clear anti-fruit · `-1` leans anti · `0` neutral or not engaged · `+1` leans toward the fruit · `+2` clear embodiment.
It scores what the sentence *does* in context (its mechanism), not the words it uses: sarcasm, a quoted opponent,
correction given gently, a hard truth told for the reader's good (that is love, even if no "love" word appears).

To keep output small, the reply is compact arrays. A reason is required **only** when |value| = 2, or when the sign
disagrees with the Stage 1 lexicon signal for that fruit.

```json
{"chunk": 3, "sentences": [
  {"id": "S081", "v": [2,0,1,0,1,1,0,0,0], "why": {"love": "tells the reader a cost-bearing truth for their sake"}},
  {"id": "S082", "v": [-1,0,-1,0,-2,0,0,-1,0], "why": {"kindness": "mocks the opponent's intelligence", "counterfeit": "kindness words, contempt mechanism"}}
]}
```

Fruit order is fixed: love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, self_control.
**Every call receives the whole paper** (full context: no chunking of the input). Only the output is split: each call is
told "score sentences S001-S080" (and so on), because a reply that scores every sentence of a long paper can exceed the
output-token cap. These range calls are independent and run in parallel. For a paper short enough to fit the output
limit, it is one call.

## Stage 3: aggregation (local)

- **Love curve** (and one curve per fruit): the sentence values, plus a 5-sentence rolling mean.
- **Spikes**: any sentence at ±2, and any sentence where the rolling mean crosses zero (a turn). List the top 5 toward
  and top 5 away from each fruit, with the sentence quoted.
- **Paragraph and section roll-ups**: mean, min, max and share of negative sentences per fruit.
- **Lexicon-vs-meaning gap: the counterfeit detector.** For each sentence and fruit, compare Stage 1 (words) with
  Stage 2 (mechanism). Many fruit words with a negative mechanism = **counterfeit candidate** (virtue vocabulary doing
  anti-fruit work). Few fruit words with a positive mechanism = **hidden fruit** (love done, not advertised). Nothing else
  in the system measures this, and it is the part of the Fruits report most readers will not have seen anywhere.
- **Balance**: love is the root (canonical: "singular Fruit, nine dimensions"), so report how the other eight track the love
  curve (correlation per fruit). Where they diverge, e.g. high self-control with negative love, name the pattern.
- **Characterization**: apply the Truth Engine Characterizations patterns (Grounded Truth-Teller, Sophisticated Propagandist,
  Fear Merchant, Pure Fruit ...) to the aggregated ratios, as a labeled secondary read.

## Stage 4: the four arms (API, run in parallel; each gets the paper plus the Stage 3 summary)

| Arm | Contract | Page |
|---|---|---|
| **Fruits verdict** | rubric v0.3.0: hard gates (truth/evidence, contradiction, agency) → 9 dimensions 0-4 with cited sentence ids → 8 stress tests → veto check → gated-profile verdict. Must cite the Stage 3 spikes and gap by sentence id. | 1-2 |
| **Master equation** | MASTER_EQUATION_STATION_V2: core relation, product (zero-collapse) test, 10-slot mapping, breaks; run twice, agreement computed locally. | 1 |
| **Axiom nodes** | existing runner contract: engaged nodes only, alignment + exact quote + confidence; primary mode. | 1 |
| **Coherence** | existing prompt: 4 dimensions with reasons and affected sentence ids; contradictions (definitional/local/structural), tensions, missing definitions. Reuses Stage 1 contradiction/negation hits as candidates to check. | 1 |

Cross-arm checks (local, after Stage 4), listed in the report as **Where the arms disagree**:
- Coherence finds a structural contradiction but the Fruits truth gate passed → one of them is wrong; show both.
- Master-equation product test is multiplicative, and a Fruits dimension scores 0 → name the zero-collapse.
- An axiom node is `contested` in a sentence that scores +2 on love → possibly a charitable disagreement; flag it for David.

## Stage 5: the report (placeholder layout until David sends his format)

```
Page 1-2  FRUITS OF THE SPIRIT
          verdict line · gate results · nine-dimension profile (0-4) · love curve sparkline across the paper
          the three highest and three lowest moments (sentence quoted, fruit, why)
          counterfeit candidates and hidden fruit (the gap) · stress tests · veto status · repair instructions
Page 3    MASTER EQUATION: core relation · product test · slot map (fit per slot) · agreed vs contested
Page 4    AXIOM NODES: engaged nodes table (node, alignment, quote, confidence) · unmapped claims
Page 5    COHERENCE: score with reasons · contradictions · tensions · missing definitions
Last      WHERE THE ARMS DISAGREE · audit (hashes, models, prompt versions, token cost)
```

Also write an **XLSX in the Truth Engine v2.0 layout**: one row per sentence with the 9 fruit values, lexicon hits, the gap, and
the TRUTH / COHERENCE / FRUIT / ANTI-FRUIT / GROUNDING / CONTRADICTION / PROPAGANDA columns, so David can sort and chart it in Excel.

---

## Invariants (from rubric v0.3.0, kept)

No assessment without a cited sentence id or an explicit unknown. No positive verdict after a failed hard gate. No claims about
hidden motives, salvation or divine origin. Vocabulary is not character evidence. Missing evidence is reported as missing, never
filled in with invented precision. The analysis is an AI proposal until David reviews it.

## Decisions David still has to make (ask before building)

1. **Page format**: he will send it. Build stages 0-4 first; only the renderer waits on this.
2. **Axiom registry**: the runner maps to `AXIOMS_PART1` (191 nodes, 7 AX_CORE such as A1.1 Existence), the pills use
   `AX-###` ids, and the DeepSeek HOME says the framework has exactly one root axiom ("God Is"). Which registry is canonical?
3. **Sentence scale**: -2..+2 per fruit (proposed; it shows direction, which spikes need) vs the rubric's 0-4 (which has no
   negative side). The proposal keeps 0-4 for the paper-level verdict and uses -2..+2 per sentence.
4. **Which lexicon wins** where the Truth Engine sheets and lexicons_master_enhanced disagree (e.g. "love" tiering).
5. **Scope**: papers only, or also YouTube transcripts (the lens system could call the arms as focus 18).

## Cost (deepseek-chat, 5,000-word paper ≈ 250 sentences)

Stage 2 ≈ 3-4 range calls × whole paper (~8k in + ~6k out each) · Fruits verdict ≈ 15k · Master equation 2 × ~10k · Axiom ≈ 12k · Coherence ≈ 10k,
so roughly 100k tokens per paper. Stages 1, 3 and 5 are free.
