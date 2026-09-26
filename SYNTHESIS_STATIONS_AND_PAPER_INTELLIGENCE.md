# SYNTHESIS v0.8: David's existing stations and Paper Intelligence suite, mapped to the ONE_MENU plan

For the online Claude/Codex working on ONE_MENU. You cannot reach David's NAS, so this is the map of what exists there.
**v0.8** = deep reads of the 23 active stations (4b, Part A) and the Paper Intelligence suite (4c, Part B). The grader deep read is still pending;  (2026-09-26): built from folder listings, file dates and earlier reads. Deep reads of the code are running.
A v1 with every field name will replace this file. Read with `CODEX_MASTER_PROMPT.md` (the build plan) in this repo.

---

## 1. Provider policy (David, 2026-09-26): add this to the build

- **List every provider** in `config/providers.json`: DeepSeek, OpenRouter, OpenAI, Anthropic, Moonshot/Kimi (already used by
  `API_DEEP` llm_client), Gemini, Groq, Together, Mistral, local Ollama. Each entry holds base_url, default model, key env var
  name, OpenAI-compatible yes/no, and cost tier.
- **Primary right now: DeepSeek only** (`deepseek-chat`, key `DEEPSEEK_API_KEY`).
- **Fallback: the free option.** Use OpenRouter free models (key `OPENROUTER_API_KEY`), e.g. `deepseek/deepseek-r1:free`, already
  referenced by `turbo_pipeline_runner.py`. The fallback triggers on repeated DeepSeek failure or when `--provider free` is chosen.
  Log every fallback in the receipt.
- **Later:** embeddings (the local M19 model on the NAS, then an API option), and other providers per station.
- **Every statistic must have a deterministic Python path.** David wants "a programming way of achieving the same data every time."
  So for every metric an API station produces, record whether a local Python computation exists or can exist. Where it can, the Python
  version is the reference and the API version is a backup or an enrichment. Mark each metric `method: python | api | both` in
  the output. The Python metric suites below already cover most of the text statistics, and they should *mirror* the station
  folders one-to-one.

---

## 2. Where things live (David's machine / NAS; not reachable from the cloud)

| Location | What | Size |
|---|---|---|
| `\\NAS\h_hp\Desktop\Folders\THEOPHYSICS_PAPER_INTELLIGENCE` | Paper Intelligence suite, **copy A** (older, 12 module folders) | 5,200 files / 315 MB, 63 .py |
| `\\NAS\h_hp\Desktop\Folders\THEOPHYSICS_PAPER_INTELLIGENCE (1)` | Paper Intelligence suite, **copy B** (superset, 22 module folders) | 5,967 files / 557 MB, 87 .py |
| `X:\04_STATIONS` (= `\\NAS\brain\04_STATIONS`) | The **station library**: 30 active stations, A_* support systems, `_DORMANT` (62 retired stations) | 22,102 files / 2.4 GB, ~1,100 code files |
| `X:\Python API` (= `\\NAS\brain\Python API`) | 116 metric scripts behind the grader | see `04_PAPER_GRADER/API_DEEP_PAPER_GRADER_prompts/paper_metric_registry.json` in this repo |

Almost everything by size is run output (thousands of .md/.html/.json results). The code is small.

---

## 3. Paper Intelligence suite: the Python statistics engine (mirror these as stations)

Module folders (copy B / the station version; copy A has 00-07 + lib only):

| # | Module | What it produces (from names, schema and earlier reads) |
|---|---|---|
| 00 | ORCHESTRATOR | runs the modules in order for one paper |
| 01 | TEXT_ANALYTICS | counts, sentences, paragraphs, lexical diversity (schema layer 02) |
| 02 | ACADEMIC_STANDARD | academic rubric scores (layer 12) |
| 03 | THEOPHYSICS_METRICS | framework-specific scores (χ-related) |
| 04 | ANALYTICS | structural analytics (layer 04); holds ~5,000 per-paper outputs |
| 04 | OPENAI_7Q | the "7 questions" API pass (OpenAI; RUN_7Q_GTQ.bat, hotkeys) |
| 05 | NLP_DEEP | entities, topics, semantics (layer 05) |
| 06 | TRUTH_ENGINE | claims, evidence, verification (layer 06); the Truth Engine v2.0 lexicons live in Excel |
| 07 | KNOWLEDGE_GRAPHS | concept graph, .graphml outputs (layer 07) |
| 08 | EMOTION_PROFILE | emotion scores (layer 08; GoEmotions) |
| 09 | LINGUISTIC_DEPTH | abstract/concrete, metaphor, analogy (layer 09) |
| 10 | IDEA_DENSITY | ideas and claims per 1,000 words (layer 10) |
| 11 | HTML_REPORT | per-paper HTML report (layer 11) |
| 12 | HEARTBEAT | sentence-level "heartbeat" signal (heartbeat_analyzer) |
| 13 | ANALYST_REPORT / WEB_INTAKE | narrative analyst report; web intake (layer 13) |
| 14 | LOCAL_API / OBSIDIAN_BRAIN_ARM | local HTTP API over the suite; Obsidian vault arm |
| 15 | PAPER_GRADER | the grader integration |
| 20-22 | DROP_PAPER_ONLY / DROP_BRAIN_ONLY / DROP_BOTH_ALIGNMENT | drop-folder front doors: paper alone, vault alone, or alignment of both |
| lib | shared helpers | |

Root of the station version: `pipeline.py` (2026-06-18), `pipeline_legacy.py`, `fruit_dynamics.py`, `wiring_spec.json`,
`config.json`, Docker files, and the **contracts**: `MASTER_VARIABLE_SCHEMA.md` (366 variables in 20 layers; a copy is in this repo under
`04_PAPER_GRADER/Academic_paper-proof-grader_Jul/`), `OUTPUT_CONTRACT.md`, `VARIABLE_INVENTORY.md`, `FIELD_MAPPING.md`, `OUTPUT_ARTIFACT_MAP.json`.

**Build implication:** the STATISTICS_WALL station (42) should *wrap* this suite rather than re-implement it. Its 20 layers are the
families of the approved matrix. Add the new families from `STATISTICS_WALL_V1.md` (richness, info theory, metadiscourse, citations,
Obsidian, reliability) as new modules numbered in the same style.

---

## 4. The station library `X:\04_STATIONS` (30 active)

Each station is a folder `<name>.station` with its own code, prompts and inbox/outbox. Shared helpers are in `_shared`, and the lifecycle
folders are `_front_door`, `_inbox`, `_processed`, `_outbox`, `_state` and `_logs`.

| Station | Role (from name; deep read pending) | Maps to ONE_MENU station |
|---|---|---|
| paper-intelligence-suite | the Python statistics engine above (188 code files) | 42 STATISTICS_WALL |
| paper-proof-grader | grader: pipeline.py, run_axiom_7q_stations.py, fruits_of_spirit_bridge.py, formal_verification.py, expanded_report.py (19 code files; the July Desktop copy also has chi_qi_v5_metric_engine.py + nlp_deep_runner.py) | 43 PAPER_GRADER |
| paper-grade-composer | composes the final grade from parts | 43 / 46 REPORT_COMBINE |
| fruits-spirit-canon | Fruits canon + scoring | 40 ANALYTICAL_ARMS (Fruits plug-in) |
| chi-evaluator · nabla-chi-classifier | χ evaluation / ∇χ classification | 40 (master equation arm) |
| claim-extraction · claim-classification | claims pulled from text, then typed | 21 CKG_EXTRACT_CPE / 40 coherence |
| convergence-tagger · method-convergence · method-packet-builder | convergence across methods | new: 48 CONVERGENCE |
| article-taxonomy-classifier · topbar-tagger · audience-level | classification and website tagging | 44 TAGGER + web pipeline |
| exec-summary · summarizer · summary-quad · plain-language · reading-level-glossary | summaries at several reading levels + glossary | new: 60s WEB/READING-LEVEL group |
| atlas-admission-gate · atlas-record-assembler | admission into the Consilience Atlas + record assembly | new: 54-55 ATLAS |
| youtube-fact-finder | fact-checking for YouTube | 04 YT_LENSES (focus 7 "facts to check") |
| external-api-audit · local-nlp-audit | audits of API vs local NLP | 90 HEALTHCHECK / the "python vs api" mirror check |
| NLP_file-intelligence-system-master | file intelligence (FIS) | utility |

**Support systems**
- `A_BIL`: Behavioral Intelligence Layer (bil_service.py, engines, adapters, clipboard watcher, Postgres sync, Docker).
- `A_GUI`: brain dashboard.
- `A_AI-RESEARCH-AGENTS`: gpt-researcher + local-deep-researcher (open-source clones + launchers).
- the OBS behavioral plugin.

**`_DORMANT` (62 retired stations; reuse before rebuilding):**
- 7q-classifier, 7q-engine, apologetic-pipeline, axioms, brain-map
- claim-extractor, classify-documents, coherence-discoherence, contradiction-deep / -detector / -scan
- deberta-runner, evidence-map, fact-verifier, falsification, graph-linker, hdbscan-cluster
- lightfm / recbole / preference recommenders, load-bearing-claims
- master-equation-canon, math-layer, math-translation-layer, math-verify
- mda-citation-spine, metadata-extractor, operators-canon, paper-grader-nlp, paper-review, paperqa2
- readability-rewriter, sbert-embedder, section-splitter, series-flow-auditor
- theophysics-engine, timeline-verifier, trinity-canon
- whisper-transcribe, youtube-fetch / -qa / -scrape, and more

Several of these already implement pieces the new specs need: contradiction-*, load-bearing-claims, sbert-embedder, series-flow-auditor
(Story station), master-equation-canon, math-verify.

---

## 4b. What the deep read of the 23 active stations found (full detail: `SYNTHESIS_PART_A_ACTIVE_STATIONS.md`)

**The existing contract to keep.** Every `.station` follows the *Station Script Standard v1* (`_shared/SSS_v1_STANDARD.md` +
`SSS_TEMPLATE_v1.py` + `newstation.py` scaffolder + `teststation.py`):
- 13 fixed sections; only `06 NLP_ROUTE` and `07 PROCESS` are station-specific.
- A standard artifact envelope `ART_{ts}__{STATION_ID}__{stem}.json` with `input_file, station_id, station_name, nlp_used, api_endpoint,
  processed_at, success, artifacts[], errors[], data{}`.
- **Build ONE_MENU's station wrapper on this envelope** rather than inventing a new one, and move the 11 shared sections into an importable
  `engine/` module so the `_FIX_*` patch scripts are no longer needed.

**The local model layer already exists.** A FastAPI NLP service at `localhost:8700/nlp/{classify, embed, summarize, ner, sentiment, qa,
contradiction}` (code: `D:\GitHub\BACKSIDE-NLP-NEW\nlp_api\main.py`, models M01-M16: BART-large-CNN, DeBERTa-v3 zero-shot/NLI,
Qwen3-Embedding, roberta squad2, bert-base-NER).
- It was down on 06-19 and 08-14.
- **`/nlp/generate` does not exist (404)**, so every "LLM" branch in plain-language, summary-quad and audience-level silently falls back.
- **Action:** that `generate` role becomes DeepSeek (with OpenRouter free as fallback) through `engine/llm.py`. Health-check the 8700 service in station 90.

**David's "API and Python get the same data" idea already has a working prototype:** the Atlas Method Comparison
(`method-packet-builder` → `local-nlp-audit` + `external-api-audit` (DeepSeek `deepseek-chat`) → `method-convergence`).
- It freezes one source.
- It runs the same 8-stage contract (claims, classification, dependencies, falsification, evidence, contradictions, dynamics, synthesis) through the local lane and the API lane.
- It scores agreement: structural 0.25 / field 0.35 / content 0.40; high ≥ 0.80. The last run scored 0.52, LOW.

**Generalize this into ONE_MENU:** every API station with a Python mirror reports its API-vs-Python agreement the same way.

**Reconcile before building the arms (conflicts found):**
1. **χ is modelled three incompatible ways:**
   - chi-evaluator uses a 10-factor product *including C*.
   - nabla-chi-classifier / `master_equation_types.py` say "C_W is a wrapper, not a tenth factor" (9 factors).
   - `_shared/canon_index.py` has a third set.

   MASTER_EQUATION_STATION_V2 in this repo uses 10 slots including C. **Ask David which is canonical.**
2. **Fruits is scored four ways:**
   - embedding cosine (fruits-spirit-canon SSS)
   - `fruits_coherence_engine.py`
   - chi-evaluator's tanh fruit_output
   - paper-intelligence `fruit_dynamics`

   `fruits_coherence_engine.py` is production-grade and already scores **word → sentence → paragraph-role → paper** against the lexicon xlsx, with per-sentence CSV + word trace. That is the local half of ANALYTICAL_ARMS' Fruits stage 1-3, so reuse it as the deterministic layer. (David is redesigning Fruits; keep it pluggable.)
3. **Claim mode vocabularies disagree:**
   - ST_003: factual/model/opinion/definition
   - Atlas contract: 14 modes, AXIOM…PREDICTION
   - atlas-record-assembler's `normalized_mode` matches neither, so every claim becomes UNKNOWN.

   Pick one vocabulary.
4. **Two tag registries:**
   - `D:\GitHub\David-OS-tagger-publish\tagger\spiritual_tag_registry.csv` (topbar-tagger)
   - `C:\Theophysics_Tagger\01_REGISTRY\tag_registry.csv` (convergence-tagger)

   The TAGGER station (44) should adopt one as `config/tags.json`'s source.
5. **Summaries and reading level are duplicated 4 ways each:** exec-summary, summarizer, summary-quad and Atlas synthesis; plain-language, audience-level, reading-level-glossary and taxonomy.
   - Merge the summaries into one SUMMARY station (sentence / paragraph / executive / story).
   - Merge the reading-level stations into one READING_LEVEL station (Flesch ladder + 3 tiers + glossary + DeepSeek rewrites).

**Scaling lesson:** claim-extraction timed out because it made one zero-shot call **per sentence**. This confirms the master prompt's rule: one whole-document call per station, splitting only the output.

**Security:** a Postgres password is hard-coded in `NLP_file-intelligence-system-master/config/settings.ini` *and* `settings.example.ini`. Never copy those into git, and replace the example value with a placeholder.

**Portability:** stations reference `C:\Theophysics_Tagger`, `D:\GitHub\...`, `C:\Users\lowes\...` (an old user profile), `Z:\Theophysics_Vault`, `\\dlowenas\HPWorkstation`. Every one of these goes into `config/paths.json`.

## 4c. What the deep read of the Paper Intelligence suite found (full field list: `SYNTHESIS_PART_B_PAPER_INTELLIGENCE.md`)

- **Use copy B** (`THEOPHYSICS_PAPER_INTELLIGENCE (1)`): it is the current one. No hard-coded keys.
- **The suite is ready for STATISTICS_WALL (42) to wrap:**
  - `metric_registry.json` already lists **356 fields** (334 verified in real output).
  - `14_LOCAL_API/server.py` already exposes it as a loopback HTTP job service (`POST /runs/paper`, `GET /jobs/{id}/results`, `GET /metrics`).
  - Station 42 should call this API (or `run_pipeline.py` directly) rather than re-implementing it.
- **It already does per-sentence scoring:** L14 heartbeat gives every sentence 9 fruit scores, 10 χ scores and 14 structural markers, with peak and valley. L6 gives a per-claim ledger with evidence candidates and truth status. Both feed ANALYTICAL_ARMS directly.
- **DeepSeek is already the provider** for 7Q (L4) and the series analyst (L13), via `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL`.
  - **But L4 truncates papers to 6,000 characters.** That violates the one-whole-document-per-call rule; fix it when wrapping.
  - The o3 / gpt-4o-mini side tools in 12_HEARTBEAT are not wired in.
- **Bugs to fix when wrapping:**
  - L5 topics are always empty (`build_corpus_model` is never called).
  - L10 idea density always sees 1 paragraph (whitespace is collapsed before the split).
  - L7 graph edges use fields that no longer exist.
  - L6 anti-fruit lists have only 4 terms each.
  - The textdescriptives "quality" component is skipped.
  - 4 fields that are referenced are never produced.
  - The runner exits 0 on layer failure.
  - The `fruits_scorer_v2` import points to another subnet.
  - `paper_analyzer.py` (grammar, drift, density, argument, flow, links: about 70 fields) is fully written but **not wired in**. Wire it in; it covers much of STATISTICS_WALL's "syntax / cohesion / density" families.
- **Existing 7Q forward/reverse/promotion prompts** (verbatim structure in Part B) are strong candidates for the CKG/grader stations. Reuse them.

## 5. What to do with this (for the online build)

1. Treat the Paper Intelligence suite + `X:\Python API` as the **deterministic Python layer**. Every station in ONE_MENU gets a Python
   mirror where one is possible (David: "the same data every time"). API calls add judgment on top, never replace the Python numbers.
2. Put `.station` folders into the numbered `NN_NAME` scheme (CODEX_MASTER_PROMPT section 5). Keep the `.station` lifecycle folders as the per-station
   inbox/outbox, and route outputs into the per-paper working folder.
3. **Group calls**, so it's never 1,000 calls per paper. One call per paper per station, with several stations' questions batched only when they
   share the same input and fit the output limit. The four analytical arms are already one grouped run.
4. Before building a new station, check `_DORMANT` for an existing implementation.
5. Ask David to run an inventory script locally (below) if you need exact field lists before v1 of this synthesis lands.

### Inventory script David can run locally (read-only; prints code-only file lists and argparse flags)
```powershell
$roots='\\192.168.2.50\brain\04_STATIONS','\\192.168.2.50\h_hp\Desktop\Folders\THEOPHYSICS_PAPER_INTELLIGENCE (1)'
foreach($r in $roots){ Get-ChildItem -LiteralPath $r -Recurse -File -Filter *.py -ErrorAction SilentlyContinue |
  Where-Object FullName -notmatch '\\(venv|\.venv|__pycache__|site-packages|OUTPUT|output)\\' |
  ForEach-Object { $a=(Select-String -LiteralPath $_.FullName -Pattern 'add_argument\((.+?)\)' -AllMatches | ForEach-Object { $_.Matches.Groups[1].Value }) -join ' | ';
  '{0}`t{1}' -f $_.FullName,$a } } | Out-File "$env:USERPROFILE\Desktop\STATION_INVENTORY.tsv" -Encoding utf8
```
