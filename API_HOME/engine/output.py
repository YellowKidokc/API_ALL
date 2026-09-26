from __future__ import annotations
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""): h.update(block)
    return h.hexdigest()

def dated_run_dir(paper: Path, label: str) -> Path:
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    out=paper/"02_RUNS"/label/stamp; out.mkdir(parents=True, exist_ok=False); return out

def write_bundle(out: Path, label: str, data: Any, html: str, receipt: dict[str, Any], rows=None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out/f"{label}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (out/f"{label}.html").write_text(html, encoding="utf-8")
    (out/f"{label}.run.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    import importlib.util
    if importlib.util.find_spec("openpyxl"):
        from openpyxl import Workbook
        wb=Workbook(); ws=wb.active; ws.title=label[:31]
        records=rows if rows is not None else (data if isinstance(data,list) else [data])
        if records and isinstance(records[0],dict):
            headers=list(records[0]); ws.append(headers)
            for row in records: ws.append([json.dumps(row.get(k),ensure_ascii=False) if isinstance(row.get(k),(dict,list)) else row.get(k) for k in headers])
        wb.save(out/f"{label}.xlsx")
    else:
        # A clear fallback at the contracted path makes the missing optional dependency explicit.
        (out/f"{label}.xlsx").write_text("openpyxl is required for native XLSX output\n",encoding="utf-8")
