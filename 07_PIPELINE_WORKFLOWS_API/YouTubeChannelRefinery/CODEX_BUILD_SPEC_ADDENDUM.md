# ADDENDUM — Reusable packet, completion handoff, Obsidian knowledge layer, synthesis layer

Read after `CODEX_BUILD_SPEC.md`. Where they disagree, this file wins.

## A. Name and shape — reusable for ANY channel/playlist

Packet name: `YouTubeTranscriptBreakdown` (rename the folder; nothing channel-specific in code).

```text
YouTubeTranscriptBreakdown/
  INBOX/                      # drop channel_*.md / playlist_*.md / single-video .md / .srt / .vtt
  OUTBOX/                     # finished notes, grouped by channel
  PROCESSED/                  # originals after success (never deleted)
  REVIEW/                     # low-confidence or failed-validation notes
  ERROR/                      # file + .error.txt
  LOGS/
  STATE/                      # seen hashes, run manifests, resume points
  CONFIG/config.json
  PREFS/preferences.json
  PROMPTS/profiles/*.md
  SCHEMAS/*.schema.json
  SCRIPTS/
    breakdown.py              # single CLI entry: breakdown.py <stage|all> [--input] [--profile] [--dry-run]
    watcher.py                # the portable watcher (same file as tools/drop_watcher)
    health.py
    handlers/                 # one module per input type, auto-registered
      ytbsd_combined_md.py    #   channel_/playlist_ dumps
      single_video_md.py
      subtitle_srt_vtt.py
  START.bat                   # starts the watcher on INBOX (stays running)
  HEALTHCHECK.bat             # python, packages, NAS NLP, Ollama, vault path, disk space, write perms
  LAUNCH.bat                  # menu: 1 start watcher  2 process INBOX once  3 health  4 prompt box  5 open OUTBOX  6 open last report
  PROCESS_CHANNEL_MD.bat      # drag a combined channel/playlist .md onto it
  PROCESS_SUBTITLES.bat       # drag .srt/.vtt files or a folder onto it
  PROCESS_SINGLE_VIDEO.bat
  RESUME_LAST_RUN.bat
  TROUBLESHOOT.bat
  README.md
```

Rules:
- **Adding a new file type = add one handler module + one `PROCESS_<TYPE>.bat`.** No edits elsewhere.
  Handler contract: `detect(path) -> bool`, `split(path) -> list[VideoRecord]`.
- All paths come from `CONFIG/config.json`; bats contain no hard-coded paths except `%~dp0`.
- Every stage is resumable (per-video state in `STATE/<run_id>.json`); a crash restarts where it stopped.

## B. "It's done" — completion handoff

When a run finishes, write ALL of these (next process watches for them):

1. `OUTBOX/<Channel>/_RUN_COMPLETE.json`
   ```json
   {"workflow": "YouTubeTranscriptBreakdown", "run_id": "...", "channel": "Gary Habermas",
    "source": "channel_Gary Habermas - Videos_20260915_153130.md",
    "videos_total": 359, "notes_written": 351, "no_transcript": 8, "review": 12, "errors": 0,
    "stages": ["split","clean","extract","validate","route"], "finished_at": "...",
    "next": "ObsidianKnowledgeLayer"}
   ```
2. A `READY` signal in repo `signals/ready/` using `schemas/signal.schema.json` (existing convention).
3. `OUTBOX/<Channel>/_RUN_REPORT.md` — human summary: counts, top people/themes, what went to REVIEW and why.
4. Optional notify (config flags): Windows toast, and/or POST to the comms hub URL.

Downstream packets start by watching for `_RUN_COMPLETE.json` — never by guessing a folder is finished.
Partial runs write `_RUN_PARTIAL.json` instead.

## C. Obsidian knowledge layer (separate packet: `ObsidianKnowledgeLayer`)

Input = a completed OUTBOX channel folder. Output = vault notes. Vault root TBD by David.

```text
<vault>/YouTube/<Channel>/Chapters/<Channel> - Chapter 001 - <title>.md
<vault>/YouTube/<Channel>/<Channel> - 000 Index.md
<vault>/Entities/People/<Name>.md
<vault>/Entities/Places/<Name>.md
<vault>/Entities/Organizations/<Name>.md
<vault>/Themes/<Theme>.md
<vault>/Timelines/<Channel> Timeline.md
<vault>/Connections/<Corpus A> x <Corpus B>.md
```

- **Entity notes**: YAML (`aliases`, `type`, `first_seen`, `mention_count`, `appears_in: [[...]]`), a short
  "who/what" line, and a Dataview block listing every chapter that mentions them.
- **Theme notes**: definition ("what it means"), how this channel treats it, strongest quotes with
  chapter links, related themes, and a **"Across corpora"** section filled by section D.
- **Alias resolution** before writing (`Habermass` → `Gary Habermas`); keep a `STATE/aliases.yaml` David can edit.
- **Karpathy wiki layer**: feed chapter + entity + theme notes into the existing `olw` workspace
  (`docs/karpathy-wiki-layer.md`, `D:\FAP\wiki-compiler`) so it compiles concept pages. Drafts land in
  `wiki/.drafts` for review — never straight into the vault.
- Never overwrite below `<!-- manual -->`. Regenerate only generated blocks.

## D. Synthesis layer — "go wild" (packet: `CorpusSynthesis`)

Runs only after C is complete. Purpose: find what no single video says.

Stations, each writing notes to `<vault>/Connections/` and ideas to `REVIEW/synthesis/`:

1. **Bridge finder** — embed every chapter chunk (NAS `/embed`); for each pair of corpora (this channel vs.
   existing vault: axioms, Logos papers, other channels) list the top cross-corpus neighbours with the
   linking passage from each side.
2. **Theme drift** — how a speaker's treatment of a theme changes over upload date.
3. **Agreement / tension map** — NAS `/nli` on claim pairs across corpora: `supports`, `contradicts`,
   `same claim different words`. Contradictions are the most valuable output — surface them first.
4. **Citation graph** — scholars/sources cited → who cites whom, most-cited, cited-but-not-in-vault (`GAP` signal).
5. **Timeline merge** — events from all corpora on one timeline with source lineage; flag date conflicts.
6. **Strategic brief** (LLM/API, heavy model) — per run, one `Synthesis Brief.md`:
   - 5 strongest non-obvious connections (with both source quotes)
   - 3 tensions/contradictions worth resolving
   - gaps: what the vault claims that this corpus neither supports nor tests
   - suggested next acquisitions (feed `prior-art-sweep` briefs / YTBSD downloads as `UPSTREAM` signals)
   - candidate article or paper ideas

Guardrails: every connection cites both source spans; confidence scores are triage, not truth;
nothing from D writes into Chapter/Entity notes directly — it goes to `Connections/` + `REVIEW/`.

## E. The full loop

```text
YTBSD download ─▶ INBOX ─▶ YouTubeTranscriptBreakdown ─▶ _RUN_COMPLETE
   ▲                                                         │
   │                                                         ▼
   │                                           ObsidianKnowledgeLayer ─▶ _RUN_COMPLETE
   │                                                         │
   │                                                         ▼
   └──── UPSTREAM signals (fetch this, sweep that) ◀── CorpusSynthesis ─▶ Synthesis Brief
```

## G. Align with OpenIntel (overrides C where they conflict)

Target system: `Z:\00_OPEN_INTEL\OPENINTEL STATER` (`OPENINTEL_CASE_SYSTEM.md`, `STATEMENT_LEDGER_SCHEMA.md`,
`00_SCHEMA_TEMPLATES/`, `00_CASE_TEMPLATES/OPENINTEL_SOURCE_CASE_TEMPLATE/`).

1. **Ledger is canonical, notes are projections.** Extraction writes JSONL/SQLite first
   (`sources`, `statements`, `entities`, `events`, `claims` — columns exactly as `STATEMENT_LEDGER_SCHEMA.md`).
   Obsidian notes (chapter, entity, theme, timeline) are regenerated from the ledger. YAML front-matter in a
   note is a summary copy, never the place a fact is first written (one-fill rule).
2. **One video = one SOURCE_PACKET** under `<Collection>/YouTube/<video folder>/`, using the existing template;
   `collection` = channel, `source_family` = YouTube, `perspective` = speaker.
3. **Spans must be checkable.** Re-grab captions WITH timestamps (.vtt/.srt) and store span as `t=MM:SS`;
   fall back to `L###` line spans (the C317 convention) only when no timed captions exist.
4. **No speaker labels in auto-captions.** Every machine statement gets `ATTR: HIGH/MED/LOW` like C317;
   never derive a claim from a LOW statement automatically.
5. **Machine output enters as `status: CANDIDATE`, `perspective: system extraction`.** NER entities, NLI
   contradictions and LLM claims are candidates for review, never SUPPORTED/CONFIRMED.
6. **Evidence tier ≠ source existence.** A YouTube source packet establishes what was said (per
   `SOURCE_FAMILY_RULES.md`); claims inside it start untiered until corroborated.
7. **One ID scheme.** Use `SRC-/STMT-/CLM-/EVID-/ENT-/EVT-/CONTRA-` with a collection prefix
   (e.g. `STMT-HAB-012-0045`). Do not invent `CT###`- or `EV-`-style IDs.
8. **Domain labels for theology/apologetics corpora:** tag claims `HISTORICAL / THEOLOGICAL / PHILOSOPHICAL /
   EMPIRICAL / ANALOGICAL / OPEN` and link types from `LINK_TYPES.md` (`ANALOGY_TO` is not `SUPPORTS`).

## F. Extra acceptance tests
9. Copy the packet folder to a new drive, edit only `CONFIG/config.json` → `HEALTHCHECK.bat` passes, a run works.
10. Adding `handlers/example_txt.py` + `PROCESS_TXT.bat` makes `.txt` transcripts work with no other edits.
11. A finished run always produces `_RUN_COMPLETE.json` + READY signal + `_RUN_REPORT.md`.
12. Killing the process mid-run then `RESUME_LAST_RUN.bat` finishes without duplicating notes.
