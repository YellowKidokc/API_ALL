---
title: "Claim Atom Expansion — AI Intake Template v1.1"
template_kind: "candidate_atom_opening_packet"
schema_reference: "_schema/atom_envelope_v1_1.schema.json"
canon_reference: "__1_Version_Last_Version/THE_CLAIM_ATOM_EXPANSION_CANON_v1_1_FOUR_OBJECT_LAYERS_FULL.md"
status: "CANDIDATE_DRAFT — NOT VALIDATED — NOT ADMITTED"
authority: "Template only. It creates no admission event and changes no controlling record."
---

# Claim Atom Expansion — AI Intake Template v1.1

> **Use:** Open one independently reviewable object. Do not bundle assertions merely because they occur in one paragraph.

> **Status:** `CANDIDATE_DRAFT — NOT VALIDATED — NOT ADMITTED`

## AI operating rules

1. Preserve the supplied source before analysis. Quote its exact span; do not silently rewrite it.
2. Start with the nondiscriminatory discovery questions. Do not select a domain, truth grade, or theological conclusion before the structure is exposed.
3. Choose exactly one `object_type`: `CLAIM`, `EVIDENCE`, `PROOF`, or `PROCESS`.
4. Choose one primary register only when the object is a claim. A bridge is a claim with bridge anatomy; it never transfers proof across domains.
5. Start every candidate as a complete copy of this template. Fill every supported applicable field; do not invent citations, dates, measurements, theorem receipts, dependencies, or outcomes.
6. Once the object type and register are selected, delete each whole anatomy section that is not applicable. This produces a clean import packet rather than a packet with competing blank alternatives.
7. For an applicable field that matters but is unresolved, use `OPEN`, `UNKNOWN`, or `NOT_APPLICABLE`. Leave a non-load-bearing optional field blank.
8. The importer drops remaining blank values. It preserves declared `OPEN`, `UNKNOWN`, and `NOT_APPLICABLE` values.
9. A formal proof checks only its encoded proposition under declared premises. It does not establish a physical, historical, or theological interpretation without a distinct bridge.
10. AI may propose and flag gaps. Only a separate signed human admission event can move a candidate into the admitted graph.

---

## 0. Intake control — required for every object

```yaml
identity:
  id: ""                         # immutable versioned object ID; leave blank only before assignment
  object_type: ""                # CLAIM | EVIDENCE | PROOF | PROCESS
  parent_id: ""
  atom_family: ""
  layer: ""                      # registry address, e.g. L9
  component: ""                  # registry address, e.g. C1
  version: "0.1.0-candidate"
  content_hash: ""               # assigned after normalized content is frozen

provenance:
  raw_statement: ""              # exact source wording; preserve punctuation where possible
  source_uri: ""
  source_span: ""                # heading, page, paragraph, timestamp, or line span
  source_hash: ""
  author_or_witness: ""
  date_received: ""
  ai_contribution_declared: ""   # YES | NO
  ai_contribution_role: ""       # extraction | classification proposal | drafting | review | other

admission:
  graph: "candidate"
  human_ruling: "pending"
  ruling_actor: ""
  ruling_date: ""
  rationale: ""
```

---

## 1. Nondiscriminatory structural discovery — do before classification

Answer from the source itself. Do not force every prompt to have an answer.

```yaml
discovery:
  referent: ""                   # What, if anything, is being discussed?
  identities: []                  # What remains the same across the account?
  distinctions: []                # What is distinguished from what?
  relations: []                   # What depends on, affects, maps to, or excludes what?
  operations: []                  # What happens, transforms, measures, compares, or infers?
  dependencies: []                # What must already hold for this to be meaningful?
  constraints: []                 # What cannot vary without breaking the account?
  invariants: []                  # What is claimed to remain preserved?
  collapse_conditions: []         # What would make the structure fail or become undefined?
  consequences: []                # What follows if the structure holds?
  representation_ladder: []       # plain language -> notation -> model -> test, where supplied
  formalization_boundary: ""      # What the present material does not formalize or establish
```

### Blind discovery questions

- What is the smallest assertion here that could be false while the neighboring assertions remain meaningful?
- What identities, distinctions, relations, operations, constraints, and invariants appear before any domain label is chosen?
- What is explicitly stated, what is inferred, and what is merely named?
- What would collapse if the statement were denied?
- Which terms have multiple possible meanings that must be separated?

---

## 2. Classification and burden — complete after discovery

```yaml
classification:
  emergent_labels: []             # outputs of analysis only
  inherited_labels: []            # labels already present in the source
  reconciliation_status: "OPEN"   # MATCH | AMEND | SPLIT | HOLD_OPEN | CONFLICT
  classification_rationale: ""

import_selection:
  retained_sections: []           # sections kept after classification
  removed_as_not_applicable: []   # whole anatomy blocks intentionally deleted

axes:
  lifecycle_state: ""            # INTAKE | OPENING | CANDIDATE | REVIEW | FROZEN | ADMITTED | etc.
  proof_class: ""                # see proof-class selection below
  register: ""                   # HISTORY | PHYSICS | MATHEMATICS | THEOLOGY | BRIDGE | etc.
  ic_grade: ""                   # only for a bridge; otherwise NOT_APPLICABLE
  why_outcome: ""                # WHY_CLOSED | WHY_OPEN | NOT_APPLICABLE
```

### Proof-class selection

Choose only one where applicable:

`DEFINITION | AXIOM | THEOREM | DERIVED | CONDITIONAL | MODEL | EMPIRICAL | HISTORICAL | THEOLOGICAL_DECLARATION | STRUCTURAL_ANALOGY | SPECIFICATION_ONLY | INFORMAL_ARGUMENT | NOT_ATTEMPTED | NOT_APPLICABLE`

---

## 3. Truth space — required for a CLAIM; useful for other objects when applicable

```yaml
claim:
  statement_technical: ""
  statement_plain: ""
  scope: ""
  quantifiers: []
  boundary_conditions: []
  identity_conditions: []
  exact_negations: []

truth_space:
  if_true: []
  if_false: []
  false_worlds: []
  countermodels: []
  defeat_conditions: []
  next_discriminating_test: ""

reverse_reconstruction:
  candidate_grounds: []
  inference_steps: []
  unique_recovery: "OPEN"        # YES | NO | UNDERDETERMINED | OPEN
  hidden_borrowing_risks: []
```

---

## 4. Register-native claim anatomy — retain one applicable section

> After classification, keep the one matching register anatomy below and delete the other whole `*_anatomy` blocks from the candidate copy. A claim may not use a blank alternate anatomy as a hidden second classification.

### 4A. History — transmission chain

```yaml
history_anatomy:
  event: ""
  possible_observers: []
  witnesses: []
  testimonies: []
  transmission: []
  documents: []
  preservation: []
  corroboration: []
  interpretation: ""
  present_claim: ""
  limitations: []
```

### 4B. Physics — measurement anatomy

```yaml
physics_anatomy:
  quantity: ""
  units_and_scale: ""
  dynamics: ""
  protocol: ""
  instrument: ""
  data: []
  controls: []
  analysis_and_fit: ""
  physical_claim: ""
  uncertainty: ""
  replication_status: ""
```

### 4C. Mathematics / formal methods — formal anatomy

```yaml
mathematics_anatomy:
  definitions: []
  axioms_used: []
  inference_rules: []
  lemmas: []
  derivation: []
  theorem_statement: ""
  formal_receipt: ""
  what_checked: []
  what_not_proved: []
  interpretation_boundary: ""
```

### 4D. Theology — proclamation anatomy

```yaml
theology_anatomy:
  sources: []
  textual_witness: []
  witness_tradition: []
  proclamation: ""
  theological_register: ""
  confession_class: ""
  scope: ""
  relation_to_other_claims: []
  doctrinal_alternatives: []
```

### 4E. Bridge — mapping anatomy

```yaml
bridge_anatomy:
  source_register: ""
  target_register: ""
  source_object_ids: []
  target_object_ids: []
  mapping: ""
  forward_map: ""
  reverse_map: ""                # state ABSENT if no reverse map is claimed
  preserved_structure: []
  lost_structure: []              # mandatory whenever bridge_anatomy is used
  boundary_conditions: []
  ic_grade_justification: ""
  commutativity_tests: []
  translation_tests: []
  permutation_tests: []
  rivals: []
  countermodels: []
  next_test: ""
```

> **Bridge firewall:** `lost_structure` must never be empty. A bridge records a mapping, not a proof transfer or identity claim, unless an actual two-way isomorphism has been demonstrated and stored.

---

## 5. Object extension — retain exactly one of the four sections

> After classification, keep the one matching object extension below and delete the other three whole `*_extension` blocks from the candidate copy. The shared evidence and proof ledger in Section 6 may still contain references, but it is not a second object type.

### 5A. CLAIM extension

```yaml
claim_extension:
  register_anatomy_reference: "" # e.g. 4B physics_anatomy
  truth_conditions: []
  exact_negations: []
  independently_falsifiable_components: []
```

### 5B. EVIDENCE extension

```yaml
evidence_extension:
  source: ""
  provenance_and_custody: ""
  protocol: ""
  conditions: []
  raw_record: ""
  derived_artifacts: []
  controls: []
  independence_map: []
  discrimination_statement: ""
  limitations: []
  edge_states: []                 # support/challenge only via typed edge
```

### 5C. PROOF extension

```yaml
proof_extension:
  premises: []
  inference_rules: []
  derivation_steps: []
  conclusion: ""
  assumption_register: []
  receipt: ""
  what_checked: []
  what_not_proved: []
  interpretation_boundary: ""
  countermodels_as_output: []
```

### 5D. PROCESS extension

```yaml
process_extension:
  purpose: ""
  inputs: []
  preconditions: []
  steps: []
  decision_points: []
  outputs: []
  discriminating_power: ""
  failure_modes: []
  version: ""
  run_receipt: ""
  recursive_self_application: ""
```

---

## 6. Evidence, proof, and convergence ledger — shared fields

```yaml
evidence:
  support: []                     # typed evidence-edge IDs, not prose claims
  challenge: []                   # typed evidence-edge IDs, not prose claims
  negative_controls: []
  independent_inputs: []
  limitations: []

proof:
  specification: ""
  formal_statement: ""
  axioms_used: []
  definitions_used: []
  lemmas_used: []
  receipt: ""
  what_checked: []
  what_not_proved: []

convergence:
  compared_atom_ids: []
  anonymized_signatures: []
  candidate_mapping: []
  rivals: []
  verdict: "OPEN"

why_closure:
  ladder_levels: []
  explanation_types: []
  non_restatement_pass: "OPEN"
  outcome: "WHY_OPEN"
  closure_level: ""
  next_discriminating_test: ""
```

---

## 7. Dependencies, edges, corrections, and projections

```yaml
dependencies:
  depends_on: []
  supports: []
  challenges: []
  expands: []
  bridges_to: []
  supersedes: []

typed_edges:
  - edge_id: ""
    edge_type: ""                 # DEPENDS_ON | SUPPORTS | CHALLENGES | BRIDGES_TO | etc.
    source_object_id: ""
    target_object_id: ""
    target_version: ""
    warrant: ""
    conditions: []
    ruling: "OPEN"
    receipt: ""

root_pass:
  root_id: ""
  grounding_verdict: "OPEN"
  added_premises: []

gauntlet:
  countermodels: []
  kill_conditions: []
  preregistration_receipt: ""
  execution_receipts: []

corrections: []
projections: []
```

---

## 8. AI completion report — required before handoff

```yaml
ai_completion_report:
  proposed_object_count: 1
  source_preserved: ""
  source_hash_present: ""
  independently_failing_components_separated: ""
  selected_object_type: ""
  selected_register: ""
  required_native_fields_complete: ""
  exact_negations_present: ""
  countermodels_present: ""
  evidence_proof_boundary_explicit: ""
  bridge_firewall_status: "NOT_APPLICABLE"
  unresolved_fields: []
  discovery_status: ""           # DISCOVERY_INCOMPLETE | STRUCTURALLY_OPENED
  importable_sections: []         # only sections with real nonblank content
  removed_as_not_applicable: []   # whole anatomy/extension blocks deleted before import
  do_not_import_sections: []      # remaining blank or unsupported shared sections
  human_review_questions: []
```

## 9. Human review record — do not prefill

```yaml
human_review:
  decision: "PENDING"             # APPROVE_CANDIDATE | REVISE | SPLIT | HOLD_OPEN | WITHDRAW | REJECT
  reviewer: ""
  date: ""
  rationale: ""
  signed_admission_event: ""      # remains blank unless a distinct admission event exists
```

---

## Final validation checklist

- [ ] The original wording, source, span, and source hash are preserved.
- [ ] Exactly one object type extension remains; all competing extensions were deleted.
- [ ] The selected register has its matching native anatomy, if this is a claim; competing anatomies were deleted.
- [ ] No classification, citation, proof receipt, measurement, or conclusion was guessed.
- [ ] Exact negations, countermodels, and a defeat condition are present where applicable.
- [ ] Every bridge names preserved structure, lost structure, boundary conditions, and a next test.
- [ ] `WHY_OPEN`, `UNKNOWN`, and `OPEN` have not been converted into closure.
- [ ] Evidence bearing is represented by typed edges, never used as an unscoped truth label.
- [ ] No candidate is represented as admitted, verified, kernel-verified, or canonized without its distinct receipt.
- [ ] Blank optional sections are excluded from import; declared nulls remain.

---

`CANDIDATE_DRAFT — NOT VALIDATED — NOT ADMITTED`

