# API LAYER v0.3 — Template Set
**POF 2828 | 2026-09-14**

Seven templates, one parser, joined on SHA-256 + UUID end to end.

---

## UUID tracking

Every paper gets a `paper_uuid` (UUIDv4) in YAML. Human-readable slug stays as `paper_id`.
When a paper is sorted into the four outbox copies, filenames carry copy markers:
- `{{slug}}_C1_{{uuid}}.md` — by domain
- `{{slug}}_C2_{{uuid}}.md` — by content type
- `{{slug}}_C3_{{uuid}}.md` — by series
- `{{slug}}_C4_{{uuid}}.md` — untouched archive

All versions of any paper are findable by UUID across all folders.

## Inter-paper dependencies

YAML fields `upstream_hashes` and `downstream_implications` track cascade failure paths.
If paper A depends on paper B, paper A lists B's sha256 in `upstream_hashes`.
The parser can walk these to build a vault-wide dependency graph.

---

## The seven files

| File | What it is | API call | @template marker |
|---|---|---|---|
| `MASTER_PAPER_TEMPLATE_v0.3.md` | The rendered paper: classification, evidence-sheet, six-door lens, warrant, dynamics, mermaid maps, definitions, path to 10, self-assessment, tail layers | **Call 1** — main | `@template layer=paper` |
| `CLAIMS_LAYER_TEMPLATE_v0.3.md` | Claims/proofs layer: claims table, hidden premises, Lean targets, predictions, falsifiers, bridge/correspondence registry with word-gate column | **Call 2** — claims | `@template layer=claims` |
| `MATH_LAYER_TEMPLATE_v0.3.md` | Math formalization: axiom inventory, three-layer equation breakdown, proof structure with mermaid, notation dictionary, Lean targets, version tracking, canonization readiness | **Call 3** — math (only when paper has math) | `@template layer=math` |
| `GRADING_LAYER_TEMPLATE_v0.3.md` | Framework alignment & scoring: axiom node mapping, χ variable coverage, fruits of the spirit, law alignment, raw metrics (text/readability/structure/NLP), claim-level grading, knowledge graph, spine variables, composite scores, path to 10 | **Call 4** — grading (every paper) | `@template layer=grading` |
| `SERIES_AGGREGATION_TEMPLATE_v0.3.md` | Series overview: aggregates N papers into kernel map, claim consolidation, cross-paper evidence, structural spine, destination map, gap analysis | **Call 5** — series (after all papers processed) | `@template layer=series` |
| `MASTER_INDEX_FORMAT_v0.3.md` | Tab-delimited running index: 43-column contract with source map | **Parser output** — not API | `@template layer=index` |
| `EVIDENCE_DASHBOARD_v0.3.md` | Standalone vault-wide Dataview dashboard | Not API — lives in vault, reads frontmatter | — |

Also included: `MASTER_PAPER_TEMPLATE_v0.3_SPINE.md` — the CKG spine definition from which the rendered template was built (rules, rating scale, standing rules, question bank definitions).

## How they join

```
PAPER (source_sha256) ←→ CLAIMS LAYER (source_sha256)
                     ←→ MATH LAYER (source_sha256, if math present)
                     ←→ GRADING LAYER (source_sha256, every paper)
                                    ↓
                              INDEX (one row per paper)
                                    ↑
SERIES AGG (paper_ids[]) ──────────┘
     aggregates N papers into one overview
```

## Atomicity rule (Rule 11)

One paper = the complete call set before the run moves to the next paper:
1. Main call → fills the paper template (evidence + truth predicates + six doors + warrant + dynamics + definitions + path to 10)
2. Claims call → fills the claims layer template
3. Math call → fills the math layer template (CONDITIONAL: only if paper has math content)
4. Grading call → fills the grading/alignment layer (axiom nodes, χ, fruits, laws, raw metrics, claim grading, composite scores)
5. Parser → reads all files for this paper, emits one index row

No paper leaves the run half-processed.

## Rendering order (top to bottom of a finished paper)

1. YAML frontmatter (identity, domain %, tags weighted, UUID, upstream/downstream hashes)
2. **Classification & Routing** — domain with percentages, content type, reader level, series, outbox routing
3. **The Six + Verdict** — claim, domain, physical event, bridge, defeat conditions, have/need/breaks
4. **Claims table + Evidence ledger**
5. **Q0–Q14** — varied callout types by question nature
6. **Domain checks** — varied callout types by domain
7. **Coherence + Self-Assessment** — reputation form (8 dimensions, self-grade, blind spot)
8. **Audit** — held/broke/overstated/defensible/blast radius
9. Evidence dashboard (Dataview)
10. **At a Glance** (expanded) + **Central Claim**
11. **Best Concise Argument** — provenance-tagged steps, strengthening table, supplementary arguments
12. **Six-Door Lens** — Human, Metaphysical, Theological, Scientific, Formal, External (nested callouts)
13. **Warrant** — claim/evidence/proof/kill condition/strength/coverage
14. **Dynamics** — coherence/degradation/measurement/threshold/asymmetry/restoration/counterexample
15. **Structural Map** — mermaid dependency graph + inter-paper map
16. **Truth Predicates** (exhaustive, with modality) + Terms
17. **Evidence Chain + Best Evidence + Bridge Originality**
18. **Objections + Counter-models** (structured table)
19. **What Survives / What Not Established / Corrections / Implications**
20. **Formal Path** — math table, Lean checks, empirical checks, adversarial checks (nested)
21. **Open Questions + Classification**
22. Tail layers — unanswered/deferred, audit appendix, exact source

## v0.3 structural improvements (this session)

1. **Modality column** added to truth predicate table — Axiomatic / Contingent / Heuristic per predicate
2. **Mapping Type + Preserved Structure** columns added to bridge originality seam table — isomorphism precision
3. **`upstream_hashes` / `downstream_implications`** YAML fields — inter-paper cascade failure tracking
4. **Failure Mode column** added to mathematics table — what breaks if the equation is wrong
5. **Structured counter-model table** replaces single bullet — Proposed / Why plausible / Breaking point / Status
6. **`paper_uuid`** field + C1/C2/C3/C4 copy markers for outbox routing
7. **Six-Door Explanatory Lens** — Human, Metaphysical, Theological, Scientific, Formal, External doors with nested callouts
8. **Warrant section** — full warrant control table (claim, evidence, proof, kill condition, strength, coverage, independence)
9. **Dynamics section** — coherence, degradation, measurement, threshold, asymmetry, restoration, counterexample
10. **Mermaid structural maps** — claim dependency graph + inter-paper dependency map
11. **Self-Assessment / Reputation Form** — 8 dimensions scored 0–10, self-grade, blind spot
12. **Visual overhaul** — varied callout types by purpose, tables replace bullet lists, nested callouts
13. **Domain percentage weighting** — primary + secondary domains sum to 100%, weighted tags
14. **MATH_LAYER_TEMPLATE** (Call 3) — axiom inventory, three-layer equation breakdown, proof structure with mermaid, notation dictionary, version tracking, canonization readiness, originality tracking

---

_POF 2828 · not a probability of truth · human ruling required_
