# 49_GAP_MAP

Overlay a topic synthesis on David's own work: expand / contract / holes, and who said it first (citations).

- Script: `49_gap_map.py` (run it through `ONE_MENU.bat 49`)
- Works on: own
- Menu options it accepts: limit, workers, provider, model, focus, redo, topic
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

## API goals

| id | title | asks for |
|---|---|---|
| `API-49.1` | OWN_CLAIMS | David's claims about the topic, with sentence ids |
| `API-49.2` | COVERAGE_MATCH | does David's work cover this best argument: covered / partial / missing |
| `API-49.3` | PRIOR_ART | who else made this claim in the corpus (quotes) -> cite, or appears original |

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/49_GAP_MAP/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
