# ONE_MENU

Portable orchestration for the gathered API pipelines. `ONE_MENU.bat` is the only operational front door; `RELOCATE.bat` is the one-time path repair utility after a move.

## First use

1. Copy `config/paths.example.json` to the ignored `config/paths.json` (or run `RELOCATE.bat`) and enter external locations. Blank entries are reported, never guessed.
2. Set `DEEPSEEK_API_KEY` and/or `OPENAI_API_KEY` in the environment. Never put keys in configuration files.
3. Run `ONE_MENU.bat`, or use it non-interactively:

```bat
ONE_MENU.bat 30 --limit 1 --focus "entropy"
ONE_MENU.bat 47 --item paper.md
ONE_MENU.bat 40 --item PAPER_ID_slug --limit 1
ONE_MENU.bat Y --limit 1
ONE_MENU.bat find resurrection --min 5
```

On macOS/Linux, the equivalent is `python API_HOME/engine/menu.py ...`.

## Portability and outputs

All internal paths derive from `engine/paths.py`. Every external root is a named entry in `config/paths.json`; environment variable `ONE_MENU_<KEY>` can override one. Numbered adapters invoke legacy programs only through these roots. New paper runs write dated bundles under `<paper>/02_RUNS/NN_STATION/`, never overwriting an earlier run. Station 46 builds `03_REPORT/report.html` and `report.xlsx`.

Every station has `PROMPT.md`, editable `FOCUS.md`, `station.json`, `README.md`, and a matching `NN_name.py`. Adding a station requires a folder and registry entry, never another batch file.

## Concurrency and recovery

The default call ceiling is 30. `engine/llm.py` owns API access, retry/backoff, the process-wide adaptive limiter, and token receipts. A routine executes stations in dependency order so separate station pools cannot multiply the ceiling. Each station parallelizes independent items/calls and saves an item immediately. Retry keys are defined by source, prompt, model, and focus hashes in receipts.

## Intentionally unresolved owner decisions

ONE_MENU does not silently decide these:

- YouTube canonical download root: `subtitles` or the former channel folder.
- Which 12 real metrics become the statistics headline strip.
- Canonical axiom registry.
- Fruits scale (`-2..+2` is marked provisional in its plug-in rubric) versus `0..4`.
- Which of the 23 OpenAI raw stations receive permanent individual numbers; they remain grouped at 60.
- Whether YouTube transcripts automatically run analytical arms.

Until David answers, configuration and metadata keep these choices explicit and reversible.
