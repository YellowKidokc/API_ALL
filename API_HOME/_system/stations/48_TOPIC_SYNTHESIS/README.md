# 48_TOPIC_SYNTHESIS

Bridge layer: best arguments for a topic across all papers, videos and evidence, cross-referenced, with citations; multi-page report.

- Script: `48_topic_synthesis.py` (run it through `ONE_MENU.bat 48`)
- Works on: both
- Menu options it accepts: limit, workers, provider, model, focus, redo, topic
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

## API goals

| id | title | asks for |
|---|---|---|
| `API-48.1` | EXTRACT_TOPIC_ARGUMENTS | every argument about the topic in one item: steps, kind, who holds it, quote/timestamp, strength, objections |
| `API-48.2` | SYNTHESIZE_ARGUMENT | strongest form of one cross-referenced argument, lineage, objections and replies |
| `API-48.3` | SYNTHESIS_OVERVIEW | ranked overview report across all synthesized arguments |

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/48_TOPIC_SYNTHESIS/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
