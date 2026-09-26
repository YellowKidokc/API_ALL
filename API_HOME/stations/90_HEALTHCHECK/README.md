# 90_HEALTHCHECK

Every station, every path key, every API key; checks each declared option against the script's real --help.

- Script: `90_healthcheck.py` (run it through `ONE_MENU.bat 90`)
- Works on: none
- Menu options it accepts: none
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

This station makes no API calls.

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/90_HEALTHCHECK/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
