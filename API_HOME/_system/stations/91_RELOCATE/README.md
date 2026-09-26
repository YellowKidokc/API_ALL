# 91_RELOCATE

After moving the folder: find every external path again (auto-search), confirm, save, health check.

- Script: `91_relocate.py` (run it through `ONE_MENU.bat 91`)
- Works on: none
- Menu options it accepts: none
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

This station makes no API calls.

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/91_RELOCATE/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
