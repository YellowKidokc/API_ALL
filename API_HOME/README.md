# ONE_MENU

One portable folder, one batch file, every API pipeline. Double-click `ONE_MENU.bat`, pick what to run by number
(one, several, or a routine letter), answer a few questions, and it runs in parallel: every result lands in a
predictable place and every step is shown as it happens. Copy the folder anywhere and run `RELOCATE.bat`.

## First use

1. Install Python 3.11+ and `pip install openpyxl` (for the .xlsx outputs). Optional, used when present:
   `textstat`, `vaderSentiment`, `spacy` (more statistics), `requests` and `openai` (some legacy scripts).
2. Set `DEEPSEEK_API_KEY` as an environment variable (and `OPENROUTER_API_KEY` for the free fallback).
   Keys never go in any file here.
3. Run `RELOCATE.bat` once. It creates `config/paths.json` from `config/paths.example.json`. By default all data lives in
   `ONE_MENU_DATA/` next to `API_HOME/` (relative paths, so it moves with the folder). Point any key at an existing folder
   instead, e.g. `yt_subtitles` at your current subtitles folder.
4. Run `ONE_MENU.bat`.

## The menu

```
1  What to run?     one number, several ("8 9 44"), or a routine letter ("Y"). Enter = repeat last run
2  Options          it counts first ("Found 1,000 transcripts in <channel>, 312 already done"), then asks:
                    all or how many? · how many in parallel? (default 30; 50 or 60 if you like) · provider · redo?
                    (only the options the chosen stations really accept)
3  Anything else?   shows everything that will run, then: "Is there anything else you want to add?"
                    one line each, or a saved focus number; you can save what you typed for next time
4  Run it?          then every step is printed live and saved as steps.log
```

If a run is interrupted, the next start offers to resume it; finished items are skipped, so only the items
that were mid-flight are redone. Each item is saved the moment it finishes (one for one).

Without questions:

```bat
ONE_MENU.bat 30 --limit 1 --focus "entropy"
ONE_MENU.bat Y --channel "Daily Dose Of Wisdom" --workers 50
ONE_MENU.bat 40 --limit 1
ONE_MENU.bat 48 49 --topic resurrection
ONE_MENU.bat find resurrection --min 5
ONE_MENU.bat goals                      (every API goal id, also in API_GOALS.md)
ONE_MENU.bat 40 --mock --limit 1        (fake replies, no key, no cost: tests the plumbing)
```

**What kind of channel is this?** Whenever a run includes YouTube stations the menu asks: Theology, Physics,
Conspiracy, Patterns or none (remembered per channel; station 01 asks right after a grab). Choosing one adds the CKG
index (03) and that domain's own stations right after it: Theology adds 10 CKG_THEOLOGY, Physics adds 11 CKG_PHYSICS.
Each is preselected and can be declined. Add domains or stations in `config/domains.json`. Without questions:
`ONE_MENU.bat Y --channel "Some Channel" --domain theology`.

**Top 20** starts empty on purpose: put the numbers and routine letters you use most in `config/top20.json`.
The menu suggests candidates from your run history; the full list is always shown underneath.

## Stations

| # | Station | What | API |
|---|---|---|---|
| 01 | YT_GRAB | download transcripts into `yt_subtitles`; then asks what to look for in this channel and whether to auto-process it | no |
| 02 | YT_CLEAN | clean transcripts into readable notes | no |
| 03 | YT_INDEX | CKG argument-first index per video (whole transcript per call) | yes |
| 04 | YT_LENSES | numbered lenses + lettered layers; your focus goes to its `--ask` | yes |
| 05 | YT_CATALOG | channel overviews, debate pages, catalog.xlsx / .sqlite | no |
| 06 | YT_WATCH | automatic chain for channels in WATCH_CHANNELS.txt | yes |
| 07 | YT_CONVERT | SRT / VTT / JSON to .md; originals kept in `_originals` | no |
| 10 | CKG_THEOLOGY | theology triage after the CKG index: 17 probes, CLEAN / NOTE / FLAG / CLAIM / ??, max 3 FLAGs, rules enforced in code; argument layer for the claim graph | yes |
| 11 | CKG_PHYSICS | physics mirror: which physics process a theological event mirrors (or the reverse), stage by stage, in order; identity / structural / analogy / none | yes |
| 08 | YT_SUMMARY | **base layer**: your questions in `QUESTIONS.md`, one whole-transcript call per video | yes |
| 09 | YT_DEEP | **detailed layer** on top of 08 (`DETAIL.md`) | yes |
| 20-22 | CKG | CKG run, claims/proofs/evidence split, inbox check | 20 |
| 30-39 | EVIDENCE | turbo intake (now with `--limit`), merge, best arguments, one argument, series synthesis/arcs, three dials, SQLite, sidecars, chain intake v2 | several |
| 40 | ANALYTICAL_ARMS | Fruits (per-sentence curve, counterfeit / hidden fruit) + master equation x2 + axiom nodes + coherence | yes |
| 41 | STORY | hook / sequence / coherence -> series -> gated memorable lines | yes |
| 42 | STATISTICS_WALL | 229-metric catalog in Python (same numbers every run) + corpus / series percentiles + change since last run | no |
| 43 | PAPER_GRADER | July deterministic grader | no |
| 44 | TAGGER | 20 tags 0-10; local pass first, DeepSeek confirms the candidates | yes |
| 45 | CLAIM_ATOMS | claim atoms (DeepSeek or Kimi) | yes |
| 46 | REPORT_COMBINE | aggregate every station's JSON in order; report.html (approved matrix, live data) + report.xlsx; fills your Excel templates | no |
| 47 | NEW_PAPER | per-paper working folder (`--own` marks your own work) | no |
| 48 | TOPIC_SYNTHESIS | **bridge**: best arguments for a topic across papers, videos, EVIDENCE; cross-referenced; multi-page report with citations | yes |
| 49 | GAP_MAP | **bridge**: your own work vs the synthesis: EXPAND · HOLES · CONTRACT · CITE (who said it first) · ORIGINAL | yes |
| 50-54 | LEAN + axioms | congruence matrix, GOD IS pairing, Lean atom extractor, axiom one-page, axiom-nodes runner | 52, 54 |
| 60 | OPENAI_STATIONS | the 23 api_call prompts, bundled: 22 stations in 11 calls | yes |
| 90 | HEALTHCHECK | every station, path and key; proves each declared option exists in the real script | no |
| 91 | RELOCATE | same as RELOCATE.bat | no |

Routines (`config/routines.json`): **Y** YouTube chain (07 02 08 09 44 46) · **I** CKG index + lenses + catalog ·
**P** paper complete (40 41 42 44 46) · **B** bridge (44 48 49) · **E** evidence intake · **A** evidence synthesis family.

## The bridge layer (why all of this exists)

`48 --topic resurrection` finds every paper, video and EVIDENCE companion that is really about the topic (tag score or
local pass), extracts every argument from each (one whole-source call each, all in parallel), cross-references them
into distinct arguments ranked by how many independent sources make them, writes the strongest form of each with
objections and replies, and builds a multi-page report. `49 --topic resurrection` then lays that over your own work
(papers made with `47 --own`, or files under `own_work`) and tells you where to **expand**, which objections are
**holes**, which claims to **contract**, who to **cite** because they reached the same conclusion first, and what
looks **original** in this corpus. Citations are always assembled from the source records, never written by the
model; anything from the model's general knowledge is marked "verify". Reports land in
`<syntheses_root>/<topic>/03_REPORT/`.

## Focus: your extra requests, next to the call

Three levels, appended to every prompt under `## EXTRA FOCUS FROM DAVID:`: the station's `FOCUS.md` (always),
the item's `01_NOTES/FOCUS.md` or the channel's saved focus (that item or channel), and what you type at question 3
(that run). Focus adds attention; it never removes the station's normal job. The receipt records the exact focus
text and hash. Legacy scripts receive it through the relay (below), or through their own flag (04 `--ask`).

## Parallel: many independent calls, one limit

Default 30 calls at once (question 2 or `--workers`). Every call from every station, new or legacy, passes through
one local relay (`engine/gateway.py`) that holds the only limiter, so papers x ranges x arms x stations never add up
past the limit. 429 / 5xx / timeouts retry with backoff; if more than 10% fail within a minute the limit halves, then
creeps back. One item = one whole-document call; only outputs are split (e.g. 80 sentences per range, all ranges in
parallel). A failed item never stops the batch.

## Providers

**Only DeepSeek (and the free OpenRouter fallback) can be called.** `settings.json` → `allowed_providers`: the relay
refuses every other provider, for new and legacy scripts alike, even if an OpenAI key is set on the machine. (The
`openai` Python package some scripts need is only a client library; it talks to DeepSeek.)

`config/providers.json` lists DeepSeek, OpenRouter (and `free`), OpenAI, Anthropic, Moonshot/Kimi, Gemini, Groq,
Together, Mistral, Ollama. DeepSeek is primary; when a DeepSeek call still fails after its retries (or has no key) the
call falls back to the free OpenRouter model in `settings.json` (`fallback`), and the receipt says so.

## Outputs

Every station run on an item writes, in `02_RUNS/NN_STATION/<date>/` (never overwritten):
`.json` (canonical) · `.xlsx` (its rows) · `.html` (public section) · `.run.json` (receipt: source hash, model,
prompt version, focus text + hash, tokens, time, errors) · `.md` where there is prose · `calls/<goal id>-<n>.json`
(every reply, with its API goal id) · `steps.log` (every step). Items share one folder shape
(`templates/PAPER_FOLDER`): papers under `papers_root`, videos under `yt_work/<Channel>/`.

Station 46 assembles all of it: `03_REPORT/aggregate.json|md` (every station's JSON in the order in
`config/assembly.json`, missing ones listed), `report.html` (the approved statistics matrix, fed with real data; a
chart without data says what it is waiting for), `report.xlsx` (one tab per station), and any Excel template you map
in `config/excel_templates/` (see `tools/excel_fill.py`).

## Statistics: Python first

Station 42 computes every metric it can in Python, so the same paper gives the same numbers every time, and marks
each one `python`, `python-heuristic`, `library:<name>`, `python:<suite>` or `api`. Your own suites (the Paper
Intelligence suite, `X:\Python API`) plug in through `config/metric_suites.json`; the July grader's two engines are
already on. `python stations/42_STATISTICS_WALL/42_statistics_wall.py --audit-suites` lists what each suite folder
contains and which scripts answer `--help`.

## Moving the folder

Nothing inside holds a path: internal paths come from `engine/paths.py`, external ones from `config/paths.json`
by key. After a move, `RELOCATE.bat` checks every key and finds moved ones again (same position relative to
API_HOME, same path on another drive letter, or a search by folder name + parent + fingerprint file), asks you to
confirm (`--auto` accepts), saves, and runs the health check.

## Legacy code

The gathered scripts are copied into `vendor/` by `tools/migrate_legacy.py`, which rewrites every hard-coded path to a
`paths.json` key and every provider URL to the relay, fixes the data bugs it knows about, and writes
`MIGRATION_REPORT.md` (every change, file and line). After you update a live script, copy it into the gathered folder
and re-run the tool. See `CONSOLIDATION.md` for what was merged, what is proposed, and what was retired.

## Tests

`python -m unittest discover -s tests` runs everything offline with `--mock`, including the full Y, P, 48 and 49 chains.

## Still yours to decide

1. The YouTube download location: `yt_subtitles` is the ONE location now (grab writes, the chain reads); point it at
   `subtitles\` or `E:\YouTube\channels` in `paths.json`.
2. The 12 headline numbers (a provisional 12 is in `42_statistics_wall.py`; see real numbers first).
3. The canonical axiom registry (AXIOMS_PART1 is used and named in every output; `axiom_registry` switches it).
4. The Fruits sentence scale (-2..+2 in use, marked provisional in `fruits_plugin/plugin.json`) vs 0-4.
5. Which api_call stations get their own number (all 23 run under 60, bundled).
6. Whether YouTube transcripts also run the analytical arms (40 works on videos when given them).
7. Which lexicon wins when the two Excel workbooks disagree (merged for now, source recorded).
8. Academic benchmarks for the matrix (`config/academic_norms.json`, empty until you add sources).
