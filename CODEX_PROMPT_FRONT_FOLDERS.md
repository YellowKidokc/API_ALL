# CODEX PROMPT: one front folder per API, numbered 000+, everything else hidden

**Repository:** `D:\GitHub\pipeline-workflows` (branch of your choice; do not push to main without David).
**Main folder (MAIN):** `D:\GitHub\pipeline-workflows\API_ALL\API_HOME` (the portable ONE_MENU folder). If David
names a different main folder, use it and change nothing else in this prompt.
**Read first:** `MAIN\_system\README.md`, `MAIN\_system\engine\` (station.py, menu.py, inbox.py, gateway.py, paths.py),
`MAIN\_system\stations\55_LEAN_PAPERS\` (the reference station) and `MAIN\LEAN\` (the reference front folder).

---

## 1. What David sees

Opening MAIN shows every API as its own numbered folder, even if there are 50, plus the two launchers:

```
MAIN\
  ONE_MENU.bat                  (everything, by number, as today)
  SETUP.bat                     (key, paths, hides the machinery)
  000_QUICK_CALL\
  001_YT_GRAB\
  ...
  055_LEAN_PAPERS\
  ...
  _system\                      hidden: ALL scripts, prompts, templates, config, vendor code, logs
  _data\                        hidden: working folders, receipts, caches
```

Clicking into any API folder shows only:

```
055_LEAN_PAPERS\
  1 RUN ALL.bat                 1 to 3 launchers, numbered, named in plain words. Click, don't think, it runs.
  2 RUN PRIORITY ONLY.bat
  INBOX\                        only if the API takes files in
    00_PRIORITY\
    01_SERIES\<series name>\    the folder name is the series
    02_GENERAL\<group name>\    grouped like a series without being one (e.g. "One pagers"); folder name = group
  OUTBOX\                       every paper printed flat into the root: "<title> - <kind>.md"
```

No scripts, READMEs, configs, logs or receipts in an API folder. There is exactly **one** hidden folder for all of
that: `MAIN\_system` (plus `_data` for run data). SETUP.bat already hides both (`attrib +h`).

## 2. Numbering

- Three digits, `000` upward. Keep the numbers ONE_MENU already uses so the menu and the folders agree:
  station `55` → folder `055_LEAN_PAPERS`, `07` → `007_YT_CONVERT`, and so on (full list in section 7).
- `000_QUICK_CALL` is the current `MAIN\QUICK_CALL` (move it; keep its contents exactly).
- `MAIN\LEAN` becomes `055_LEAN_PAPERS` (move it; its launchers already work; fix their `..\_system` path if the
  depth changes).
- APIs brought in from `API\API`, `API\API 2`, `API\API 3` (section 4) get the next free numbers in their family
  (YouTube 01-19, CKG 20-29, evidence 30-39, papers 40-49, Lean/axioms 50-59, bundles 60-69, then 100+ for
  anything that fits no family). Record every assignment in `MAIN\_system\config\stations.json`.

## 3. Rules every API folder and every station must meet (the rigor bar)

The reference is `55_LEAN_PAPERS`. A station is done only when all of these are true:

1. **Launchers** (`1 ... .bat`): 5-10 lines, `%~dp0`-relative, call `MAIN\_system\engine\menu.py <NN> --yes`
   (options via `--station-args "..."`), check `DEEPSEEK_API_KEY`, end with `pause`. No hard-coded paths.
2. **Paths**: the API folder's INBOX / OUTBOX are the station's `paths.json` keys (defaults in
   `config\paths.example.json`, relative, e.g. `"../055_LEAN_PAPERS/INBOX"`); working folders go to
   `../_data/<station>/work`. Scripts never live in, or write scripts to, the API folder.
3. **DeepSeek only**, through the local relay (`engine\gateway.py`); keys only from the environment.
4. **One item = one whole-document call.** Never chunk the input. Too big → skip with a clear message.
   Split only outputs if needed.
5. **Parallel**: independent calls side by side (default 30, `--workers`), one global limiter.
6. **One for one**: each item is saved the moment it finishes; a rerun skips finished items; an interrupted run
   loses only what was mid-flight.
7. **Show every step** live (`ctx.step`) and save `steps.log`; every reply saved as `calls\<goal id>-<n>.json`;
   receipt `.run.json` per item.
8. **Outputs**: JSON (canonical) + Markdown papers printed flat into OUTBOX + `.xlsx` where there are rows.
   Every paper starts with one line: lane / group / source file.
9. **API goal ids** in `station.json` (`API-NN.n TITLE`); `python _system\engine\goals.py` regenerates the catalog.
10. **The model proposes, code decides**: any rule that matters (status, caps, verification claims) is enforced in
    Python, as in `engine\triage.py` and `55_lean_papers.enforce`.
11. **Mock + dry run**: `--mock` runs the whole station offline; `--dry-run` shows what would run.
12. **Health**: `python _system\engine\health.py` shows the station OK (its declared options exist in `--help`).

## 4. Bring the other APIs out

Sources: `D:\GitHub\pipeline-workflows\API\API`, `API\API 2`, `API\API 3`, and anything under `APIs\` or `stations\`
that is an API not yet in ONE_MENU. (`API\Open-AI-CALL-OBS-Plugin-Final-Claude` is replaced by `000_QUICK_CALL`;
keep the old one as `_system\vendor\_retired\QUICK_CALL_OLD`, do not delete it.)

For each API found:
1. Copy its code into `MAIN\_system\vendor\<name>\` with `_system\tools\migrate_legacy.py` (it rewrites hard paths
   to `paths.json` keys and provider URLs to the relay, and logs every change in `MIGRATION_REPORT.md`). Extend
   the tool if a new pattern needs it; never hand-edit paths without logging it.
2. Wrap it as a station: `_system\stations\NN_NAME\` with `station.json`, `PROMPT.md`, `FOCUS.md`, `README.md`
   and either a native script (preferred, like 55) or a legacy wrapper (`engine\legacy.py`).
3. Make it meet section 3. If a legacy script cannot (e.g. it chunks input), rewrite that part natively and say so
   in `CONSOLIDATION.md`.
4. Create its front folder `MAIN\NNN_NAME\` (section 1).
5. Plumbing folders inside the old containers (INBOX, OUTBOX, PROCESSED, PROCESSING, ERRORS, RECEIPTS, RETRY,
   REVIEW, SCRIPTS, PYTHON, _BACKSIDE, logs) are not APIs: take their scripts into `_system`, their data into
   `_data`, and list what was where.
6. Two APIs with the same name (e.g. `CKG` in `API\API` and in `API\API 3`): diff them, keep the better one as the
   station, keep the other under `_system\vendor\_duplicates\`, and write the diff summary in `CONSOLIDATION.md`.

`_system\tools\pull_up_api_folders.py` shows the inventory (`python ... "<pipeline-workflows folder>"`, preview only);
use its output as the starting list.

## 5. Order of work (stop at the gate)

1. **Inventory (no moves):** write `MAIN\_system\FRONT_FOLDER_PLAN.md`: every API found, where it is now, its
   proposed number and folder name, which launchers it gets (1-3, with names), whether it has an INBOX, duplicates,
   and anything that points at a parent folder or a drive letter.
2. **Gate: stop and show David the plan.** Do nothing else until he approves or edits it.
3. Move / migrate in small commits (one family per commit, `git mv` so history stays), each followed by:
   `python -m unittest discover -s _system\tests`, `python _system\engine\health.py`, and a `--mock --limit 1` run of
   every station touched.
4. Update `_system\README.md` (the stations table and layout), `CONSOLIDATION.md`, `MIGRATION_REPORT.md`,
   `API_GOALS.md`.

## 6. Never

- Never delete anything: retire into `_system\vendor\_retired\` or `_duplicates\`.
- Never put a key in a file; never allow a provider other than DeepSeek (settings `allowed_providers`).
- Never chunk an input document; never let the model certify a result code should decide.
- Never leave a script, config or log in an API folder or at MAIN's top level, except `ONE_MENU.bat`, `SETUP.bat`
  and the numbered launchers.
- Never overwrite a folder or file that exists; report it instead.

## 7. Current ONE_MENU stations (keep these numbers)

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
| 47 | NEW_PAPER | paper files (INBOX) | local |
| 48 | TOPIC_SYNTHESIS | a topic (launcher asks) | DeepSeek |
| 49 | GAP_MAP | a topic + own work | DeepSeek |
| 50-54 | LEAN_PAIR_AXIOMS, LEAN_GOD_IS_UNPROVEN, LEAN_ATOM_EXTRACTOR, AXIOM_ONE_PAGE_TRANSFORM, AXIOM_NODES_RUNNER | Lean / axioms | mixed |
| 55 | LEAN_PAPERS | Lean inbox | DeepSeek |
| 60 | OPENAI_STATIONS (23 prompts in 11 bundles; DeepSeek) | papers | DeepSeek |
| 90 | HEALTHCHECK | — | local |
| 91 | RELOCATE | — | local |

90 and 91 stay menu-only (SETUP.bat covers them); they get no front folder.

## 8. Done means

- MAIN's top level: `ONE_MENU.bat`, `SETUP.bat`, the `NNN_` folders, and hidden `_system` / `_data`. Nothing else.
- Every `NNN_` folder: 1-3 numbered launchers, INBOX (if it takes files), OUTBOX. Nothing else.
- Every station passes section 3; tests, health check and a mock run are green; the plan file lists every API
  that existed before and where it went.
