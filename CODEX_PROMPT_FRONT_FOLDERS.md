# CODEX PROMPT: one numbered folder per API, each with its own backside, inbox and outbox

**Repository:** `D:\GitHub\pipeline-workflows` (work on a branch; do not push to main without David).
**David's sketch:** `D:\GitHub\pipeline-workflows\CODEX\` (mostly empty folders; git does not keep empty folders, so
read it on disk). Use it only for the list and names of APIs. Its inner layout is NOT the target: every API folder
holds exactly four kinds of thing, INBOX, OUTBOX, BACKSIDE and its .bat launchers (section 1).
**Main folder (MAIN):** `D:\GitHub\pipeline-workflows\API_ALL\API_HOME` (the portable ONE_MENU folder), unless David
says the CODEX folder itself is MAIN. Change nothing else in this prompt either way.
**Read first:** `MAIN\_system\README.md`, `MAIN\_system\engine\` (station.py, menu.py, inbox.py, gateway.py,
paths.py), `MAIN\_system\stations\55_LEAN_PAPERS\` (the reference station), `MAIN\LEAN\` (the reference front folder).

---

## 1. What David sees

Opening MAIN shows every API as its own numbered folder, even if there are 50:

```
MAIN\
  ONE_MENU.bat                  everything, by number, as today
  SETUP.bat                     key, paths, hides the machinery
  000_QUICK_CALL\
  001_YT_GRAB\
  ...
  055_LEAN_PAPERS\
  ...
  _system\                      hidden: the SHARED engine only (relay, menu, station framework, config, tests)
  _data\                        hidden: working folders, caches
```

Clicking into any API folder shows exactly this, and nothing else: **INBOX, OUTBOX, BACKSIDE, .bat launchers.**

```
055_LEAN_PAPERS\
  1 RUN ALL.bat                 1 to 4 launchers, numbered, plain names. Click, don't think, it runs.
  2 RUN PRIORITY ONLY.bat
  INBOX\
    00_PRIORITY\                always runs first
    01_SERIES\<series name>\    the folder name is the series
    02_GROUP\<group name>\      grouped like a series without being one (e.g. "One pagers"); folder name = group
  OUTBOX\                       every paper printed flat into the root: "<title> - <kind>.md"
  BACKSIDE\                     this API's scripts, prompts, templates, station.json, README, logs, receipts
```

Nothing else in an API folder: no README, no config, no logs, no sub-folders besides these three. The shared engine
stays in `MAIN\_system` (hidden by SETUP.bat); everything that belongs to ONE API goes into that API's `BACKSIDE`.

## 2. APIs feed each other

An API often reads another API's OUTBOX instead of its own INBOX (e.g. 055 reads 052's OUTBOX). So every station
has input keys in `paths.json`:
- `<station>_inbox`: default `../NNN_NAME/INBOX` (its own inbox);
- optional `<station>_from`: one or more other folders to read, e.g. `../052_LEAN_ATOM_EXTRACTOR/OUTBOX`.
A launcher may pass `--from 052` (resolved to that API's OUTBOX). An OUTBOX is flat, so the reading API treats its
papers as the "Ungrouped" group unless the paper's first line names a lane / group (every paper stamps it).
Nothing is copied between folders to make this work.

## 3. Numbering

- Three digits from `000`. Keep the numbers ONE_MENU uses so menu and folders agree: `55` → `055_LEAN_PAPERS`,
  `07` → `007_YT_CONVERT` (full list in section 8).
- `000_QUICK_CALL` is today's `MAIN\QUICK_CALL`, moved unchanged (it is self-contained; it gets no `BACKSIDE`).
- `MAIN\LEAN` becomes `055_LEAN_PAPERS`.
- APIs brought in from `API\API`, `API\API 2`, `API\API 3`, `API_OLD\`, `APIs\` take the next free number in their
  family (YouTube 01-19, CKG 20-29, evidence 30-39, papers 40-49, Lean / axioms 50-59, bundles 60-69, 100+ for
  anything else). If the CODEX sketch names an API, use that name.

## 4. Engine changes this needs (do these first, with tests)

1. `config\stations.json` gets a `folder` per station pointing at `../NNN_NAME/BACKSIDE` (relative to `_system`).
   `engine\station.py`, `menu.py`, `health.py`, `goals.py`, `legacy.py` resolve station folders from that field
   (today they assume `_system\stations\<label>`). `paths.inside()` keeps refusing paths outside MAIN.
2. `engine\inbox.py` already reads 00_PRIORITY / 01_SERIES / 02_GROUP (and the old 02_GENERAL). Add `--from`
   resolution (section 2).
3. Each station's working folders and receipts go to `BACKSIDE\work\` and its logs to `BACKSIDE\logs\`
   (a paths.json key per station, default relative), so an API folder carries its own history when copied.
4. The unit tests (`_system\tests`) cover the new resolution: a station found in its `BACKSIDE`, a run reading
   another API's OUTBOX, and a layout test: every `NNN_` folder holds only .bat launchers, INBOX, OUTBOX, BACKSIDE.

## 5. The rigor bar (every API; 055 is the reference)

1. **Launchers**: 5-10 lines, `%~dp0`-relative, call `..\_system\engine\menu.py <NN> --yes` (options via
   `--station-args "..."`), check `DEEPSEEK_API_KEY`, end with `pause`. No hard-coded paths. 1 to 4 per API.
2. **DeepSeek only**, through the relay (`engine\gateway.py`); keys only from the environment.
3. **One item = one whole-document call.** Never chunk the input; too big → skip with a clear message.
4. **Parallel**: independent calls side by side (default 30, `--workers`), one global limiter.
5. **One for one**: each item saved the moment it finishes; a rerun skips finished items; priority first.
6. **Show every step** (`ctx.step`), `steps.log`, every reply as `calls\<goal id>-<n>.json`, a receipt per item.
7. **Outputs**: JSON (canonical, in `BACKSIDE\work`) + papers printed flat into OUTBOX + `.xlsx` where there are
   rows. Every paper's first line: lane / group / source file.
8. **API goal ids** in `station.json` (`API-NN.n TITLE`); `python _system\engine\goals.py` regenerates the catalog.
9. **The model proposes, code decides** (see `engine\triage.py`, `55_lean_papers.enforce`).
10. **`--mock`** runs offline; **`--dry-run`** shows what would run; **health** shows the station OK.

## 6. Bringing the other APIs out

Sources: `D:\GitHub\pipeline-workflows\API\API`, `API\API 2`, `API\API 3`, `API_OLD\`, `APIs\`, and anything under
`stations\` that is an API not yet in ONE_MENU. `API\Open-AI-CALL-OBS-Plugin-Final-Claude` is replaced by
`000_QUICK_CALL`; keep it as `_system\vendor\_retired\QUICK_CALL_OLD`.

For each API:
1. Copy its code into its new `NNN_NAME\BACKSIDE\` with `_system\tools\migrate_legacy.py` (it rewrites hard paths
   to `paths.json` keys and provider URLs to the relay, and logs each change in `MIGRATION_REPORT.md`). Extend the
   tool for new patterns; never hand-edit a path without logging it.
2. Wrap it as a station in that `BACKSIDE` (`station.json`, `PROMPT.md`, `FOCUS.md`, `README.md`, native script
   preferred, or a legacy wrapper through `engine\legacy.py`).
3. Bring it up to section 5. Where a legacy script cannot (e.g. it chunks input), rewrite that part natively and
   note it in `CONSOLIDATION.md`.
4. Plumbing folders in the old containers (INBOX, OUTBOX, PROCESSED, PROCESSING, ERRORS, RECEIPTS, RETRY, REVIEW,
   SCRIPTS, PYTHON, BACKSIDE, logs): scripts go into the right API's `BACKSIDE` (or `_system` if shared), data to
   `_data`; list what was where.
5. Same-named APIs (e.g. `CKG` in `API\API` and in `API\API 3`): diff them, keep the better one, put the other in
   `_system\vendor\_duplicates\`, summarize the diff in `CONSOLIDATION.md`.

`python _system\tools\pull_up_api_folders.py "<pipeline-workflows folder>"` (preview only) gives the starting list.

## 7. Order of work (stop at the gate)

1. **Plan, no moves:** `MAIN\_system\FRONT_FOLDER_PLAN.md`: every API found (from the CODEX sketch and the
   sources), where it is now, its number and folder name, its launchers (names), whether it has an INBOX, which
   OUTBOXes it reads from, duplicates, and anything pointing at a parent folder or a drive letter.
2. **Gate: stop and show David the plan.** Nothing else until he approves or edits it.
3. Engine changes (section 4) with tests.
4. Move / migrate one family per commit (`git mv`, history kept); after each: unit tests, `health.py`, and a
   `--mock --limit 1` run of every station touched.
5. Update `_system\README.md`, `CONSOLIDATION.md`, `MIGRATION_REPORT.md`, `API_GOALS.md`.

## 8. Current ONE_MENU stations (keep these numbers)

| no. | station | takes | API |
|---|---|---|---|
| 01 | YT_GRAB | channel / URL (launcher asks) | local |
| 02 | YT_CLEAN | transcripts | local |
| 03 | YT_INDEX | transcripts | DeepSeek |
| 04 | YT_LENSES | transcripts | DeepSeek |
| 05 | YT_CATALOG | channels | local |
| 06 | YT_WATCH | watch list | DeepSeek |
| 07 | YT_CONVERT | SRT / VTT / JSON | local |
| 08 | YT_SUMMARY | videos | DeepSeek |
| 09 | YT_DEEP | videos | DeepSeek |
| 10 | CKG_THEOLOGY | videos | DeepSeek |
| 11 | CKG_PHYSICS | videos + papers | DeepSeek |
| 12 | YT_TIDY | transcripts (`--watch`) | local |
| 13 | YT_CHANNEL_SUMMARY | videos | DeepSeek |
| 20 | CKG_RUN | CKG inbox | DeepSeek |
| 21 | CKG_EXTRACT_CPE | CKG output | local |
| 22 | CKG_INBOX_CHECK | CKG inbox | local |
| 30-39 | EVIDENCE family (intake, merge, best arguments, one argument, series synthesis, arcs, three dials, SQLite, sidecars, chain intake v2) | evidence inbox | mixed |
| 40 | ANALYTICAL_ARMS | papers | DeepSeek |
| 41 | STORY | papers | DeepSeek |
| 42 | STATISTICS_WALL | papers + videos | local |
| 43 | PAPER_GRADER | papers | local |
| 44 | TAGGER | papers + videos | DeepSeek |
| 45 | CLAIM_ATOMS | papers | DeepSeek |
| 46 | REPORT_COMBINE | everything run | local |
| 47 | NEW_PAPER | paper files | local |
| 48 | TOPIC_SYNTHESIS | a topic (launcher asks) | DeepSeek |
| 49 | GAP_MAP | a topic + own work | DeepSeek |
| 50-54 | LEAN_PAIR_AXIOMS, LEAN_GOD_IS_UNPROVEN, LEAN_ATOM_EXTRACTOR, AXIOM_ONE_PAGE_TRANSFORM, AXIOM_NODES_RUNNER | Lean / axioms | mixed |
| 55 | LEAN_PAPERS | Lean inbox | DeepSeek |
| 60 | OPENAI_STATIONS (23 prompts in 11 bundles, run on DeepSeek) | papers | DeepSeek |
| 90 | HEALTHCHECK | — | local |
| 91 | RELOCATE | — | local |

90 and 91 stay menu-only (SETUP.bat covers them); no front folder.

## 9. Never

- Never delete: retire into `_system\vendor\_retired\` or `_duplicates\`.
- Never put a key in a file; never allow a provider other than DeepSeek (`allowed_providers`).
- Never chunk an input document; never let the model certify what code should decide.
- Never leave a script, prompt, config or log outside a `BACKSIDE` or `_system`, except `ONE_MENU.bat`,
  `SETUP.bat` and the numbered launchers.
- Never overwrite a folder or file that exists; report it.

## 10. Done means

- MAIN's top level: `ONE_MENU.bat`, `SETUP.bat`, the `NNN_` folders, hidden `_system` and `_data`. Nothing else.
- Every `NNN_` folder: 1-4 numbered launchers, INBOX (priority / series / group) if it takes files, OUTBOX (flat),
  `BACKSIDE`. Nothing else.
- Every station passes section 5; tests, health check and a mock run are green; the plan file lists every API that
  existed before and where it went.
