# Prompt for DeepSeek Codex — rename & organize the API stations

Repo: **https://github.com/YellowKidokc/pipeline-workflows**, branch **V2**
Path in repo: `Open-AI-CALL-OBS-Plugin-Final-Claude/stations_raw/`
(originally from a local repo called `Open-AI-CALL-claude-multi-api-batch-processor`
on a separate drive — that origin no longer matters, work only in this repo/branch)

## Before you start

All 23 stations (`api_call_01` through `api_call_23_MTL`) are now present
in `stations_raw/` — run `ls Open-AI-CALL-OBS-Plugin-Final-Claude/stations_raw/`
to confirm the full set is there before proceeding, since folder contents
can still drift between when this prompt was written and when you run it.
If any are unexpectedly missing, note it in your final report rather than
inventing or skipping silently.

Also check `Open-AI-CALL-OBS-Plugin-Final-Claude/consolidated/multi_api_batch_core/`
in this same repo — that's the shared engine (`worker.py`, `providers.py`,
`api_client.py`, `outputs.py`, `retriever.py`, `ledger.py`) that every
station folder is meant to run against. It was copied in separately from
`core/` in the original repo; treat it as the canonical engine location
going forward unless the stations reference a different relative path
internally (check `RUN.bat`/`RUN.sh` inside a station folder — they may
still point at `..\core\worker.py`, which won't resolve inside
`stations_raw/` anymore. Fix these paths as part of this task — see
Task 3 below.)

## Context

This is a folder-queue batch API processor. A shared engine
(`worker.py`, `providers.py`, `api_client.py`, `outputs.py`, `retriever.py`,
`ledger.py`) reads any `api_call_NN` folder and processes every file dropped
in that folder's `inbox/`, using that folder's `config.txt` (provider/model/
temperature/output format) and `prompt.txt` (what to do to each file).
Results land in `outbox/`; failures land in `wait/` with an `.error.txt`.

There are 23 station folders in total (only 01-10 imported so far — see
above), named only `api_call_01` .. `api_call_23_MTL`. Each one is fully
configured and working — they just aren't named or documented consistently.
Two of them (`api_call_22_CLASSIFY_AXIOMIZE_ORGANIZE`, `api_call_23_MTL`)
already got partial descriptive names; the rest didn't.

## Task

1. **Rename every `api_call_NN*` folder** to `NN_short_slug` (keep the
   two-digit number for ordering; drop the generic `api_call_` prefix since
   the slug alone is more useful than a duplicate word). Use this exact
   mapping:

   | current | new name |
   |---|---|
   | api_call_01 | 01_raw_metrics |
   | api_call_02 | 02_thesis_claim_inventory |
   | api_call_03 | 03_definition_assumption_map |
   | api_call_04 | 04_argument_structure_flow |
   | api_call_05 | 05_evidence_quality_overclaim |
   | api_call_06 | 06_domain_classification_nabla_chi |
   | api_call_07 | 07_fruits_coherence_scoring |
   | api_call_08 | 08_writing_analysis_reading_levels |
   | api_call_09 | 09_series_continuity_crossref |
   | api_call_10 | 10_final_report_compilation |
   | api_call_11 | 11_domain_classification_bar |
   | api_call_12 | 12_rewrite_high_school_level |
   | api_call_13 | 13_rewrite_academic_level |
   | api_call_14 | 14_canon_claims_json |
   | api_call_15 | 15_canon_isomorphism_json |
   | api_call_16 | 16_canon_proof_map_json |
   | api_call_17 | 17_adversarial_audit |
   | api_call_18 | 18_seo_discoverability |
   | api_call_19 | 19_page_shell_audit |
   | api_call_20 | 20_trilemma_resolver |
   | api_call_21 | 21_great_grader_20d |
   | api_call_22_CLASSIFY_AXIOMIZE_ORGANIZE | 22_classify_axiomize_organize |
   | api_call_23_MTL | 23_math_translation_layer |

2. **Do NOT delete or reorganize the contents inside each folder** —
   `config.txt`, `prompt.txt`, `RUN.bat`, `RUN.sh`, `TROUBLESHOOT.*`,
   `templates/` stay as-is. Leave `inbox/`, `process/`, `outbox/`, `wait/`
   exactly as they are (some have real job files in them — do not clear or
   move their contents).

3. **Find and fix every reference to the old folder names** anywhere in the
   repo: `RUN_ALL.bat`, `RUN_ALL.sh`, `DRY_RUN_ALL.bat`, `DRY_RUN_ALL.sh`,
   `TROUBLESHOOT_ALL.bat`, `TROUBLESHOOT_ALL.sh`, `LOAD_ALL_STATIONS.bat`,
   `PIPELINE.py`, `PIPELINE_RUN.bat`, `PIPELINE_DRY_RUN.bat`,
   `aggregate_pipeline_scores.py`, `gap_analysis.py`, `NLP_MASTER_REFERENCE_POINTER.md`,
   `START_HERE_PROJECT_MAP.md`, `STATION_ARCHITECTURE.md`, and anything else
   that hardcodes `api_call_NN` (grep the whole repo for `api_call_` first —
   don't assume this list is complete). If a script globs `api_call_*`
   generically, verify the new names still match that glob pattern
   (they do, since they don't start with `api_call_` anymore — so update the
   glob itself, e.g. to match `[0-9][0-9]_*`, and confirm sort order by
   number still holds).

4. **Add a short `README.txt` to any station missing one** (currently
   18, 19, 21, 22, 23 have no README.txt, only a `config.txt` header
   comment) — pull the description straight from that station's own
   `config.txt` header comment block, formatted to match the style of
   the existing station READMEs (see `01_raw_metrics/README.txt` for the
   format: title, Provider/Temp/Output line, purpose paragraph, INPUT/OUTPUT
   or SETUP notes if relevant).

5. **Write one new top-level index file**, `STATIONS_INDEX.md`, listing all
   23 stations in order: number, folder name, provider, one-line purpose.
   Group them under three headers matching how they're actually used:
   "Document analysis pipeline (01-10, sequential)",
   "Site/publishing tools (11-19)", "Specialized (20-23)".

6. **Verify nothing broke**: after renaming, run (or dry-run) `RUN_ALL`
   against a station with a test file in `inbox/` and confirm the engine
   still finds and processes it. Report any script you had to touch and
   why.

7. **Preserve and confirm parallel execution.** These stations are meant to
   run concurrently, not one at a time — we've already tested running
   around 30 stations/jobs in parallel successfully. Whatever `RUN_ALL`/
   `LOAD_ALL_STATIONS`/`worker.py` mechanism currently launches multiple
   stations at once (check for a `--workers` flag or a `ThreadPoolExecutor`
   in `worker.py`), make sure your renaming and any glob-pattern updates
   (Task 3) do not accidentally serialize it or cap it below what it
   already supported. If you find a hardcoded worker/thread limit lower
   than what's been tested (~30), flag it in your report rather than
   silently changing it — don't raise the limit yourself without saying so.
   The goal is: as many stations as possible should be able to run at the
   same time, limited only by provider rate limits/cost, not by folder
   naming or path assumptions you introduce.

## Constraints

- This is a live pipeline someone actively uses — be conservative. Prefer
  `git mv` for renames so history is preserved, and commit in small logical
  chunks (e.g. one commit for the folder renames, one for fixing script
  references, one for the new README/index files).
- Do not touch `core/` engine files themselves unless a rename requires a
  reference update inside them.
- Do not touch anything under `_ARCHIVE_RUNS/`, `_DND_DO_NOT_DELETE/`, or
  `__pycache__/`.
