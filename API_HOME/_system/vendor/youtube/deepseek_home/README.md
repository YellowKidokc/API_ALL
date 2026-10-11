# DeepSeek Home

DeepSeek has no memory between API calls, so this folder is its home base.
Every call sends, in order: HOME → GLOSSARY → STATE → (DEBATE_MAP) → TASK → INPUT.

| File | What it is | Who edits it |
|---|---|---|
| `HOME.md` | Project, behavior rules, rating scales. Rarely changes. | David |
| `GLOSSARY.md` | Settled term meanings. | David |
| `STATE.md` | Current focus and open questions. Keep it short. | David |
| `DEBATE_MAP.md` | Subjects and the exact questions in dispute, with permanent IDs. Every argument is placed on it. | David (add proposed questions by hand) |
| `tasks/*.md` | One file per job with its output template: `chat`, `summary`, `claims`, `index`, `synthesize`. | David |
| `requests/`, `outputs/`, `log.jsonl` | What `home.py` sent and got back, with token counts. | script |

`<!-- comments -->` in the Markdown files are notes for David and are stripped before sending.

## YouTube pipeline

1. **Download** transcripts into `subtitles/<Channel>/`.
2. **Clean** locally (Python, no API): `Python Clean Library\CLEAN_LIBRARY.bat` → `obsidian_transcripts/`.
3. **Index** with DeepSeek: `python index_video.py "..\..\subtitles\<Channel>"` → `obsidian_indexed/<Channel>/`
   - one note per video in CKG argument-first order: overview and counts → subject map →
     argument catalog → open questions → objections and replies → how each argument is built →
     where to investigate → people/places/things → cleaned transcript
   - `<title>.index.json` beside it holds the structured record
   - flags: `--limit N`, `--workers N`, `--force` (redo), `--render-only` (redraw from JSON, no API)
3b. **Lenses** (optional, DeepSeek): `python lens_pass.py <channel dir or file> --lens clips,soft-spots --ask "your own focus"`
   - adds `## Lens · ...` sections to the video note; results in `_API/<title>.lens.json`
   - saved lenses are `lenses/*.md` (`--list`); add a file to add a lens; `_FORMAT.md` is the shared output shape
   - accepts raw `subtitles/` files or cleaned `obsidian_transcripts/` notes; about 9k tokens per lens for a 13-minute video
4. **Catalog** (no API): `python build_catalog.py`
   - `<Channel>/_CHANNEL_OVERVIEW.md`: counts, debates covered, strength, origin, speakers
   - `_DEBATES/<Q-ID>.md`: every argument on one question across all channels (e.g. `Q-JESUS-RESURRECTION`)
   - `catalog.xlsx` and `catalog.sqlite`: Videos, Arguments, Exchanges, Channels, Questions

Cost: roughly 100-150k tokens per hour of video with deepseek-chat.
Everything produced here is an AI proposal (inventory PARTIAL, verification UNRESOLVED) until David reviews it.

## Quick chat

```
python home.py chat "a question"
```

Use the system `python`, since the project venv lacks the `openai` package.
