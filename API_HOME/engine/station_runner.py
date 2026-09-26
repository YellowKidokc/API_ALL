"""Shared entry point used by every numbered station wrapper."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from .paths import API_HOME, external

def parser(label: str) -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog=label)
    p.add_argument("items",nargs="*"); p.add_argument("--limit",type=int)
    p.add_argument("--focus",default=""); p.add_argument("--workers",type=int)
    p.add_argument("--provider",choices=("deepseek","openai"),default=None)
    p.add_argument("--model"); p.add_argument("--redo",action="store_true")
    p.add_argument("--dry-run",action="store_true"); return p

def legacy_main(number: str, label: str, path_key: str, relative_script: str) -> int:
    args, passthrough=parser(label).parse_known_args()
    root=external(path_key)
    script=root/relative_script
    if not script.is_file(): print(f"{label}: legacy script not found: {script}",file=sys.stderr); return 2
    cmd=[sys.executable,str(script),*args.items,*passthrough]
    # Forward only flags proven to be supported by this adapter's station metadata.
    meta=json.loads((API_HOME/"stations"/label/"station.json").read_text(encoding="utf-8"))
    accepted=set(meta.get("options",[]))
    for key,value in (("limit",args.limit),("workers",args.workers),("provider",args.provider),("model",args.model)):
        if value is not None and key in accepted: cmd += [f"--{key}",str(value)]
    if args.redo and "redo" in accepted: cmd.append("--force")
    if args.focus and "focus" in accepted: cmd += [meta.get("focus_flag","--focus"),args.focus]
    print("PLAN",json.dumps({"station":label,"command":cmd,"dry_run":args.dry_run},ensure_ascii=False))
    return 0 if args.dry_run else subprocess.run(cmd,cwd=root).returncode
