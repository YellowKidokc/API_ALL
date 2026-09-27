# FRONT FOLDER PLAN: every API out on the main page

Status: **PLAN ONLY. Nothing has been moved.** Written 2026-09-27 by the local session from the disk at
`D:\GitHub\pipeline-workflows` (branch `V2`) and `API_ALL` (branch `claude/youthful-lovelace-o6kq85`).
Checks before planning: 22/22 unit tests OK; `health.py` 1 problem (`catalog_db` missing: `_data\catalog.sqlite`
is not created until station 05 runs; harmless).

MAIN below = `API_ALL\API_HOME` (the prompt's default). **Gate question 1 decides this; see the end.**

---

## A. What is really on disk (differs from the handoff)

| Source | On disk? | What it actually is |
|---|---|---|
| `API\API` | yes, 209 files | **Empty scaffold.** Every station folder holds only `.gitkeep` plumbing (INBOX/OUTBOX/PROCESSED/...); `_BACKSIDE\STATIONS\*` are empty too. The only content is `README.md` (the "Complete Grading Bundle" contract: six stations or no grade) and `_BACKSIDE\CONFIG\grading_bundle.example.json`. No code to migrate. |
| `API\API 2` | yes, 2,675 files, **untracked** | The old top-level `engines\` folder, moved by hand (git on `V2` shows `engines\*` as deleted, `API\API 2` as untracked). |
| `API\API 3` | yes, 361 files, **untracked** | The gathered copies (2026-09-24) that `migrate_legacy.py` already vendored into `_system\vendor` (youtube, ckg, evidence, evidence_chain, grader, lean_atom, api_deep). |
| `API\Open-AI-CALL-OBS-Plugin-Final-Claude` | yes, 6,705 files / ~75 MB, **untracked** | Moved by hand from the repo root (root copy shows as deleted). `stations_raw\api_call_01..23` (prompts **plus ~6,500 old output .md/.json/.html**), `consolidated\` (copies), `call_openai.py` quick-call. |
| `API_OLD` | **no**: only on `origin/main` | Older AXIOM_NODES / FRUITS / MASTER_EQUATION (0 identical files with `API\API` for AX/ME; 2 for Fruits). |
| `APIs` | **no**: only on `origin/main` | Snapshot of the NAS `Desktop\APIs\APIs`: CKG, EVIDENCE, LEAN4 (already vendored via API 3), **CANONIZATION** (skeleton + README), `stations\Stories` (30 files), `Reusable_Tools_From_Theophysics` (~250 tool files), `workbench\`. |
| `CODEX\` sketch | yes, empty folders | API names: **ATOMS, CLAIMS_PROOFS_EVIDENCE, COHERENCE_SCORE, EVIDENCE, FRUITS, STORIES** (+ plumbing ERRORS, INBOX, _BACKSIDE). |

### Git blockers (these change step 4 of the prompt)

1. **`pipeline-workflows` V2 has ~9,300 uncommitted changes**: the hand-moves above (`engines\` → `API\API 2`,
   root quick-call → `API\`). `git mv` needs a clean, committed starting point. Fix: commit those moves on a branch
   first (one commit: "move engines and old quick-call under API\"), or revert them. Your call.
2. **`API_ALL` is its own git repo** nested inside pipeline-workflows. Moving anything from `pipeline-workflows\API\...`
   into `API_ALL\API_HOME` crosses repos: no `git mv`, it is **copy in + retire at source** (history stays in
   pipeline-workflows). If MAIN is the top of pipeline-workflows instead, it is the reverse problem: the engine
   (`_system`) lives in API_ALL.
3. **A live API key sits in `API\API 2\writing-analyzer\config.txt`.** Untracked today, so it is not on GitHub.
   It must never be copied or committed; the migrated writing-analyzer reads `DEEPSEEK_API_KEY` from the environment.
   Worth rotating that key anyway.

---

## B. Front folders: existing ONE_MENU stations (numbers kept)

Name rule: menu number; **the CODEX-sketch name where the sketch names the same API** (marked ✎).
Launchers are plain names; every one calls `..\_system\engine\menu.py <NN> --yes`.

| Folder | From station | INBOX | Reads OUTBOX of | Launchers |
|---|---|---|---|---|
| `000_QUICK_CALL` | `API_HOME\QUICK_CALL` (moved unchanged, no BACKSIDE) | input\ | — | 0 NEW COPY · RUN · DRY RUN |
| `001_YT_GRAB` | 01 | no (asks channel/URL) | — | 1 GRAB CHANNEL |
| `002_YT_CLEAN` | 02 | yes | 001 | 1 RUN ALL |
| `003_YT_INDEX` | 03 | yes | 012 | 1 RUN ALL · 2 RUN PRIORITY ONLY |
| `004_YT_LENSES` | 04 | yes | 012 | 1 RUN ALL · 2 RUN WITH A QUESTION |
| `005_YT_CATALOG` | 05 | no | 003, 004 | 1 BUILD CATALOG |
| `006_YT_WATCH` | 06 | no (watch list in BACKSIDE) | — | 1 RUN WATCH LIST |
| `007_YT_CONVERT` | 07 | yes | — | 1 CONVERT ALL |
| `008_YT_SUMMARY` | 08 | yes | 012 | 1 RUN ALL · 2 RUN PRIORITY ONLY |
| `009_YT_DEEP` | 09 | no | 008 | 1 RUN ALL |
| `010_CKG_THEOLOGY` | 10 | no | 003 | 1 RUN ALL |
| `011_CKG_PHYSICS` | 11 | yes (papers) | 003 | 1 RUN ALL |
| `012_YT_TIDY` | 12 | yes | 007 | 1 RUN ALL · 2 WATCH A DOWNLOAD |
| `013_YT_CHANNEL_SUMMARY` | 13 | no | 012 | 1 RUN ALL |
| `020_CKG` ✎ | 20 CKG_RUN | yes | — | 1 RUN ALL · 2 CHECK INBOX (=22) |
| `021_CLAIMS_PROOFS_EVIDENCE` ✎ | 21 CKG_EXTRACT_CPE | no | 020 | 1 SPLIT CKG OUTPUT |
| `022_CKG_INBOX_CHECK` | 22 | no | 020 inbox | 1 CHECK |
| `030_EVIDENCE` ✎ | 30 EVIDENCE_INTAKE | yes | — | 1 RUN ALL · 2 RUN PRIORITY ONLY |
| `031`–`039` | 31–39 (names kept) | no | 030 | 1 each (39: own INBOX, v2 intake) |
| `040_ANALYTICAL_ARMS` | 40 | yes (papers) | — | 1 RUN ALL · 2 RUN PRIORITY ONLY |
| `041_STORIES` ✎ | 41 STORY | yes | — | 1 RUN ALL |
| `042_STATISTICS_WALL` | 42 | yes | — | 1 RUN ALL |
| `043_PAPER_GRADER` | 43 | yes | — | 1 GRADE ALL |
| `044_TAGGER` | 44 | yes | — | 1 RUN ALL |
| `045_ATOMS` ✎ | 45 CLAIM_ATOMS (`vendor\api_deep\ATOMS`) | yes | — | 1 RUN ALL |
| `046_REPORT_COMBINE` | 46 | no | all | 1 BUILD REPORT |
| `047_NEW_PAPER` | 47 | yes | — | 1 NEW PAPER · 2 NEW OWN PAPER |
| `048_TOPIC_SYNTHESIS` | 48 | no (asks topic) | 044 | 1 RUN A TOPIC |
| `049_GAP_MAP` | 49 | no (asks topic) | 048 | 1 RUN A TOPIC |
| `050`–`053` | 50–53 (names kept) | 52: yes | 50/51: 030 | 1 each |
| `054_AXIOM_NODES` ✎ | 54 AXIOM_NODES_RUNNER (`vendor\api_deep\AXIOM_NODES`) | yes | — | 1 RUN ALL |
| `055_LEAN_PAPERS` | 55 + `API_HOME\LEAN` (the reference) | yes | 052 (optional `--from`) | 1 RUN ALL · 2 RUN PRIORITY ONLY |
| `060_OPENAI_STATIONS` | 60 | yes | — | 1 RUN ALL BUNDLES |

90 / 91 stay menu-only. That is **44 front folders** from what already runs.

## C. New front folders (not in ONE_MENU today)

| Folder | Source | What / decision | INBOX | Reads |
|---|---|---|---|---|
| `061_FRUITS` ✎ | station 40's `fruits_plugin` | CODEX names FRUITS as its own API. Launcher runs 40 fruits-only (needs a new `--arms` option on 40). Papers 40-49 are full, so it overflows into 6x. | yes | — |
| `062_COHERENCE_SCORE` ✎ | `API 3\05_API_DEEP_STATIONS\COHERENCE_SCORE\PROMPT.md` (prompt only, never built) | New native station. | yes | — |
| `063_GRADING_BUNDLE` | `API\API\README.md` + `grading_bundle.example.json` | The six-or-nothing grade: 40 (coherence, ME, axiom nodes, fruits) + 045 ATOMS + 062 COHERENCE_SCORE, one paper id, retries only failed arms. | yes | — |
| `023_CANONIZATION` | `APIs\CANONIZATION` (origin/main) + `canonization_root` | Only a README + lane folders exist here; code is in the Canonizationv1 repo. Placeholder until you point at the code. | yes | 020 |
| `100_CHI_EVALUATOR` | `API 2\01_chi-evaluator` **wins** over `API 2\chi-evaluator` (74 vs 42 files; 9 shared, 5 of those differ) → loser to `_duplicates` | DeepSeek, direct URL → relay. | yes | — |
| `101_WRITING_ANALYZER` | `API 2\writing-analyzer` (RUN, PROCESS, PROCESS_MULTI, PASS2, COMPARE ...) | DeepSeek. 13 .bat today → 4 launchers: RUN · RUN MULTI · PASS 2 · COMPARE. `config.txt` (key) **not** copied. | yes (has INBOX) | — |
| `102_UNIVERSALITY` | writing-analyzer `run_universality.py` + `universality-class-runner\` | DeepSeek. | yes | 101 |
| `103_FRUIT_REVIEW` | writing-analyzer `fruit-review-orchestrator\` (18 .py; 168 .xlsx/.md results → `_data`) | DeepSeek, several models? (check: relay allows DeepSeek only). Overlaps 061; diff before building. | yes | — |
| `104_EASY_ACADEMIC_LAYER` | writing-analyzer `Easy Academic Layer\Deep Seek Call\batch_rewrite.py` (1,911 .md are data → `_data`) | DeepSeek rewrite batch. | yes | — |
| `105_VECTORIZE` | writing-analyzer `vectorize*.py` + `vectorization\` | Local (no API). | yes | 101 |
| `106_EXCEL_INTERROGATION` | writing-analyzer `run_excel_interrogation.py` + the `.xlsx` | DeepSeek. | no | — |

## D. Not front folders (retire intact, never delete)

| What | Why | Goes to |
|---|---|---|
| `API\API` (all 15 station scaffolds + plumbing) | Empty; its README becomes 063's contract | `_system\vendor\_retired\API_API_SCAFFOLD` (only README + CONFIG carry content) |
| `API\API 3` | Already vendored. Before retiring: hash-check every vendored file against it. Not vendored on purpose: `02_CKG\backside_workbench` (incompatible runner) → `_duplicates`; `08_NEW_STATION_SPECS` → `_system\docs\specs`; `07\TikTokPrep`, `YouTubeChannelRefinery`, `Paper-Grader-NLP` (specs / stub) → retired | `_system\vendor\_retired\API_3_SOURCES` |
| `API\Open-AI-CALL-OBS-Plugin-Final-Claude` | Replaced by 000_QUICK_CALL; its 23 prompts already run under 060 | code + prompts → `_system\vendor\_retired\QUICK_CALL_OLD`; the ~75 MB of old outputs stay **out of git** (`_data\_retired\QUICK_CALL_OLD_outputs`) |
| `API 2\P01`–`P07` recommenders, `pipeline\` (fap_*, `llm_hub.py` uses Anthropic), `truth\` (Ollama), `embeddings\`, `threshold_engine.py`, `_front_door`, `_inbox`, START / HEALTHCHECK / PROCESS_INBOX .bat | Local ML / preference engines, not DeepSeek APIs; `llm_hub` would break "DeepSeek only" | `_system\vendor\_retired\ENGINES_API2` (or leave where they are: question 3) |
| `API_OLD` (origin/main only) | Superseded by the API_DEEP copies | nothing to move; noted here |
| `APIs\Reusable_Tools_From_Theophysics`, `APIs\workbench` (origin/main only) | Tools, not APIs; workbench already vendored as `vendor\ckg\workbench` | nothing to move |
| `APIs\stations\Stories` (origin/main only) | Older Story station; 041 is built from STORY_STATION_V2 | diff against 041 when 041 moves; winner stays |
| API\API names with no code anywhere: `PILLS`, `SERIES_SUMMARY`; `COHERENCE`, `MASTER_EQUATION`, `LEAN4` | PILLS is reference data (`me_pills`); SERIES_SUMMARY never built; the other three are covered by 040 / 055 | no folder unless you say so |

## E. Hard-coded / parent-relative paths found

- `API\API 3` sources: already rewritten into `paths.json` keys by `migrate_legacy.py` (`MIGRATION_REPORT.md`).
- `API\API 2`: 1 drive-letter path in code (`writing-analyzer\fruit-review-orchestrator\feature_extractor.py`), plus
  ~170 in its result JSON (data, left alone). No `..\..` parent jumps. Every direct `api.deepseek.com` URL
  (chi-evaluator ×3, writing-analyzer ×8, fruit-review, batch_rewrite) gets rewritten to the relay by `migrate_legacy.py`.
- The station folders themselves: engine resolves `_system\stations\<label>` today; after the move it resolves
  `../NNN_NAME/BACKSIDE` from `stations.json` (engine change, step 3).

## F. Order once approved

0. Resolve git blocker 1 (commit or revert the hand-moves on V2) so every source is in a known state.
1. Engine changes + tests (station folder from `stations.json`, `--from NNN`, BACKSIDE\work + logs, layout test).
2. One family per commit in API_ALL: 000/055 (reference) → YouTube 001-013 → CKG 020-023 → evidence 030-039 →
   papers 040-049 → Lean 050-054 → 060-063 → 100-106. After each: tests, health, `--mock --limit 1` per station.
3. Retire the sources (section D), one commit per source, in pipeline-workflows on a branch.
4. README, CONSOLIDATION, MIGRATION_REPORT, API_GOALS updated. Nothing pushed to main without you.

## G. Questions for David (the gate)

1. **Where is "the main page"?** (a) `API_ALL\API_HOME` (the prompt's default; engine is already there), or
   (b) the top of `D:\GitHub\pipeline-workflows`, next to `CODEX\`. Nothing moves until you answer.
2. The ~9,300 uncommitted hand-moves on `pipeline-workflows` V2 (`engines` → `API\API 2`, quick-call → `API\`):
   commit them as they are, or put them back first?
3. `API 2`'s non-DeepSeek engines (P01-P07, fap pipeline, truth, embeddings): retire, or leave them where they are?
4. OK to use CODEX names on existing stations (`020_CKG`, `030_EVIDENCE`, `041_STORIES`, `045_ATOMS`,
   `054_AXIOM_NODES`, `021_CLAIMS_PROOFS_EVIDENCE`), and 061-063 for FRUITS / COHERENCE_SCORE / GRADING_BUNDLE?
