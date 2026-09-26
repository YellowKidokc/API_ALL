# CODEX MASTER PROMPT: build ONE_MENU, the single front door for every API pipeline

This prompt replaces and consolidates every earlier prompt (`CODEX_PROMPT_ONE_MENU.md` and the specs are still here as detail).
Where the two disagree, this file wins. Owner: David. Written 2026-09-26.

---

## 0. The goal in one paragraph

David runs dozens of API pipelines: YouTube indexing, CKG, EVIDENCE intake, paper grading, Fruits of the Spirit, master equation,
axiom nodes, coherence, Lean, and more. Today each variant is its own .bat file, scattered across folders, with hard-coded paths.
Build **one portable folder** with **one batch file**. Double-click it, pick what to run by number (one, several, or a preset
routine), answer a few questions (turbo? how many? anything extra to focus on?), and it runs, in parallel, with every result
landing in a predictable place. Copy the folder anywhere and it still works.

---

## 1. What is in this repo (read these first)

| Path | What it is |
|---|---|
| `00_READ_ME_FIRST.md` | Where every gathered folder came from (live original locations) |
| `01_YOUTUBE` … `07_PIPELINE_WORKFLOWS_API` | Copies of all current scripts, prompts, templates, schemas |
| `08_NEW_STATION_SPECS/` | New specs to build: `STORY_STATION_V2.md`, `MASTER_EQUATION_STATION_V2.md`, `ANALYTICAL_ARMS_V1.md`, `STATISTICS_WALL_V1.md`, `STATISTICS_MATRIX_PROTOTYPE.html` |
| `09_SOURCE_API_FOLDERS/` | Code and prompts from `D:\GitHub\pipeline-workflows\API` (`API`, `API 2`, `Open-AI-CALL-OBS-Plugin-Final-Claude`, whose 23 `api_call_NN` stations each have prompts and templates). Run data (inbox/outbox) was left out. |
| `CODEX_PROMPT_ONE_MENU.md` | The earlier, longer prompt: station tables, YouTube workflow detail |

Real run data and API keys are **not** in this repo. Keys come from environment variables (`DEEPSEEK_API_KEY`, `OPENAI_API_KEY`).
Never commit a key. A local `config.txt` with real keys exists on David's machine in `API 2\writing-analyzer` and is git-ignored.

---

## 2. The folder you build

```
API_HOME\
  ONE_MENU.bat              the ONLY front door (about 10 lines: find Python, run engine\menu.py)
  RELOCATE.bat              run after moving the folder: fixes every external path in one pass
  README.md
  config\
    paths.json              every location OUTSIDE API_HOME (git-ignored; ship paths.example.json)
    settings.json           max_concurrent_calls, default provider/model, retry policy
    stations.json           the station list: number, name, folder, script, rank, options it accepts
    routines.json           pre-made combos (e.g. "A = 21 22 23 24")
    tags.json               the tagger's ~20 tags
  engine\
    paths.py                the ONLY place paths resolve
    menu.py                 the menu
    llm.py                  the ONLY place API calls are made (global limiter, retries, receipts)
    focus.py                assembles standing, per-paper and per-run focus into the prompt
    report.py               combines station outputs into report.html + report.xlsx
  stations\
    01_YT_GRAB\             01_yt_grab.py         PROMPT.md  FOCUS.md  station.json  README.md
    02_YT_CLEAN\            02_yt_clean.py        ...
    ...                     (full list in section 5)
  templates\PAPER_FOLDER\   the per-paper working-folder skeleton (section 8)
  lenses\  layers.json      YouTube focus library (numbered lenses + lettered layers)
  LOGS\  STATE\
```

### Naming rule (David's request)
**Every station folder is `NN_NAME`. Its main script is `NN_name.py`, with the same number and the same name in lower case.** The menu
number is the folder number. Backside copies, logs, receipts and outputs all use the same `NN_NAME` label, so a number in a
log line points straight at the folder that produced it. Numbers are permanent. A retired station keeps its number and is marked
`retired` in stations.json, and its number is never reused.

---

## 3. Portability: copy it anywhere and it works

- No script contains an absolute path. Paths inside API_HOME resolve relative to `engine\paths.py`. Everything outside it comes
  from `config\paths.json` by key (e.g. `subtitles`, `vault`, `lean_root`, `nas_brain`, `excel_lexicons`, `papers_root`).
- **Migration step (do this first):** search every copied script for hard-coded roots (`D:\`, `C:\Users`, `\\192.168.2.50`,
  `X:`, `E:`, `O:`), replace each with a `paths.py` key, and write `MIGRATION_REPORT.md` listing every replacement.
- **RELOCATE.bat:** detects its own location, then walks `paths.json` and marks each entry found / missing. For missing ones it asks for
  the new location (Enter = keep), validates, saves, and finishes with a health check of every station. Nothing else changes,
  because scripts hold no paths.

---

## 4. The menu

```
 1  What to run?      one number, several ("22 23 24"), or a routine letter ("Y").  Enter = repeat last run
 2  Options           Turbo? (concurrency preset) · How many items? [all] · Provider [deepseek] · Redo finished items? [N]
 3  Extra focus?      0 = none · a saved focus number · or type it in your own words   (adds to FOCUS.md, see section 6)
 4  Confirm           show the exact plan (stations, item count, focus, estimated tokens and time), then run
```
- Show the **top 20 stations by `rank`** by default, and `M` shows all of them (about 60 now, more coming). Log every run. Suggest re-ranking when
  usage drifts, but David's manual rank always wins.
- Only ask the options a station accepts (stations.json declares them). Never fake an option a script doesn't have.
- Everything also works without questions: `ONE_MENU.bat 22 23 --turbo --limit 5 --focus "biblical prophecy"`.
- `ONE_MENU.bat find resurrection --min 5` runs the tagger search (section 10).
- Adding a station = a new `stations\NN_NAME\` folder plus one entry in stations.json. It never needs a new .bat.

---

## 5. Stations and numbers

Group numbers by family, leaving room to grow. Build the ones marked **NEW** from their specs. Wrap the rest (keep their logic, move
their paths and API calls onto `engine\`). The `rank` column seeds the top-20 menu; David will adjust it.

| NN | Station | Source today | Rank |
|---|---|---|---|
| 01 | YT_GRAB (channel / playlist / video) | `yt-transcript-downloader\ytgrab.py`, GRAB_CHANNEL / GRAB_BIG_CHANNEL | 1 |
| 02 | YT_CLEAN (local Python, never an API) | `Python Clean Library\clean_library.py` | 2 |
| 03 | YT_INDEX (standard CKG argument-first) | `deepseek-home\index_video.py` | 3 |
| 04 | YT_LENSES (numbered focus + layers) | `deepseek-home\lens_pass.py` | 4 |
| 05 | YT_CATALOG (overviews, debate pages, xlsx/sqlite) | `deepseek-home\build_catalog.py` | 5 |
| 06 | YT_WATCH (automatic chain) | `deepseek-home\watch_pipeline.py` | 6 |
| 07 | YT_CONVERT (SRT/VTT/JSON → md, keep originals) | conversion station `Run-Inbox.ps1` on X: | 15 |
| 20 | CKG_RUN | `_BACKSIDE\CKG\PYTHON\run_ckg.py` | 7 |
| 21 | CKG_EXTRACT_CPE (claims / proofs / evidence) | `extract_claims_proofs_evidence.py` | 16 |
| 22 | CKG_INBOX_CHECK | CHECK_CKG_INBOX.bat | 30 |
| 30 | EVIDENCE_INTAKE (turbo runner; add --limit, --focus) | `turbo_pipeline_runner.py` | 8 |
| 31 | EVIDENCE_MERGE_ORIGINALS | `api_original_merge.py` | 25 |
| 32 | EVIDENCE_BEST_ARGUMENTS (no API) | `best_arguments_and_weaknesses.py` | 12 |
| 33 | EVIDENCE_BUILD_ONE_ARGUMENT | `argument_builder.py` | 13 |
| 34 | EVIDENCE_SERIES_SYNTHESIS | `series_grand_synthesizer.py` | 22 |
| 35 | EVIDENCE_SERIES_ARCS | `series_evaluator.py` | 23 |
| 36 | EVIDENCE_THREE_DIALS | `three_dials_annotate.py` | 26 |
| 37 | EVIDENCE_SQLITE_SYNC | `sync_to_sqlite.py` | 27 |
| 38 | EVIDENCE_SIDECARS (sync / search) | `evidence_sidecars.py` | 31 |
| 39 | EVIDENCE_CHAIN_INTAKE_V2 | `EvidenceChainIntake\SCRIPTS\epistemic_intake_v2.py` | 32 |
| 40 | **ANALYTICAL_ARMS** (Fruits + master equation + axiom nodes + coherence, always together) **NEW** | `ANALYTICAL_ARMS_V1.md` | 9 |
| 41 | **STORY** (hook / sequence / coherence → series → memorable lines) **NEW** | `STORY_STATION_V2.md` | 14 |
| 42 | **STATISTICS_WALL** (every academic + Obsidian metric, percentiles) **NEW** | `STATISTICS_WALL_V1.md` | 10 |
| 43 | PAPER_GRADER (July grader, 20-layer schema) | `Academic_paper-proof-grader_Jul\pipeline.py` | 17 |
| 44 | **TAGGER** (20 tags, 0-10 each, searchable) **NEW** | section 10 | 11 |
| 45 | CLAIM_ATOMS | `API_DEEP\ATOMS\run_atoms.py` | 28 |
| 46 | REPORT_COMBINE (report.html + report.xlsx per paper) **NEW** | section 8 | 18 |
| 47 | NEW_PAPER (create the per-paper working folder) **NEW** | section 8 | 19 |
| 50 | LEAN_PAIR_AXIOMS (congruence matrix) | `theophysics_congruence_matrix.py` | 24 |
| 51 | LEAN_GOD_IS_UNPROVEN | `god_is_unproven_to_lean.py` | 29 |
| 52 | LEAN_ATOM_EXTRACTOR | `LEAN_ATOM_EXTRACTOR` | 33 |
| 53 | AXIOM_ONE_PAGE_TRANSFORM | `axiom_one_page_transform.py` | 34 |
| 60 | OPENAI_STATIONS 01-23 | `09_SOURCE_API_FOLDERS\Open-AI-CALL…\stations_raw\api_call_NN` (read each prompt; give each its own number 60-82 if it earns a place, otherwise list it as one grouped station) | 20 |
| 90 | HEALTHCHECK (every station, keys present, paths found) | new | 21 |
| 91 | RELOCATE | new | 35 |

Numbers 08-19, 23-29, 48-49, 54-59 and 83-89 are free for growth.

---

## 6. FOCUS: David's extra request, written on paper next to the call (David's idea)

Every station folder has a plain-text **`FOCUS.md`**. David writes 2-4 things he wants that station to hone in on, for example:
```
- Be especially alert to biblical prophecy and fulfilment claims.
- Flag every place the argument depends on the resurrection.
- Note any Hebrew or Greek word study and check it.
```
`engine\focus.py` gathers focus from three levels and appends them to every prompt the station sends, under
`## EXTRA FOCUS FROM DAVID`:
1. **Standing:** `stations\NN_NAME\FOCUS.md` (applies to every run of that station)
2. **Per paper / per channel:** `01_NOTES\FOCUS.md` in the paper's folder, or `focus\<Channel>.json` for YouTube
3. **Per run:** the answer to menu question 3

Rules:
- Focus **adds attention, it never removes** the station's normal job. The station still returns its full output. The focus
  adds a section `## Focus findings` answering each focus point, citing sources (sentence ids / timestamps).
- An empty FOCUS.md adds nothing. Lines starting with `#` are comments.
- The receipt (`<station>.run.json`) records the exact focus text and its hash, so every result shows what it was asked to look for.
- Why a paper file and not Python: David can change it without touching code, it lives in the exact folder of the call it affects,
  and it's versioned with the station.

---

## 7. Parallel by default: one whole item per call, 30 at a time

- **One item = one independent call, whole.** Parallel means many separate calls side by side: one per paper, per station, per arm.
  Never pack several items into one call. Never split a document that fits the model's context window: send it whole so every call has
  full context. No call continues from another.
- **The only split is on output size.** Replies are capped (deepseek-chat ≈ 8k output tokens). If a job must return something for every
  sentence of a long paper, send the **whole paper in every call** and split only *which sentences each call answers for* (S001-S080,
  S081-S160 …). Those calls also run in parallel. Chunk the input only when a document exceeds the context window, and log it.
  Existing input-chunking to remove: `index_video.py` (2,500-word chunks), `home.py claims` (1,200-word chunks).
- **Default 30 concurrent calls** (`settings.json`). Turbo presets 10 / 30 / 60, and `--workers N` overrides. The cost is identical to
  running one at a time; only wall-clock time changes (10,000 items in about an hour instead of a day).
- **One global limiter** in `engine\llm.py` that every call passes through. Papers × output ranges × arms must never multiply
  past the limit.
- **Rate limits:** on 429 / 5xx / timeout, retry with exponential backoff + jitter (3 tries). If errors pass ~10% over a minute, halve concurrency,
  then creep back up. Log every change.
- **Failures stay isolated:** one item failing never stops the batch. Save each finished item immediately (checkpoint). A rerun skips
  completed items (keyed by source hash + prompt version + model + focus hash).
- **Live progress line:** done / running / failed / remaining · tokens · estimated time left.

---

## 8. Outputs: template stations, one working folder per paper

**Every station run on an item writes:**
`<NN_station>.json` (canonical) · `<NN_station>.xlsx` (its own rows, e.g. per sentence) · `<NN_station>.html` (public-facing section) ·
`<NN_station>.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors).

**One working folder per paper**, created by station 47 NEW_PAPER from `templates\PAPER_FOLDER\`, always the same shape:
```
<PAPER_ID>_<slug>\
  paper.json        id, title, series, status, source hash, stations run, headline scores, tags
  00_SOURCE\        read-only copy of the original + sha256
  01_NOTES\         David's notes, review decisions, FOCUS.md for this paper
  02_RUNS\NN_STATION\<date>\   json / xlsx / html / receipt (dated, reruns never overwrite)
  03_REPORT\        report.html (public), report.xlsx (one tab per station), statistics.json, assets
  04_MEDIA\         audio, video, images
  05_WEB\           exactly what ships to the website
```
Every station writes only inside the paper's folder. `papers_root` comes from paths.json. Station 46 REPORT_COMBINE builds
`report.html` + `report.xlsx` from whatever stations have run.

**The public report's statistics view must follow `08_NEW_STATION_SPECS\STATISTICS_MATRIX_PROTOTYPE.html` exactly.** David approved
this design. Keep its encodings and feed it `statistics.json` instead of demo data:
- headline strip of 12
- the matrix: one band per family, one circle per statistic, colour = needs work↔strong on a diverging scale, size = |z|,
  inner glyph = computed / AI-judged / runs disagree, dashed = no academic benchmark, a corpus vs academic toggle
- family map: academic × corpus
- 15 specialised charts
- the full searchable wall

---

## 8b. Baselines: the two standard runs (David, 2026-09-26)

Put these in `config/routines.json` as the first two routines, and show them at the top of the menu:

| Routine | Applies to | Stations |
|---|---|---|
| **B: Baseline** | every paper, transcript or document | SUMMARY + CKG (20 CKG_RUN) |
| **P: Published paper** | every paper David publishes (most of the corpus) | Baseline + **40 ANALYTICAL_ARMS** (axiom nodes, master equation, coherence, Fruits, run together as one grouped run) + **42 STATISTICS_WALL** + 46 REPORT_COMBINE |

- SUMMARY is one merged station replacing the four existing summarizers (exec-summary, summarizer, summary-quad, Atlas synthesis). It gives one sentence, one paragraph, an executive summary and a story version, with DeepSeek as the writer.
- Everything else stays optional, picked from the menu when wanted.

**Report pipeline (JSON → HTML, per paper):**
1. Each station writes its canonical `NN_station.json` into the paper folder (`02_RUNS/`).
2. Each station folder keeps its **own HTML template** (`stations/NN_NAME/templates/section.html`), the piece of the report that station owns.
3. Station 46 REPORT_COMBINE loads every JSON for the paper, fills each station's template, and assembles `03_REPORT/report.html`, the finished public report for that paper. The statistics section uses the approved matrix template.
4. Templates contain no logic beyond placeholders and loops. Data comes only from the JSON, so any paper can be re-rendered at any time without new API calls.

## 9. The new stations: build from their specs

- **40 ANALYTICAL_ARMS**: `ANALYTICAL_ARMS_V1.md`. Local word-level lexicon pass → per-sentence scores from -2 to +2 on 9 fruits (whole
  paper per call, output ranges) → local curves, spikes, and the lexicon-vs-meaning gap (counterfeit / hidden fruit) → the four arms in
  parallel → cross-arm disagreements. **David is redoing Fruits himself:** build Fruits as a plug-in whose prompt, rubric and lexicons
  load from files. His Excel sources: `Fruits Template (1) (1).xlsx` (Truth Engine v2.0) and `lexicons_master_enhanced.xlsx` (paths in paths.json).
- **41 STORY**: `STORY_STATION_V2.md`. Paper pass → series pass → a gated memorable-lines pass (one line per paragraph, only if coherent).
- **42 STATISTICS_WALL**: `STATISTICS_WALL_V1.md`. Step 1: run the existing 116 metric scripts (`\\192.168.2.50\brain\Python API`)
  on one paper and report which of the 366 schema variables actually come out. Then add the listed families, and give every
  metric a corpus percentile, a series percentile and the change since the previous version.
- **44 TAGGER**: section 10.
- **Master equation** analog logic: `MASTER_EQUATION_STATION_V2.md` (runs inside 40).

---

## 10. Tagger (station 44): find the right papers and videos fast

- `config\tags.json`: about 20 tags David edits. Draft: resurrection, existence of God, problem of evil/suffering, creation/evolution,
  fine-tuning, consciousness, information/logos, Bible reliability, prophecy, Christology/Trinity, salvation/grace, morality,
  miracles, science and faith, apologetics method, church and ethics, end times, prayer, one-world/conspiracy, master equation/Theophysics.
- Every paper and every video gets a **0-10 score per tag**. Anything scored 5 or more carries one quote or timestamp and a one-line reason.
- Keep it cheap: run the local zero-shot model first (M22, `nas_brain\05_MODELS`) and confirm only scores of 5+ with DeepSeek.
- Store the scores in the catalog SQLite `tag_scores(item_id, kind, tag, score, reason, quote_or_ts)` and in paper.json / the video index JSON.
- `ONE_MENU.bat find resurrection --min 5` lists items scoring 5+, best first, with path and reason.
- It runs automatically after YouTube indexing and after NEW_PAPER.

---

## 11. YouTube chain (already partly built in `01_YOUTUBE\deepseek-home`)

The chain: download → keep the original + converted .md → clean (local) → index (CKG) → channel focus (lenses) → tagger → catalog, fully automatic.
- Built and tested: numbered lenses 1-17 (`lenses\*.md`, id in front matter), lettered **layers** in `layers.json` (A Arguments,
  C Christianity, S Science/Theophysics, W One-world/conspiracy, K Clips), a per-channel saved focus via
  `lens_pass.py --pick` → `focus\<Channel>.json`, and the watcher applying that focus to every new video.
- To add: ask the focus question right after a grab (`lens_pass.py --pick-only`), then "auto-process new videos from this channel?"
  → add the channel to WATCH_CHANNELS.
- **Gap to fix:** GRAB_CHANNEL.bat saves to `E:\YouTube\channels`, but the whole chain reads `subtitles\`. Make one default; ask David which.
- **Originals:** SRT/VTT/JSON are converted by the X: conversion station. Keep the original beside the .md
  (`subtitles\<Channel>\_originals\`), named by video title with the video ID in front matter. Report what Run-Inbox.ps1 does before changing it.

---

## 12. How to work and how you are done

1. Read `00_READ_ME_FIRST.md` and this file. Inventory every script's real CLI flags; don't assume.
2. Build `engine\` (paths, llm with limiter, focus, menu) and the path migration first, with MIGRATION_REPORT.md.
3. Wrap existing stations into numbered folders, then build the NEW ones.
4. **Test with real runs at small limits** (API cost for tests is fine):
   - `ONE_MENU.bat 30 --limit 1 --focus "entropy"`
   - `ONE_MENU.bat 40 --limit 1`
   - `ONE_MENU.bat Y --limit 1`
   - `ONE_MENU.bat find resurrection --min 5`
   - Copy API_HOME to another drive, run RELOCATE.bat, then run station 90 HEALTHCHECK.
5. Report: what ran, where the outputs landed, tokens used, anything that failed, and every decision below still open.

Acceptance:
- one .bat
- no absolute paths in scripts
- every station is `NN_NAME\NN_name.py` with a FOCUS.md
- 30-way parallel through one limiter
- per-paper folders created from the template
- report.html uses the approved matrix design
- no keys in git

## 13. Decisions to ask David (don't guess these)
1. One download location for YouTube: `subtitles\` or `E:\YouTube\channels`?
2. The 12 headline numbers for the statistics strip (he wants to see real numbers first).
3. Which axiom registry is canonical: AXIOMS_PART1 (A1.1…), the AX-### pills, or the single root axiom "God Is"?
4. Sentence scale for Fruits: -2..+2 (proposed) vs 0-4.
5. Which of the 23 OpenAI `api_call_NN` stations earn their own number.
6. Whether YouTube transcripts also run the analytical arms.
