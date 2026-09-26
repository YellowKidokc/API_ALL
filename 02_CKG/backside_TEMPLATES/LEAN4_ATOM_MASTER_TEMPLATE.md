---
record_version: LEAN4_ATOM_RECORD_V1.0
template_status: LOCKED_ORDER_DRAFT
record_kind: LEAN_FILE
# ORDER LOCK: keys and sections follow the engine's run order. A later block may
# only use facts produced by an earlier block. Never reorder; append new stages at the end.

# 1 - IDENTITY                                 (station: scan)
lean_file_uuid: null
readable_address: null
title: null
record_revision: null

# 2 - SOURCE                                   (station: scan / harvest)
source:
  project: null
  project_root: null
  relative_path: null
  file_sha256: null
  also_in: []
  harvest_manifest_ref: null
  version_rank: null
  superseded_by: null

# 3 - INVENTORY                                (station: scan)
inventory:
  theorems: null
  lemmas: null
  definitions: null
  structures: null
  inductives: null
  classes: null
  instances: null
  axioms: null

# 4 - TRUST, TEXT AUDIT                        (station: audit)
trust:
  text_audit: NOT_RUN
  sorry_count: null
  admit_count: null
  unsafe_count: null
  declared_axioms: []

# 5 - BUILD                                    (station: verify - Lean compiler)
toolchain:
  pinned: null
  used: null
  lake_manifest_sha256: null
build:
  status: NOT_RUN
  command: null
  exit_code: null
  checked_at: null
  receipt_hash: null
  log_ref: null

# 6 - TRANSITIVE AXIOM AUDIT                   (station: axiom_audit - Lean compiler)
axiom_audit:
  status: NOT_RUN
  clean_theorems: null
  theorems_using_sorryAx: []
  theorems_using_custom_axioms: []

# 7 - LANES                                    (station: classify)
lanes:
  primary: null
  basis: null
  distribution: {}

# 8 - BRIEF                                    (station: briefs - DeepSeek)
brief:
  status: NOT_RUN
  ref: null
  model: null
  written_at: null
  kind: AI_EXPLANATION_NOT_EVIDENCE

# 9 - PILLS & RAILS                            (station: pills)
pills:
  status: NOT_RUN
  theorem_pills: null
  definition_pills: null
  folder: null

# 10 - GRAPH                                   (station: pills - graph pass)
graph:
  node_ids: []
  edges_out: null
  edges_in: null
  outside_mentions: null
  graph_ref: null

# 11 - CORRESPONDENCE                          (station: paper_linker - CocoIndex)
correspondence:
  status: NOT_SEARCHED
  linked_claims: []
  linker_run: null

# 12 - ADMISSION                               (human)
admission:
  graph: candidate
  human_ruling: pending
  ruling_actor: null
  ruling_date: null
  rationale: null

# 13 - RUN & INTEGRITY                         (engine)
stations:
  order: [scan, audit, verify, axiom_audit, classify, briefs, pills, paper_linker]
  completed: []
  failed: []
  pending: []
run_uuid: null
generated_at: null
engine: LEAN_ATOM_EXTRACTOR
engine_version: null
integrity:
  file_hash_verified: null
  receipt_matches_file_hash: null
  every_theorem_has_pill: null
  every_edge_resolves: null
  brief_covers_all_theorems: null
  markdown_json_agree: null
---

<!-- BLANK TEMPLATE. null = not yet supplied. [] = not yet populated, never "none exist". -->
<!-- Who writes what: Python = identity, source, inventory, counts, edges. Lean compiler = build and axiom audit. DeepSeek = brief only. CocoIndex = correspondence candidates only. Human = lane rulings, correspondence rulings, admission. -->
<!-- ORDER LOCK: sections 1-13 below match the front matter 1-13 and the engine's run order. A section may cite earlier sections only. -->

# {{HUMAN TITLE OF THE LEAN FILE}}

**File:** `{{source.relative_path}}` · **Project:** {{source.project}} · **Build:** {{build.status}} · **Axiom audit:** {{axiom_audit.status}} · **Lane:** {{lanes.primary}} ({{lanes.basis}})  
**Record:** {{readable_address}} · **UUID:** {{lean_file_uuid}} · **Revision:** {{record_revision}}

> [!important] The Formal Contract
> A Lean theorem shows that its statement follows from the definitions, structure fields and hypotheses in this file plus Lean's core and imported libraries. It does not show that the real-world things the names suggest behave this way. Any theological, moral, physical or historical reading is a separate claim that needs its own bridge.

> [!success] At a glance
> | | |
> |---|---|
> | Formalizes | {{from 8 · brief.purpose}} |
> | Main results | {{from 8 · theorems with role = main}} |
> | Rests on | {{from 4 + 6 · declared axioms, assumption bundles}} |
> | Compiled | {{from 5 · status, toolchain, receipt}} |
> | Does NOT prove | {{from 8 · top does_not_prove items}} |
> | Breaks if | build fails with statements unchanged, or the axiom audit finds sorryAx / an undeclared axiom |

---

## 1 · Identity
| Field | Value |
|---|---|
| UUID | {{lean_file_uuid}} |
| Readable address | {{readable_address}} |
| Title | {{title}} |
| Revision | {{record_revision}} |

## 2 · Source
| Field | Value |
|---|---|
| Project / root | {{source.project}} · {{source.project_root}} |
| File / SHA-256 | `{{source.relative_path}}` · {{source.file_sha256}} |
| Identical copies | {{source.also_in}} |
| Harvest row / version rank | {{source.harvest_manifest_ref}} · {{source.version_rank}} |
| Superseded by | {{source.superseded_by}} |

## 3 · Inventory
| Kind | Count |
|---|---|
| Theorems / lemmas | {{ }} |
| Definitions / abbrevs | {{ }} |
| Structures / inductives / classes / instances | {{ }} |
| Declared axioms | {{ }} |

## 4 · Trust — text audit
{{sorry / admit / unsafe per declaration, comments and strings excluded. Declared axioms and assumption bundles (structures whose fields are hypotheses).}}

| Declaration | Finding | Line |
|---|---|---|
| {{ }} | {{CONTAINS_SORRY / CONTAINS_ADMIT / CUSTOM_AXIOM / UNSAFE / ASSUMPTION_BUNDLE}} | {{ }} |

## 5 · Build
| Field | Value |
|---|---|
| Toolchain pinned / used | {{toolchain.pinned}} / {{toolchain.used}} |
| Command | `{{build.command}}` |
| Result / exit | {{build.status}} / {{build.exit_code}} |
| Checked at | {{build.checked_at}} |
| Receipt | {{build.receipt_hash}} |
| Log | {{build.log_ref}} · {{first error line if failed}} |

## 6 · Transitive axiom audit
| Theorem | `#print axioms` result | Verdict |
|---|---|---|
| {{ }} | {{propext, Classical.choice, Quot.sound / sorryAx / custom}} | {{STANDARD_ONLY / USES_SORRY / USES_CUSTOM}} |

## 7 · Lanes
| Node | Lane | Basis |
|---|---|---|
| {{ }} | {{physics / master_equation / ten_laws / trinity / axioms / consciousness / morality / crown / story / meta / other}} | {{INFERRED_FROM_NAMES / HUMAN_RULED}} |

## 8 · Brief (human companion — AI explanation, not evidence)
**Purpose:** {{ }}

**Definitions:** {{name — plain meaning}}

**What it proves:** {{name (role) — plain meaning}}

**Depends on:** {{ }}

**What it does NOT prove:** {{ }}

**How to cite:** {{ }}

## 9 · Pills & rails (per atom)
| Node | 1 Claim | 2 Lane | 3 Type | 4 Defense | 5 Needed | 6 Present | 7 Gap | 8 Kill | 9 Story | 10 Beacon |
|---|---|---|---|---|---|---|---|---|---|---|
| {{ }} | {{statement}} | {{from 7}} | mathematical_formalism | {{DERIVATION / ROOT / AXIOM}} | lean_formal | {{from 5}} | {{from 6, 11}} | {{condition}} | kept separate | {{uuid · receipt}} |

## 10 · Graph
| Node | Uses | Used by | Mentioned in (other nodes) |
|---|---|---|---|
| {{ }} | {{node ids}} | {{node ids}} | {{file · node id}} |

## 11 · Correspondence (candidates until ruled)
| Claim / paper passage | Candidate atom | Basis | Score | Would NOT establish | Status |
|---|---|---|---|---|---|
| {{ }} | {{node id}} | {{linker / mention / human}} | {{ }} | {{boundary from 8}} | {{CANDIDATE / REVIEWED / RULED}} |

## 12 · Admission
| Field | Value |
|---|---|
| Graph state | {{admission.graph}} |
| Human ruling | {{admission.human_ruling}} · {{admission.ruling_actor}} · {{admission.ruling_date}} |
| Rationale | {{admission.rationale}} |

## 13 · Run & integrity
| Check | Result |
|---|---|
| Stations completed / failed / pending | {{ }} |
| File hash verified | {{ }} |
| Receipt matches file hash | {{ }} |
| Every theorem has a pill | {{ }} |
| Every edge resolves | {{ }} |
| Brief covers all theorems | {{ }} |
| Markdown and JSON agree | {{ }} |

---

# APPENDIX A · Atom record (repeat per declaration, same order)
1. **Identity:** node id · uuid · kind · namespace · name
2. **Source:** file · lines · file hash · also in
3. **Statement & body:** exact statement · proof/body · binders
4. **Trust:** sorry · admit · unsafe · axiom declaration
5. **Build:** receipt (command · result · lean version · hash · time)
6. **Axiom audit:** `#print axioms` result
7. **Lane:** lane · basis
8. **Explanation:** plain line · role · brief ref (AI, not evidence)
9. **Rails:** 1–10
10. **Edges:** uses · used by · mentioned in
11. **Correspondence:** linked claims · status
12. **Admission:** state · ruling

# APPENDIX B · Lean source
**SHA-256:** {{source.file_sha256}}
<!-- LEAN_SECTION:{{lean_file_uuid}}:SOURCE:BEGIN -->
```lean
{{SOURCE — BYTE-FOR-BYTE}}
```
<!-- LEAN_SECTION:{{lean_file_uuid}}:SOURCE:END -->

---
**Pills:** `PROOF/<file>/` · **Brief:** `PROOF/00_BRIEFS/<file>.md` · **Graph:** `PROOF/00_LEAN_GRAPH.json` · **API:** `http://127.0.0.1:8989/api/lean/node?id=<node_id>`
