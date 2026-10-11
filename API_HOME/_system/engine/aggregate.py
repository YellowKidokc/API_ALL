"""Assemble every station's JSON for one item (video or paper) into one document, in order.

The order is a procedure in config/assembly.json, e.g. for a video:
  08_YT_SUMMARY -> 09_YT_DEEP -> 44_TAGGER -> 40_ANALYTICAL_ARMS ...
It is smart about what is there: for each station it takes the latest successful run,
skips stations that never ran (and lists them as missing), and appends any station
that ran but is not in the procedure at the end, so nothing is silently dropped.

Output: <item>/03_REPORT/aggregate.json and aggregate.md
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .items import Item
from .paths import inside
from .station import latest_run


def procedures() -> dict[str, list[str]]:
    return json.loads(inside("config", "assembly.json").read_text(encoding="utf-8"))


def _ran(item: Item) -> list[str]:
    runs = item.folder / "02_RUNS"
    return sorted(p.name for p in runs.iterdir() if p.is_dir()) if runs.is_dir() else []


def assemble(item: Item, procedure: str | None = None) -> dict[str, Any]:
    procs = procedures()
    name = procedure or item.kind
    order = procs.get(name) or procs.get("default", [])
    ran = _ran(item)
    sections, missing, failed = [], [], []
    for label in order + [x for x in ran if x not in order]:
        run = latest_run(item, label)
        if run is None:
            (failed if label in ran else missing).append(label)
            continue
        data_path = run / f"{label}.json"
        md_path = run / f"{label}.md"
        receipt = json.loads((run / f"{label}.run.json").read_text(encoding="utf-8"))
        sections.append({
            "station": label, "run": str(run.relative_to(item.folder)), "in_procedure": label in order,
            "model": receipt.get("model"), "prompt_version": receipt.get("prompt_version"),
            "focus_hash": receipt.get("focus_hash"), "tokens": receipt.get("tokens"),
            "goal_ids": sorted({c.get("goal_id") for c in receipt.get("calls", []) if c.get("goal_id")}),
            "data": json.loads(data_path.read_text(encoding="utf-8")) if data_path.exists() else None,
            "markdown": md_path.read_text(encoding="utf-8") if md_path.exists() else None,
        })
    meta = item.meta
    return {"item": {"id": item.id, "kind": item.kind, "title": item.title, "source_hash": item.source_hash,
                     "channel": meta.get("channel"), "series": meta.get("series"), "url": meta.get("url")},
            "procedure": name, "order": order, "assembled_at": datetime.now(timezone.utc).isoformat(),
            "sections": sections, "missing": missing, "failed_latest": failed}


def to_markdown(doc: dict[str, Any]) -> str:
    item = doc["item"]
    lines = [f"# {item['title']}", "", f"*{item['kind']} `{item['id']}` · procedure `{doc['procedure']}` · "
             f"assembled {doc['assembled_at'][:19]}Z*", ""]
    if item.get("url"):
        lines += [f"Source: {item['url']}", ""]
    for section in doc["sections"]:
        lines += [f"## {section['station']}", "",
                  f"*goals {', '.join(section['goal_ids']) or 'local (no API)'} · model {section['model']} · "
                  f"run {section['run']}*", ""]
        if section["markdown"]:
            body = section["markdown"].strip()
            lines += [body.split("\n", 1)[1].strip() if body.startswith("# ") and "\n" in body else body, ""]
        else:
            lines += ["```json", json.dumps(section["data"], indent=2, ensure_ascii=False)[:6000], "```", ""]
    if doc["missing"]:
        lines += ["## Not run yet", "", *[f"- {m}" for m in doc["missing"]], ""]
    if doc["failed_latest"]:
        lines += ["## Ran but no successful run on record", "", *[f"- {m}" for m in doc["failed_latest"]], ""]
    return "\n".join(lines)


def write(item: Item, procedure: str | None = None) -> tuple[Path, Path]:
    doc = assemble(item, procedure)
    folder = item.folder / "03_REPORT"
    folder.mkdir(parents=True, exist_ok=True)
    json_path, md_path = folder / "aggregate.json", folder / "aggregate.md"
    json_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(to_markdown(doc), encoding="utf-8")
    return json_path, md_path
