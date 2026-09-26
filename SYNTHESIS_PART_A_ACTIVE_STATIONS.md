# 04_STATIONS station library: code and docs survey

**Scope:** Read-only pass over `//192.168.2.50/brain/04_STATIONS`, covering the 23 stations you listed plus `_shared`, `_logs` and the top-level files. I did not open the A_*, _DORMANT, paper-intelligence-suite or paper-proof-grader folders. I also briefly read `03_WORKFLOWS/AtlasMethodComparison`, because four of the stations are only stubs that point to runner scripts there.

---

## 0. The ".station" convention and the shared contract

**Where it is defined**
- `_shared/SSS_v1_STANDARD.md` (the "Station Script Standard v1")
- `_shared/SSS_TEMPLATE_v1.py`
- `_shared/newstation.py` (scaffolder)
- `_shared/teststation.py` (smoke tester)
- `_ABOUT.md`, which says: "drop a file into a station's _inbox, run RUN.bat, result appears in _outbox… one file in, one processed file out."

**Folder layout.** Each station is a folder named `<name>.station/` containing:
- `_inbox/`: inputs land here.
- `_outbox/`: JSON artifacts go here; the next station picks them up from here.
- `_processed/`: inputs are moved here after processing. A timestamp suffix is added if the name collides.
- `_logs/`: log file named `{STATION_ID}_{STATION_NAME}_{YYYYMMDD}.log`.
- `_state/`
- `_exports/`: only for terminal stations.
- Files: `pipeline.py`, `config.json`, `RUN.bat`, and optionally `README.md` and `station.json`.

**Script structure.** `pipeline.py` has 13 fixed sections:
- 00 IMPORTS, 01 CONSTANTS, 02 CONFIG, 03 LOGGING, 04 INGEST, 05 VALIDATE
- **06 NLP_ROUTE** and **07 PROCESS** are the only per-station sections
- 08 ARTIFACTS, 09 WORKFLOW/JOB_CARD, 10 HANDOFF, 11 ARCHIVE, 12 MAIN

The maintenance scripts depend on this structure. `_FIX_ALL_STATIONS.py`, `_FIX_SLOW_STATIONS.py` and `_FIX_SUMMARY_STATIONS.py` rewrite code between the literal markers `# 06_NLP_ROUTE  *** STATION-SPECIFIC ***` and `# 08_ARTIFACTS`.

**Paths.**
- Everything is relative to the script: `HERE → STATIONS → BRAIN`.
- `_resolve("05_MODELS","models")` tries the numbered NAS folder first and falls back to the flat repo layout. It is used for `05_MODELS`, `06_ENGINES`, `03_WORKFLOWS` / `03_JOB_CARDS` and `10_EXPORTS`.

**`config.json` manifest fields**
- Identity: `station_id` (ST_nnn), `station_name`, `description`
- `station_type`: `"one_for_one"`
- `input_extensions`
- `workers`: `{default:[Mxx], optional:[]}`
- `outputs`: `{artifact_type:"json", update_job_card, final_export}`
- `templates`: grouped by role and resolved against `15_TEMPLATES`

A separate `station.json` (schema `theophysics.station.v1`) appears on some stations with `role`, `status`, `inputs`, `outputs` and `side_effects`.

**Artifact envelope.** The artifact is named `ART_{YYYYMMDD_HHMMSS}__{STATION_ID}__{input_stem}.json`. It contains:
- `input_file`, `station_id`, `station_name`, `nlp_used`, `api_endpoint`
- `processed_at`, `success`
- `artifacts[]`, `errors[]`, `data{}`

This comes from `_shared/station_helpers.base_result`. `teststation.py` asserts that these keys are present.

**Lifecycle:** config → log → ingest → validate → nlp_route → process → artifact → workflow/job card (a no-op stub in all stations) → handoff (copies to `_exports` only if `final_export`) → archive.

**Shared NLP service**
- All model work goes over HTTP to a FastAPI service at `http://localhost:8700/nlp/{endpoint}`. The code lives at `D:\GitHub\BACKSIDE-NLP-NEW\nlp_api\main.py`, not in this library.
- Documented endpoints: `contradiction`, `classify`, `embed`, `summarize`, `ner`, `sentiment`, `qa`, plus `/health`.
- **`/nlp/generate` is not implemented:** it returned 404 in the ST_002 artifact. So every "LLM" path that uses `generate` silently falls back.
- The model ID registry (M01–M16, from `CORE_8_NLP_CHEAT_SHEET.md`) maps IDs to Hugging Face models:
  - summarizer: BART-large-CNN
  - zero-shot: `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`
  - NLI: DeBERTa-v3-large-mnli-fever-anli-ling-wanli
  - embed: Qwen3-Embedding-0.6B / MiniLM
  - QA: `roberta-base-squad2`
  - NER: `dslim/bert-base-NER`
  - The LLM slot is "phi4" (Ollama).

**Registries and other top-level files**
- `STATION_REGISTRY.json` (updated 2026-08-11 for the method stations; ST_068 youtube-fact-finder appears at the end of the file) has one entry per station with `path`, `has_run_bat`, `type` (`local`/`api`/`remote`) and `note`. The rule: "Workflows resolve paths from this file." Most entries still point at `X:\Backside\_Stations\...` legacy paths.
- `ATLAS_STATION_CAPABILITY_REGISTRY.v1.json`: 15 ordered capabilities, one per station, each with the AtlasRecord fields it owns and whether it is required for Candidate or Admission. Its canonical schema is `D:/GitHub/Faith-through-physics-atoms/_schema/atlas_record_v1.schema.json`. It lists nabla-chi-classifier under `_DORMANT`, but that station now sits at the top level.
- `TYPED_STATION_FOLDERS_20260613.md` proposes typed `INPUT\claims` / `OUTPUT\verdicts` subfolders. Nothing in scope uses them.
- Top-level `START.bat` / `PROCESS_INBOX.bat` / `HEALTHCHECK.bat` call `_front_door\process_inbox.py` and `health.py`, but **`_front_door/` is empty**, so these are no-ops.
- `README.md` is a two-line stub.
- `_logs/` holds only June sbert/whisper logs.
- `_state/paper_vectors/` holds running-mean series vectors written by `station_helpers._build_series_context`.

**Other `_shared` modules**
- `station_helpers.py`:
  - `api_call`/`call_nlp`, `read_input`, `text_from_input`, `strip_html`
  - `split_sentences`/`split_paragraphs`/`split_sections`, `top_label`, `cosine`, `flesch_reading_ease`, `nlp_route`
  - `build_vectorization_payload` (calls `/nlp/embed` and keeps the series context)
- `job_card.py`: a JobCard class that writes to `_shared/job_cards/`. No station calls it.
- `topbar_common.py`: helpers for the top-bar station family.
  - `safe_generate()` calls `/nlp/generate` with the `NLP_GEN_MODEL` env var (default phi4) and degrades to extractive output.
  - Also provides the Flesch → audience ladder mapping.
  - Registry tag matching reads the CSV at env `TAG_REGISTRY_CSV` (default `D:\GitHub\David-OS-tagger-publish\tagger\spiritual_tag_registry.csv`).
- `canon_index.py`: deterministic canon index keyed to chi variables (G/M/E/S/T…); CLI `--out` and `--source`.
- `canonical_lexicon.py`: reads the lexicon xlsx at env `PAPER_GRADER_LEXICON_XLSX`.
- `fingerprint.py`: near-duplicate finder; CLI `folders… --threshold --report --export-river --max-files`.
- Health and validation tools: `station_healthcheck.py`, `validate_stations.py`, `scaffold_core_8.py`.
- `writing_audit/`: three local regex auditors (kimi measure-first, GPT-style adversarial, combined). Despite the names, none of them call an API.

**API keys.** Across the in-scope stations, only the NLP_FIS configs contain secrets: a hard-coded Postgres password in `NLP_file-intelligence-system-master/.../config/settings.ini` and in `settings.example.ini`. No LLM keys are hard-coded in scope. Only the Atlas method runner in `03_WORKFLOWS` uses LLM keys, and it reads them from env vars.

---

## 1. Station-by-station

### article-taxonomy-classifier (ST_009)
1. **Purpose:** Splits an article across 20 Theophysics topic categories (physics, theology, math, info-theory … ai) as percentages summing to 100, and infers audience and reading complexity. **Input:** `.html` / `.md` files in `_inbox`.
2. **Entry:** `pipeline.py` (not SSS format).
   - No argparse; reads `sys.argv` directly. Running it with no arguments processes the inbox.
   - `--file <path>` prints the result for one file only and writes nothing.
   - `RUN.bat` passes `%*` and honors env `PYTHON_EXE`.
3. **Output:** `_outbox/{stem}_taxonomy.json` plus a combined `_outbox/_all_taxonomy.json`. Fields:
   - `file`, `title`
   - `categories{20 × int%}`, `top_categories[5]`
   - `audience[believer|skeptic|researcher|story]`
   - `reading_complexity[story|framework|proof]`
   - It does **not** use the standard ART_ envelope.
4. **Local vs API:** Fully local keyword density (stdlib `re`). No model is used.
5. **Prompts:** `prompt.py` holds a SYSTEM_PROMPT that asks for JSON over the 20 categories, plus a USER_TEMPLATE. **It is never imported.** `station.json` says "hybrid — keyword + LLM refinement", but the LLM half is not implemented.
6. **Dependencies:** none.
7. **Status:**
   - Newest code: pipeline 2026-07-11; last output 07-11.
   - `station.json` says "scaffolded".
   - Bug: the keywords "AI"/"GPT"/"PEAR"/"GCP" are uppercase and the text is lowercased, so they never match.
   - The title is taken only from `<title>`, so `.md` files come out as "Untitled".
   - Verdict: a working baseline; the LLM half is a stub.

### atlas-record-assembler (ST_ATLAS_ASSEMBLE_001)
1. **Purpose:** An adapter, not a classifier. It combines a source file and the native station artifacts into one **Candidate** `AtlasRecord v1`. Anything missing becomes an explicit `unresolved[]` entry. **Input:** a source file plus optional station JSON artifacts.
2. **Entry:** `assemble.py`.
   - Required: `--source`, `--output`.
   - Optional: `--schema` (default is the D: path above), `--claims`, `--classification`, `--load-bearing`, `--falsification`, `--evidence`, `--contradiction`, `--nabla`, `--meta`.
   - `RUN.bat` runs `python assemble.py %*`.
3. **Output:** a single JSON file at `--output`, schema `atlas-record/v1`. Top-level keys:
   - `id{record_id, atom_id, stable_uid=sha256}`
   - `source{kind, title, content_hash, paths, source_spans, provenance}`
   - `nabla{classification, semantic_address, routing_hints, deterministic_status}`
   - `periodic15{marker_1..marker_15}`
   - `atom_stack{atom, components, claims[{claim_id, text, mode, mode_native, standing, native_grade, source_span_ids}], warrant, tests, dynamics.translation{probe_id, visible_questions, stored_fields, semantic_vector, factor_mentions, possible_veto_flags, veto_status}}`
   - `evidence_receipts`, `edges`, `bridges`, `anchors`
   - `reality_mirror`, `meta_argument`
   - `computed{graph_signature, grade_projection, load_bearing}`
   - `audit{candidate_or_admitted:"Candidate", subsystem_receipts, warnings}`
   - `unresolved`
   - The output is validated with `jsonschema` (Draft 2020-12).
4. **Local vs API:** local, deterministic; stdlib plus `jsonschema`.
5. **Prompts:** none.
6. **Dependencies:**
   - Consumes artifacts from claim-extraction (`data.claims`), claim-classification (`data.classified_claims`), the dormant load-bearing / falsification / evidence-map / contradiction-scan stations, nabla-chi-classifier (`nabla_proposal`, `dg7`), and a Meta-Argument adapter.
   - Needs the schema file on `D:\GitHub\Faith-through-physics-atoms`.
7. **Status:**
   - 2026-08-11, "implemented"; a `.bak` from before the nabla packet was added sits alongside.
   - Mismatch: `normalized_mode()` maps only axiom/assumption/empirical/formal/theorem. ST_003 emits `factual_claim` / `model_claim` / `opinion` / `definition`, so **every claim's `mode` comes out `UNKNOWN`**.
   - `_inbox`/`_outbox` are unused (CLI only).

### atlas-admission-gate (ST_ATLAS_ADMISSION_001)
1. **Purpose:** A fail-closed gate on AtlasRecord. It audits a record and leaves it as Candidate. It promotes to Admitted only when `--admit --reviewer` is given **and** every hard gate passes. **Input:** an AtlasRecord JSON.
2. **Entry:** `gate.py` with `--record` (required), `--schema`, `--output`, `--receipt`, `--admit`, `--reviewer`. `--admit` requires `--reviewer`. `RUN.bat` passes `%*`. Exit code 3 means Blocked.
3. **Output:**
   - `<record>.audited.json`: sets `audit.candidate_or_admitted` to Candidate, Admitted or Blocked, and appends a receipt, warnings and provenance.
   - `<record>.admission-receipt.json`: `receipt_type:"atlas_admission_gate/v1"`, `requested`, `resulting`, `reviewer`, `hard_gate_findings[{code, message}]`.
   - Finding codes: `SOURCE_HASH_MISSING`, `SOURCE_SPAN_MISSING`, `CLAIMS_MISSING`, `GRADE_UNRESOLVED`, `CANDIDATE_BRIDGE_IN_MARKER_4`, `REALITY_MIRROR_MARKER_16`, `META_ARGUMENT_NOT_SCORED`, `UNRESOLVED_REQUIREMENTS`, `LOAD_BEARING_REVIEW_MISSING`.
4. **Local vs API:** local; `jsonschema`.
5. **Prompts:** none.
6. **Dependencies:** consumes atlas-record-assembler output; uses the same D: schema.
7. **Status:** 2026-08-11, implemented and clean. As the assembler is currently wired, admission can never pass, because `unresolved` is always non-empty and `meta_argument` is not scored. The gate is behaving as designed.

### audience-level (ST_065)
1. **Purpose:** Places a document on the 7-rung ladder (ELI5, Middle School, High School, College, Graduate, PhD, Expert/Research) from its Flesch score. It also reports which of the three reading tiers (High School / College / PhD) the text natively fits. **Input:** `.md/.txt/.html/.htm` in `_inbox`.
2. **Entry:** `pipeline.py` (a slim SSS variant).
   - No CLI flags.
   - Env `AUDIENCE_MAKE_REWRITES=1` turns on LLM rewrites.
   - Exposes `run_text()` for an orchestrator.
   - **No `RUN.bat`**, and there are no `_inbox`/`_outbox` folders yet; they are created on first run.
3. **Output:** `_outbox/ART_*__ST_065__*.json`. The envelope comes from `topbar_common` and adds a `method` field. `data` contains:
   - `detected_level`, `native_tier`, `flesch_reading_ease`, `grade_estimate`, `word_count`, `audience_ladder`
   - `reading_tiers{High School|College|PhD:{available, native, text, flesch}}`
   - `method` (llm or extractive)
4. **Local vs API:** local Flesch. The optional rewrite goes to `localhost:8700/nlp/generate` (phi4), which does not exist, so the rewrite never happens.
5. **Prompts:** "Rewrite the following at a {10th-grade high-school / undergraduate college / doctoral} reading level. Preserve every claim and the section structure."
6. **Dependencies:** `_shared/topbar_common.py`.
7. **Status:** 2026-07-19. Config says worker `M22_zero_shot`, but the code never uses it. No runs recorded. Deterministic core works; the LLM path is dead.

### chi-evaluator (ST_CHI)
1. **Purpose:** χ-Evaluator v2. Scores a claim on 10 channels (G, M, E, S_eff, T, K, R, Q, F, C) and computes χ as the product of per-channel `v_pos × (1 − v_neg)`. It also runs 10 pressure states, infers a gradient and a verdict (coherent / partially coherent / fragile / high-signal deception / collapsed / repairable), and computes a Fruit score (tanh). **Input:** a claim.
2. **Entry:** `pipeline.py` with manual `sys.argv`:
   - `--demo`: hand-scored example, which it saves.
   - `--claim "text"`: **only prints the LLM prompt**.
   - No arguments: only prints "Would process…" for `_inbox` `*.md/*.txt`.
   - `RUN.bat` passes `%*`.
3. **Output:** `_outbox/CHI_{ts}__ST_CHI__{name}.json`, which is the `ChiEvaluation` dataclass:
   - `claim`, `claim_type`, `compressed_claim`
   - `channel_results[{channel, name, v_pos, v_neg, effective_score, gradient_direction, confidence, reasoning, evidence, failure_mode, repair_path}]`
   - `pressure_results[{pressure_state, chi, notes}]`
   - `fruit_output{dominant_fruits, dominant_antifruits, fruit_score, notes}`
   - `final_report`, `static_chi`, `gradient`, `zero_channels`, `weakest_channels`, `strongest_channels`, `verdict`
   - It does not use the standard envelope.
4. **Local vs API:** `chi_engine.py` is pure-math and local. `station.json` lists `llm_api` as a worker, but **no API call is implemented**. `prompt.py` says the prompt is for "OpenAI, Claude, DeepSeek, or local models".
5. **Prompts:** The SYSTEM_PROMPT defines the Master Equation χ = G·M·E·S_eff·T·K·R·Q·F·C ("product, not a sum"), the per-channel scoring, the 10 pressure states, and a Fruit vs anti-Fruit test. It includes "Be strict… Return only valid JSON." The USER_TEMPLATE asks for strict JSON with the keys listed above.
6. **Dependencies:** none. (The channel set conflicts with the nabla station's rule that "C_W is a wrapper, not a 10th factor"; see Overlap.)
7. **Status:** code dated 2026-06-18; the only outputs are three identical `demo` runs (last 07-11). **Stub**: the engine is real, the LLM integration is missing.

### claim-extraction (ST_003, Core-8)
1. **Purpose:** Extracts claims from text with their section context. **Input:** `.md/.txt/.html`.
2. **Entry:** SSS `pipeline.py` with no flags. `RUN.bat` runs `python pipeline.py`.
3. **Output:** `_outbox/ART_*__ST_003__*.json`. `data` contains:
   - `claims[{claim_id:"{stem}:claim-NNN", text, section, paragraph_index, sentence_index, claim_type ∈ factual_claim|model_claim|opinion|definition, classifier_score}]`
   - `total_claims`, `claims_by_type`
4. **Local vs API:** local NLP service. The route is labelled `qa_extractor` / `qa`, but it **actually calls `/nlp/classify` (zero-shot DeBERTa) once per sentence** with the labels factual claim, model claim, opinion, definition, narrative, metadata.
5. **Prompts:** none (zero-shot labels only).
6. **Dependencies:** `_shared.station_helpers`; the 8700 API. Its output feeds ST_004 and the atlas assembler.
7. **Status:**
   - pipeline.py dated 2026-07-17.
   - Only one success (demo, 06-17). The real article run on 06-19 **timed out at 120 s**, because one call per sentence is too many.
   - Many empty failure artifacts in `_outbox`.
   - Verdict: works as designed, but unscalable.

### claim-classification (ST_004, Core-8)
1. **Purpose:** Classifies each extracted claim by maturity and domain. **Input:** a `.json` / `.csv` ST_003 artifact.
2. **Entry:** SSS `pipeline.py`; `RUN.bat`; no flags.
3. **Output:** `data` contains:
   - `classified_claims[{...original claim, maturity_label, maturity_score, domain, domain_score, all_maturity_scores, all_domain_scores}]`
   - `maturity_distribution`, `domain_distribution`
   - Maturity labels: Formal Model, Structural Correspondence, Public Proof Claim, Empirical Support, Analogy, Metaphor, Assertion.
   - Domain labels: physics, theology, mathematics, consciousness, information_theory, ethics, empirical_data, historical.
4. **Local vs API:** local; `/nlp/classify` (zero-shot) twice per claim. The README describes an SBERT + DeBERTa two-stage design that is not what the code does.
5. **Prompts:** none.
6. **Dependencies:** ST_003 output; `_shared`; the 8700 API.
7. **Status:** code 2026-07-17. Every `_outbox` artifact (06-18) has empty `classified_claims`: the upstream inputs were HTML test files, not ST_003 JSON. It has not been proven on real data.

### convergence-tagger (ST_067)
1. **Purpose:** A wrapper that runs the external C-drive Theophysics tagger over a folder and mirrors the tag/search ledgers into the atom repo runtime. It "does not promote claims to canon". **Input:** a folder or file (default `D:\GitHub\faiththruphysics-site-data\B_consciousness`).
2. **Entry:** `pipeline.py` with argparse `--source`, `--limit N`, `--copy-by-primary-tag`. `RUN.bat` passes `%*`.
3. **Output:**
   - The native tagger writes CSVs to `C:\Theophysics_Tagger\02_INDEX`: `*_document_tags.csv`, `*_paragraph_tags.csv`, `*_sentence_tags.csv`, `*_folder_suggestions.csv`, `*_summary.json`.
   - These are copied to `D:\GitHub\Faith-through-physics-atoms\_runtime\convergence_tagger_runs\{ts}_convergence_tagger\`, together with `run_manifest.json` and `run_receipt.md`.
   - The station artifact `_outbox/ART_*__ST_067__convergence_tagger.json` has: `generated_at`, `started_at`, `status`, `returncode`, `source`, `registry`, `tagger_script`, `summary_path`, `copied_outputs`, `documents_tagged`, `paragraph_hits`, `sentence_hits`, `stdout`, `stderr`.
4. **Local vs API:** local subprocess of `C:\Theophysics_Tagger\tools\tagger.py` with registry `C:\Theophysics_Tagger\01_REGISTRY\tag_registry.csv`.
5. **Prompts:** none.
6. **Dependencies:** the external tagger on C: and the atoms repo on D:. It only works on David's workstation, not from the NAS alone.
7. **Status:** 2026-08-01, one passing run (3 docs). An ST_066-stamped copy of this receipt sits in `topbar-tagger.station/_outbox`, which looks like it was first built in the wrong folder and reused ST_066.

### exec-summary (ST_001, Core-8)
1. **Purpose:** Executive summary plus key entities. **Input:** `.md/.txt/.json/.html`.
2. **Entry:** SSS `pipeline.py`; `RUN.bat`; no flags.
3. **Output:** `data` contains `title`, `summary`, `key_entities[{entity, word, score, start, end}]`, `section_count`, `word_count`, `estimated_reading_time_min`, `source_format`.
4. **Local vs API:** local. It calls `/nlp/summarize` (BART) and chunk-maps above 4096 characters, then calls `/nlp/ner` (`bert-base-NER`).
5. **Prompts:** none.
6. **Dependencies:** `_shared`; the 8700 API.
7. **Status:**
   - Code 2026-07-17.
   - One real success on 06-19. The NER output is raw wordpieces (`##ve`, `Decoh`) with no aggregation.
   - Latest run (08-14) failed with "connection refused" on port 8700.
   - Works when the API is up; output quality is rough.

### external-api-audit (ATLAS_METHOD_03)
1. **Purpose:** The external-API lane of the Atlas Method Comparison. It runs the shared 8-stage contract through an external LLM, isolated from the local lane.
2. **Entry:** The station folder contains only `station.json` plus empty lifecycle dirs. The runner is `03_WORKFLOWS/AtlasMethodComparison/SCRIPTS/run_lane.py`:
   - `--packet`, `--contract`, `--runtime` (required)
   - `--lane {local_nlp, external_api}`
   - `--provider {deepseek, openai}`
   - `--output`, `--raw-dir`
   - Launched through `RUN_COMPARISON.bat paper.md deepseek`.
3. **Output:** `external-api.run.json` plus raw API receipts, per run under `03_WORKFLOWS/AtlasMethodComparison/OUTPUT/<ts>_<hash>/`. It follows schema `atlas-method-run/v1` with stages:
   - 01_claims, 02_classification, 03_dependencies, 04_falsification, 05_evidence, 06_contradictions, 07_dynamics (Nabla/DG7), 08_synthesis
   - Required keys come from `CONFIG/process-contract.v1.json`, e.g. `claims[{claim_id, text, source_quote, extraction_status}]`, `claim_assessments[{mode, domain, standing, confidence}]`, `dependencies`, `load_bearing_claim_ids`, `tests`.
4. **Local vs API — API:**
   - **DeepSeek:** `https://api.deepseek.com/chat/completions`, model `deepseek-chat`, env **`DEEPSEEK_API_KEY`**, `temperature` 0, JSON response format, 5000 max tokens per stage.
   - **OpenAI:** `https://api.openai.com/v1/responses`, model `gpt-5-mini`, env **`OPENAI_API_KEY`**.
   - Source text is capped at 30,000 characters. No hard-coded key.
5. **Prompts:** A system prompt in `method_core.py` plus per-stage instructions from the contract. Example for claims: "Extract at most 30 material, separable claims. Ignore navigation… Preserve exact source quotations." Classification uses a fixed 14-value mode vocabulary (AXIOM … PREDICTION, UNKNOWN).
6. **Dependencies:** method-packet-builder (packet); consumed by method-convergence.
7. **Status:** 2026-08-11. Several real runs; per `IMPLEMENTATION_RECEIPT.md` the final run completed 8/8 stages with 8 raw receipts. **Production-ish**; the station folder itself is a pointer.

### fruits-spirit-canon (ST_017)
This folder holds **three separate tools**.

**(a) SSS `pipeline.py`**
- Purpose: embed-classifies the document against the 9 Fruits.
- It calls `/nlp/embed` once (the first 1000 characters plus the 9 labels) and ranks by cosine. It adds a keyword-hit check and vectorization.
- `data` fields: `fruits_present{fruit:{score, keyword_hit}}`, `fruit_count`, `dominant_fruit`, `full_ranking[{label, score}]`, `vectorization`.
- `final_export: true`, so it copies to `10_EXPORTS`.

**(b) `fruits_coherence_engine.py`**
- The real engine: a local multi-layer word → sentence → paragraph-role → paper scorer with domain polarity and structural-invariant checks.
- CLI: `input` (positional), `--lexicon xlsx`, `--outdir`, `--xlsx`, `--context-window`.
- The wired launcher is `run_fruits_engine.py` / `RUN_FRUITS_ENGINE.bat`. It takes `DROP_HERE\`, auto-picks the newest `LEXICON\*.xlsx` (env `PAPER_GRADER_LEXICON_XLSX` points to a default on `\\dlowenas\HPWorkstation`), and writes to `EXPORTS\fruits_reports\run_<ts>\`.
- Output files: `fruits_coherence_report.json` / `.md`, `paper_scores.csv`, `paragraph_scores.csv`, `sentence_scores.csv`, `word_trace.csv`, `.xlsx`.
- The per-paper `PaperScore` has: `file`, `word_count`, `sentence_count`, `paragraph_count`, `raw_score`, `normalized_score` (0–100), `grade` (A…F), `fruit_scores`, `domain_scores`, `top_positive_fruits`, `top_negative_fruits`, `paragraph_role_distribution`, `summary`, `warnings`.

**(c) `station.py`**
- Canon index built with `_shared/canon_index.py` over two source files on `\\dlowenas\HPWorkstation\Desktop\Cannon\`.
- Invoked through `RUN.bat` → `station.py --out <dir>`.
- Outputs `canon-index.json` / `.md`.

**Shared facts for all three**
- Local vs API: (a) uses the 8700 embed service; (b) and (c) are pure local (`openpyxl` optional). There is no LLM call, although `prompt.md` describes an extraction prompt ("Extract fruit terms, anti-fruit terms, equation mappings, and chi-variable evidence").
- Dependencies: `_shared/station_helpers`, `_shared/canon_index`, the lexicon xlsx.
- Status:
  - Engine 2026-06-16; the last EXPORTS run was 06-03; `_outbox` runs are from 06-18.
  - `pipeline_legacy.py` is byte-identical to `run_fruits_engine.py`.
  - The config template points at `15_TEMPLATES/Fruits Template (1).xlsx`.
  - The engine is production-grade; the SSS pipeline is a thin embed-only version.

### local-nlp-audit (ATLAS_METHOD_02)
1. **Purpose:** The local lane of the same 8-stage method contract.
2. **Entry:** `station.json` only. The runner is `run_lane.py --lane local_nlp`, or `RUN_LOCAL_ONLY.bat paper.md`.
3. **Output:** `local-nlp.run.json` with the same stage schema.
4. **Local vs API:** tries `localhost:8700/nlp/classify` (8 s timeout, `/health` probe first). If that fails it uses `deterministic_lexical` and labels the result as such. In every recorded run the service was down, so the fallback was used.
5. **Prompts:** none.
6. **Dependencies:** method-packet-builder.
7. **Status:** 2026-08-11. Pointer station; the runner works.

### method-packet-builder (ATLAS_METHOD_01)
1. **Purpose:** Freezes one source together with the process contract, stage order and SHA-256 hashes into `atlas-method-packet/v1`.
2. **Entry:** `station.json` → `03_WORKFLOWS/AtlasMethodComparison/SCRIPTS/build_packet.py`.
3. **Output:** `method-packet.json`, `source.md` copy and `manifest.json` in the run folder.
4. **Local vs API:** local.
5. **Prompts:** none.
6. **Dependencies:** `CONFIG/process-contract.v1.json` and `runtime.json`.
7. **Status:** 2026-08-11. Pointer station; `STATION_REGISTRY` marks `has_run_bat: false`.

### method-convergence (ATLAS_METHOD_04)
1. **Purpose:** Compares the two lanes field by field **without** promoting anything to truth or grade.
2. **Entry:** `station.json` → `compare_runs.py`.
3. **Output:** `comparison.json` (`atlas-method-comparison/v1`) with per-stage agreement scores and an overall agreement band.
   - Weights: structural 0.25, field 0.35, content 0.40.
   - Bands: high ≥ 0.80, moderate ≥ 0.60.
   - Last run: 0.5191, LOW.
4. **Local vs API:** local.
5. **Prompts:** none.
6. **Dependencies:** outputs from both lane stations.
7. **Status:** 2026-08-11. Pointer station.

### nabla-chi-classifier (revived from _DORMANT 2026-08-11)
1. **Purpose:** Proposes a Nabla semantic address (a 10-dimension vector G M E S T K R Q F C) and a DG7 dynamics reading. It **never computes χ** and never enforces a veto. **Input:** `.md/.markdown/.txt` in `_inbox`, or `source_globs` from config. Minimum 40 words.
2. **Entry:** SSS-style `pipeline.py` with no flags. `RUN.bat`. There is also `test_packet.py`.
3. **Output:**
   - `_outbox/{stem}.nabla-dg7.json`, schema `nabla-chi/1.1`:
     - `station`, `generated_utc`
     - `identity{path, filename, title, sha256, words}`
     - `nabla_proposal{proposer, words, semantic_vector, semantic_vector_string, evidence_terms, factor_mentions, factor_names, possible_veto_flags, veto_status:"NOT_ADJUDICATED", confidence}`
     - `dg7{visible_questions, stored_fields}`. Stored fields: coherence, degradation, measure, threshold, asymmetry, restoration_self, restoration_external, counterexample. Status is PRESENT / PARTIAL / ABSENT only.
     - `classification:"NABLA_SEMANTIC_PROPOSAL"`, `semantic_address`, `pairing_hash`, `routing_hints`, `lane`
   - Also writes `_SUMMARY_{ts}.json`, `_NEEDS_RULING.json` (ABSENT slots and veto flags queued for a human), and `_state/last_run.json`.
   - Inputs are **not** archived (`archive_inputs: false`).
4. **Local vs API:** local, stdlib regex density only ("Tier 1"). The Tier 2 M02 embed rerank is not wired.
5. **Prompts:** none.
6. **Dependencies:** own modules (`nabla_engine.py` is marked "do not edit", plus `semantic_proposer`, `dynamics_probe`, `master_equation_types`). Its output feeds `atlas-record-assembler --nabla`.
7. **Status:**
   - Code 2026-08-11/12, but `_outbox` is empty: no run recorded here.
   - README: "Known, not yet calibrated" (`mention_min` thresholds).
   - The capability registry still lists its path under `_DORMANT`.
   - The code itself looks production-grade.

### NLP_file-intelligence-system-master (FIS v1 repo, not a .station)
1. **Purpose:** File-classification and renaming system. It extracts text, runs YAKE + spaCy (+ KeyBERT at low confidence), assigns a domain/subject code with an SGD classifier, and renames to `slug_DOMAIN.SUBJECT_SEQ.ext`. Above 85 confidence it auto-renames; 50–85 goes to a queue; below 50 goes to a kickout list. It stores everything in Postgres, and a River-based "BIL" behavioral learner sits on top. **Input:** watched folders (Desktop, OneDrive, Downloads, `O:\_Theophysics_v3`), hotkeys, or backfill.
2. **Entry:** `python -m fis <cmd>` with manual argv commands: watch, backfill, popup, tray, export, import, init, seed, bil-export, api [port, default 8420], clipboard, all, codes, start, stop, status, install, uninstall, `_service`, cold-start [--dry-run]. There is also `INSTALL.bat`, an AHK hotkey script (Ctrl+Alt+F/S/K/B), a browser extension, and `obsidian_auto_sorter.py`. The sorter is a standalone lexicon-CSV sorter with hard-coded `Z:\Theophysics_Vault` paths that writes a dry-run CSV.
3. **Output:** Postgres `fis_db` (schema in `sql/01_schema.sql`), `.fis_meta.json` per folder, renamed files, a kickouts xlsx, BIL daily digests, and a local HTTP API on :8420.
4. **Local vs API:**
   - All local: YAKE, spaCy `en_core_web_sm`, KeyBERT (`distilbert-base-nli-mean-tokens`), Model2Vec, faster-whisper (small, int8, CUDA), scikit-learn, River, PySide6.
   - No LLM.
   - **Hard-coded Postgres password in `config/settings.ini` and `config/settings.example.ini`.** The example file should not contain a real password.
5. **Prompts:** only `AI_CODE_AUDIT_DEBUG_PROTOCOL.md`, a paste-in prompt for code review ("You are a senior software engineer and code auditor…").
6. **Dependencies:** a Postgres host (settings.ini points it at a different port from the example). Standalone otherwise. `STATION_REGISTRY` lists both a legacy `file-intelligence.station` and `_front_door/fis.station` ("FIS v2"), but `_front_door` is empty.
7. **Status:** repo dated 2026-06-10; the sorter was touched 07-15. It is a vendored app with no SSS wrapper. A zip copy also sits at the 04_STATIONS root.

### paper-grade-composer (ST_050)
1. **Purpose:** Composes a paper-grade payload for dashboards by combining the source text with the latest paper-intelligence-suite (ST_038) and paper-proof-grader (ST_039) outputs. **Input:** `.md/.txt/.json/.html/.htm`.
2. **Entry:** SSS `pipeline.py`; `RUN.bat` (honors `PYTHON_EXE`, passes `%*`, but there is no argparse).
3. **Output:** Three files in `_outbox` plus the standard envelope:
   - `ART_*__ST_050__{stem}.paper-grade.json`, with fields:
     - `paper_id`, `source_file`, `source_path`, `generated_at`
     - `metrics{word_count, char_count, section_count, equation_count, claim_candidate_count, top_terms, proof_anchor_count, source_hash, fruit_density, dominant_fruit}`
     - `sections`, `equations`, `claims`, `claims_source`, `station_marks`
     - `version_reading{easy, academic}`, `lossless_summary`, `upstream`, `proof_scores`, `fruit_dynamics`, `vectorization`
   - `.paper-grade.md`
   - `.paper-snapshot.json`, with `semantic_address`, `semantic_vector`, `semantic_hash`, `epistemic_status{rigor_verdict, overall_tier}`, `math_translation_layer`, `station_marks`
4. **Local vs API:** local; the only service call is `/nlp/embed` for vectorization.
5. **Prompts:** none.
6. **Dependencies:** reads `_outbox` of `paper-intelligence-suite.station` and `paper-proof-grader.station`; `_shared.station_helpers`. `EXPORTS` resolves to `10_EXPORTS/1 Exports TEST`.
   - Risk: `_find_station_output` falls back to **the newest artifact regardless of stem**, so it can attach another paper's upstream data.
7. **Status:** 2026-06-18, two test runs. Working prototype.

### plain-language (ST_002, Core-8)
1. **Purpose:** Rewrites a document at three levels: easy (grade 6), standard (grade 10), and academic (the original). **Input:** `.md/.txt`.
2. **Entry:** SSS `pipeline.py`; `RUN.bat`.
3. **Output:** `data` contains `versions{easy|standard|academic:{text, reading_level, flesch_kincaid, word_count}}` and `section_count`.
4. **Local vs API:** calls `localhost:8700/nlp/generate` with `model: "phi4"`. **That endpoint returns 404.** On failure the station records an error; if the call "succeeds" with an empty result, the `_rewrite` fallback returns the original text.
5. **Prompts:**
   - Inline: "Rewrite this at a {target} reading level. Keep all facts and preserve section structure."
   - `prompt.md` has a richer, unused template: keep all facts and numbers, sentences under 20 words, everyday analogies, no new claims.
6. **Dependencies:** `_shared`; the 8700 API.
7. **Status:** code 2026-07-17. **Every recorded run failed** (404). Broken until `/generate` exists.

### reading-level-glossary (ST_047)
1. **Purpose:** Estimates Flesch-Kincaid grade against a target (8th grade by default) and builds a glossary of terms likely above that level. It does not rewrite text. **Input:** `.md/.txt/.json/.html/.htm`.
2. **Entry — two entry points:**
   - SSS `pipeline.py`: `_inbox` → `_outbox`; no flags.
   - `pipeline_legacy.py`: argparse `--file` (repeatable), `--target-grade`, `--max-terms`. It reads `DROP_HERE` and writes to `EXPORTS/run_*`. The README describes this legacy path.
   - `RUN.bat` hard-codes Python paths under `C:\Users\lowes\...` and runs the SSS `pipeline.py` with `%*`, but that script ignores the arguments.
3. **Output:**
   - `_outbox/ART_*__ST_047__*.json` with `data.analysis`.
   - `_outbox/phase2_logic/{stem}.readability_glossary.json` / `.md` and `{stem}.glossary.csv`.
   - Fields: `source_file`, `source_name`, `timestamp`, `target_label`, `target_grade`, `estimated_grade`, `status` (PASS / REVIEW / TOO_SHORT), `word_count`, `sentence_count`, `syllable_count`, `glossary_count`, `glossary_definition_sources{api, heuristic, api_failed}`.
   - `glossary[{term, key, count, syllables, estimated_word_grade, reason, definition, definition_source, definition_error, context}]`
   - The legacy path also writes `run_index.json` / `.md`.
4. **Local vs API:**
   - Local syllable counting and heuristics.
   - An optional generic definition API is configured under `definition_api` in `config.json`. It is `enabled: false`, the endpoint is empty, and the key is empty. It supports `api_key_env` or an inline `api_key`.
   - Config names worker `ner_general`, but the code does not use it.
5. **Prompts:** none (the API payload is `{"term": "${term}"}`).
6. **Dependencies:** none. `templates` points at `15_TEMPLATES` lexicon and definition templates.
7. **Status:**
   - pipeline 06-18, legacy 07-11; last output 07-11 (a successful 55 KB artifact).
   - The SSS `pipeline.py` is a copy of a multi-station generated blob. Its `process_one` has branches for classify-documents, session-handoff-drop, link-pull, harvest-links and paper-proof-grader, and only the `reading-level-glossary` branch runs.
   - Working.

### summarizer (ST_054)
1. **Purpose:** Three-tier summary: one sentence, one paragraph, and a 3–4-paragraph executive summary (map-reduce over chunks of about 3500 characters). **Input:** `.md/.txt/.json`.
2. **Entry:**
   - SSS `pipeline.py` calls `summary_runner.py`.
   - `RUN.bat` (honors `PYTHON_EXE`).
   - `FRONT_DOOR.bat`: an optional `FETCH_SOURCE.txt` names a folder to xcopy into `_inbox` first.
3. **Output:**
   - Envelope `data{action, worker, input_type, summaries{sentence, paragraph, executive[], chunks_skipped, engine:"bart-via-nlp_api", quality_note}}`.
   - Plus `_outbox/{stem}.summary.json` (`{source, summaries}`) and `{stem}.summary.md`.
4. **Local vs API:** local BART via `/nlp/summarize`. The URL can be overridden with env `NLP_API_URL` or config `nlp_api_url`. Chunks that are less than 65% prose are skipped, and each call is retried once.
5. **Prompts:** none sent. `prompt.md` has unused guidance: "Compress without flattening the structure… cite section anchors."
6. **Dependencies:** the 8700 API.
7. **Status:**
   - Wired 2026-07-01. One successful run (about 4 minutes for one document).
   - The README still says "SKELETON" — stale.
   - Promised "source span pointers" and "compression ratio" are not implemented.
   - Working.

### summary-quad (ST_064)
1. **Purpose:** One pass, four summaries: `one_sentence`, `two_sentence`, `executive` (about 120 words), `short_story`. **Input:** `.md/.txt/.html/.htm`.
2. **Entry:** `pipeline.py` (slim SSS; `run_text()` for an orchestrator). No `RUN.bat` and no lifecycle dirs yet.
3. **Output:** `_outbox/ART_*__ST_064__*.json`, with `data{title, summaries{one_sentence, two_sentence, executive, short_story}, word_count, method}`.
4. **Local vs API:** `safe_generate` → `/nlp/generate` (phi4), which does not exist. It therefore always falls back to extractive TextRank-lite via `topbar_common.keyword_sentences`. The fallback "short story" is a template that wraps extracted sentences in canned framing ("It starts with a simple question hiding inside…").
5. **Prompts:**
   - "In ONE sentence, state the single central claim of this text."
   - "In exactly TWO sentences, summarize this text: what it argues and why it matters."
   - "Write a ~120-word executive summary… Preserve the key claims and the conclusion."
   - "Retell the core idea… as a short, plain-language narrative (4-6 sentences)… Keep it faithful."
6. **Dependencies:** `_shared/topbar_common.py`.
7. **Status:** 2026-07-19. No outputs recorded. Extractive-only in practice.

### topbar-tagger (ST_066)
1. **Purpose:** Registry-driven tagging for the faiththruphysics top bar. It finds which spiritual-registry tags, tag categories and Master-Equation variables (C E F G K M Q R S T) appear in a document, and builds term pills, paragraph-level tags and the `/api/tagger/top-bar-options` payload. **Input:** `.md/.txt/.html/.htm`.
2. **Entry:** `pipeline.py` (slim SSS; `run_text()`). No `RUN.bat`.
3. **Output:** `_outbox/ART_*__ST_066__*.json`, with `data` containing:
   - `tag_count`, `tags[{tag, slug, category, master_equation_variable, hits}]`
   - `categories`, `master_equation`
   - `term_pills[{id, label, tone, category, master_equation_variable, hits}]`
   - `paragraph_tags[{index, top_tags}]`
   - `top_bar_options{audienceLevel, tagCategories, masterEquation, scope, copyMode}`
   - `selected{tagCategories, masterEquation}`
   - `method:"registry"`
4. **Local vs API:** pure local regex/alias matching over the CSV at `D:\GitHub\David-OS-tagger-publish\tagger\spiritual_tag_registry.csv` (env `TAG_REGISTRY_CSV`). If that CSV is missing, it silently produces zero tags.
5. **Prompts:** none.
6. **Dependencies:** `_shared/topbar_common.py`; the D: registry CSV.
7. **Status:**
   - Code 2026-07-19.
   - No genuine ST_066 run: the only `_outbox` file is the misplaced convergence-tagger receipt.
   - `config.json` was edited 08-01.

### youtube-fact-finder (ST_068)
1. **Purpose:** Takes a YouTube transcript, extracts claims that look check-worthy, classifies each one, and tests it against its own transcript with NLI. **It does not verify external truth** ("'checkable' marks a claim worth verifying, not a verified claim"). **Input:** `.json` (`url` / `video_id` / `transcript` / `text`), or `.txt` / `.md` containing either a transcript or a YouTube URL.
2. **Entry:** SSS `pipeline.py` scaffolded by `newstation.py`; no flags. `RUN.bat` uses `py -3.12` (overridable with env `STATION_PY`). Config: `checkworthy_threshold` 0.5, `max_claims` 40.
3. **Output:** `_outbox/ART_*__ST_068__*.json`. `data` contains:
   - `source{input_kind, video_id, url, transcript_origin ∈ supplied|fetched|fetch_failed|file_text}`
   - `transcript_chars`, `transcript_words`, `method` (nlp or heuristic), `claim_count`, `by_maturity`, `needs_human_verification`, `verification_note`
   - `claims[{claim_index, claim, checkworthiness, maturity, maturity_score, domain, domain_score, checkable, checkable_score, self_consistency, method}]`
4. **Local vs API:**
   - Optional `youtube_transcript_api` fetch (supports both old and new API shapes).
   - The check-worthiness score is a heuristic: factual verbs, numbers and length raise it; hedges lower it.
   - When the service is alive (env `NLP_API_URL`, default `localhost:8700`), it makes three `/nlp/classify` calls per claim (maturity, domain, checkability) plus one `/nlp/contradiction` call (the first 2000 characters of the transcript as premise).
   - If the service is down, the result is labelled `HEURISTIC_ONLY`.
   - No LLM, no keys.
5. **Prompts:** none. The zero-shot label sets reuse ST_004's maturity and domain labels (lower-cased) plus three "checkability" labels.
6. **Dependencies:** the 8700 API and the optional pip package. It does not use `_shared.station_helpers`; it has its own urllib client.
7. **Status:** 2026-08-15/16. Three successful runs with `method=nlp` on 08-16 (5, 12 and 40 claims). Newest and most polished station. Limit: NLI self-consistency uses only the first 2000 characters, so claims late in a long transcript are tested against unrelated context.

---

## 2. Status notes that apply across stations

- **Port 8700 dependency.** Every Core-8 / SSS model station depends on the NLP FastAPI service. It was down on 06-19 (timeout) and 08-14 (refused), and up on 08-16. The `/generate` endpoint used by plain-language, summary-quad and audience-level does not exist, so the "LLM" branches never run.
- **Core-8 is not end-to-end.** The pipeline ST_001→ST_008 has ST_005–008 in `_DORMANT`. The job card (09) and handoff (10) are stubs everywhere, and nothing auto-routes one station's `_outbox` into the next `_inbox`.
- **Stale docs:**
  - summarizer README says "SKELETON" but the station is wired.
  - claim-classification README describes an SBERT + DeBERTa design; the code is zero-shot only.
  - chi-evaluator lists `llm_api` as a worker, but nothing is wired.
  - `_ABOUT.md` lists "API fruits-api-caller — 12 Fruits via Claude API", which is not in this folder.
- **ID collisions and irregular IDs:**
  - ST_066 was used by both topbar-tagger and the first convergence-tagger run.
  - Non-numeric IDs: ST_CHI, ST_ATLAS_*, ATLAS_METHOD_0x, "nabla-chi-classifier", ST-HTML-* in several `station.json` files.
- **Machine-specific paths:** `C:\Theophysics_Tagger`, `D:\GitHub\...` (schema, registry CSV, atoms runtime), `C:\Users\lowes\...` Python paths, `Z:\Theophysics_Vault`, and `\\dlowenas\HPWorkstation\...` for canon and lexicon files. These stations are not portable from the NAS alone.

---

## (a) Summary table

| Station | API or local | Key outputs |
|---|---|---|
| article-taxonomy-classifier | Local keyword (LLM prompt unused) | `{stem}_taxonomy.json`: `categories{20%}`, `top_categories`, `audience`, `reading_complexity` |
| atlas-record-assembler | Local deterministic + jsonschema | AtlasRecord v1 Candidate: `id`, `source`, `nabla`, `periodic15`, `atom_stack`, `evidence_receipts`, `edges`, `audit`, `unresolved` |
| atlas-admission-gate | Local deterministic | `.audited.json` + `.admission-receipt.json` (Candidate/Admitted/Blocked, `hard_gate_findings`) |
| audience-level | Local Flesch (+ dead `/generate`) | `detected_level`, `native_tier`, `flesch_reading_ease`, `grade_estimate`, `reading_tiers` |
| chi-evaluator | Local math; LLM stub (no calls) | `CHI_*.json`: `channel_results`, `pressure_results`, `static_chi`, `verdict`, `gradient`, `fruit_output` |
| claim-classification | Local NLP svc (zero-shot) | `classified_claims[+maturity_label, domain…]`, distributions |
| claim-extraction | Local NLP svc (zero-shot per sentence) | `claims[{claim_id, text, section, claim_type, classifier_score}]` |
| convergence-tagger | Local subprocess (C: tagger) | document/paragraph/sentence/folder tag CSVs + run receipt |
| exec-summary | Local NLP svc (BART + NER) | `summary`, `key_entities`, `word_count`, `reading_time` |
| external-api-audit | **API: DeepSeek `deepseek-chat` (`DEEPSEEK_API_KEY`) / OpenAI `gpt-5-mini` (`OPENAI_API_KEY`)** | `external-api.run.json` (8 stages) + raw receipts |
| fruits-spirit-canon | Local (engine, canon index); NLP svc embed (SSS) | fruits_coherence_report json/md/csv/xlsx (grade A–F); `fruits_present`; canon-index |
| local-nlp-audit | Local NLP svc or lexical fallback | `local-nlp.run.json` (8 stages) |
| method-packet-builder | Local | `method-packet.json` (source + contract hashes) |
| method-convergence | Local | `comparison.json` (per-stage agreement, band) |
| nabla-chi-classifier | Local regex (stdlib) | `*.nabla-dg7.json`, `_SUMMARY_*`, `_NEEDS_RULING.json` |
| NLP_file-intelligence-system | Local (YAKE, spaCy, KeyBERT, whisper, sklearn, River) + Postgres; **hard-coded DB password in settings.ini / settings.example.ini** | renamed files, Postgres records, `.fis_meta.json`, kickouts xlsx, :8420 API |
| paper-grade-composer | Local (+ NLP svc embed) | `.paper-grade.json/.md`, `.paper-snapshot.json` |
| plain-language | Local NLP svc `/generate` phi4 (**404, broken**) | `versions{easy, standard, academic}` |
| reading-level-glossary | Local; optional generic definition API (disabled) | `readability_glossary.json/.md`, `glossary.csv` (PASS/REVIEW) |
| summarizer | Local NLP svc (BART) | `summary.json/.md`: `sentence`, `paragraph`, `executive[]` |
| summary-quad | Local extractive (dead `/generate`) | `one_sentence`, `two_sentence`, `executive`, `short_story` |
| topbar-tagger | Local registry CSV | `tags`, `categories`, `master_equation`, `term_pills`, `paragraph_tags`, `top_bar_options` |
| youtube-fact-finder | Local NLP svc (zero-shot + NLI) + optional YouTube transcript fetch | `claims[{checkworthiness, maturity, domain, checkable, self_consistency}]` |

## (b) Overlap and duplication

1. **Summarization is done in four places:**
   - exec-summary (ST_001: BART + NER)
   - summarizer (ST_054: BART three-tier)
   - summary-quad (ST_064: four summaries, extractive/LLM)
   - the atlas method lane's 08_synthesis
   
   ST_001 and ST_054 both call `/nlp/summarize` with different chunking. summary-quad's "executive" duplicates both.
2. **Reading level is handled by four stations:**
   - plain-language (ST_002: rewrites with FK scores)
   - audience-level (ST_065: Flesch ladder, optional rewrites with a near-identical prompt)
   - reading-level-glossary (ST_047: FK grade + glossary)
   - article-taxonomy's `reading_complexity`
   
   There are three separate Flesch implementations: `station_helpers`, `topbar_common` and glossary legacy.
3. **Claim extraction and classification are done three ways:**
   - ST_003 + ST_004 (zero-shot)
   - youtube-fact-finder, which copies ST_004's maturity/domain labels and re-does extraction with its own heuristic
   - the Atlas method lanes (01_claims / 02_classification, using a *different* 14-value mode vocabulary)
   
   atlas-record-assembler's `normalized_mode` matches neither the ST_003 labels nor the method-contract modes.
4. **Topic and tag classification is done three ways:**
   - article-taxonomy-classifier (20 hard-coded categories)
   - topbar-tagger (the spiritual tag registry CSV on D:)
   - convergence-tagger (a *different* registry at `C:\Theophysics_Tagger\01_REGISTRY\tag_registry.csv`)
   
   Two tag registries and two "master-equation variable" mappings exist side by side.
5. **Master Equation / χ is modelled incompatibly:**
   - chi-evaluator computes χ as a 10-channel product that **includes C**.
   - nabla-chi-classifier and `master_equation_types.py` explicitly forbid a 10-field product: "C_W is wrapper, not a tenth factor", with factors G M E S T K Q R F.
   - `_shared/canon_index.py` has yet another CHI_VARIABLES set.
   - These need reconciling.
6. **Fruits scoring is done three ways:**
   - fruits-spirit-canon SSS pipeline (embedding cosine)
   - `fruits_coherence_engine.py` (lexical multi-layer grade)
   - chi-evaluator's `fruit_output` (tanh of χ)
   
   paper-grade-composer also pulls `fruit_dynamics` from paper-intelligence-suite, which is a fourth source.
7. **Code duplication:**
   - `pipeline_legacy.py` is byte-identical to `run_fruits_engine.py`.
   - reading-level-glossary's `pipeline.py` carries dead branches for five other stations.
   - Each SSS pipeline repeats the 10 "never changes" sections instead of importing them. This is why the `_FIX_*` scripts have to patch every file.
   - youtube-fact-finder re-implements its own NLP client instead of using `station_helpers.call_nlp`.
8. **Two FIS copies:** `NLP_file-intelligence-system-master` (plus its zip at the root), the registry's legacy `file-intelligence.station`, and the registry's "FIS v2" in the now-empty `_front_door`.
9. **Registry drift:** `STATION_REGISTRY.json` marks exec-summary / claim-* etc. as `X:\04_STATIONS` but most other entries as `X:\Backside\_Stations`. The capability registry points nabla-chi-classifier at `_DORMANT`. `summarizer` and `reading-level-glossary` are registered under Backside paths although they live here.
