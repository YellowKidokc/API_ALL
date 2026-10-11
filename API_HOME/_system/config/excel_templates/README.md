# Excel templates

Put one map file here per template (`<name>.json`, format in `tools/excel_fill.py`). Station 46 fills every
map for every item it reports on and writes the result into the item's `03_REPORT/`. Build a template from
the baseline workbooks the stations already write (each station's `.xlsx`, and `03_REPORT/report.xlsx`),
save it under `templates/excel/`, then map its cells here.
