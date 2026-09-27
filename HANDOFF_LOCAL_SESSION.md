# HANDOFF: for the next Claude session, running LOCALLY on David's computer

Written at the end of a cloud session that could not reach `D:\`. Everything it built is on GitHub, repo
`YellowKidokc/API_ALL`, branch `claude/youthful-lovelace-o6kq85` (draft PR #2, not merged yet). This file tells the
local session what exists, what David wants, and what to do first. Read all of it before touching anything.

---

## 0. First five minutes

1. Get the branch on disk (David's clone of API_ALL sits inside pipeline-workflows):
   ```
   cd /d D:\GitHub\pipeline-workflows\API_ALL
   git fetch origin
   git checkout claude/youthful-lovelace-o6kq85
   git pull
   ```
   If that folder is not a clone of `YellowKidokc/API_ALL`, clone it next to it instead and tell David.
2. Read `API_HOME\_system\README.md` (how everything works) and `CODEX_PROMPT_FRONT_FOLDERS.md` (the job).
3. Run the checks: `python -m unittest discover -s API_HOME\_system\tests` (22 tests, all passed in the cloud)
   and `python API_HOME\_system\engine\health.py`.
4. Then do section 3, starting with the plan and the gate.

## 1. Who David is and how to work with him

- David Lowe (POF 2828), Theophysics research: physics, theology, information theory, Lean proofs. Christian;
  the framework is ministry. He speaks by voice-to-text: fast, stream of consciousness, tangents that are
  connections. Track the thread underneath.
- He wants: challenge over agreement, no performance ("great question"), mistakes named and fixed in one line, dead
  threads aborted, and things that work the first time or are marked untested.
- He wants to click a .bat and not think. Folders must be clean. He hates chunked inputs, hard-coded paths, keys in
  files, and anything that loses work on restart.
- He runs several AIs (Codex, GPT, Gemini, Kimi ...). Codex, given `CODEX_PROMPT_FRONT_FOLDERS.md`, only added the
  prompt file to pipeline-workflows (PR #25, one file, merged) and moved nothing. The job below is still undone.

## 2. Settled decisions (do not reopen)

- **DeepSeek only.** `settings.json` `allowed_providers` = `deepseek` + `mock`; no fallback. Key from the
  environment variable `DEEPSEEK_API_KEY` (SETUP.bat saves it with `setx`). The `openai` Python package is only a
  client library that talks to DeepSeek.
- **One item = one whole-document call.** Never chunk input. Split outputs only.
- **Parallel**: default 30 calls at once (50/60 allowed), one global limiter in the local relay
  (`engine\gateway.py`) that every call, new or legacy, passes through.
- **One for one**: each item saved when done; reruns skip finished items; interrupted runs resume.
- **Show every step** live; `steps.log`, every reply as `calls\<API goal id>-<n>.json`, a receipt per item.
- **API goal ids**: `API-NN.n TITLE`, catalog in `API_GOALS.md`.
- **The model proposes, code decides** (triage caps, verification status, physics-mirror levels ...).
- **Inbox lanes**: `00_PRIORITY` (always first), `01_SERIES\<series>`, `02_GROUP\<group>` (a group is carried like a
  series without being one, e.g. "One pagers"; the folder name is the group). `02_GENERAL` still read.
- **Outbox**: flat. Every paper printed into the root as `<title> - <kind>.md`, first line stamps lane / group /
  source. Titles get cleaned up later; classification folders later, as copies.
- **Every API folder = INBOX, OUTBOX, BACKSIDE, 1-4 numbered .bat launchers. Nothing else.** BACKSIDE holds that
  API's scripts, prompts, templates, logs, receipts. One shared engine in a hidden `_system`. APIs may read each
  other's OUTBOX (`--from NNN`).
- **Numbering**: three digits from `000`; keep the ONE_MENU numbers (`55` → `055_LEAN_PAPERS`).
- **QUICK_CALL** (`000_QUICK_CALL`): self-contained copy-me folder (prompt.txt + input\ → RUN.bat → output\,
  DeepSeek, one call per file side by side). Replaces the old OpenAI quick-call folder.
- **Argument-graph SQLite** (CrossVideoSynthesis) lives on the Obsidian side, not here.

## 3. The job: every API out on the main page, cleaned up

Full spec: `CODEX_PROMPT_FRONT_FOLDERS.md` (also merged into pipeline-workflows as the same file). Summary:

1. **Plan, no moves.** Inventory every API in:
   - `D:\GitHub\pipeline-workflows\API\API` (on GitHub: ATOMS, AXIOM_NODES, CKG, CLAIMS_PROOFS_EVIDENCE, COHERENCE,
     COHERENCE_SCORE, EVIDENCE, FRUITS, LEAN4, LEAN_ATOM_EXTRACTOR, MASTER_EQUATION, PAPER_GRADER, PILLS,
     SERIES_SUMMARY, STORIES; plumbing: ERRORS, INBOX, OUTBOX, PROCESSED, PROCESSING, PYTHON, RECEIPTS, RETRY,
     REVIEW, SCRIPTS, _BACKSIDE)
   - `API_OLD` (AXIOM_NODES, FRUITS, MASTER_EQUATION: duplicates of API\API)
   - `APIs` (CANONIZATION, EVIDENCE, LEAN4, stations\Stories: EVIDENCE / LEAN4 / Stories duplicate)
   - **local only, never on GitHub:** `API\API 2` (chi-evaluator, P01-P07 recommenders, truth, writing-analyzer ...),
     `API\API 3`, `API\Open-AI-CALL-OBS-Plugin-Final-Claude`, and David's sketch folder `CODEX\` (empty folders;
     use it for the list and names of APIs only, not its inner layout)
   - the ONE_MENU stations already in `API_ALL\API_HOME\_system\stations` (section 8 of the prompt)
   Write `FRONT_FOLDER_PLAN.md`: each API, where it is, number + name, launchers (plain names), INBOX yes/no,
   which OUTBOXes it reads, duplicates and which one wins (diff them), parent-relative or drive-letter paths.
   `python API_ALL\API_HOME\_system\tools\pull_up_api_folders.py "D:\GitHub\pipeline-workflows"` gives a preview.
2. **Gate: show David the plan and wait.** Ask him to confirm where "the main page" is: the top of
   `D:\GitHub\pipeline-workflows` (next to `CODEX\`), or `API_ALL\API_HOME`. The prompt assumes API_HOME; he may
   mean pipeline-workflows. Do not guess.
3. Engine changes first (station folders resolved from `stations.json` into each API's BACKSIDE, `--from`), with
   tests.
4. Move one family per commit with `git mv`; after each: tests, health, `--mock --limit 1` on every station touched.
   Never delete (retire to `_system\vendor\_retired` / `_duplicates`), never overwrite, never push to main without
   David.

## 4. What already exists (API_ALL, branch above)

```
API_HOME\
  ONE_MENU.bat        numbered menu for everything (counts items, asks all/how many, parallel, anything to add)
  SETUP.bat           key via setx, paths (relocate), hides _system and _data
  LEAN\               the reference front folder: 1 RUN ALL.bat, 2 RUN PRIORITY ONLY.bat, INBOX, OUTBOX
  QUICK_CALL\         copy-me DeepSeek folder (0 NEW COPY.bat, RUN.bat, DRY_RUN.bat)
  _system\            engine\ stations\ config\ templates\ vendor\ tools\ tests\ (+ README, API_GOALS, CONSOLIDATION,
                      MIGRATION_REPORT)
```

Stations worth knowing (full table in `_system\README.md`):
- **10 CKG_THEOLOGY**: 17-probe theology triage after the CKG index; 3-flag cap etc. enforced in `engine\triage.py`.
- **11 CKG_PHYSICS**: physics mirror, stage by stage, in order; level set in `engine\mirror.py`.
- **12 YT_TIDY**: uniform names (`Ch 159 - The Historical Jesus.md`, rule in `engine\ytnames.py`), Obsidian notes;
  `--watch` waits for a channel download to go quiet, then runs 07, 12, 13.
- **13 YT_CHANNEL_SUMMARY**: 3-sentence summary, 2-3 keywords and 19 probe columns (David's
  youtube_specific_probes, `COLUMNS.md`) per video; channel `.xlsx` / `.tsv` / index note rebuilt after each video.
- **55 LEAN_PAPERS**: the reference station. Per Lean source: formal paper, reader paper, claims in
  `templates\lean\CLAIM_TEMPLATE.md` (assumptions only by id), a separate assumptions paper; masters
  `00_ALL_CLAIMS.md`, `00_ALL_ASSUMPTIONS.md`, `00_ASSUMPTIONS_REVIEW.xlsx` (review marks survive rebuilds).
  No certification from the model; PASS only with a cited source line.
- **48 / 49**: topic synthesis across the corpus and gap map against David's own work.
- **60**: the 23 api_call prompts, bundled into 11 calls.

Nothing has made a real DeepSeek call yet (no key in the cloud); everything was tested with `--mock`. The .bat files
were never run on Windows. First real runs: `ONE_MENU.bat 55 --limit 1`, `ONE_MENU.bat T --limit 1`.

## 5. Open items from David

- Where the Obsidian staging folder is, and whether a watcher moves results into the vault.
- After the assumptions review (LEAN), "run" probably means compile with Lean: have `axiom_compile.py` (in
  `06_LEAN\LEAN_ATOM_EXTRACTOR`) compile only claims whose assumptions are all marked OK. Confirm with David.
- CrossVideoSynthesis spec v2 (`pipeline-workflows\API\CrossVideoSynthesis\DESIGN_SPEC_v2.md` + schema) was only on
  his disk. Plan agreed so far: a stance registry first (so `hostility_score` is computed, not guessed), probes
  folded into station 10's rubric rows, channel profile as a new station (Python for drift / escalation, DeepSeek
  only for cross-video reading).
- The 12 headline numbers, axiom registry, Fruits scale, academic norms (listed in `_system\README.md`).
