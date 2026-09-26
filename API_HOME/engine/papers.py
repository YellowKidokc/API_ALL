from __future__ import annotations
import json,re,shutil
from datetime import datetime,timezone
from pathlib import Path
from .output import sha256_file
from .paths import external,inside
from .tagger import tag_item

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+","-",text.lower()).strip("-")[:80] or "untitled"

def create(source: Path, *, title: str|None=None, paper_id: str|None=None, series: str="") -> Path:
    source=source.expanduser().resolve()
    if not source.is_file(): raise FileNotFoundError(source)
    title=title or source.stem; digest=sha256_file(source)
    paper_id=paper_id or digest[:12].upper(); destination=external("papers_root")/f"{paper_id}_{slugify(title)}"
    if destination.exists(): raise FileExistsError(f"Paper folder already exists: {destination}")
    shutil.copytree(inside("templates","PAPER_FOLDER"),destination)
    copied=destination/"00_SOURCE"/source.name; shutil.copy2(source,copied)
    copied.chmod(0o444); (destination/"00_SOURCE"/"sha256.txt").write_text(f"{digest}  {source.name}\n",encoding="utf-8")
    paper={"id":paper_id,"title":title,"series":series,"status":"new","source_hash":digest,
           "source_file":source.name,"created_at":datetime.now(timezone.utc).isoformat(),"stations_run":[],"headline_scores":{},"tags":{}}
    (destination/"paper.json").write_text(json.dumps(paper,indent=2),encoding="utf-8")
    # Tagging is automatic when a catalog database is configured; creation remains
    # usable offline when it is intentionally blank.
    try:
        if external("catalog_db", required=False) != Path():
            values=tag_item(paper_id,"paper",destination,source.read_text(encoding="utf-8",errors="replace"))
            paper["tags"]={x["tag"]:x for x in values}
            (destination/"paper.json").write_text(json.dumps(paper,indent=2),encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    return destination

def discover(items:list[str], limit:int|None=None)->list[Path]:
    result=[]
    for item in items:
        p=Path(item).expanduser()
        if p.is_dir() and (p/"paper.json").is_file(): result.append(p.resolve())
        elif p.is_file(): result.append(p.resolve())
    if not items:
        root=external("papers_root"); result=sorted(p.parent for p in root.glob("*/paper.json"))
    return result[:limit] if limit is not None else result
