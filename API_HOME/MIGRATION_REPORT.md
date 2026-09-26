# Path migration report

## Scope and strategy

The gathered directories at repository root are archival source copies. They were not modified. ONE_MENU does not copy their hard-coded paths into the portable tree. Instead, each numbered adapter resolves its legacy source root through `engine/paths.py` and a `config/paths.json` key. New code contains no drive letter, user-home literal, or UNC root.

| Former hard-coded location family | Portable key |
|---|---|
| YouTube downloader, cleaner, indexer, lenses, catalog and watcher roots | `legacy_youtube`, with data at `subtitles` |
| CKG front/back roots | `legacy_ckg` |
| Evidence inbox/outbox/script roots | `legacy_evidence` |
| July grader root | `legacy_grader` |
| Lean repositories/export roots | `legacy_lean`, `lean_root` |
| Raw OpenAI station root | `legacy_openai_stations` |
| NAS metrics/models | `nas_brain` |
| Vault | `vault` |
| Excel Fruits sources | `excel_fruits`, `excel_lexicons` |
| Paper workspaces | `papers_root` |
| Catalog database | `catalog_db` |

`RELOCATE.bat` walks every key, reports FOUND/MISSING, accepts replacements only when interactive, validates entered paths, writes the ignored `paths.json`, and invokes station health checks.

## Legacy CLI inventory verified from gathered documentation/code

- `run_ckg.py`: `--root`, `--workers`; its own item selector is interactive.
- `turbo_pipeline_runner.py`: `--workers`, `--provider`, `--model`, `--timeout`, `--continuous`, `--root`; the adapter adds orchestration-level limit/focus only where supported by migrated deployments.
- `index_video.py` and `lens_pass.py`: `--limit`, `--workers`, `--force`; lenses uses `--ask` for free-text focus.
- Local scripts expose only their actual flags declared in `config/stations.json`; ONE_MENU never forwards undeclared options.

## Known migration boundaries

Legacy programs that still make API calls internally must be upgraded in their configured live roots before they can share `engine/llm.py`; the newly built stations use it directly. Health check reports missing roots rather than substituting a machine-specific path. The unavailable conversion station script is deliberately surfaced as a missing configured legacy script rather than guessed.
