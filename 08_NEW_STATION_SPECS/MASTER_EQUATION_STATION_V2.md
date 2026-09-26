# MASTER_EQUATION station V2: what in this paper plays the role of the master equation?

Replaces the main task of `API_DEEP\MASTER_EQUATION\PROMPT.md`. V1 only listed a paper's own equations;
keep that as optional **Part B** for papers that contain math.
David's spec, 2026-09-24: for every paper, ask what is analogous to the master equation. This is subjective,
so the station is built to show where it is subjective.

## The reference (send this block with every call)

χ_total = ∫_{t0}^{t1} ∫_Ω G·M·E·S_eff·T·K·R·Q·F·C d³x dt  (ME-EQ-001). Locally, χ = G·M·E·S_eff·T·K·R·Q·F·C (ME-EQ-002).
The factors multiply, so if any required factor is zero the whole collapses (zero-collapse, ME-EQ-006).

| Slot | Meaning (canonical pill ME-01-020..029) |
|---|---|
| G | External negentropy influx: coherence can't sustain itself in a closed system and needs an outside source |
| M | Alignment: coupling is strongest when the system is aligned with its reference |
| E | Signal fidelity: whether truth survives transmission through noise |
| S_eff | Effective entropy: entropy enters as what lowers coherence |
| T | Temporal integration: time turns possibility into accumulated consequence |
| K | Compression: ordered meaning compresses and noise does not |
| R | Phase transition: some thresholds change state, not just degree |
| Q | Superposition: open possibility stays unresolved until actualized |
| F | Non-local correlation: related systems are no longer independent |
| C | Integration: the local integrator inside the product |

Source: `D:\GitHub\Faith-through-physics-atoms\mothership\pills\master-equation\01_canonical\`. The runner
should read the slot meanings from those pills at run time rather than hard-coding this table.

## Part A: the analog (every paper)

1. **The paper's own core relation**: in one sentence, what does everything else in this paper depend on?
   It may be verbal, e.g. "restoration requires confession AND grace AND time together". Quote the span that
   comes closest to stating it.
2. **The product test** (the most objective step, weighted most heavily): if one ingredient of that relation is
   zero or missing, does the paper's conclusion fail entirely (**multiplicative**, like χ) or only weaken
   (**additive**)? Quote the evidence. Answer `multiplicative | additive | threshold | unclear`.
3. **Slot mapping**: for each of the 10 slots, say what in the paper plays that role, with a quoted span, and
   rate the fit `direct | analogous | stretched | absent`. Absent is a normal answer. Do not fill slots to look complete.
4. **Where it breaks**: the places the analogy stops working, e.g. a slot the paper treats as optional,
   or a factor the paper adds that has no slot.
5. **Overall**: an analog strength of 0-5, a confidence of low/medium/high, and a one-line statement of the analog.
   Always labeled as an analogy proposal, never a derivation.

```json
{"paper": "", "core_relation": {"sentence": "", "quote": ""},
 "product_test": {"answer": "multiplicative", "quote": "", "reason": ""},
 "slots": [{"slot": "G", "plays_role": "", "quote": "", "fit": "analogous"}],
 "breaks": [], "extra_factors": [],
 "analog_strength": 3, "confidence": "medium", "one_line": ""}
```

## Handling the subjectivity

Run Part A **twice independently**: two calls with different seeds (temperature 0.7), or two models when available.
The runner, not the model, then compares the results:
- product-test answers and slot fits that agree are marked `agreed`
- disagreements are marked `contested` and listed at the top of the report for David to rule on
- the reported analog strength is the lower of the two, with the spread shown (e.g. `3 (3-4)`)

Across a series, add a roll-up: which slots every paper fills, which are never filled, and whether the product
test holds for the series as a whole.

## Part B (optional: papers with equations)

The V1 equation extraction (exact expression, symbols, units, dimensional check, relationship to
χ: instantiates | approximates | contradicts | independent). Run it only when Part A finds at least one equation.
