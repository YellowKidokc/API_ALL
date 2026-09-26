# 11_CKG_PHYSICS

Physics mirror pass after the CKG index: which physics process a theological event mirrors (or the reverse), stage by stage, in order, and whether it is identity, structural isomorphism or only analogy (rules enforced in code).

- Script: `11_ckg_physics.py` (`ONE_MENU.bat 11`, or picked automatically: menu question "What kind of channel is this?")
- Works on: both
- Menu options: limit, workers, provider, model, focus, redo, channel
- Standing focus: `FOCUS.md`

## API goals

| id | title | asks for |
|---|---|---|
| `API-11.1` | PHYSICS_MIRROR | mirrors between theological events and physics processes: stages in order, direction, level (identity / structural / analogy / none), transferring prediction, breaks, law axis |

## Rules (engine/mirror.py, enforced in code)

- A stage counts only when it is matched AND cites a timestamp or quote.
- STRUCTURAL needs 3+ counted stages, the same order (directional = yes) and a prediction that transfers; otherwise ANALOGY.
- IDENTITY also needs every stage to be a direct match.
- The report shows the level claimed and the level earned, and why.

## Outputs

`02_RUNS/11_CKG_PHYSICS/<date>/`: .json, .md, .html, .xlsx (one sheet per part), .run.json, calls/, steps.log.
