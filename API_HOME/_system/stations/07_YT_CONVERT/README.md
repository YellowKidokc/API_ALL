# 07_YT_CONVERT

Convert SRT / VTT / JSON transcripts to ytgrab-style .md; originals kept in <Channel>/_originals (local).

- Script: `07_yt_convert.py` (run it through `ONE_MENU.bat 07`)
- Works on: videos
- Menu options it accepts: limit, channel, redo
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

This station makes no API calls.

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/07_YT_CONVERT/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
