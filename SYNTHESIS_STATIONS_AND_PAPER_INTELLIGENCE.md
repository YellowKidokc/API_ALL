# SYNTHESIS v0: David's existing stations and Paper Intelligence suite, mapped to the ONE_MENU plan

For the online Claude/Codex working on ONE_MENU. You cannot reach David's NAS, so this is the map of what exists there.
**v0 = first pass** (2026-09-26): built from folder listings, file dates and earlier reads. Deep reads of the code are running.
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
