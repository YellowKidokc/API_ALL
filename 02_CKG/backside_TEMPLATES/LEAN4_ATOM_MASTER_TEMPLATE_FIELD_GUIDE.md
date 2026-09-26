# LEAN4 Atom Record — Field Guide

Companion to `LEAN4_ATOM_MASTER_TEMPLATE.md`. Same locked order: blocks 1–13 are
the engine's run order, and each block may only use facts from blocks before it.

**Who fills a field**

| Tag | Meaning |
|---|---|
| **PY** | Python in `LEAN_ATOM_EXTRACTOR` — deterministic: paths, hashes, counts, edges |
| **LEAN** | The Lean compiler (`lake env lean`) — the only source of build and axiom facts |
| **DS** | DeepSeek — writes explanations only; never evidence, never status |
| **COCO** | CocoIndex paper linker — proposes candidates only |
| **HUMAN** | You — lane rulings, correspondence rulings, admission |

**Implementation status**: ✅ running today · ◐ partial · ⬜ designed, not built yet

**API base**: `http://127.0.0.1:8989` (or `http://192.168.2.51:8989` on the LAN)

| Endpoint | Returns |
|---|---|
| `GET /api/declarations` | every declaration with source, build, trust, lane, meaning, brief facts, edges |
| `GET /api/lean/node?id=<node_id or uuid or name>` | one atom + uses / used_by / mentioned_in |
| `GET /api/lean/search?q=<text>&lane=<lane>` | atoms whose name matches, optional lane filter |
| `GET /api/lean/graph` | the full graph (nodes + edges) |
| `GET /api/brief?name=<File.md>` | a brief's full markdown |
| `POST /api/export?id=<declaration id>` | writes one Atom JSON record to `exports/` |

---

## Header

| Field | Meaning | Filled by | Status |
|---|---|---|---|
| `record_version` | Template/schema version this record follows | PY | ✅ |
| `template_status` | Whether the template itself is draft or locked | HUMAN | ✅ |
| `record_kind` | `LEAN_FILE` — one record per distinct Lean file; theorems and definitions are atoms inside it | PY | ✅ |

## 1 · Identity — station `scan`

| Field | Meaning | Filled by | API | Status |
|---|---|---|---|---|
| `lean_file_uuid` | Permanent id for the file record (uuid5 in the faiththruphysics.com namespace, same scheme as mothership pills) | PY | — | ◐ atoms have uuids; file-level record not yet emitted |
| `readable_address` | Human alias, e.g. `LEAN/Theophysics/AccountabilityBoundaryGauntlet` | PY | — | ◐ |
| `title` | Human title; taken from the brief once one exists | DS→PY | `/api/declarations` → `brief_title` | ✅ |
| `record_revision` | Increments when the file hash changes | PY | — | ⬜ |

## 2 · Source — station `scan` / `harvest`

| Field | Meaning | Filled by | API | Status |
|---|---|---|---|---|
| `project` | Registry project name (e.g. `Theophysics`) | PY | `/api/declarations` → `project_id` | ✅ |
| `project_root` | Folder holding `lakefile` + `lean-toolchain` | PY | — | ✅ |
| `relative_path` | File path inside the project | PY | `relative_path` | ✅ |
| `file_sha256` | Hash of the exact bytes scanned; changes = re-scan | PY | `source_hash` | ✅ |
| `also_in` | Other paths with byte-identical content | PY | pill `rails.10_beacon.also_in` | ✅ |
| `harvest_manifest_ref` | Row in `H:\Desktop\ALL_LEAN4\MANIFEST.csv` | PY | — | ◐ harvest done; not yet linked into records |
| `version_rank` | 1 = newest of files sharing a name; 2+ = older variants | PY | — | ◐ in manifest |
| `superseded_by` | The version that replaces this one | HUMAN | — | ⬜ |

## 3 · Inventory — station `scan`

| Field | Meaning | Filled by | Status |
|---|---|---|---|
| `theorems` … `axioms` | Count of each declaration kind, comments stripped | PY | ✅ |

## 4 · Trust, text audit — station `audit`

| Field | Meaning | Filled by | API | Status |
|---|---|---|---|---|
| `text_audit` | Worst finding: `CLEAN / CONTAINS_SORRY / CONTAINS_ADMIT / CUSTOM_AXIOMS / UNSAFE_FEATURE` | PY | `primary_trust_status` | ✅ |
| `sorry_count` / `admit_count` | Tactic uses in code, comments and strings excluded | PY | `sorry_count`, `admit_count` | ✅ |
| `unsafe_count` | `unsafe` keyword uses | PY | — | ✅ |
| `declared_axioms` | Top-level `axiom` declarations in this file | PY | — | ✅ |

Text audit only sees this file. A theorem that depends on a `sorry` elsewhere looks clean here — that is what block 6 is for.

## 5 · Build — station `verify`

| Field | Meaning | Filled by | API | Status |
|---|---|---|---|---|
| `toolchain.pinned` | The project's `lean-toolchain` | PY | — | ✅ |
| `toolchain.used` | `lean --version` run **inside** the project | LEAN | `lean_version` | ✅ |
| `lake_manifest_sha256` | Pins the dependency versions (Mathlib etc.) | PY | — | ⬜ |
| `status` | `NOT_RUN / PASSED / FAILED / TIMEOUT / TOOLCHAIN_MISMATCH` | LEAN | `build_result` | ✅ |
| `command` | e.g. `lake env lean AccountabilityBoundaryGauntlet.lean` | PY | pill `formal_receipts` | ✅ |
| `exit_code` | Compiler exit code | LEAN | pill | ✅ |
| `checked_at` | When the build ran | PY | pill | ✅ |
| `receipt_hash` | SHA-256 of command + exit + output + time — the evidence fingerprint | PY | `receipt_hash` | ✅ |
| `log_ref` | Where full output is kept | PY | — | ◐ stored in the database, no file link yet |

**Only this block can make an atom `lean_passed`.**

## 6 · Transitive axiom audit — station `axiom_audit`

| Field | Meaning | Filled by | Status |
|---|---|---|---|
| `status` | Whether `#print axioms` has been run for every theorem | LEAN | ⬜ |
| `clean_theorems` | Theorems whose axioms are only Lean's standard ones (`propext`, `Classical.choice`, `Quot.sound`) | LEAN | ⬜ |
| `theorems_using_sorryAx` | Theorems that depend on a `sorry` anywhere, even in another file | LEAN | ⬜ |
| `theorems_using_custom_axioms` | Theorems that rely on your declared axioms | LEAN | ⬜ |

This is the real trust check. Until it runs, every pill lists it as a gap.

## 7 · Lanes — station `classify`

| Field | Meaning | Filled by | API | Status |
|---|---|---|---|---|
| `primary` | Main Claim Evidence Lane for the file | PY | `lane` (per atom) | ✅ |
| `basis` | `INFERRED_FROM_NAMES` until a human rules | PY / HUMAN | — | ✅ inferred · ⬜ ruling |
| `distribution` | Count of atoms per lane | PY | `/api/lean/search?lane=` | ✅ |

## 8 · Brief — station `briefs`

| Field | Meaning | Filled by | API | Status |
|---|---|---|---|---|
| `status` | `NOT_RUN / WRITTEN / REVIEWED` | PY / HUMAN | — | ✅ written · ⬜ reviewed |
| `ref` | `PROOF/00_BRIEFS/<file>.md` (and `.brief.json`) | PY | `brief_md` | ✅ |
| `model` / `written_at` | Which model wrote it, when | PY | `brief_model` | ✅ |
| `kind` | Always `AI_EXPLANATION_NOT_EVIDENCE` | PY | — | ✅ |

Brief content (purpose, definitions, theorems + roles, depends on, **does not prove**, how to cite) comes from DS and is cached per file hash — unchanged files are never re-sent. `GET /api/brief?name=` returns it.

## 9 · Pills & rails — station `pills`

| Field | Meaning | Filled by | Status |
|---|---|---|---|
| `status` / counts | Pills written for theorems and definitions | PY | ✅ |
| `folder` | `CLAIMS_PROOFS_EVIDENCE\PROOF` | PY | ✅ |

Each pill carries the 10 rails of the Claim Evidence Lane Framework:

| Rail | For a Lean atom | Source block |
|---|---|---|
| 1 Claim | Exact Lean statement | 3 |
| 2 Lane | Lane + basis | 7 |
| 3 Physics type | `mathematical_formalism` | fixed |
| 4 Defense | `DERIVATION` (theorems) · `ROOT` (definitions) · `AXIOM` (axioms, assumption bundles) | 3 |
| 5 Evidence needed | `lean_formal` | fixed |
| 6 Evidence present | Build receipt | 5 |
| 7 Evidence gap | Missing build, missing axiom audit, bridge owed | 5, 6 |
| 8 Kill condition | Build fails unchanged, or axiom audit finds `sorryAx` / undeclared axiom | 5, 6 |
| 9 Story | Empty, kept separate | — |
| 10 Beacon | uuid, node id, receipt hash, copies | 1, 2, 5 |

## 10 · Graph — station `pills` (graph pass)

| Field | Meaning | Filled by | API | Status |
|---|---|---|---|---|
| `node_ids` | `tp:lean/<project>/<Namespace.name>` for each atom | PY | every endpoint | ✅ |
| `edges_out` (uses) | Definitions/theorems named in the statement or proof | PY | `/api/lean/node` → `uses` | ✅ |
| `edges_in` (used by) | Reverse of uses | PY | `used_by` | ✅ |
| `outside_mentions` | Files on other nodes (atoms repo, CLAIM, EVIDENCE, CKG) that name the atom | PY | `mentioned_in` | ✅ |
| `graph_ref` | `PROOF/00_LEAN_GRAPH.json` | PY | `/api/lean/graph` | ✅ |

Ambiguous short names are skipped, not guessed.

## 11 · Correspondence — station `paper_linker`

| Field | Meaning | Filled by | Status |
|---|---|---|---|
| `status` | `NOT_SEARCHED / CANDIDATES_FOUND / MATCH_REVIEWED` | COCO / HUMAN | ⬜ |
| `linked_claims` | Claim or paper passage → atom, score, boundary, status | COCO proposes · HUMAN rules | ⬜ |
| `linker_run` | CocoIndex run id and index version | COCO | ⬜ |

Matches are meaning-based leads from the briefs, not proofs. A linked theorem still proves only its Lean statement.

## 12 · Admission — human

| Field | Meaning | Filled by | Status |
|---|---|---|---|
| `graph` | `candidate` until ruled | HUMAN | ✅ default |
| `human_ruling` / `ruling_actor` / `ruling_date` / `rationale` | Who admitted it, when, why | HUMAN | ⬜ |

No station can admit anything. A passing build is not admission.

## 13 · Run & integrity — engine

| Field | Meaning | Filled by | Status |
|---|---|---|---|
| `stations.order` | Fixed run order: scan → audit → verify → axiom_audit → classify → briefs → pills → paper_linker | PY | ✅ |
| `completed / failed / pending` | Per-station outcome for this file | PY | ◐ |
| `run_uuid` / `generated_at` / `engine_version` | Run provenance | PY | ◐ |
| `integrity.*` | Structural checks: hash re-verified, receipt matches current bytes, every theorem has a pill, every edge resolves, brief covers every theorem, Markdown/JSON agree | PY | ◐ counts exist; per-file checks ⬜ |

Structural checks confirm the record is complete and consistent. They do not make any claim true.

---

## Where each block lives today

| Block | Stored in |
|---|---|
| 1–7 | `LEAN_ATOM_EXTRACTOR\lean_atoms.db` (tables `declarations`, `source_files`, `trust_findings`, `builds`, `classifications`) |
| 8 | `PROOF\00_BRIEFS\*.brief.json` + `.md` |
| 9 | `PROOF\<file>\*.pill.yaml`, `PROOF\00_LEAN_DEFINITIONS\...` |
| 10 | `PROOF\00_LEAN_GRAPH.json` (+ `lean_graph.json` next to the database, loaded by the API) |
| 11 | not yet built (CocoIndex) |
| 12 | not yet stored (human rulings) |
| 13 | database + run logs |

## Build next, in order
1. Emit this file-level record (Markdown + JSON) per Lean file — blocks 1–10 already have their data.
2. Station 6: run `#print axioms` for every theorem and record the result.
3. Link harvest rows (block 2) and compile the 1,166 harvested files in their own projects.
4. Station 11: CocoIndex paper linker.
5. Human ruling fields (blocks 7, 11, 12) in the dashboard.
