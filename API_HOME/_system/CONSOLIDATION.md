# Consolidation: what was merged, what is proposed, what was retired

Evidence comes from reading every gathered script (file:line references are to the gathered copies).

## Done in this build

| What | Before | Now |
|---|---|---|
| **API calls** | 13+ separate implementations of the same OpenAI-style POST: `index_video.call` L110, `home.py` L140, CKG `providers._post` L51, `series_grand_synthesizer.call_llm` L52, turbo `call_deepseek_raw` L159, `series_evaluator` L339/L388, `argument_builder` L444, `three_dials` L111, `epistemic_intake_v2.call_json` L182, `semantic_analysis` L545/L620, `daily_api_preflight` L45, API_DEEP `llm_client` (x3 identical copies), `fruits_grade`, `lean_atom/briefs`, `axiom_registry` | one relay (`engine/gateway.py`) every call passes through, one limiter, one retry policy, one receipt log with goal ids; native stations use `engine/llm.py`. Legacy code keeps its own call code (behaviour preserved) but its URLs point at the relay. |
| **Station launchers** | ~60 .bat files with hard-coded paths, several pointing at folders that do not exist (`..\_BACKSIDE\CKG`, `..\core\worker.py`) | `ONE_MENU.bat` + one generic runner (`engine/legacy.py`) driven by each `station.json` |
| **Input chunking** | `index_video.py` 2,500 words, `home.py` claims 1,200 words | whole transcript per call; the halve-on-truncated-reply fallback stays |
| **The 23 api_call stations** | 23 folders, identical RUN.bat calling a missing `core/worker.py`, no config.txt (would all default to gpt-4o) | station 60: prompts kept verbatim, grouped into bundles, 22 stations answered in 11 whole-document calls |
| **Duplicate copies** | `transcript_polish.py` x2 (identical), `llm_client.py` x3 (identical), `consolidated/` (a grab-bag of copies, several diverged) | vendored once, from the gathered originals |
| **Two CKG runners** | `backside_CKG/workbench` and `backside_workbench` (v3.1.1): same file names, incompatible `complete()` signatures | `backside_CKG/workbench` is wired (it is what `run_ckg.py` uses); `backside_workbench` is not vendored |
| **Fruits** | `fruits_grade.py` (paper-level 0-4, system prompt file missing), api_call 06 (Yukawa variant), `FRUITS/PROMPT.md` (unimplemented) | station 40 fruits plug-in: rubric v0.3.0 copied in, prompts and lexicons as editable files; api_call 06 still runs under 60 |

## Data bugs fixed (details in MIGRATION_REPORT.md, `bug-fix` rows)

- `sync_to_sqlite.py` stored Source Role as the warrant and Modality as the formal form (and matched nothing on the real template).
- `theophysics_congruence_matrix.py`: one PROVEN Lean receipt marked **every** paper proven; zero evidence counted as 4, so every paper read SUPPORTED.
- `series_evaluator.py` re-read its own outputs and the synthesizer's master paper as input papers.
- `series_grand_synthesizer.py`: "The Six" and the predicate table regexes never matched the template.
- `turbo_pipeline_runner.py` wrote the same invented numbers (14 support, 6 claims, 18 predicates ...) into every master-index row; it now reads them from the reply or leaves them empty.

## Proposed next merges (not done: they change behaviour and need your real data to check)

1. **`evidence.py` with subcommands**: `ingest {turbo | epistemic | packet | semantic}`, `report {aggregate | congruence | sqlite-sync | merge-originals | sidecars}`, `lean {bridge | god-is | canonical-proofs}`. Three ingest routes classify the same paper today (turbo, epistemic_intake_v2, run_packet + semantic_analysis).
2. **`outbox.py` with subcommands** for the EvidenceChainIntake organizers and audits (organize, unified, curated, classify-api, transfer; audit generation/source/ckg/entire/completion; repair packet/titles/source): they already share `organize_and_retake_folders.py` helpers.
3. **One frontmatter/section parser**: six regex YAML readers and three section extractors across the evidence scripts.
4. **The synthesis family (32-35) onto station 48's output**: they read only the turbo companion markdown; the epistemic JSON (`claimed_mode`, `subject_tags`, `claim_evaluations`) and the three-dials `.ckg.json` are richer and unused. Station 48 now does the cross-corpus version.
5. **Normalize the rating scales** before combining anything: `paper_rating` 0-8, best-arguments /100, epistemic `final_score` 0-100.
6. **Paper Intelligence suite + `X:\04_STATIONS`**: not in the repo yet. Copy their code in (like the other folders) and station 42 wraps the suite through `config/metric_suites.json`; `_DORMANT` stations (contradiction-*, load-bearing-claims, series-flow-auditor, master-equation-canon, math-verify, sbert-embedder) should be checked before building anything new.

## Retired (not wired to the menu)

`taxonomy_validator.py` (nothing imports it), `lean_prover_bridge.py` (writes tautological `exact h` proofs; has a truncated duplicate `def`),
`generate_canonical_proof_companions.py` (hard-coded outputs), `migrate_outbox_to_flat.py` (one-off), `consolidated/` copies.
They are still vendored where they sit beside wired scripts, so nothing that imports them breaks.
