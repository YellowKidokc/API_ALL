# 40_ANALYTICAL_ARMS

Fruits (flagship) + master equation x2 + axiom nodes + coherence, always together (ANALYTICAL_ARMS_V1).

- Script: `40_analytical_arms.py` (run it through `ONE_MENU.bat 40`)
- Works on: papers
- Menu options it accepts: limit, workers, provider, model, focus, redo, channel
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

## API goals

| id | title | asks for |
|---|---|---|
| `API-40.1` | FRUITS_SENTENCES | -2..+2 per fruit for every sentence in an output range, whole paper each call |
| `API-40.2` | FRUITS_VERDICT | rubric v0.3.0 gated verdict citing the curve spikes and lexicon gap |
| `API-40.3` | MASTER_EQUATION_ANALOG | what plays the role of the master equation; product test; 10-slot map (run twice) |
| `API-40.4` | AXIOM_NODES | engaged axiom nodes with alignment, exact quote, confidence |
| `API-40.5` | COHERENCE | 4 coherence dimensions, contradictions, tensions, missing definitions |

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/40_ANALYTICAL_ARMS/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
