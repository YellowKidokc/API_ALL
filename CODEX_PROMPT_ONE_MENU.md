# Codex task: ONE menu for every pipeline (papers, CKG, grader, YouTube)

**Start by reading `00_READ_ME_FIRST.md`.** Every script is copied into this folder
(`D:\GitHub\pipeline-workflows\API\API 3`, also on the NAS at `\\192.168.2.50\h_hp\Desktop\Folders\___Pipeline_Done_New\ONE_MENU_SOURCES`) so you can read it all in one
place. The table there gives each file's live original location. Read here, but make changes and
test runs against the live originals, since the copies are a snapshot.

## V2 REQUIREMENTS (David, 2026-09-25): these override anything below that conflicts

### 1. One portable folder, one front door
This folder (`API 3`) becomes the single home for every API station. The target shape:

```
API_HOME\
  ONE_MENU.bat            the only front door
  RELOCATE.bat            run after moving/copying the folder: fixes every path in one go
  config\paths.json       EVERY location outside API_HOME (subtitles, vault, NAS, Lean dir, Excel lexicons ...)
  config\stations.json    all stations (~58 now, more coming), each with a "rank"
  config\routines.json    pre-made combos
  config\tags.json        the tagger's tag list (section 5)
  engine\paths.py         the ONLY place paths are resolved
  engine\menu.py
  stations\<NN_name>\     one template folder per station (section 3)
  templates\PAPER_FOLDER\ the per-paper working-folder template (section 4)
```

**Portability rule:** copy API_HOME anywhere and it runs immediately. No script contains an absolute path.
Paths inside API_HOME resolve relative to `engine\paths.py`'s own location. Paths outside it come from
`config\paths.json`. Migration step: search every script for hard-coded roots (`D:\`, `C:\Users`,
`\\192.168.2.50`, `X:`, `E:`, `O:`), replace each with a `paths.py` key, and report the full list of replacements.

**RELOCATE.bat:** detects its own new location automatically, then lists every entry in `paths.json`, marks the
ones that no longer exist, asks for the new location of each missing one (Enter = keep), validates, and saves.
Nothing else is edited, because scripts never hold paths. Finish with a health check of every station.

### 2. Menu: top 20 first, room to grow
`stations.json` gives each station a `rank`. The menu shows the **top 20** by default. `M` shows all of them.
Adding a station = drop its folder in `stations\` + one entry in stations.json. It never needs a new .bat.
Log every run (station, date) so David can see which ones he actually uses. Suggest re-ranking when usage
drifts, but David's manual rank always wins. Expect many additions and refinements over the next two weeks,
so keep everything data-driven.

### 3. Every station is a template folder with several outputs per paper
Each station folder holds its prompt(s), rubric/schema, script and a README. Every run on a paper produces:
- `<station>.json`: canonical result (what everything else reads)
- `<station>.xlsx`: the station's own spreadsheet (per-sentence / per-item rows, where the station has them)
- `<station>.html`: a public-facing section of the report
- `<station>.run.json`: receipt (source hash, model, prompt version, tokens, time, errors)

After all stations have run, a combiner merges them into one workbook (one tab per station) and one public HTML
report with the statistics.

**Fruits of the Spirit is being redone by David.** Treat the Fruits section of `ANALYTICAL_ARMS_V1.md` as provisional:
build Fruits as a pluggable module whose prompt, rubric and lexicons load from files, so his new version drops in.

### 4. One working folder per paper, from beginning to end
Every paper that gets scored, classified and prepared for the website gets its own folder, built from
`templates\PAPER_FOLDER\`, always identical in shape:

```
<PAPER_ID>_<slug>\
  paper.json          manifest: id, title, series, status, source hash, stations run, headline scores, tags
  00_SOURCE\          read-only copy of the original + sha256
  01_NOTES\           David's notes and review decisions
  02_RUNS\<station>\  each station's json / xlsx / html / receipt (dated subfolders, so reruns never overwrite)
  03_REPORT\          report.html (public), report.xlsx (all station tabs), assets
  04_MEDIA\           audio, video, images
  05_WEB\             exactly what ships to the website
```
A `NEW_PAPER` station creates the folder from a source file and is idempotent. All stations write only inside
the paper's folder. The location of the papers root comes from `paths.json`.

### 5. Tagger station (new, light and cheap): for papers AND YouTube transcripts
Purpose: David searches "resurrection" and sees at once which papers and videos matter, strongest first.
- `config\tags.json` holds ~20 tags that David edits. Draft list: resurrection, existence of God, problem of evil and suffering,
  creation/evolution, fine-tuning, consciousness, information/logos, Bible reliability, prophecy, Christology/Trinity,
  salvation/grace, morality, miracles, science and faith, apologetics method, church and ethics, end times, prayer,
  one-world/conspiracy, master equation / Theophysics.
- Each item gets a **0-10 relevance score per tag**, with one quote (or timestamp) and a one-line reason for every score of 5 or more.
- Keep it cheap: one short call per item on the opening + summary + the index's argument list, or run a local
  zero-shot model first (David's NAS model M22 at `\\192.168.2.50\brain\05_MODELS`) and use DeepSeek only to
  confirm scores of 5 or more.
- Store the scores in the catalog SQLite as `tag_scores(item_id, kind, tag, score, reason, quote_or_ts)`, and in
  paper.json / the video's index JSON.
- Search: `ONE_MENU.bat find resurrection --min 5` lists papers and videos scoring 5+, sorted by score, with the
  path and reason. The same search is a menu station.
- For YouTube, it runs automatically after indexing, alongside the channel's saved focus.

### 6. Parallel by default: 30 at once
Cost per item is the same whether items run one at a time or 30 at a time, and local CPU, RAM and bandwidth barely
change. So every API station runs in parallel by default. The goal: 10,000 items in about an hour, not a day.
- **One item = one independent call, whole.** Parallel means many separate calls running side by side, one per paper,
  per station, per arm. Never pack several papers into one call. Never split a paper into chunks when it fits the model's
  context window: send the whole document so every call has full context. Each call stands alone and does not
  depend on or continue from another.
- **The one exception is the output limit, not the input.** A reply is capped (deepseek-chat: 8k output tokens), so a
  job that must return something for every sentence of a long paper can overflow it. In that case, still send the
  **whole paper in every call** and only split *which sentences each call answers for* (e.g. call 1 answers S001-S080,
  call 2 answers S081-S160). Those calls run in parallel too. Chunk the input itself only when a document is larger
  than the context window, and log it when that happens.
- Existing code that chunks input and must change: `index_video.py` (2,500-word chunks) and `home.py claims`
  (1,200-word chunks). Move them to whole-document calls, with the output-range split only where needed.
- **Default 30 concurrent API calls**, set once in `config\settings.json` (`"max_concurrent_calls": 30`). The menu's
  Turbo option picks a preset (e.g. 10 / 30 / 60), and `--workers N` overrides it for one run.
- **One global limit, not per level.** Stations parallelize at several levels at once: papers, chunks inside a paper,
  and the four analytical arms. So use ONE shared limiter (a semaphore in `engine\`) that every API call goes
  through. Otherwise 30 papers × 7 chunks × 4 arms = 840 calls at once.
- **Rate limits:** DeepSeek has no fixed concurrency cap but slows or rejects under load. On HTTP 429/5xx or a timeout,
  retry with exponential backoff and jitter (3 tries). If errors pass ~10% over a minute, halve the concurrency
  automatically, then creep back up. Log every adjustment.
- **Failures stay isolated:** one item failing never stops the batch. Every finished item is saved at once (checkpoint),
  and a rerun skips completed items, so closing the window loses at most the calls in flight.
- **Live progress line:** done / running / failed / remaining, tokens so far, estimated time left.
- Existing worker settings to replace with the global setting: turbo_pipeline_runner `--workers 12`, CKG 30,
  index_video / lens_pass 4, watch_pipeline 8, series_evaluator 12, fruits 2/12.

### 7. Git
This folder lives in `D:\GitHub\pipeline-workflows\API\API 3` (repo `YellowKidokc/pipeline-workflows`, which is **public**).
Never commit keys or `config\paths.json` with private paths: commit `paths.example.json` instead. Do not
touch the unrelated uncommitted changes elsewhere in that repo.

---

## The problem
David has dozens of near-duplicate batch files (1_RUN_EVIDENCE_PIPELINE, 2_RUN_DEEPSEEK_PIPELINE,
RUN_TURBO_PARALLEL_12X, RUN_PIPELINE, GRAB_CHANNEL ...). Each one hard-codes one variant
(turbo or not, provider, worker count), so every new variant becomes another .bat.

## What to build
**One** front-door file, `ONE_MENU.bat`, that is identical everywhere it is copied, plus a
backside folder that holds the real logic:

```
\\192.168.2.50\h_hp\Desktop\APIs\APIs\_BACKSIDE\MENU\
    menu.py            the interactive menu (Python, not batch logic)
    stations.json      every runnable thing: number, name, command, which options it accepts
    routines.json      pre-made combos, e.g. "A = Evidence full run" -> [2, 9, 4, 10]
    focus\*.md         saved "look at this" presets (see Focus below)
    README.md
    LOGS\, STATE\menu_last.json
```

`ONE_MENU.bat` is ~10 lines: find Python, then run
`python "\\192.168.2.50\h_hp\Desktop\APIs\APIs\_BACKSIDE\MENU\menu.py" --here "%~dp0" %*`.
It uses an absolute path, so a copy dropped in any folder works. `--here` lets the menu default
to that folder: if the folder holds transcripts, it becomes the target channel; if it is an
EVIDENCE root, it becomes the evidence root.
Put copies in:
- `\\192.168.2.50\h_hp\Desktop\Folders\___Pipeline_Done_New\One page paper API\EVIDENCE\`
- `D:\GitHub\Research-Acquisition\yt-transcript-downloader\pipeline-workflows\deepseek-home\`
- `D:\GitHub\Research-Acquisition\yt-transcript-downloader\`

Leave every existing .bat working. Do not delete them. Optionally turn them into one-line
calls to the menu with arguments, e.g. `ONE_MENU.bat 2 --turbo`.

## Menu flow (every run asks the same four questions)
```
 1  What to run?     one number, several ("1 5"), or a routine letter ("A").  Enter = repeat last run
 2  Options          Turbo? [y/N] (12 workers vs 4) · How many? [all] · Provider [deepseek] · Redo done items? [N]
 3  Look at anything else?   0 = no · 1-9 = a saved focus from focus\ · or type it in your own words
 4  Confirm          print the exact commands, then run them in order; stop at the first failure
```
Only ask the options a chosen station accepts (stations.json says which). All flags must also
work non-interactively: `ONE_MENU.bat 2 9 --turbo --limit 5 --focus "entropy"` asks nothing.
Save the last choices to STATE\menu_last.json and log each run to LOGS\menu-YYYYMMDD.log.

## Stations to register (verify each command and flag before listing it)
Evidence (front root `...\One page paper API\EVIDENCE`, real scripts in `_BACKSIDE\EVIDENCE\SCRIPTS`,
front SCRIPTS\*.py are wrappers that set EVIDENCE_ROOT):

| # | Station | Script | Flags it has now |
|---|---|---|---|
| 1 | Paper intake: OpenRouter | turbo_pipeline_runner.py --provider openrouter | --workers --provider --model --timeout --continuous --root |
| 2 | Paper intake: DeepSeek | turbo_pipeline_runner.py --provider deepseek | same |
| 3 | Series grand synthesis | series_grand_synthesizer.py | --series --provider --model |
| 4 | Sync to SQLite | sync_to_sqlite.py | --db |
| 5 | Idle-timer inbox daemon | SCRIPTS\pipeline_watcher.exe | --idle-mins --root |
| 6 | Axioms × evidence × Lean pairing | theophysics_congruence_matrix.py | --db |
| 7 | GOD IS unproven claims → Lean | god_is_unproven_to_lean.py | --god-is-dir --lean-dir --local-lean-dir |
| 8 | Three Dials annotate one article | three_dials_annotate.py <article> | --model |
| 9 | Merge API output with originals | api_original_merge.py | --shelf --limit |
| 10 | Best arguments + shared weaknesses (no API) | best_arguments_and_weaknesses.py | --shelf --threshold --top |
| 11 | Build one argument | argument_builder.py | --find --ranks --name --list --model |
| 12 | Evaluate series arcs | series_evaluator.py | --series --all --provider --model --workers |
| 13 | Axiom one-page transform | axiom_one_page_transform.py | (read its argparse) |
| 14 | Sidecars: sync / search | evidence_sidecars.py | --root --search --search-prompt |
| 15 | Healthcheck | healthcheck.py | --root |

YouTube (`D:\GitHub\Research-Acquisition\yt-transcript-downloader`, see `pipeline-workflows\deepseek-home\README.md`):

| # | Station | Command |
|---|---|---|
| 20 | Grab channel / video URL | GRAB_CHANNEL.bat "<url>" (routes big channels to GRAB_BIG_CHANNEL) |
| 21 | Clean transcripts (local, no API) | Python Clean Library\clean_library.py --src subtitles --out obsidian_transcripts [--channel X] --punctuate |
| 22 | Index: standard CKG argument-first | deepseek-home\index_video.py <channel dir> --workers N --limit N [--force] |
| 23 | Lenses: look closer | deepseek-home\lens_pass.py <dir> --lens a,b --ask "<text>" --workers N --limit N |
| 24 | Catalog, overviews, debate pages (no API) | deepseek-home\build_catalog.py |
| 25 | Watch mode | deepseek-home\watch_pipeline.py |

CKG, grader and API_DEEP stations (see `02_CKG`, `04_PAPER_GRADER`, `05_API_DEEP_STATIONS`, `06_LEAN`):

| # | Station | Command (confirm flags by reading the code) |
|---|---|---|
| 30 | CKG check inbox | `APIs\CKG\CHECK_CKG_INBOX.bat` |
| 31 | CKG run (standard) | `_BACKSIDE\CKG\PYTHON\run_ckg.py --root APIs\CKG --workers N` (turbo = 30) |
| 32 | CKG extract claims/proofs/evidence | `_BACKSIDE\CKG\PYTHON\extract_claims_proofs_evidence.py` |
| 33 | Paper grader | `Folders\Academic Paper Grading\paper-proof-grader\pipeline.py` (read RUN.bat for the call) |
| 34 | Axiom 7Q stations | `paper-proof-grader\run_axiom_7q_stations.py` |
| 35 | Fruits of the Spirit grading | `API_DEEP\FRUITS\...\scripts\fruits_grade.py` (pilot 2 / full 12 / validate-only bats show the flags) |
| 36 | Claim atoms | `API_DEEP\ATOMS\SCRIPTS\run_atoms.py` |
| 37 | Axiom nodes | `API_DEEP\AXIOM_NODES\SCRIPTS\run_axiom_nodes.py` |
| 38 | Lean atom extractor | `LEAN_ATOM_EXTRACTOR\LAUNCH_LEAN_ATOM.bat` and its python |
| 39 | Evidence chain intake v2 | `pipeline-workflows\API\EvidenceChainIntake\SCRIPTS\epistemic_intake_v2.py` |

| 40 | **Story** (paper → series → memorable lines) | NEW: build from `08_NEW_STATION_SPECS\STORY_STATION_V2.md` |
| 41 | **Master-equation analog** | NEW: build from `08_NEW_STATION_SPECS\MASTER_EQUATION_STATION_V2.md` |
| 43 | **Statistics wall** (every academic + Obsidian metric, with corpus percentiles) | NEW: build from `08_NEW_STATION_SPECS\STATISTICS_WALL_V1.md`. Start by running the existing 116 metric scripts on one paper and reporting which of the 366 schema variables actually come out. |
| 42 | **Analytical arms** (Fruits + Master equation + Axiom nodes + Coherence, always run together) | NEW: build from `08_NEW_STATION_SPECS\ANALYTICAL_ARMS_V1.md`. It replaces running 35 / 37 / 41 / coherence separately. Ask David the 5 open decisions at the end of that spec first. |

Stations 40 and 41 are the two runners to build now. Follow their specs exactly: three passes and a gate
for Story, two independent passes plus agreement for the master equation. Use DeepSeek (`DEEPSEEK_API_KEY`) and JSON mode.
Test each on one real series (e.g. `01_GOD_IS`) and report the outputs.

The prompt-only stations in API_DEEP (COHERENCE_SCORE, LEAN4, MASTER_EQUATION, STORIES,
PAPER_GRADER\PROMPT.md) have no runner. Do not invent one. List them in the README as "prompt
ready, needs a runner" and ask David. The CKG START_HERE says grader/Fruits are not connected to
CKG. Keep them as separate stations and don't wire them together unless asked.

Suggested routines (put in routines.json; David will edit them):
- **A** Evidence full: 2 → 9 → 4 → 10
- **B** Lean pairing: 6 → 7
- **Y** YouTube full: 21 → 22 → 23 → 24 (channel from `--here` or asked)
- **H** Health: 15, plus a check that DEEPSEEK_API_KEY / OPENROUTER key are set

## Small script changes needed (back up each file first as `<name>.bak-YYYYMMDD`)
1. `turbo_pipeline_runner.py`: add `--limit N` ("how many papers"). Slice `collect_workload()`
   after priority ordering. Add `--force` too if re-running done papers is not already possible.
2. **Focus**, the key new feature. Add `--focus "<text>"` to turbo_pipeline_runner.py (and to
   series_evaluator.py / three_dials_annotate.py if simple). When given, append this to the prompt:
   `## EXTRA FOCUS FROM DAVID\nLook closely at: <text>. Add a section "## Focus: <text>" with the
   relevant passages (quoted), why they matter, and what is missing.` Record the focus in the
   master-index row / sidecar so outputs remain traceable.
   The YouTube side already has this: `lens_pass.py --ask "<text>"` (custom focus) and
   `lenses\*.md` (saved lenses: clips, soft-spots, theophysics, rhetoric). Use the same idea for
   papers: `_BACKSIDE\MENU\focus\*.md` presets. The menu's question 3 lists the presets for the
   chosen station type (paper presets for paper stations, `lens_pass.py --list` for YouTube).
3. Stations that already have `--limit`/`--workers` just pass them through. Stations without
   them hide those options. Never fake an option.

## Rules
- Real logic lives in the backside, front folders hold only ONE_MENU.bat and data.
- Never overwrite or move outputs, and never delete old .bat files.
- Python 3.12 on Windows, stdlib only for menu.py. Plain `input()` prompts, no curses.
- Test with real runs at small limits, e.g. `ONE_MENU.bat 2 --limit 1 --focus "entropy"` and
  `ONE_MENU.bat Y --limit 1`. API cost for test runs is fine. Report what ran and where outputs landed.
- Finish with README.md: how to add a station (edit stations.json), a routine (routines.json),
  and a focus preset (drop a .md in focus\).

## YouTube workflow: one automatic chain, with focus chosen per channel (added 2026-09-25)

The chain David wants, fully automatic once a channel is set up:

```
download (ytgrab) -> original kept + converted .md -> clean (local Python) -> index (standard CKG)
                  -> channel's saved focus/layers (lens_pass) -> catalog
```

Already built and tested in `deepseek-home` (copied here under `01_YOUTUBE\deepseek-home`):
- **Numbered focus menu 1-17**: `lenses\*.md`, with the number in the front matter `id`. `python lens_pass.py --list` shows it.
- **Layers** are lettered bundles of focus numbers in `layers.json`: A Arguments, C Christianity, S Science/Theophysics,
  W One-world/conspiracy claims, K Content/clips. David types a mix like `C 7 16`.
- **Per-channel focus**: `lens_pass.py "<subtitles>\<Channel>" --pick` asks "what should DeepSeek focus on", saves the
  answer to `focus\<Channel>.json`, and runs it. `--pick-only` saves without running.
- **Watcher**: `watch_pipeline.py` applies the channel's saved focus to every new video right after indexing it.

What the menu must add:
1. **Ask the focus question at download time.** After a GRAB station finishes a channel, call
   `lens_pass.py "<subtitles>\<Channel>" --pick-only`. Then ask "Auto-process new videos from this channel? [Y/n]"
   and, on yes, append the channel folder name to `deepseek-home\WATCH_CHANNELS.txt`.
2. **Fix the folder gap.** `GRAB_CHANNEL.bat` defaults to `E:\YouTube\channels\<Channel>`, but clean, index and
   the watcher all read `yt-transcript-downloader\subtitles\<Channel>`. Downloads that go to E: never get
   processed (E:\YouTube\channels does not exist on this machine right now). Make `subtitles\` the single
   default, or have the watcher also scan the E: root. Ask David which he wants.
3. **Keep the original and the conversion side by side.** SRT/VTT/JSON drops go through the conversion station
   (`X:\00_CONVERSION_STATION\Transcripts to Markdown\scripts\Run-Inbox.ps1`, where X: = `\192.168.2.50\brain`).
   Confirm the original file is kept (e.g. `subtitles\<Channel>\_originals\<same name>.srt`) next to the
   converted `<Channel>\<title>.md`, named after the video title with the video ID in the front matter.
   Never delete an original. Report what Run-Inbox.ps1 does today before changing it.
4. **Menu question 3** for YouTube stations lists the focus numbers and layer letters, and pre-fills the
   channel's saved focus (Enter = keep).
5. **New layers are data, not code**: adding a layer = one entry in `layers.json`; adding a focus = one
   `lenses\<name>.md` with the next `id`.

Cost to show in the menu before running: about 9k tokens per focus for a 13-minute video, scaling with length.
