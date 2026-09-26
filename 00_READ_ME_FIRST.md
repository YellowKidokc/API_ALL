# API 3: every pipeline script in one place

Local copy at `D:\GitHub\pipeline-workflows\API\API 3` (copied 2026-09-25 from the NAS folder `Desktop\Folders\___Pipeline_Done_New\ONE_MENU_SOURCES`).

Gathered 2026-09-24 for Codex. These are **copies**. The originals were not moved or changed.
Only code and config were copied (.py .bat .ps1 .json .md .yaml .toml, requirements, one .exe).
Data, inbox/outbox, logs, records, venvs, outputs, git and old backups were left out.

**The task for Codex is in `CODEX_PROMPT_ONE_MENU.md` in this folder.**

## Where each folder came from

| Folder here | Original location (the live one to edit) | Files |
|---|---|---|
| `01_YOUTUBE\yt-transcript-downloader_ROOT` | `D:\GitHub\Research-Acquisition\yt-transcript-downloader` (top level only) | 23 |
| `01_YOUTUBE\Python Clean Library` | `...\yt-transcript-downloader\Python Clean Library` | 5 |
| `01_YOUTUBE\deepseek-home` | `...\yt-transcript-downloader\pipeline-workflows\deepseek-home` (CKG argument indexing + lenses) | 26 |
| `01_YOUTUBE\YT-Transcript-GUI` | `...\yt-transcript-downloader\YT-Transcript` | 3 |
| `01_YOUTUBE\youtube-transcript-ytdlp` | `D:\GitHub\Research-Acquisition\youtube-transcript-ytdlp` (older yt-dlp scraper + watch downloader) | 9 |
| `02_CKG\front_CKG` | `\\192.168.2.50\h_hp\Desktop\APIs\APIs\CKG` (top-level .bat only) | 5 |
| `02_CKG\backside_CKG` | `\\192.168.2.50\h_hp\Desktop\APIs\APIs\_BACKSIDE\CKG` | 19 |
| `02_CKG\backside_workbench` | `...\APIs\APIs\_BACKSIDE\workbench` | 4 |
| `02_CKG\backside_CONFIG` / `_TEMPLATES` / `_TESTS` | `...\APIs\APIs\_BACKSIDE\CONFIG`, `\TEMPLATES`, `\TESTS` | 12 |
| `02_CKG\backside_ROOT` | `...\APIs\APIs\_BACKSIDE\run.py` + MIGRATION_RECEIPT.json | 2 |
| `03_EVIDENCE\front_EVIDENCE` | `\\192.168.2.50\h_hp\Desktop\Folders\___Pipeline_Done_New\One page paper API\EVIDENCE` (the 12 numbered .bat + helpers) | 21 |
| `03_EVIDENCE\backside_SCRIPTS` | `...\APIs\APIs\_BACKSIDE\EVIDENCE\SCRIPTS` (real code; the front SCRIPTS\*.py are wrappers that exec these) | 40 |
| `04_PAPER_GRADER\Academic_paper-proof-grader_Jul` | `\\192.168.2.50\h_hp\Desktop\Folders\Academic Paper Grading\paper-proof-grader`, the **only complete grader code** (pipeline.py, chi_qi_v5_metric_engine.py, nlp_deep_runner.py ...) | 10 |
| `04_PAPER_GRADER\API_DEEP_PAPER_GRADER_prompts` | `...\APIs\APIs\API_DEEP\PAPER_GRADER` (prompt + metric registry; no runner) | 4 |
| `04_PAPER_GRADER\Paper-Grader-NLP-API-03-Axiom` | `D:\GitHub\Paper-Grader-NLP-API-03-Axiom` (plans, schema, Docker; code is a stub) | 16 |
| `04_PAPER_GRADER\atoms_station_paper_grader` | `D:\GitHub\Faith-through-physics-atoms\stations\paper_grader` | 1 |
| `05_API_DEEP_STATIONS` | `...\APIs\APIs\API_DEEP`: ATOMS, AXIOM_NODES (runnable); FRUITS grading station; COHERENCE_SCORE, LEAN4, MASTER_EQUATION, STORIES (PROMPT.md only) | 35 |
| `06_LEAN\LEAN_ATOM_EXTRACTOR` | `...\APIs\APIs\LEAN_ATOM_EXTRACTOR` (exports\ data left out) | ~45 |
| `06_LEAN\front_LEAN4` | `...\APIs\APIs\LEAN4` (.bat only) | 2 |
| `07_PIPELINE_WORKFLOWS_API` | `...\yt-transcript-downloader\pipeline-workflows\API`: EvidenceChainIntake, PaperGrading packet, TikTokPrep, YouTubeChannelRefinery specs | 59 |
| `08_NEW_STATION_SPECS` | NEW specs written 2026-09-24: Story V2, Master-equation analog V2 | 2 |

**Paths moved during gathering (2026-09-24 ~20:00):** `___Pipeline_Done_New` is now under `Desktop\Folders\`, and
`Desktop\APIs\APIs\API_DEEP` + `\CKG` are gone from that spot (a copy exists at `Desktop\Folders\APIs\APIs\API_DEEP`;
a new empty skeleton is at `Desktop\APIs\MAIN`). Confirm with David where the live code now lives before editing.

## Not gathered (duplicates or older)
- `\\192.168.2.50\h_hp\Desktop\Folders\paper-proof-grader`: 128 files, last changed May 2026, older than the July grader.
- The many `pipeline-workflows` copies in `D:\GitHub\Canonizationv1`, `D:\GitHub\pipebad`, `D:\GitHub\pipeline-workflows` and the `workflows\New Folder` tree: duplicates of the templates above.
- `...\pipeline-workflows\engines\*` (P01-P07 recommenders, writing-analyzer), `Codex-Powershell_GUI`, `subtitles\PORTABLE_TTS`: not part of paper/CKG/YouTube processing. Ask David if they belong in the menu.

## Known facts for the menu (checked 2026-09-24)
- DeepSeek key comes from env `DEEPSEEK_API_KEY`. The YouTube scripts use the system `python` (the repo venv lacks `openai`).
- CKG: `run_ckg.py --root <front CKG> --workers 30`; the runner itself asks ALL or a number. Its START_HERE says Grader, Fruits and series synthesis are **not connected** to CKG yet.
- EVIDENCE `turbo_pipeline_runner.py` has `--workers --provider --model --timeout --continuous --root` and **no `--limit`**.
- YouTube `index_video.py` and `lens_pass.py` already take `--limit --workers --force`; `lens_pass.py --ask "<text>"` is the free-text "look at this" option.
