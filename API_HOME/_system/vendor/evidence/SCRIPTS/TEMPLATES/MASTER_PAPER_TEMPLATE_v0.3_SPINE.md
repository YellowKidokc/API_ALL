# MASTER PAPER TEMPLATE — v0.3 BETA (CKG SPINE + QUESTION BANK)
**POF 2828 | 2026-09-14 | canonical copy: 999_TEMPLATES**
*Working copy: EVIDENCE_CHAIN_INTAKE\SCRIPTS\COMPANION_TEMPLATE.md.
v0.3 adds the DEFERRAL RULE and the full QUESTION BANK to v0.2.
Paper is source of truth; every index, shelf, dashboard, Excel view
is generated from it.*

---

## THE DEFERRAL RULE (new in v0.3)

Ask EVERY question in the bank, EVERY run — way overboard on purpose.
Expansion costs nothing at run time; missing coverage costs a rerun.
But the body stays clean:

- A question that gets a real answer stays in its section.
- A question the paper cannot answer, does not deal with, or that is
  not applicable is MOVED (never deleted) to the bottom section
  `## Unanswered and not applicable — with reasons`, one line each:
  `Q-id — reason (NOT_ADDRESSED | INSUFFICIENT_SOURCE | NOT_APPLICABLE | GATED)`
- Unanswered is not zero and not silence. The bottom section IS the
  coverage record; evd_coverage in Layer 0 is computed from it.
- Nothing in the bank may be skipped silently. Skipping is a parse
  error, not a judgment call.

---

## THE RATING SCALE (locked)

| Rating | Meaning | Who awards |
|---|---|---|
| +10 | Lean-receipted (LEAN_FLOOR/OUTBOX/00_VERIFIED_RECEIPTS) | Lean only |
| +9 | Survived full adversarial pass AND human review | Human only |
| +8 max | API ceiling — survived audit, strong support | API |
| +1..+7 | Graded surviving support | API |
| 0 | Asserted, untested | default |
| -1..-10 | Tested and FAILED — negative control, never deleted | anyone |

Grade ([T]/[C]/[D]) = kind of support. Rating = how it fared. Never fuse.

---

## LAYER 0 — MACHINE HEADER (YAML)
One header, two consumers: pipeline scripts + Obsidian Dataview
(evidence dashboard reads these fields directly).

```yaml
---
# identity
paper_id:              # slug + short hash
original_title:
clean_title:
source_sha256:
chapter:               # ONE_STORY key or null
```
```yaml
# closed vocabularies (ballots pending)
content_type:          # CLAIM_OR_ARGUMENT | STORY_OR_EXPLANATION |
                       # OBJECTION_OR_COUNTERMODEL | FORMALIZATION |
                       # METHOD_OR_GOVERNANCE | INFRASTRUCTURE | EVIDENCE_OR_SOURCE*
domain:                # closed ~16
reader_category:       # closed ~10
tags: []               # open, metadata only, never folders
# substance
governing_question:
one_sentence_finding:
claim_ids: []          # <CHAPTER>-<PAPER>-C###
topic_keys: []         # definitive-works registry keys
# ratings under the cap rule
paper_rating:          # -10..+10
rating_awarded_by:     # API | HUMAN:<name> | LEAN:<receipt-id>
evidence_status:       # CANDIDATE -> AUDITED -> APPROVED (earned)
formal_status:         # NOT_ESTABLISHED | TARGETS_QUEUED | RECEIPTED
lean_receipts: []
# dashboard fields (evidence-sheet contract)
type: evidence-sheet
status: candidate        # candidate | reviewed | canon | retired
evd_state: UNSCORED      # UNSCORED | SCORED | GATED
evd_support: 0
evd_counter: 0
evd_balance: null        # null while UNSCORED/GATED — never 0
evd_families: 0
evd_coverage: 0.00       # computed from the deferral section
```
```yaml
evd_gated: false         # true if a verified counterexample is open
evd_stable: null         # sign survives ±25% weights, cap ±1, counter ±25%
evd_weakest_claim: ""
evd_unassessed: 0        # unassessed is not zero
evd_assessors: []        # no human name => machine-only, inadmissible
coherence: null          # 0-5, separate axis from evidence
physical_event: undecided
# audit trail (API DONE contract — full run provenance, per call)
semantic_provider:       # e.g. deepseek | openrouter
semantic_model:          # EXACT version string, e.g. deepseek/deepseek-v3.2
call_routes: []          # per-call: ["call_1=deepseek/deepseek-v3.2 (audit)",
                         #  "call_2=... (claims+evidence)", "call_3=... (bank)",
                         #  "call_4=... (truth atoms)"]
usage_tokens: {}         # prompt/completion/total/cost, per run
score:  grade:  canonical_rec:   # epistemic V2 outputs
run_id:  processed_date:
---
```

---

## THE BODY — CKG 14 HEADINGS (completion contract, ckg_record_v2.0)

### 1. At a glance
Plain English, declaration register: what we claim / what the machine
checks (incl. the standing one-paragraph "what Lean is" block) / why
it matters. Stamp `TRANSLATION: DRAFT — NOT REVIEWED` until human-read.

### 2. Central claim
Strongest defensible version, ordinary language. `@claim` marker on it.

### 3. Best concise argument
Load-bearing reasoning, numbered steps.

### 4. System or model
Entities, distinctions, relationships, sequence.
#### Terms and plain-language bridge
| Term/symbol | Exact role | Plain meaning | Analogy/example |
Analogy illustrates; it is not evidence.

### 5. Evidence chain
Claim -> Support -> Inference -> Confidence -> Boundary, per step.
Evidence-ledger table: | Family | Cluster | Claim | Dir | Raw | Discr. |
Timing | Rival | Assessor | Finding |. Two items are one family if they
cannot fail independently.

### 6. Best evidence and sources
Primary / external / local formal receipt / secondary / analogy —
separate. Provenance markers: ORIGINAL | HISTORICAL_WITNESS:<name> |
MODERN_PARALLEL:<ref> | UNVERIFIED; @witness verified=YES/NO.
#### Bridge originality (the unification seam)
Where domains meet in this paper, name the ORIGINAL contribution at
the seam: which correspondence/mapping/argument is new here vs
borrowed or standard. One line per seam: seam (domain A <-> domain B),
the move made, provenance tag, and nearest prior art if any
(UNVERIFIED until checked). This is where original-vs-witness gets
decided, per paper, at the exact joint where unification is claimed.

### 7. Strongest objection and negative controls
Best opposing case; countermodel, converse, ablation, permutation,
vacuity. Negative-rated rows (-1..-10) cited here, never deleted.

### 8. What survives
Narrowest defensible core after pressure, ratings per claim.

### 9. What this does not establish
Hard boundary: what the checkmark means / does not mean. Lean =
consequences of encoded definitions and premises only.

### 10. Corrections and revisions
"What we went through" — the story of what failed and got narrowed —
PLUS the lawyer audit table:
| What held | What broke | What's overstated | Defensible version | Blast radius |
@rating-change markers (dated) live here.

### 11. Implications
Formal / empirical / philosophical / semantic / theological — separate.

### 12. Formal or testable path
#### Mathematics (MANDATORY when any math is present)
What mathematics appears in this paper: each object/equation listed,
explained in plain language (three-layer rule: equation, term-by-term
translation, meaning), then judged: Is it coherent as written? Does it
test out (dimension check, limiting cases, known-result recovery)?
Status per item: COHERENT_TESTED | COHERENT_UNTESTED | DEFECTIVE |
DECORATIVE (present but carries no load — say so plainly).
If no mathematics is present, one line: "No mathematical content" —
this heading never silently disappears.
#### Lean / formal checks
| Theorem/invariant | Visible premises | Status | Reader meaning | Passing establishes |
Build result, #print axioms audit, proof-escape scan, receipt refs.
#### Empirical / literature checks
#### Adversarial checks

### 13. Open questions and next actions
Prioritized. @tangent topic=... definitive=PENDING feeds writing queue.

### 14. Recommended classification and relationships
supports / contradicts / refines / depends_on / tests edges.

---

## THE QUESTION BANK (ask all, every run — deferral rule governs)

### A. Opening the claim (evidence-sheet Q0-Q14)
Q0 exact expression · Q1 referent · Q2 identity and distinction ·
Q3 dependency floor · Q4 variation and invariance · Q5 capabilities
and operations · Q6 transitions · Q7 constraints · Q8 consequences
and licenses · Q9 representation ladder · Q10 preservation and loss ·
Q11 if true · Q12 if false / rivals · Q13 discriminating checks ·
Q14 emergent role

### B. Atom-level (ATOM-Q01..Q08)
narrowest independent assertion · exact referent · distinguished from
what · meaningfulness preconditions · invariants under translation/
transformation/time · undefined/contradictory/false conditions ·
representation ladder plain->symbol->formal->consequence · decompose?

### C. Definition lane (DEFINITION-Q01..Q10)
ordinary definition · authoritative disciplinary definition · major
reference sources · specialist dispute · necessary features · commonly
confused with · simplest analogy · components/mechanism · use in this
artifact · Theophysics use: preserve/narrow/extend/map/redefine/conflict

### D. Domain checks (each PASS / PARTIAL / FAIL / N-A with one line)
Physics: quantity, units, dynamics, protocol, instrument, data,
controls, analysis/fit. History: event, observers, witness, testimony,
transmission, document, preservation, corroboration, interpretation.
Theology: source, textual witness, tradition, proclamation, register,
confession class, scope, relation. Math/formal: definitions, axiom
use, inference rules, lemmas, derivation, theorem, receipt,
interpretation boundary. Bridge: source/target registers and objects,
mapping, preserved, LOST (mandatory), boundaries, grade, reverse map,
commutativity, countermodels, why-gate, next test.
Reverse reconstruction B0-B8. Why-closure by ladder level.
Independent AI review.

### E. Truth-atom extraction
Per paragraph: atomic statements, each tagged mode (11-mode taxonomy)
+ warrant (scripture | mathematical fact | external result |
definition | framework assertion). Ledger admission is rule-based;
API never judges "objectively true."

---

## TAIL LAYERS (fixed order, bottom of every paper)

1. `## Unanswered and not applicable — with reasons`  (deferral rule)
2. `## Audit appendix` (collapsed <details>: scorecard, gates, probes,
   adversarial tests, remediation — machine output verbatim)
3. `## Exact source, untouched` (SHA-256 fenced, never edited)

---

## INLINE MARKER SYSTEM
HTML comments, block-level, above the unit they mark. Types:
@claim @evidence @witness @tangent @delta @rating-change.
Fields: id, mode, grade, rating, topic, provenance, lean, falsifier,
verified, definitive, points-to, from/to/date/reason.

## STANDING RULES (v0.3)
1. Paper is source of truth; index/shelves/Excel/dashboard generated.
2. Six flat OUTBOX lanes + closed vocabularies; tags never folders.
3. Evidence is earned standing (CANDIDATE->AUDITED->APPROVED).
4. Rating caps: API <=+8; +9 human review; +10 Lean receipt only.
5. Truth atoms: API tags mode+warrant; ledger admission rule-based.
6. Heading 1 declaration register; headings 5-14 canon register.
7. evd_balance never fakes 0; unassessed is not zero; machine-only
   assessments inadmissible until a human is in evd_assessors.
8. Negative controls kept, cited, never deleted.
9. Atom guards: analogy never promoted to identity; bridge never
   propagates as proof; model theorem never = empirical validation;
   WHY_OPEN never silently closed; UNKNOWN never replaced by the
   preferred answer.
10. DEFERRAL RULE: every bank question asked every run; unanswered
    ones moved to the bottom section with reasons, never deleted,
    never silently skipped.
11. ATOMICITY RULE: one paper = the complete call set (audit +
    claims/evidence + bank + truth atoms) before the run moves to the
    next paper. Claims/evidence is a separate API call but never a
    separate pass — no paper leaves the run half-processed.
12. PRESENTATION: rendered output follows the API DONE look —
    evidence-sheet block on top (the six, verdict line, claims table,
    evidence ledger, Q0-Q14 callouts, domain checks, audit table),
    CKG 14 headings beneath, tail layers at the bottom.
    Footer on every paper: "POF 2828 · not a probability of truth ·
    human ruling required".

*v0.3 BETA | 2026-09-14 | canonical home: 999_TEMPLATES.
Working copy in EVIDENCE_CHAIN_INTAKE\SCRIPTS is v0.2 — superseded by
this file. Guinea pig: Numbers in God Core Case.*
