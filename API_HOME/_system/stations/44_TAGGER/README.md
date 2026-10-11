# 44_TAGGER

20 tags scored 0-10 per paper and video; local pass first, DeepSeek confirms scores of 5+.

- Script: `44_tagger.py` (run it through `ONE_MENU.bat 44`)
- Works on: both
- Menu options it accepts: limit, workers, provider, model, redo, channel
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

## API goals

| id | title | asks for |
|---|---|---|
| `API-44.1` | TAG_CONFIRM | confirm/adjust 0-10 per candidate tag with a quote or timestamp and a reason |

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/44_TAGGER/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
