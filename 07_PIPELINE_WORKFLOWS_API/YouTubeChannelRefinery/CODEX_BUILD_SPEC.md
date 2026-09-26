# CODEX BUILD SPEC — YouTubeChannelRefinery + Portable Watcher + Prompt Box

Build this inside `pipeline-workflows`. Follow the existing packet layout
(`templates/workflow_packet`) and reuse existing code instead of rewriting it.

## 0. Real input to test with

`D:\GitHub\Research-Acquisition\yt-bulk-subtitles-downloader\subtitles\channel_Gary Habermas - Videos_20260915_153130.md`

- 12 MB, one file, **359 videos, 351 with transcripts**.
- Header: `# <Channel> - Videos`, `**Total Videos:**`, table of contents.
- Each video section:

```text
## 12. <Video title>

**Video ID:** abc123
**URL:** https://www.youtube.com/watch?v=abc123
**Transcript Language:** English (auto-generated)

### Transcript

<one long paragraph>

---
```

Reuse: `yt-bulk-subtitles-downloader\split_playlist_markdown.py` already parses
this (`SECTION_RE`, `META_RE`, `slugify`, `write_index`). Import or vendor it.

---

## 1. Portable watcher — `tools/drop_watcher/`

One self-contained file that can be copied into ANY folder and started with a .bat.

```text
tools/drop_watcher/
  drop_watcher.py        # single file, stdlib + optional watchdog (fallback: polling)
  watch_rules.yaml       # what to do when files land
  WATCH.bat              # double-click: starts watcher on the folder it sits in
  INSTALL_WATCHER.bat    # copies the 3 files above into a folder you pick
```

### Behavior
- Watches a folder (default: the folder `WATCH.bat` is in; `--path` overrides). Recursive optional.
- Waits until a file is **stable** (size unchanged for N seconds) — channel downloads are written slowly.
- Matches files against rules in order; first match wins (or `continue: true`).
- Actions (all must support `dry_run: true`):
  - `move` / `copy` to a folder (templated path)
  - `rename` (templated name)
  - `mkdir`
  - `run` a script/command with `{file}`, `{stem}`, `{dir}` placeholders
  - `pipeline` — hand off to a workflow packet (`workflows/<Name>/INPUT`)
- Never deletes. Replaced/processed originals go to `ARCHIVE/` or `_processed/`.
- Every action appended to `LOGS/watch_actions.jsonl` (time, rule, action, src, dst, ok, error).
- `drop_watcher.py --undo <n>` reverses the last n move/rename actions from that log.
- Errors move the file to `ERROR/` with a `.error.txt` beside it; watcher keeps running.
- Remembers processed files by hash in `_state/seen.json` so restarts don't redo work.

### Example `watch_rules.yaml`

```yaml
settle_seconds: 20
rules:
  - name: youtube channel dump
    match: "channel_*.md"
    actions:
      - pipeline: YouTubeChannelRefinery
  - name: youtube playlist dump
    match: "playlist_*.md"
    actions:
      - pipeline: YouTubeChannelRefinery
  - name: pdfs to papers
    match: "*.pdf"
    actions:
      - move: "D:/Inbox/Papers/{yyyy}-{mm}/"
```

---

## 2. Prompt Box — `tools/prompt_box/`

Small always-available window for talking to the pipeline without editing files.

- `PROMPT_BOX.bat` → opens a local page (FastAPI + one HTML file, port 8790) or a Tkinter window.
- Fields:
  - **Target**: file or folder picker (drag-drop supported)
  - **Profile**: dropdown from `PROMPTS/profiles/*.md` (christian, conspiracy, science, general…)
  - **Prompt**: free text box ("pull every scholar he cites and when")
  - **Engine**: `auto` | `nas-nlp` | `ollama` | `api`
  - **Mode**: `preview` (show result) | `write yaml` | `save as new prompt`
- "Save as new prompt" writes the text to `PROMPTS/profiles/<name>.md` so a good one-off becomes reusable.
- History of prompts + results kept in `LOGS/prompt_box.jsonl`.

---

## 3. Workflow packet — `workflows/YouTubeChannelRefinery/`

Standard packet folders (`INPUT OUTPUT REVIEW ARCHIVE ERROR CONFIG PREFS PROMPTS SCRIPTS LOGS`)
plus `RUN_PIPELINE.bat`, `RUN_THIS_STAGE.bat`, `TROUBLESHOOT.bat`.

### Stage 1 — Split (no AI)
- One `.md` per video.
- Folder: `<vault_root>/YouTube/<Channel>/`
- File name: `<Channel> - Chapter 001 - <Video Title>.md`
  (3-digit, zero-padded, in channel order; titles sanitized for Windows/Obsidian).
- Videos with no transcript still get a file, tagged `status: no_transcript`.
- Writes `<Channel> - 000 Index.md` (Obsidian `[[wikilinks]]` to every chapter).
- Original combined file → `ARCHIVE/`.

### Stage 2 — Clean (no AI, optional)
- Remove `[music]`, `[applause]`, repeated filler (`uh`, `um`) per `PREFS`.
- Break the single paragraph into ~150–250 word paragraphs at sentence boundaries.
- Keep the raw transcript in a collapsed callout so nothing is lost:
  `> [!quote]- Raw transcript`

### Stage 3 — NLP baseline extraction → YAML front-matter
Run per chapter, chunked (transcripts exceed model limits). Uses the NAS NLP server
(`X:\05_MODELS\_NAS_NLP_SERVER\nas_nlp.py`, `http://192.168.2.50:8765`) first.

| field | engine |
|---|---|
| `people`, `places`, `organizations` | NAS `/ner` (dedupe, count mentions) |
| `themes` | NAS `/zeroshot` against the profile's theme list |
| `scripture_refs` | regex (book chapter:verse), no model |
| `dates_mentioned` | regex + `dateparser` |
| `events` / `timeline` | LLM step (Ollama → API fallback) |
| `summary` | LLM step (NAS `/summarize` for short, LLM for long) |
| `key_claims` | LLM step |
| `guests` / `host` | title parse (`- Gary Habermas with @Real Seekers`) + NER |

### Stage 4 — Validate
- YAML must parse and match `schemas/youtube_chapter.schema.json`.
- Empty or low-confidence fields → note goes to `REVIEW/`, not the vault.

### Stage 5 — Route
- Write/replace only the YAML block and the generated sections; never overwrite hand edits
  below a `<!-- manual -->` marker.

### Target note format

```markdown
---
type: youtube_chapter
channel: Gary Habermas
chapter: 12
title: "…"
video_id: abc123
url: https://www.youtube.com/watch?v=abc123
transcript_language: English (auto-generated)
status: extracted          # split | cleaned | extracted | reviewed | no_transcript
profile: christian
people: [Gary Habermas, Sean McDowell]
places: [Jerusalem, Corinth]
organizations: [Liberty University]
themes: [resurrection, early creeds, minimal facts]
scripture_refs: ["1 Corinthians 15:3-7"]
events:
  - {when: "c. AD 30-33", what: "Crucifixion", source_quote: "…"}
key_claims: ["…"]
summary: "…"
extracted_by: {ner: nas-nlp/bert-base-NER, themes: nas-nlp/deberta-zeroshot, llm: ollama/llama3.2}
extracted_at: 2026-09-15
---

# Chapter 012 — <title>

> [!summary]- Summary
> …

> [!list]- Timeline
> …

## Transcript
…
```

---

## 4. Profiles (the "different kinds of YouTube" layer)

`workflows/YouTubeChannelRefinery/PROMPTS/profiles/`

- `general.md` — baseline fields only
- `christian.md` — adds `scripture_refs`, `doctrines`, `apologetic_arguments`, `scholars_cited`
- `conspiracy.md` — adds `claims`, `claimed_evidence`, `named_sources`, `verifiability`, `counterclaims`
- `science.md` — adds `studies_cited`, `quantities`, `hypotheses`

Each profile = YAML header (`themes:` list for zero-shot, `extra_fields:`) + an LLM prompt body.
`PREFS/preferences.json` sets the default profile; the Prompt Box or `--profile` overrides.

---

## 5. Engine routing ("if NLP can't, call the API")

Reuse `engines/pipeline/llm_hub.py` (already has ollama + claude backends). Add:

```text
auto = NAS NLP (fast, local)
     → Ollama on NAS/desktop (reasoning steps)
     → API (DeepSeek / Claude / OpenAI) only when:
         - local output fails schema validation twice, or
         - profile step marked `needs: api`, or
         - user picks `api` in the Prompt Box
```

- API keys from environment only, never in repo.
- Log cost/tokens per chapter to `LOGS/api_usage.jsonl`; stop at `PREFS.api_budget_usd`.

---

## 6. Config the user fills in

`CONFIG/config.json`

```json
{
  "vault_root": "O:/<TBD Obsidian folder>",
  "watch_folder": "D:/GitHub/Research-Acquisition/yt-bulk-subtitles-downloader/subtitles",
  "nas_nlp_url": "http://192.168.2.50:8765",
  "ollama_url": "http://192.168.2.50:11434",
  "default_profile": "christian",
  "chapter_prefix": "Chapter",
  "dry_run": false
}
```

---

## 7. Acceptance tests

1. Drop the Gary Habermas file into the watch folder → 359 chapter notes + index appear, original archived.
2. Re-dropping the same file does nothing (hash seen).
3. `--dry-run` prints the plan, touches nothing.
4. `--undo 1` restores the last move.
5. Chapter 1 has valid YAML with non-empty `people` and `themes`.
6. Kill the NAS NLP server mid-run → affected chapters land in `REVIEW/` with a reason; the run completes.
7. Prompt Box: pick chapter 5, type a prompt, preview works; "save as new prompt" creates a profile file.
8. `WATCH.bat` copied to an unrelated folder works with only `watch_rules.yaml` beside it.

## Build order
1. Splitter stage (reuse existing parser) + naming
2. Portable watcher
3. NLP extraction with NAS server + YAML schema
4. Profiles + LLM/API fallback
5. Prompt Box
