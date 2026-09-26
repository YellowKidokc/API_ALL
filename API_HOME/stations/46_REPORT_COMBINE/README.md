# 46_REPORT_COMBINE

Assemble every station's JSON in procedure order (aggregate.json/.md) and build report.html + report.xlsx.

- Script: `46_report_combine.py` (run it through `ONE_MENU.bat 46`)
- Works on: both
- Menu options it accepts: limit, channel
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

This station makes no API calls.

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/46_REPORT_COMBINE/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
