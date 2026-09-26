# 47_NEW_PAPER

Create the per-paper working folder from templates/PAPER_FOLDER (then tags it).

- Script: `47_new_paper.py` (run it through `ONE_MENU.bat 47`)
- Works on: none
- Menu options it accepts: none
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

This station makes no API calls.

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/47_NEW_PAPER/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
