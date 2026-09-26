# 10_CKG_THEOLOGY

Theology triage after the CKG index: 17 probes (CLEAN / NOTE / FLAG / CLAIM / ??), rules enforced in code, argument layer for the claim graph, YouTube platform notes.

- Script: `10_ckg_theology.py` (`ONE_MENU.bat 10`, or picked automatically: menu question "What kind of channel is this?")
- Works on: videos
- Menu options: limit, workers, provider, model, focus, redo, channel
- Standing focus: `FOCUS.md`

## API goals

| id | title | asks for |
|---|---|---|
| `API-10.1` | THEOLOGY_TRIAGE | 17-probe verdicts + expansions, collapse question, platform notes, argument layer (claims, premises, hidden premises, edges, tests, win condition) |

## Rules (engine/triage.py, enforced in code)

- Scale: CLEAN · NOTE · FLAG · CLAIM · ??. Default CLEAN; anything else needs a timestamp or it becomes NOTE.
- At most three FLAGs. Warrant (2), Doctrine tier (3) and Opponent (9) win a slot first, then severity.
- Rows 16 and 17 never compete for a slot; CLAIMs never count; a hit on 17 is always CLAIM.
- Rows 5 and 6 (church history) are leads to verify: never CLAIM.
- Row 15 reads comments saved beside the transcript (`<transcript>.comments.json` / `.info.json`, or `--fetch-comments` with yt-dlp); none acquired = ??.
- Row 13: the collapse question is always written; FLAG only when the speaker steers around it.
- The 11 platform probes (`PLATFORM_PROBES.md`) are notes only.
- CLAIM rows are added to the argument layer (claims RC##) for the claim graph.

Edit the probes in `RUBRIC.md` and `PLATFORM_PROBES.md`; the output is the `youtube_deep_analysis_v1` document.

## Outputs

`02_RUNS/10_CKG_THEOLOGY/<date>/`: .json, .md, .html, .xlsx (one sheet per part), .run.json, calls/, steps.log.
