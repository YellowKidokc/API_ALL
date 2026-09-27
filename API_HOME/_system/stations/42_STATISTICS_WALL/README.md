# 42_STATISTICS_WALL

Every academic + Obsidian metric in Python (same numbers every run), with corpus / series percentiles and change since last version.

- Script: `42_statistics_wall.py` (run it through `ONE_MENU.bat 42`)
- Works on: both
- Menu options it accepts: limit, redo, channel
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

This station makes no API calls.

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/42_STATISTICS_WALL/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
