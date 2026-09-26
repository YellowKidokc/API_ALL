# CLAIMS LAYER TEMPLATE — v0.3 (ONE PER PAPER, SEPARATE API CALL)
**POF 2828 | 2026-09-14 | canonical copy: 999_TEMPLATES/API_LAYER_v0.3**
*Claims/proofs layer. Own API call under the atomicity rule (Rule 11).
Formatted for Lean Floor staging. Joined to its paper on source_sha256.*

<!-- @template layer=claims version=0.3 -->

---

```yaml
---
# identity — joins to paper on source_sha256
type: claims_layer
parent_paper_id: "{{paper_id}}"
source_sha256: {{source_sha256}}
template_version: CLAIMS_LAYER_V0.3
generated_at: {{ISO_8601_timestamp}}

# audit trail (this call only)
semantic_provider: "{{provider}}"
semantic_model: "{{exact_model_string}}"
call_route: "{{call_N=model (claims+evidence)}}"
usage_tokens: {{prompt_completion_total_cost_object}}
---
```

---

## Claims table

<!-- Every claim from the paper, one row. Register: NATIVE (comes from source domain),
     BRIDGE (created at a domain crossing), DERIVED (follows from other claims).
     Load-bearing = something above it falls if this claim is wrong. -->

|ID|Version|Register|Load-bearing|Depends on|Text|Rating|Awarded by|Falsifier|State|
|---|---|---|---|---|---|---|---|---|---|
|{{CHAPTER-PAPER}}-C001|v1|{{NATIVE / BRIDGE / DERIVED}}|{{yes/no}}|{{dependency_claim_ids}}|{{claim_text}}|0|API|{{what_would_disprove_it}}|{{UNTESTED / SUPPORTED / COUNTERED / GATED}}|
|{{CHAPTER-PAPER}}-C002|v1|{{register}}|{{yes/no}}|{{deps}}|{{text}}|0|API|{{falsifier}}|{{state}}|
<!-- Continue for every claim. No cap. -->

---

## Hidden premises

<!-- Premises the argument requires but never states. These are the silent
     load-bearing assumptions. If one breaks, the claim above it breaks.
     DeepSeek: find ALL of them. One row per hidden premise. -->

|ID|Hidden premise|Required by (claim ID)|If false, what breaks|Blast radius|
|---|---|---|---|---|
|HP-001|{{unstated_assumption}}|{{claim_id}}|{{consequence}}|INERT / LOCAL / STRUCTURAL|
<!-- Continue for every hidden premise. -->

---

## Lean targets

<!-- Claims queued for formal verification. Status tracks the Lean Floor pipeline:
     NOT_ESTABLISHED → TARGET_QUEUED → ENCODING → PROOF_ATTEMPT → RECEIPTED / FAILED -->

|Claim ID|Lean theorem statement|Visible premises to encode|Status|Receipt ID|What passing establishes|
|---|---|---|---|---|---|
|{{claim_id}}|{{lean_theorem_statement}}|{{premises}}|{{NOT_ESTABLISHED / TARGET_QUEUED / ENCODING / PROOF_ATTEMPT / RECEIPTED / FAILED}}|{{receipt_id_or_null}}|{{what_it_proves_in_plain_language}}|
<!-- One row per claim with a formal target. Not every claim needs one. -->

---

## Predictions table

<!-- Micro-predictions: testable, time-bounded, falsifiable consequences of claims.
     This is where predictions get LOGGED — not discussed, logged.
     Each prediction has a deadline and a check method. -->

|Pred ID|Claim ID|Prediction|Deadline|Check method|Outcome|Logged by|Date logged|
|---|---|---|---|---|---|---|---|
|{{CHAPTER-PAPER}}-P001|{{claim_id}}|{{specific_testable_prediction}}|{{date_or_condition}}|{{how_to_check}}|{{PENDING / CONFIRMED / FALSIFIED / EXPIRED}}|{{API / HUMAN:<name>}}|{{date}}|
<!-- Continue for every prediction. Falsified predictions are NEVER deleted. -->

---

## Falsifier registry

<!-- The single most efficient way to kill each claim. Not the same as "strongest
     objection" — this is the minimum experiment, observation, or derivation that
     would force retraction. One row per claim. -->

|Claim ID|Falsifier|Type|Status|If triggered, blast radius|
|---|---|---|---|---|
|{{claim_id}}|{{what_would_kill_it}}|{{empirical / formal / logical / testimonial}}|{{UNTESTED / TESTED_SURVIVED / TRIGGERED}}|INERT / LOCAL / STRUCTURAL|

---

## Bridge / correspondence registry

<!-- Every cross-domain mapping claimed or implied in the paper. The WORD-GATE
     column is the key innovation: what single word or phrase, if it means
     something different in domain A vs domain B, breaks the bridge? -->

|Bridge ID|Source domain|Source object|Target domain|Target object|Mapping type|Preserved|LOST (mandatory)|Word-gate|Grade|Reverse map exists|Countermodel|
|---|---|---|---|---|---|---|---|---|---|---|---|
|{{CHAPTER-PAPER}}-B001|{{domain_A}}|{{object_A}}|{{domain_B}}|{{object_B}}|{{analogy / homomorphism / isomorphism / embedding / metaphor}}|{{what_survives_crossing}}|{{what_is_lost_crossing — MANDATORY, never blank}}|{{the_word_that_breaks_it_if_equivocated}}|{{A-F}}|{{yes/no — if yes, cite it}}|{{known_countermodel_or_none}}|
<!-- Continue for every bridge. LOST column is NEVER blank — if nothing is lost,
     the mapping is an isomorphism and you must say so explicitly and justify it. -->

---

## Explicit boundaries

<!-- What the paper says it is NOT claiming. Load-bearing — these prevent
     scope creep and register mixing. Pulled from the source verbatim. -->

|ID|Boundary statement|Protects (claim IDs)|Source anchor|
|---|---|---|---|
|BND-001|{{boundary_statement}}|{{claim_ids_protected}}|{{verbatim_anchor}}|

---

## Explicit uncertainties

<!-- What the paper says is OPEN, UNRESOLVED, or OWED. These drive next actions
     and prevent false confidence. -->

|ID|Uncertainty|Affects (claim IDs)|Status|Next action|
|---|---|---|---|---|
|U-001|{{uncertainty_statement}}|{{claim_ids}}|{{OPEN / IN_PROGRESS / RESOLVED}}|{{what_to_do_next}}|

---

## Reuse and routing

<!-- Outbox routing signal. The classification that determines which folders
     this paper copies into. -->

| Field | Value |
|---|---|
| Reuse grade | {{A-F}} |
| Reuse score | {{0-100}} |
| Reuse recommendation | {{CANONICAL / PRODUCTION / ARCHIVE_ONLY / RETIRE}} |
| Canonical recommendation | {{ADMIT / HOLD / REJECT}} |
| Primary outbox | {{domain-based folder}} |
| Secondary outbox(es) | {{content-type folder, series folder, etc.}} |

---

## Dependency graph (edges only)

<!-- Machine-readable edge list for the paper's internal dependency structure.
     Direction: A depends_on B means if B falls, A is exposed. -->

|From (claim/bridge)|Relation|To (claim/bridge)|Weight|
|---|---|---|---|
|{{id}}|{{depends_on / supports / contradicts / refines / tests}}|{{id}}|{{CRITICAL / STRONG / WEAK}}|

---

## Layer integrity

<!-- Completeness checks — parser uses these to flag incomplete layers -->

| Check | Value |
|---|---|
| Total claims | {{count}} |
| Claims with falsifiers | {{count}} |
| Claims missing falsifiers | {{list or "none"}} |
| Hidden premises found | {{count}} |
| Lean targets queued | {{count}} |
| Predictions logged | {{count}} |
| Bridges registered | {{count}} |
| Bridges with blank LOST column | {{must be 0 — if not, list them}} |
| Bridges with blank word-gate | {{list or "none"}} |
| Boundaries registered | {{count}} |
| Uncertainties registered | {{count}} |
| Uncertainties still OPEN | {{count}} |
| Reuse grade | {{A-F}} |
| Routing: primary outbox | {{folder}} |

---

_POF 2828 · not a probability of truth · human ruling required_

<!-- @template layer=claims version=0.3 end -->
