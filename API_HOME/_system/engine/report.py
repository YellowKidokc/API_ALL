"""Station 46 REPORT_COMBINE: one item's public report.

  03_REPORT/aggregate.json + aggregate.md   every station's JSON, in the procedure order (engine/aggregate.py)
  03_REPORT/report.html                     the approved statistics matrix fed with live statistics.json,
                                            then every station's public section
  03_REPORT/report.xlsx                     one tab per station (each station's own sheets copied in)
  03_REPORT/<template>.xlsx                 David's Excel templates, filled by tools/excel_fill.py maps
"""
from __future__ import annotations

import html
import json
import statistics
from pathlib import Path

from .aggregate import write as write_aggregate
from .items import Item, all_items
from .paths import inside
from .station import latest_data, latest_run


def families() -> list[dict]:
    catalog = json.loads(inside("config", "metric_catalog.json").read_text(encoding="utf-8"))
    return [{"k": f["k"], "n": f["n"], "src": f["src"]} for f in catalog["families"]]


def academic_percentile(value: float, norm: dict) -> float | None:
    """Piecewise-linear percentile from p25/p50/p75 (and optional p10/p90)."""
    points = sorted((int(k[1:]), v) for k, v in norm.items() if k.startswith("p") and k[1:].isdigit() and isinstance(v, (int, float)))
    if len(points) < 2:
        return None
    if value <= points[0][1]:
        return max(1.0, points[0][0] * value / points[0][1]) if points[0][1] else float(points[0][0])
    for (p1, v1), (p2, v2) in zip(points, points[1:]):
        if v1 <= value <= v2:
            return p1 + (p2 - p1) * ((value - v1) / (v2 - v1) if v2 != v1 else 0)
    return min(99.0, points[-1][0] + (100 - points[-1][0]) / 2)


def corpus_medians(item: Item) -> dict[str, float]:
    values: dict[str, list[float]] = {}
    for other in all_items(item.kind + "s"):
        data = latest_data(other, "42_STATISTICS_WALL")
        for m in (data or {}).get("metrics", []) if isinstance(data, dict) else []:
            values.setdefault(m["name"], []).append(m["value"])
    return {k: statistics.median(v) for k, v in values.items() if len(v) >= 2}


def live_payload(item: Item) -> dict:
    stats_path = item.folder / "03_REPORT" / "statistics.json"
    stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {"metrics": [], "headline": []}
    norms = json.loads(inside("config", "academic_norms.json").read_text(encoding="utf-8"))
    fams = families()
    known = {f["k"] for f in fams}
    for m in stats.get("metrics", []):
        norm = norms.get(m["name"])
        if isinstance(norm, dict):
            m["academic_percentile"] = academic_percentile(m["value"], norm)
        if m["family"] not in known:
            fams.append({"k": m["family"], "n": m["family"].replace("_", " "), "src": "L"})
            known.add(m["family"])
    return {"families": fams, "metrics": stats.get("metrics", []), "headline": stats.get("headline", []),
            "extras": stats.get("extras", {}), "corpus_medians": corpus_medians(item),
            "target_bands": norms.get("target_bands", {}), "has_statistics": stats_path.exists()}


def latest_runs(item: Item):
    runs = item.folder / "02_RUNS"
    for station in sorted(p for p in runs.iterdir() if p.is_dir()) if runs.is_dir() else []:
        run = latest_run(item, station.name)
        if run:
            yield station.name, run


def build(item: Item) -> dict[str, Path]:
    report = item.folder / "03_REPORT"
    report.mkdir(parents=True, exist_ok=True)
    agg_json, agg_md = write_aggregate(item)
    payload = live_payload(item)
    template = inside("templates", "statistics_matrix_live.html").read_text(encoding="utf-8")
    page = template.replace("__LIVE_PAYLOAD__", json.dumps(payload, ensure_ascii=False).replace("</", "<\\/"))
    page = page.replace("LIVE DATA · __LIVE_TITLE__", "LIVE DATA · " + html.escape(item.kind)).replace("__LIVE_TITLE__", html.escape(item.title))
    if not payload["has_statistics"]:
        page = page.replace("<body>", "<body><div style='padding:12px 16px;background:#fff3cd;color:#5c4400'>No statistics yet for this item: "
                            "run station 42 STATISTICS_WALL, then 46 again.</div>", 1)
    sections = []
    for label, run in latest_runs(item):
        section = run / f"{label}.html"
        if section.exists():
            body = section.read_text(encoding="utf-8", errors="replace")
            inner = body.split("<body>", 1)[-1].rsplit("</body>", 1)[0]
            sections.append(f'<section class="panel" data-station="{html.escape(label)}"><div class="panel-head"><div><h2>{html.escape(label)}</h2>'
                            f'<div class="sub">{html.escape(str(run.relative_to(item.folder)))}</div></div></div>{inner}</section>')
    page = page.replace("</body>", "".join(sections) + "</body>", 1)
    html_path = report / "report.html"
    html_path.write_text(page, encoding="utf-8")
    xlsx_path = report / "report.xlsx"
    combined = combine_workbooks(item, xlsx_path)
    return {"report.html": html_path, "report.xlsx": xlsx_path if combined else None, "aggregate.json": agg_json, "aggregate.md": agg_md}


def combine_workbooks(item: Item, target: Path) -> bool:
    try:
        from openpyxl import Workbook, load_workbook
    except ImportError:
        return False
    wb = Workbook()
    wb.remove(wb.active)
    for label, run in latest_runs(item):
        source = run / f"{label}.xlsx"
        if not source.exists():
            continue
        try:
            src = load_workbook(source, read_only=True)
        except Exception:
            continue
        for ws in src.worksheets:
            name = f"{label[:2]}_{ws.title}"[:31]
            out = wb.create_sheet(name)
            for row in ws.iter_rows(values_only=True):
                out.append(list(row))
    stats = item.folder / "03_REPORT" / "statistics.xlsx"
    if stats.exists():
        src = load_workbook(stats, read_only=True)
        for ws in src.worksheets:
            out = wb.create_sheet(f"stats_{ws.title}"[:31])
            for row in ws.iter_rows(values_only=True):
                out.append(list(row))
    if not wb.worksheets:
        wb.create_sheet("README").append(["No station outputs yet"])
    wb.save(target)
    return True
