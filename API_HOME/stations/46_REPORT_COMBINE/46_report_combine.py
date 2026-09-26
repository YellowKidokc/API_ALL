"""46_REPORT_COMBINE: aggregate every station's JSON in procedure order, build report.html (live matrix) and
report.xlsx, and fill every Excel template map in config/excel_templates/. Local, no API."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.output import page  # noqa: E402
from engine.paths import inside  # noqa: E402
from engine.report import build  # noqa: E402
from engine.station import ItemResult, Station  # noqa: E402


def process(ctx):
    ctx.step("assembling every station's JSON in procedure order")
    paths = build(ctx.item)
    for name, path in paths.items():
        ctx.step(f"wrote {name}: {path if path else 'skipped (openpyxl missing)'}")
    filled = []
    maps = sorted(inside("config", "excel_templates").glob("*.json"))
    if maps:
        sys.path.insert(0, str(inside("tools")))
        from excel_fill import fill
        for spec in maps:
            try:
                out, missing = fill(ctx.item, spec.stem)
                filled.append({"template": spec.stem, "output": str(out), "empty_cells": missing})
                ctx.step(f"excel template {spec.stem}: {out.name} ({len(missing)} empty cell(s))")
            except Exception as exc:
                ctx.warnings.append(f"excel template {spec.stem}: {exc}")
    data = {k: str(v) if v else None for k, v in paths.items()}
    data["excel_templates"] = filled
    return ItemResult(data, page("Report", f"<p>Report: {paths['report.html']}</p>"), {"outputs": [{"file": k, "path": v} for k, v in data.items() if k != "excel_templates"]})


if __name__ == "__main__":
    station = Station("46_REPORT_COMBINE", kind="both")
    station.per_item = False
    raise SystemExit(station.run(process))
