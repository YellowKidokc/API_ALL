# 41_STORY

Hook / sequence / coherence per paper -> series pass -> gated memorable lines (STORY_STATION_V2).

- Script: `41_story.py` (run it through `ONE_MENU.bat 41`)
- Works on: papers
- Menu options it accepts: limit, workers, provider, model, focus, redo
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

## API goals

| id | title | asks for |
|---|---|---|
| `API-41.1` | STORY_PAPER_PASS | hook, paragraph roles, through-line, drift, landing, verdict |
| `API-41.2` | STORY_SERIES_PASS | series through-line, handoffs, repeats, missing beats |
| `API-41.3` | STORY_MEMORABLE_LINES | one memorable line per paragraph (only when coherent) |

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/41_STORY/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
