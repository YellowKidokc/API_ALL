# SYSTEM INDEX — YouTube argument and story pipeline

The one page to read before touching this pipeline or pointing another API at it.
Folder: `yt-transcript-downloader/pipeline-workflows/deepseek-home/`

## What this is, and what it is not

| This pipeline | Not this |
|---|---|
| YouTube transcripts → argument, story and teaching records → Obsidian notes, catalog, SQL | CKG paper review (`\\192.168.2.50\h_hp\Desktop\APIs\APIs\_BACKSIDE`, `workbench/ckg.py`) |
| DeepSeek via `home.py` (one shared prompt home) | chi-evaluator (`pipeline-workflows/engines/chi-evaluator`), writing-analyzer, OpenAI stations |
| Outputs are **proposals**: inventory PARTIAL, human ruling pending | Canon or admitted atoms (`D:\GitHub\Faith-through-physics-atoms`), which only a human ruling changes |

It borrows the CKG template's shape but does not call the CKG engine or write to its RECORDS.

## Stations

| # | Station | Script | API | Input → output |
|---|---|---|---|---|
| 0 | Convert | `X:\00_CONVERSION_STATION\Transcripts to Markdown` (engine `transcript_adapter.py`, `deliver-transcripts.ps1`) | none | SRT / VTT / SBV / transcript JSON / pasted YouTube panel in `inbox\<Channel>\` → `subtitles/<Channel>/` |
| 1 | Download | `ytgrab.py` / `ytbsd.py` (repo root) | YouTube | → `subtitles/<Channel>/<title>.md` ([mm:ss] lines, Video ID) |
| 2 | Clean | `Python Clean Library/clean_library.py` | none (local punctuation model) | → `obsidian_transcripts/<Channel>/` |
| 3 | Index | `index_video.py` | DeepSeek (`index` per chunk, `synthesize` once per video) | → `obsidian_indexed/<Channel>/Videos/<title>.md` + `_API/<title>.index.json` |
| 4 | Catalog | `build_catalog.py` | none | → `<Channel>/Arguments, Stories, Teaching`, channel overview; shared `_DEBATES, _PEOPLE, _EVIDENCE, _THEOLOGY`; `catalog.xlsx`, `catalog.sqlite` |
| — | All of it | `RUN_PIPELINE.bat [channel]` | | safe to run while downloads continue |
| — | Ask DeepSeek | `home.py chat "..."` | DeepSeek | → `outputs/` |

## What DeepSeek is sent, in order (`home.build`)

`HOME.md` → `GLOSSARY.md` → `STATE.md` → `DEBATE_MAP.md` → CKG argument template, front half, read live from
`D:\GitHub\nerve\source\html\atoms\Template\CKGARGUMENT_TEMPLATE_V1.md` → `templates/STORY_TEMPLATE_V1.md` →
`tasks/index.md` (the JSON output contract) → the transcript chunk.

The fixed part comes first, so DeepSeek's prompt cache makes repeated calls cheap.

## IDs: permanent, never reused

| Thing | ID | Example | Defined in |
|---|---|---|---|
| Video | YouTube video ID | `kfXAp9P8Ba8` | transcript header |
| Subject | `S-…` | `S-BEGIN` | `DEBATE_MAP.md` |
| Question (a debate) | `Q-…` | `Q-JESUS-RESURRECTION` | `DEBATE_MAP.md` (new ones proposed, added by hand) |
| Argument | `<video>-A##` | `kfXAp9P8Ba8-A07` | assigned when the note is drawn |
| Story | `<video>-S##` | `kfXAp9P8Ba8-S02` | assigned when the note is drawn |
| Claim step | argument ID + step `n` | `kfXAp9P8Ba8-A07.3` | argument `steps` |
| Person, place, thing | canonical name (aliases merged by `synthesize`) | `Stephen Meyer` | `.index.json` → Obsidian `[[links]]` |

## Record kinds, and David's 10 profiles

| Profile | Where it lives now | Status |
|---|---|---|
| 1 Sources | Videos tab; note header (`source_file`, `source_sha256`) | built |
| 2 People, places, things | `people/places/things` + tags `person/…` | built; alias merge per video only |
| 3 Subjects and questions | `DEBATE_MAP.md`; `_DEBATES/<Q-ID>.md`; Questions tab | built |
| 4 Claims | argument `steps` (numbered, with `disputed_by`) | built as steps; not yet CLAIM atoms |
| 5 Arguments | Arguments tab; `### A##` in notes | built |
| 6 Evidence and proof refs | `evidence_cited`, `resources` (UNRESOLVED), `checks` | partial |
| 7 Objections and responses | Exchanges tab (DIRECT / REPORTED / SELF_POSED); PROPOSED per argument | built |
| 8 Assessments | strength/support/confidence (AI); story and teaching ratings; `david_*` columns empty | built; David's ratings pending |
| 9 Research tasks | `research_queries` (NOT_SEARCHED), `claims_to_verify`, `next_needed` | built as lists |
| 10 Relationships | `question_id`, `used_as_evidence_for`, `disputed_by`, `[[links]]` | implicit; no typed edge table yet |
| + Stories, teaching, concepts, lessons | Stories / Teaching / Concepts / Lessons tabs | built |

## Status vocabulary (same words everywhere)

- Inventory: `PARTIAL` (AI extraction, unreviewed) · `COMPLETE` (after human review)
- Resource verification: `UNRESOLVED` → `IDENTITY_VERIFIED` → `CONTENT_INSPECTED`
- Research: `NOT_SEARCHED` → `CANDIDATE_FOUND` → …
- Exchange mode: `DIRECT` · `REPORTED` · `SELF_POSED` · analyst `PROPOSED` (never counted as an exchange)
- Coverage: `ADDRESSED` · `PARTLY_ADDRESSED` · `NOT_ADDRESSED`
- Admission: `candidate`, `human_ruling: pending`

## Rules other APIs and sessions must follow

1. **Order is fixed: convert → deliver to `subtitles/<Channel>/` → clean (Obsidian-ready) → API.**
   `index_video.py` refuses any video without a cleaned note. Transcript cleaning stays local
   Python; DeepSeek is for analysis only.
2. Add debate questions to `DEBATE_MAP.md`; never rename or reuse an ID.
3. Stories and arguments: one passage is one record. A story offered as evidence stays a story and links to its argument.
4. Never fill David's rating columns, and never mark anything verified.
5. The `.index.json` is the authoritative record; the Markdown note is drawn from it (`--render-only` redraws with no API calls).
6. Nothing here writes to the atoms repo or CKG RECORDS. Export there is a separate, reviewed step (not built yet).

## Open decisions

- Atoms: argument steps as CLAIM atoms plus linked records (CKG-consistent), or new atom types in `vocab.json`.
- SQL: `catalog.sqlite` has flat tables now; a typed relationships table (profile 10) comes with the SQL build.
- Cross-video people merging (same person, different spellings across videos).
