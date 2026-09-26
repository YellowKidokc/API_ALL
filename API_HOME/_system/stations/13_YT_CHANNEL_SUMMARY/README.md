# 13_YT_CHANNEL_SUMMARY

The channel summary folder: per video a three-sentence summary, 2-3 keywords and one value per line of
`COLUMNS.md`, in one DeepSeek call per video (30+ at once).

- Script: `13_yt_channel_summary.py` (`ONE_MENU.bat 13 --channel "Gary Habermas"`)
- Works on: videos
- Menu options it accepts: limit, workers, provider, model, focus, redo, channel
- Columns: `COLUMNS.md`, one line each, `column name | what to put in it` (placeholder columns until David's list)

## API goals

| id | title | asks for |
|---|---|---|
| `API-13.1` | YT_CHANNEL_SUMMARY | three-sentence summary, 2-3 keywords, one value per COLUMNS.md column |

## Outputs

In `yt_summary/<Channel>/`: one summary note per video (`<transcript note name> (summary).md`, linked to the transcript note),
`_rows/<video id>.json`, and `<Channel> - summary.xlsx | .tsv | .md`, rebuilt after every video, so an interrupted
run keeps every finished row. The keywords also go into the transcript note's front matter. The usual dated run
folder with receipt, calls and steps.log is written per item as well.
