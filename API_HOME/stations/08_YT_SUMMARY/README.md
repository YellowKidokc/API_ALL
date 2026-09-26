# 08_YT_SUMMARY

Base layer for a video: the summary questions in QUESTIONS.md, whole transcript in one call.

- Script: `08_yt_summary.py` (run it through `ONE_MENU.bat 08`)
- Works on: videos
- Menu options it accepts: limit, workers, provider, model, focus, redo, channel
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

## API goals

| id | title | asks for |
|---|---|---|
| `API-08.1` | YT_SUMMARY | answers to QUESTIONS.md (base summary) with timestamps |

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/08_YT_SUMMARY/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
