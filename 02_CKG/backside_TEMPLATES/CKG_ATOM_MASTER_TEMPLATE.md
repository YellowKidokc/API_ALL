---
record_version: CKG_ATOM_RECORD_V3.2_UNIFIED
template_status: REVIEW_DRAFT
title: null
paper_uuid: null
paper_number: null
readable_address: null
record_revision: null
legacy_ids: []
legacy_template_version: null
source_document_uuid: null
source_version_uuid: null
source_file: null
source_sha256: null
original_title: null
project: null
subject: null
collection: null
content_type: null
reader_category: null
domains: []
series: {id: null, name: null, position: null}
display_keywords: []
keywords: []
topic_keys: []
framework_keys: []
classification_vocabulary: {name: null, version: null}
inherited_classification: null
proposed_classification: null
classification_reconciliation: NOT_RUN
governing_question: null
one_sentence_finding: null
lifecycle_state: RAW
review_status: NOT_REVIEWED
evidence_assessment_status: NOT_ASSESSED
formal_build_status: NOT_RUN
admission:
  graph: candidate
  human_ruling: pending
  ruling_actor: null
  ruling_date: null
  rationale: null
stations:
  requested: []
  completed: []
  failed: []
  pending: []
  cancelled: []
  enabled:
    ckg: true
    atoms: false
    axiom_nodes: false
    coherence_score: false
    fruits: false
    lean4: false
    master_equation: false
    paper_grader: false
    stories: false
grading:
  status: NOT_RUN
  rubric_version: null
  section_results: []
  score_total: null
  score_ceiling: null
  coherence: null
  evidence_balance: null
  evidence_coverage: null
  legacy_scores: null
identity_registry_ref: null
atom_map_ref: null
json_package_ref: null
publication_receipt_ref: null
run_uuid: null
captured_at: null
processed_at: null
provider: null
model: null
call_routes: []
usage_tokens: null
address_spec_version: ADDRESS_SPEC_V1.0
curator_pass_version: CURATOR_PASS_V1.0
registry_pattern_version: DEFINITION_REGISTRY_V1.0
integrity:
  source_hash_verified: null
  yaml_keys_unique: null
  required_sections_complete: null
  source_spans_verified: null
  references_resolve: null
  json_schema_valid: null
  markdown_json_agree: null
  truncation_detected: null
---

<!-- BLANK TEMPLATE: no paper has been assessed. Null means not yet supplied; [] is an unpopulated collection, not a finding that none exist. -->
<!-- Python supplies IDs, hashes, timestamps, execution facts, arithmetic and validated indexes. AI proposes content and classifications. Only an authorized human ruling admits objects. -->
<!-- Preserve all CKG sections. Mark applicability, completion, missing information and reasons rather than silently omitting work. No automatic API/human/Lean score ladder. -->
<!-- Each meaningful section/object has a permanent UUID registered by Python. Human addresses are aliases, e.g. CKG/P000123/S02/DEFINITIONS/DE003/MATHEMATICAL. Fields use parent UUID + field path. Do not turn this hierarchy into nested physical folders. -->
<!-- Renderers wrap sections in paired PAPER_SECTION:<paper_uuid>:<section_key>:BEGIN/END markers; reject delimiter collisions. Duplicate presentations link to one object identity/version. -->

# {{DESCRIPTIVE PAPER TITLE}}

**Part of:** {{project}} · **Subject:** {{subject}} · **Domain:** {{domains}}  
**Document purpose:** {{content_type}} · **Series:** {{series and position}}  
**Keywords:** {{up to three display keywords}}  
**Paper ID:** {{readable address}} · **UUID:** {{paper_uuid}} · **Version:** {{record_revision}}

[Overview](#overview) · [Atom Map](#atom-map) · [Argument](#argument) · [Mathematics](#mathematics) · [Original](#original) · [Evidence and proof](#evidence-proof) · [Definitions](#definitions-library) · [Keywords](#keyword-index)

<a id="overview"></a>

> [!important] 📜 The Axiomatic Contract & Epistemic Preamble
> **What does it mean that “God Is” is an axiom?**
> In Theophysics, “God Is” is an openly declared starting premise, A₀. God's self-existence is part of the theological foundation; it is not a property inferred merely from calling a statement an axiom.
>
> 1. **The Starting Ground:** We take the Trinitarian God and His self-revealed character as the theological foundation of this framework. Additional interpretive and mathematical premises are declared separately.
> 2. **The Consequential Consistency Test:** We derive consequences from stated premises and test their logical consistency and, where applicable, their agreement with observation. Physics alone is not presented as proving the starting theological premise.
> 3. **The Reader Contract:** If a proposed consequence conflicts with formal reasoning or observation, we identify the affected claim, examine its premises and mapping, and record any correction or unresolved issue openly.
>
> **Application to this paper:** {{which premises are used; distinguish the author's premises from the reviewing framework. For unrelated or imported documents, state that this preamble describes the review framework only.}}

> [!success] The Six
>
> | Field | Reading |
> |---|---|
> | Claim | {{defensibly scoped finding; links to component claims}} |
> | Domain | {{domains; percentages only if a defined method supports them}} |
> | Physical event | {{observable event, proposed event, or NOT_APPLICABLE with reason}} |
> | Bridge | {{mapping, preserved/lost structure, proposed grade, WHY state; or NOT_APPLICABLE}} |
> | Unique power / proposed contribution | {{contribution and strongest rival comparison; uniqueness unestablished unless tested}} |
> | Have / need / breaks if | **Have:** {{records and scope}} **Need:** {{open work}} **Breaks if:** {{claim-specific defeat conditions}} |

> [!important] Verdict
> {{What the review establishes, what remains proposed, what is overstated, the central conclusion's dependencies, and the limits of the checks actually performed. If not assessed, say NOT_ASSESSED.}}

## Proof review at a glance — when applicable

| Check | Result |
|---|---|
| Exact conclusion assessed | {{statement and claim version}} |
| Work performed | {{source review / derivation inspection / actual build / other}} |
| Build and receipt | {{NOT_RUN or executed result with receipt link}} |
| Necessary premises and custom axioms | {{list or UNKNOWN}} |
| What was established | {{bounded finding}} |
| What was not established | {{interpretation and verification limits}} |

## THE AUDIT

### What held
{{Object IDs, scope, checks, evidence and assumptions under which each finding held.}}

### What broke
{{Exact defect, test/receipt, affected conclusion, load-bearing paths, and known unaffected claims. Unchecked suspicions are not recorded as failures.}}

### What is overstated → defensible wording

| Object | Exact original wording and span | Proposed correction | Impact and dependency path | Review status |
|---|---|---|---|---|
| {{ID}} | {{quote}} | {{proposal}} | {{INERT / LOCAL / STRUCTURAL / UNASSESSED, with reason}} | {{status}} |

### What remains untested or disputed
{{Unresolved comparisons, competing versions, missing sources and receipts.}}

### Audit inventory — what this paper contains

**Inventory status:** {{NOT_COMPUTED / PARTIAL / COMPLETE}} · **Source coverage:** {{examined / expected units; unresolved units}}  
**Computed by:** {{Python version / run UUID / timestamp}} · **Record set:** {{paper version and linked object versions}}

| Record kind | Unique records | Assessed | Pending assessment | Disputed or unresolved | Detail index |
|---|---|---|---|---|---|
| Claims | — | — | — | — | {{claim IDs}} |
| Evidence items | — | — | — | — | {{evidence IDs}} |
| Proof records | — | — | — | — | {{proof IDs}} |
| Arguments | — | — | — | — | {{argument IDs}} |
| Definitions | — | — | — | — | {{definition IDs}} |
| Equations / mathematical objects | — | — | — | — | {{math IDs}} |
| Bridges / mappings | — | — | — | — | {{mapping IDs}} |
| Isomorphism claims | — | — | — | — | {{subset of claim IDs}} |
| Tests / predictions | — | — | — | — | {{test IDs}} |
| Protocols / processes | — | — | — | — | {{process IDs}} |

**Counting rule:** Count unique registered identities at the selected paper version, not mentions, presentation copies or API repetitions. Multiple historical versions are reported separately. Categories can overlap: an isomorphism claim is already a claim, and a definition may also have an Atom representation. Do not sum these rows into an undeduplicated grand total. Assessed/pending are mutually exclusive only under a declared review rule; disputed/unresolved is an independent flag and can overlap either. A count of zero requires a completed inventory; unknown counts remain blank.

### Argument and contribution provenance

| Origin category | Arguments | Claims | Derivations / proofs | Source references and rationale |
|---|---|---|---|---|
| Author-proposed original contribution | — | — | — | {{attribution; novelty not independently established}} |
| Author-original; independently convergent with historical witness | — | — | — | {{independent-origin assertion and verification status; witness citation; no borrowing inferred}} |
| Attributed prior work / established formulation | — | — | — | {{exact source and inspection status}} |
| Adaptation or extension of prior work | — | — | — | {{what changed; source links}} |
| Synthesis of multiple sources | — | — | — | {{contributing sources}} |
| AI-generated proposal added during review | — | — | — | {{run and role; not attributed to the original author}} |
| Mixed provenance | — | — | — | {{component-level attribution}} |
| Unknown or unresolved origin | — | — | — | {{missing attribution}} |

{{Assign one primary origin category per record for this tally; retain detailed contributor roles separately. Originality is separate from validity, warrant and admission. “Original” means attributed/proposed origin unless a documented novelty search supports more.}}

### Status and warrant breakdowns

- **Claims:** {{assessment counts; supporting/opposing/unassessed relationships; load-bearing versus supplementary roles; declared assumptions versus proposed deductions. These are separate axes, not one combined grade.}}
- **Evidence:** {{supporting, opposing, testing and unassessed edge counts, clearly distinguished from unique evidence-item counts; independent families; inspected versus citation-only records; stale links.}}
- **Proof:** {{specification-only, source-reviewed, build-not-run, passed, failed, timed-out and toolchain-mismatch records; external results separately; axiom/sorry/trust findings. Build result is not substantive theorem adequacy.}}
- **Arguments:** {{fully traced versus missing steps; checked versus unchecked inference; strong/weak/unassessed only under a named rubric with reasons; outstanding objections and conclusion dependencies.}}
- **Bridges:** {{proposed versus assessed mappings; preservation/loss recorded or missing; isomorphism obligations discharged or open; linked proof receipts.}}

### Completeness and reconciliation checks

| Check | Result / missing IDs |
|---|---|
| Every Atom Map row resolves to a UUID/version | {{ }} |
| Every argument conclusion links to a claim | {{ }} |
| Every evidence relationship names a claim/version | {{ }} |
| Every proof names its exact conclusion and assumptions | {{ }} |
| Every originality label has attribution or an explicit unknown | {{ }} |
| Repeated records and classified copies excluded from totals | {{ }} |
| Inventory agrees with JSON and master index | {{ }} |
| Unmapped source passages and omitted objects are reported | {{ }} |

**Audit boundary:** These totals show what has been inventoried and checked. More claims, citations or proofs do not by themselves make the paper stronger or establish its truth. Detailed results remain in A8; this table is their readable summary.

<a id="atom-map"></a>

## ATOM MAP

| ID / link | Type | Register | Statement or record description | Warrant and boundary | IC / WHY | Audit | Rests on |
|---|---|---|---|---|---|---|---|
| {{short ID linked to UUID/version}} | {{CLAIM / EVIDENCE / PROOF / PROCESS}} | {{register}} | {{standalone wording}} | {{actual support or unknown}} | {{separate values and proposed/ruled status}} | {{finding or NOT_ASSESSED}} | {{typed versioned links}} |

**Reading the map:** {{central conclusion, load-bearing paths, weakest unresolved link and affected conclusions. No incoming edges alone does not establish that a component is unimportant.}}

**Coverage:** {{source units examined; mapped units; unmapped units and reasons; extraction pass and completeness status.}}

## At a glance — expanded explanation
{{Accessible connected explanation of the paper, its framework, main argument, result and limitations. Preserve assumptions when simplifying.}}

## Build next

| Object | Missing work | Next discriminating action | Dependency / priority | Completion criterion |
|---|---|---|---|---|
| {{ID}} | {{gap}} | {{action}} | {{dependency}} | {{observable criterion}} |

# FULL CKG EXPLANATION

## S01 · Classification & Routing
{{Narrative explanation of the paper's subject, purpose and placement.}}

| Field | Record |
|---|---|
| Project / subject / domains | {{values}} |
| Document purpose / reader category | {{values}} |
| Collection / series / order | {{values}} |
| Keywords / framework references | {{values}} |
| Inherited classification | {{original labels and origin}} |
| Proposed classification | {{suggestions and reasons}} |
| Vocabulary and reconciliation | {{version; disagreements; ruling}} |
| Stations selected | ckg, atoms, axiom_nodes, coherence_score, fruits, lean4, master_equation, paper_grader, stories — applicability, reason, status |

## S02 · Claim Definition

### Central finding and independently assessable components
{{Exact central assertion; distinguish paper summary from individual atom claims.}}

### Claim inventory
| Claim ID | Exact statement / source span | Plain rendering | Assertion mode | Scope / quantifiers | Status |
|---|---|---|---|---|---|
| {{ID}} | {{text and span}} | {{rendering}} | {{asserted / used / quoted / modeled / generated / other}} | {{limits}} | {{status}} |

### Definitions used in this paper
| Definition ID | Term | Plain meaning | Mathematical meaning | Domain / context | Source / version | Conflicts |
|---|---|---|---|---|---|---|
| {{ID}} | {{term}} | {{meaning}} | {{expression or N/A}} | {{context}} | {{reference}} | {{open issues}} |

### Preflight Q15–Q18
- **Q15 — Smallest reviewable unit:** {{unit and decomposition reason}}
- **Q16 — Assertion mode:** {{asserted, used, quoted, modeled, rendered, generated, mixed}}
- **Q17 — Epistemic level:** {{object, model, meta, method, language, workflow, projection}}
- **Q18 — Domain-ablated invariant:** {{what remains without domain labels, or N/A with reason}}

### Open the question — Q0–Q14
{{Paper-level orientation below; each opened component receives its own version-linked answers in A1.}}

| Question | Answer / unresolved reason |
|---|---|
| Q0 Exact expression | {{ }} |
| Q1 Referent | {{ }} |
| Q2 Identity and distinction | {{ }} |
| Q3 Dependency floor | {{ }} |
| Q4 Variation and invariance | {{ }} |
| Q5 Capabilities and operations | {{ }} |
| Q6 Transitions | {{ }} |
| Q7 Constraints | {{ }} |
| Q8 Consequences and licenses | {{ }} |
| Q9 Representation ladder | {{ }} |
| Q10 Preservation and loss | {{ }} |
| Q11 If true | {{ }} |
| Q12 If false / exact negation / rivals | {{ }} |
| Q13 Discriminating checks | {{ }} |
| Q14 Emergent role | {{ }} |

<a id="argument"></a>

## S03 · Argument Structure & Four-Dimensional Review

### System or model
{{Objects, operations, assumptions and intended explanation.}}

### Primary argument
| Step ID | Premise / inference / conclusion | Input IDs | Inference license | Provenance | Status |
|---|---|---|---|---|---|
| {{ID}} | {{statement}} | {{references}} | {{rule or open gap}} | {{original / source-based / proposed}} | {{status}} |

### Supplementary and rival arguments
{{Each argument with its own conclusion, premises, steps and dependency links.}}

### Historical witnesses and prior-work relationships
{{Who said what, exact source, relevance and interpretation boundary; attribution and inspection status.}}

### Four-dimensional review
- **Formal / mathematical:** {{derivation and definition burdens}}
- **Physical / empirical:** {{observable claims and tests}}
- **Philosophical:** {{inference and metaphysical premises}}
- **Theological / exegetical:** {{texts, doctrine, interpretive premises and scope}}

### Hidden premises
| ID | Premise | Required by | If false | Affected conclusions |
|---|---|---|---|---|
| {{ID}} | {{premise}} | {{links}} | {{consequence}} | {{paths}} |

### Argument strengthening and alternatives
| Weak step | Why unresolved | Proposed repair | Added assumptions | Source / test | Status |
|---|---|---|---|---|---|
| {{ID}} | {{reason}} | {{proposal}} | {{premises}} | {{reference}} | {{status}} |

### Extracted truth predicates
| ID | Exact predicate / span | Source role | Modality | Formal expression | Warrant |
|---|---|---|---|---|---|
| {{ID}} | {{text}} | {{role}} | {{modality}} | {{expression or pending}} | {{reference}} |

### Terms, plain-language translation and structural map
{{Explain technical terms; include a diagram only when grounded in recorded dependencies.}}

## S04 · Evidence & Support

### Claim-by-claim evidence coverage
| Claim/version | Supporting records | Opposing records | Missing checks | Independence | Assessment status |
|---|---|---|---|---|---|
| {{ID}} | {{IDs}} | {{IDs}} | {{gaps}} | {{clusters}} | {{status}} |

### Evidence ledger
| Evidence ID | Source / finding | Claim/version | Direction | Lane | Family / cluster | Discrimination | Limitations |
|---|---|---|---|---|---|---|---|
| {{ID}} | {{record}} | {{target}} | {{supports / contradicts / falsifies / tests / unassessed}} | {{native / bridge / identification}} | {{independence}} | {{rival comparison}} | {{limits}} |

### Warrant control
{{Exact claim, evidence, proof/test, counterevidence, kill condition, assumptions, coverage and independence. Distinguish citations from inspected evidence.}}

### Dynamics
{{Coherence, degradation, measurement, thresholds, asymmetry, restoration and counterexamples—only where applicable, with definitions.}}

### Best evidence and sources
{{Primary records/formal results; secondary interpretation; analogies/bridges; verified citation locations.}}

### Coherence assessment
{{Reasoned assessment; quantitative score only if the optional versioned grader ran.}}

## S05 · Objections & Survival

### Strongest objection and negative controls
{{Objection; response; negative control; executed outcome or NOT_RUN.}}

### Countermodels and rival explanations
| Rival ID | Formulation | Same observations explained? | Discriminating test | Outcome / status |
|---|---|---|---|---|
| {{ID}} | {{strong formulation}} | {{assessment}} | {{test}} | {{status}} |

### What survives
{{Bounded findings after the checks actually performed; retain unresolved objections.}}

### Independent review
{{Reviewer/model, sources seen, preserved first assessment, subsequent comparison, shared-source dependence and disagreements.}}

### Six-Door Explanatory Lens
- **Human:** {{ }}
- **Metaphysical:** {{ }}
- **Theological:** {{ }}
- **Scientific:** {{ }}
- **Formal:** {{ }}
- **External reference:** {{ }}

## S06 · Boundaries & Honesty

### What this does not establish
{{Interpretation, scope and verification limits.}}

### Explicit boundaries
| ID | Boundary | Protects which claim | Source / rationale |
|---|---|---|---|
| {{ID}} | {{boundary}} | {{IDs}} | {{basis}} |

### Corrections and revisions
{{Link to correction ledger; distinguish proposals from applied and human-ruled changes.}}

### Self-assessment and blind spots
{{Argument strength, evidence quality, originality, bridge integrity, formal readiness, clarity, scope honesty and defeat-condition clarity. Reasons first; scores optional.}}

### Implications by register
{{Formal, philosophical, empirical, semantic and theological implications, each with premises and limits.}}

<a id="mathematics"></a>

## S07 · Mathematics & Formal Work

### Equation and mathematical-object inventory
| Math ID | Exact expression | Plain meaning | Types / domain / codomain | Units | Premises / boundary conditions | Status |
|---|---|---|---|---|---|---|
| {{ID}} | {{expression}} | {{meaning}} | {{types}} | {{units or N/A}} | {{conditions}} | {{proposed / defined / derived / checked / open}} |

### Symbol dictionary
| Symbol ID | Symbol | Definition | Scope | Units / type | Alternative uses | Definition link |
|---|---|---|---|---|---|---|
| {{ID}} | {{symbol}} | {{meaning}} | {{scope}} | {{type}} | {{ambiguities}} | {{ID/version}} |

### Derivations and mathematical checks
{{Stepwise derivation; units; limiting cases; normalization; existence/uniqueness; assumptions; applicable checks and outcomes.}}

### Lean4 / Z3 / other formal checks
{{Exact proposition, visible premises, declaration, toolchain, execution status, linked receipt, meaning and limitations. No receipt is invented from an API explanation.}}

### Formal-work discovery and retrieval plan
Lack of an attached proof is not evidence that no proof exists in the corpus. When the actual paper supplies enough content, identify what existing formal work could help assess its argument. Separate source-stated propositions from analyst-proposed formalizations. Do not invent a theorem from a missing-document routing question.

| Target claim / argument step | Proposed formal question | Required definitions and premises | Search terms / symbols / aliases | Expected matching result | What that result would not establish |
|---|---|---|---|---|---|
| {{ID/version}} | {{precise proposition or formalization gap}} | {{definitions and conditions}} | {{conceptual and mathematical terms}} | {{lemma, counterexample, model, definition or build receipt}} | {{boundary}} |

**Retrieval state:** {{NOT_SEARCHED / SEARCHED_NO_MATCH / CANDIDATES_FOUND / MATCH_REVIEWED, with scope and reason}}. Record searched roots/index version, date and queries only when a search actually runs. Each candidate carries a path, declaration name, source hash, statement, assumptions, receipt availability and correspondence assessment. Similar names are retrieval leads, not proof matches. A matched proof is linked to the exact claim/version; a successful build does not establish additional empirical or theological premises. Distinguish NOT_SUPPLIED from NOT_FOUND_IN_SEARCHED_SCOPE.

### Domain-specific checks
{{Physics; history/testimony; theology; philosophy/metaphysics; mathematics/formal; cross-domain bridge. Include reverse reconstruction B0–B8 and WHY closure by level where applicable. Exclusions carry reasons.}}

## S08 · Bridges, Mappings & Isomorphism Claims

### Bridge registry
| Bridge ID | Source structure | Target structure | Mapping | Preserved | LOST | Proposed IC grade | Reverse map | Countermodels |
|---|---|---|---|---|---|---|---|---|
| {{ID}} | {{objects/version}} | {{objects/version}} | {{function/relation}} | {{properties}} | {{loss/boundary}} | {{grade and basis}} | {{map or absence}} | {{IDs}} |

### Mapping obligations
{{Definitions of both structures; domain/codomain; preservation; injectivity/surjectivity/inverse where claimed; composition/commutativity; exact proof obligations; tested examples and counterexamples. Separate the mapping record, the claim that it is isomorphic, and the proof of that claim.}}

### Bridge originality and prior art
{{Existing mappings, exact proposed contribution, textual witnesses, limits of witness as formal or empirical support.}}

### Label removal, permutation, rival and holdout checks
{{Procedure, preregistration when available, result/NOT_RUN and limitations.}}

### WHY closure
{{Outcome, level, non-restatement test, explanation, open burden and next test. WHY analysis is not restricted to bridges.}}

## S09 · Falsifiability, Predictions & Open Work

### Defeat-condition registry
| ID | Target claim/version | Exact negation / defeat condition | Preconditions | Test | Result / status | Impact |
|---|---|---|---|---|---|---|
| {{ID}} | {{target}} | {{condition}} | {{scope}} | {{method}} | {{status}} | {{paths}} |

### Prediction registry
| ID | Claim | Prediction | Date registered | Deadline | Method | Outcome | Receipt |
|---|---|---|---|---|---|---|---|
| {{ID}} | {{target}} | {{prediction}} | {{date}} | {{date/N/A}} | {{method}} | {{NOT_RUN or result}} | {{link}} |

### Uncertainty and next actions
{{Unknowns, competing candidates, what has failed, next discriminating test, tangents and affected claims.}}

## S10 · Audit & Provenance

### Review summary
| What held | What broke | What is overstated | Defensible formulation | Impact |
|---|---|---|---|---|
| {{ }} | {{ }} | {{ }} | {{ }} | {{ }} |

### Inter-paper dependencies and recommended relationships
{{Typed links to exact versions; distinguish inherited, AI-proposed, machine-checked and human-ruled relationships.}}

### Coverage and integrity summary
{{Source units processed; missing sections; exact-quote checks; hashes; unresolved references; completion and validation results.}}

### Recommended classification and relationships
{{Record types, domains, projects, keywords, series, source collections, support/test/dependency/contradiction/refinement/correction links; no automatic admission.}}

## Optional Paper Grader, Fruits review & scorecard

**Default: NOT_RUN.** Retain this section without fabricated zeros or grades. If enabled, specify rubric version, assessor, per-item reasons, uncertainty and scope. Framework alignment is not evidence of truth or spiritual standing.

### Framework alignment rubric
{{Master Equation definitions; axiom use; Fruits interpretive alignment; Lean applicability/receipts; internal coherence. Each dimension independently NOT_ASSESSED / NOT_APPLICABLE / assessed with reasons.}}

| Section | Assessment | Positive | Negative | Net | Ceiling | Reasons / receipt |
|---|---|---|---|---|---|---|
| S01 Classification & Routing | NOT_ASSESSED | — | — | — | — | {{ }} |
| S02 Claim Definition | NOT_ASSESSED | — | — | — | — | {{ }} |
| S03 Argument Structure | NOT_ASSESSED | — | — | — | — | {{ }} |
| S04 Evidence & Support | NOT_ASSESSED | — | — | — | — | {{ }} |
| S05 Objections & Survival | NOT_ASSESSED | — | — | — | — | {{ }} |
| S06 Boundaries & Honesty | NOT_ASSESSED | — | — | — | — | {{ }} |
| S07 Formal & Math | NOT_ASSESSED | — | — | — | — | {{ }} |
| S08 Bridge Integrity | NOT_ASSESSED | — | — | — | — | {{ }} |
| S09 Falsifiability & Predictions | NOT_ASSESSED | — | — | — | — | {{ }} |
| S10 Audit & Provenance | NOT_ASSESSED | — | — | — | — | {{ }} |

### Source-heading scorecard and improvement path
{{Each actual source heading; assessment; reason; next improvement. No automatic promotion by reviewer type or Lean build.}}

### Per-atom support and dependency review
{{Show where a central claim lacks support; do not pool evidence across unrelated registers or average away decisive counterexamples. Numerical roll-ups require a declared compatible rubric.}}

<a id="original"></a>

# ORIGINAL ARTICLE

**Preserved source:** {{file link}}  
**Source version:** {{UUID}} · **SHA-256:** {{computed value}}  
**Verification:** {{VERIFIED against available source bytes / UNVERIFIED with reason}}

<!-- PAPER_SECTION:{{paper_uuid}}:ORIGINAL:BEGIN -->
{{ORIGINAL ARTICLE TEXT — INSERT WITHOUT REWRITING. PRESERVE ORIGINAL FILE BYTES SEPARATELY.}}
<!-- PAPER_SECTION:{{paper_uuid}}:ORIGINAL:END -->

# ATOM RECORDS & LIBRARY INDEXES

{{In the rendered paper, A1–A15 may be collapsible. The original and essential findings remain accessible.}}

## A1 · Atom identities, discovery & native anatomies

### Repeat this block for each independently addressable object
- **UUID / version / content hash:** {{ }}
- **Short ID / readable address / aliases:** {{ }}
- **Descriptive title / parent / ordering:** {{ }}
- **Type:** {{exactly one of CLAIM / EVIDENCE / PROOF / PROCESS}}
- **Register and selection reason:** {{ }}
- **Exact source text / source UUID / source hash / span:** {{ }}
- **Author or witness / received date / AI contribution provenance:** {{ }}
- **Project / domains / topics / series / collection memberships:** {{ }}
- **Technical statement / plain rendering:** {{ }}
- **Source meaning versus analyst's proposed revision:** {{ }}
- **Five independent axes:** {{lifecycle; applicable proof class; register; IC grade; WHY outcome}}
- **Admission:** {{candidate; human ruling pending unless a real ruling is linked}}

### Ordered Atom opening stages — repeat per object
0. **Preserve:** raw text, source location/span/hash, attribution, legacy identifier, known/unknown source AI contribution and declared processing AI contribution.
1. **Segment:** bundled status, child IDs, independently assessable parts, split rationale.
2. **Type:** one object type, register, burden, decomposed-from reference; preflight Q15–Q18.
3. **Expose dependencies:** formulation, truth-making, evidential, inference licenses, hidden premise check; typed versioned links.
4. **Open native anatomy:** applicable type block below and register-specific chain. Other blocks explicitly NOT_APPLICABLE.
5. **Truth space:** if true, if false, exact negation where applicable, false worlds and countermodels.
6. **Attach evidence:** evidence/version, target claim/version, direction, lane, rival comparison, independence and boundaries.
7. **Rivals:** strongest alternative, same observable signature, selection timing, open disagreements.
8. **Gauntlet:** kill conditions, preregistration if any, actual execution receipts, label-removal/permutation/collapse/translation/holdout tests and NOT_RUN states.
9. **Termini:** branch endpoint, primitive/input/open status, justification, open question, failed attempts, next test and affected claims.
10. **Bridge grading when applicable:** forward/reverse maps, preservation/loss, countermodels, IC proposal and justification. Record WHY separately for any relevant object.
11. **Governance:** completion status, unresolved required fields, waiver rationale/authority, human ruling, corrections and projection links.

### Per-component Q0–Q14 answers
{{Repeat every Q0–Q14 row from S02 for this object. Mark unopened answers explicitly with reasons. Link answers already recorded rather than duplicate conflicting values.}}

### Claim anatomy
{{Technical/plain statement; register anatomy; truth conditions; exact negation; quantifiers; identity conditions; definitions; scope; boundary conditions; formalization boundary.}}

### Register-native chains
- **History:** event → observers → witness → testimony → transmission → document → preservation → corroboration → interpretation → present claim.
- **Physics:** quantity → units → dynamics → protocol → instrument → data → controls → analysis/fit → physical claim.
- **Mathematics:** definition → axiom use → inference rule → lemma → derivation → theorem statement → build receipt → interpretation boundary.
- **Theology:** source → textual witness → witness tradition → proclamation → theological register → confession class → scope → relation to other claims.
- **Bridge:** registers → objects → mapping → preserved → lost → boundary → grade → reverse map → commutativity → countermodels → WHY gate → next test.
- **Other register:** {{versioned applicable anatomy; missing schema remains an explicit open item}}.

<a id="evidence-proof"></a>

## A2 · Evidence records
{{Repeat per evidence UUID/version.}}

1. Source and exact record.
2. Provenance and custody.
3. Protocol.
4. Conditions.
5. Raw record and hash.
6. Derived artifacts, transformation and information lost/added.
7. Controls, expected/observed results and limitations.
8. Independence families, clusters and common causes.
9. Discrimination statement for each target claim/rival.

**Assessment fields:** {{direction, native/bridge/identification lane, timing, assessor, reason, optional rubric-weight, decisive counterexample, stale status, limitations.}}

## A3 · Proof records and formal classification
{{Repeat per proof UUID/version; conclusions are separate linked claims.}}

1. Premises and their exact versions.
2. Inference rules.
3. Ordered, individually addressable derivation steps.
4. Exact conclusion and target claim version.
5. Assumption register, custom axioms and sensitivity.
6. Actual receipt or explicit absence.
7. Interpretation boundary: what was checked and what was not proved.

| Dimension | Value / reason |
|---|---|
| Applicability | {{FORMALIZABLE / PARTIAL / NOT_APPLICABLE / UNKNOWN}} |
| Formalization status | {{NONE / TARGET / DRAFT / PARSES / CHECKED / FAILED / SUPERSEDED}} |
| Declaration kind | {{AXIOM / DEFINITION / THEOREM / LEMMA / STRUCTURE / CLASS / INSTANCE / INDUCTIVE / ABBREVIATION / EXAMPLE; pending if unknown}} |
| Logical role | {{PRIMITIVE / ASSUMPTION / DEFINITIONAL / DERIVED / EQUIVALENCE / EXISTENCE / UNIQUENESS / IMPOSSIBILITY / CONSISTENCY / INDEPENDENCE / COUNTEREXAMPLE / MODEL_WITNESS}} |
| Statement form | {{UNCONDITIONAL / CONDITIONAL / BICONDITIONAL / UNIVERSAL / EXISTENTIAL / UNIQUE_EXISTENCE / NEGATION / EQUALITY / INEQUALITY}} |
| Reasoning regime | {{CONSTRUCTIVE / CLASSICAL / NONCOMPUTABLE / DECIDABLE / MIXED / UNKNOWN}} |
| Proof method | {{TERM / TACTIC / REWRITE / SIMPLIFICATION / INDUCTION / CASES / CONTRADICTION / ARITHMETIC / AUTOMATION / COMPUTATION / EXTERNAL_GENERATION / MIXED}} |
| Build result | {{NOT_RUN / PASSED / FAILED / TIMEOUT / TOOLCHAIN_MISMATCH}} |
| Trust status | {{CLEAN / CONTAINS_SORRY / CONTAINS_ADMIT / CUSTOM_AXIOMS / UNSAFE_FEATURE / PROOF_ESCAPE / AUDIT_REQUIRED; retain all applicable findings}} |
| Correspondence | {{EXACT / PARTIAL / MODEL_ONLY / PROPOSED / DISPUTED / MISMATCH}} |
| Formal result | {{PROVED_IN_SYSTEM / REFUTED / COUNTERMODEL_FOUND / CONSISTENCY_RELATIVE / SATISFIABLE_WITNESS / INCONCLUSIVE / NO_RESULT}} |

**Receipt details:** {{module, declaration, exact statement, variables/types, imports, definitions, transitive axiom dependencies, tactic/term, failed attempts, source/toolchain/dependency versions, command, exit status, logs, receipt hash.}}

**External results:** {{bibliographic identity, exact proposition, inspected derivation/replication status and applicable assumptions; separate from local build status.}}

## A4 · Typed relationships and dependency graph
| Edge UUID/version | Source UUID/version | Predicate | Target UUID/version | Load-bearing? | Role / lane | Reason / evidence | Status |
|---|---|---|---|---|---|---|---|
| {{ }} | {{ }} | {{ }} | {{ }} | {{ }} | {{ }} | {{ }} | {{ }} |

{{Predicates: supports, contradicts, falsifies, tests, proves, dependsOn, defines, interprets, bridgesTo, derivedFrom, generatedBy, auditedBy, expands, forksFrom, instantiates, supersedes, corrects. Maintain explicit legacy crosswalk. Narrative-only illustrates/motivates/entranceFor links confer no warrant.}}

## A5 · Termini and open branches
| Branch UUID | Target | Terminus | Justification / independent input | Open question | Candidates / failed attempts | Next test | Affected claims |
|---|---|---|---|---|---|---|---|
| {{ }} | {{ }} | {{PRIMITIVE / INDEPENDENT_EMPIRICAL_INPUT / OPEN}} | {{ }} | {{ }} | {{ }} | {{ }} | {{ }} |

## A6 · Axes, labels and vocabulary crosswalk
{{Lifecycle, review, admission, proof class, register, evidence lane, IC grade, WHY outcome and optional scores are independent. Preserve legacy labels; document mappings and unresolved conflicts. Pending schema changes are not silently treated as approved vocabulary.}}

## A7 · Correction ledger
| Correction UUID | Target/version | Defect class | Previous wording/value | Proposed successor | Reason / receipt | Application status | Human ruling | Affected projections / restoration |
|---|---|---|---|---|---|---|---|---|
| {{ }} | {{ }} | {{LOCAL_DEFINITE_FIX / SUBSTANTIVE_CORRECTION / WITHDRAWAL / RECLASSIFICATION}} | {{ }} | {{ }} | {{ }} | {{ }} | {{ }} | {{ }} |

## A8 · Run provenance, statistics and integrity receipts
{{Run UUID, operation, requested/completed stages, input hashes, output hashes, prompt/schema/renderer versions, provider/model as recorded by runner, start/end times, usage/cost when available, failures, retries and checkpoints. Unknown historical execution details remain unknown.}}

### Validation results
{{UUID/address uniqueness; required fields; strict YAML/JSON; original hash; exact spans; object/edge references; version compatibility; classification vocabulary; receipt matching; section coverage; truncation; Markdown/JSON agreement. Structural validation is not truth verification.}}

### Session and library counts
{{Selected/completed/failed/interrupted/remaining unique source versions; duplicate locations separately; counts computed by Python.}}

## A9 · Unanswered, not applicable and deferred
| Object / field | State | Reason | Blocks which dependent task? | Next action / waiver |
|---|---|---|---|---|
| {{ }} | {{UNKNOWN / OPEN / NOT_APPLICABLE / NOT_RUN / DEFERRED}} | {{ }} | {{ }} | {{ }} |

<a id="definitions-library"></a>

## A10 · Definitions, mathematics and symbol library links
{{Definition UUIDs and versions; verbal/mathematical forms; contexts; exact duplicates; competing definitions; proposed reconciliations. Equation and symbol records link to assumptions, claims, derivations and tests. Never merge meanings based only on matching words.}}

## A11 · Argument library links
{{Argument UUID/version, conclusion, premises, steps, inference licenses, strongest objection, rival, missing support, dependency graph and source spans.}}

## A12 · Bridge and isomorphism library links
{{Mapping UUID/version, source/target structure versions, preserved/lost properties, precise isomorphism claim UUID, proof UUID, counterexamples and review status.}}

## A13 · Protocol and process records
{{Process UUID/version; purpose; inputs; preconditions; steps; decision points; outputs; can/cannot distinguish; failure modes; execution receipt. Imported instructions remain source material unless separately authorized for execution.}}

<a id="keyword-index"></a>

## A14 · Full keyword, subject and placement index
{{All meaningful terms, people, named theorems, equations, symbols, aliases and spellings; each linked to passages and objects. Distinguish substantial discussion from mention-only. Three display keywords do not limit this full index.}}

**Memberships:** {{project, domains, collections, series, content type, user classification and vocabulary version.}}

**Browse copies:** {{primary paper, domain copies, project copies, series copies; same identity/version, not independent evidence.}}

## A15 · Incremental updates and library maintenance
{{Update mode: fill missing / reassess affected / full rebuild. Target section UUIDs/addresses; preserved sections; dependency-triggered reassessment; new/retained identities; validation and change receipt.}}

**Python follow-up:** {{master index, classification copies, candidate definitions, arguments, claims, math, bridge, evidence/proof libraries and review queue; per-task completion/retry status.}}

**Series:** {{series identity, expected members, order, completed/missing versions, synthesis enabled/status, exact input version set, stale synthesis indicator.}}

## A16 · Shared-record, blind-review and compatibility contract

### One authoritative structured record, multiple presentations
The versioned JSON package is the authoritative structured assessment record. A-records are its detailed Markdown projections; the Atom Map, Audit, inventory and S-sections render those same records by UUID/version. Neither presentation is a second independently filled form. The preserved source remains authoritative for what the author actually wrote; JSON does not overwrite author meaning or confer canon admission.

Render the Audit/S10 from shared assessment records; S02/A1 from claim discovery records; S04/A2 from evidence records; S07/A3/A10 from mathematical and proof records; S08/A12 from mapping records; S03 hidden premises/A1 stage 3 from dependency records. Paper-level synthesis may add prose, but must cite the same underlying versions and introduce no unsupported verdicts. Human edits to any rendered section become revision proposals to reconcile into the structured record, followed by re-rendering.

### Blind comparison packet
{{Required when the versioned IC assessment rule calls for blinded comparison; otherwise explicit NOT_APPLICABLE with reason.}}

| Field | Value |
|---|---|
| Packet UUID/version and artifact reference | {{ }} |
| Packet SHA-256 and creation receipt | {{ }} |
| Neutral tokens / anonymization procedure | {{ }} |
| Included candidate and rival pairings | {{ }} |
| Selection rule and pre-result registration | {{rule version, hash, timestamp}} |
| Separate deblinding-key artifact and hash | {{restricted reference; do not expose key in blinded packet}} |
| Evaluator, available information and blind exposure | {{ }} |
| Execution state, results and receipt | {{NOT_RUN or result}} |
| Deblinding event and subsequent interpretation | {{ }} |
| Grade proposal versus validated grade | {{distinct fields}} |

An IC grade remains a proposal until its required checks have receipts or an explicit recorded ruling addresses exceptions. Missing blinded work blocks only the grade promotion that requires it, not unrelated processing. Do not claim anonymity just because a packet field exists.

### Required reasons, falsification and termini
Before any paid review, detect routing questionnaires, missing-document references and empty sources. Preserve them as intake records with INSUFFICIENT_SOURCE; do not publish them as reviews of the referenced paper. A routing decision never substitutes for fetching the actual document. A no-object mapping stops downstream review and records the reason. Legitimate procedures and short substantive claims must not be rejected solely for length.

When the same blocking unknown affects three or more sections, assign one stable unresolved-item ID, explain it once in the overview and A9, and render dependent sections as “blocked: <ID>” plus only section-specific findings. Retain section markers without repeated empty tables. Always retain the optional scorecard skeleton with NOT_ASSESSED rows when grading is disabled.

Every NOT_APPLICABLE, NOT_RUN, DEFERRED, UNKNOWN or OPEN section carries a reason and applicability/completion state. Empty required reasons fail structural validation. The report separately displays coverage, actual checks completed and deferred work; placeholder completeness is not assessment completeness.

Every `falsifies` edge names its target claim/version, exact defeat condition/version, observed result and receipt. Link preregistration when present; retrospective application requires an explicit ruling and rationale. Preserve unruled retrospective findings as proposals; absence of preregistration does not erase a genuine counterexample.

No terminus may close merely by renaming the desired conclusion. Record the reviewer, premises and non-circularity rationale. Python checks that the record exists and flags missing/cyclic references; substantive circularity is a reasoning review, not something a field-presence check can prove absent.

### Independent convergence and historical witnesses
Add the provenance category **Author-original; independently convergent with historical witness**. Preserve the author's independent-origin assertion, dated source when available, witness citation, structural correspondence and verification status. Do not infer borrowing merely because older related work exists, or infer independent discovery merely from resemblance. Historical witness is not automatically independent empirical confirmation. Retain adaptation/prior-work categories where actual borrowing is documented.

### Dashboard migration contract
Inspection of EVIDENCE/SCRIPTS/TEMPLATES/EVIDENCE_DASHBOARD_v0.3.md confirms queries read flat `evd_*` fields and many require `type = "evidence-sheet"`. Nested fields alone will not satisfy those queries. For migration, Python may emit read-only flat compatibility projections from the same structured record, never a second AI-authored set: evd_state, evd_support, evd_counter, evd_balance, evd_families, evd_coverage, evd_gated, evd_stable, evd_weakest_claim, evd_unassessed and evd_assessors; applicable s##_pos/neg/net fields likewise derive from recorded rubric assessments.

Unassessed numbers remain null, not zero; flat evd_state maps NOT_ASSESSED/NOT_RUN to UNSCORED with the original state retained. Gate and stability values remain unknown unless checked. Before rollout, update dashboard filters to accept the new record_version as well as legacy evidence-sheet records, handle nulls as unknown, and avoid treating missing stability as a failed robustness test. Keep document purpose distinct from legacy dashboard type. Test a not-run record and an assessed record. This template change does not itself modify deployed dashboards.

Legacy scores remain UUID/version-addressable for comparison, with origin and date, but never become current assessment by default. Stage numbering in this template is 0–11 (twelve stages), with governance at 11; the earlier request template uses stages 0–10 followed by governance. Preserve an explicit mapping rather than describing the two as literally identical.

## Z · Preserved legacy records
{{Links to immutable byte-preserved legacy artifacts and hashes. Optional verbatim embedded copies, clearly marked historical, including any old scores and errors. Never render a legacy verdict as the current assessment.}}

---

[Overview](#overview) · [Atom Map](#atom-map) · [Argument](#argument) · [Mathematics](#mathematics) · [Original](#original) · [Evidence and proof](#evidence-proof) · [Definitions](#definitions-library) · [Keywords](#keyword-index)

**Complete JSON package:** {{link}} · **Master index:** {{link}} · **Open work:** {{link}} · **Publication receipt:** {{link}}

<!-- JSON companion contract: paper identity/source/presentation metadata; versioned objects; separately addressable definitions/math/arguments/mappings; typed edges; runs; corrections; projections; validation findings. Paper-library collections do not create extra primary Atom types. Markdown is a readable projection with the same critical assumptions, findings and boundaries. Publication receipt hashes both artifacts without circular self-hashing. -->
