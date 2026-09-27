# 09_YT_DEEP

Detailed, rigorous layer on top of the base summary (reads 08's output + the whole transcript).

- Script: `09_yt_deep.py` (run it through `ONE_MENU.bat 09`)
- Works on: videos
- Menu options it accepts: limit, workers, provider, model, focus, redo, channel
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

## API goals

| id | title | asks for |
|---|---|---|
| `API-09.1` | YT_DEEP_ANALYSIS | detailed analysis per DETAIL.md, building on the 08 summary |

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/09_YT_DEEP/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
