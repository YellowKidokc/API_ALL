from __future__ import annotations
import json,os,sys
from pathlib import Path
if __package__ in (None,''):
 sys.path.insert(0,str(Path(__file__).resolve().parents[1])); from engine.paths import CONFIG_DIR
else: from .paths import CONFIG_DIR

def main()->int:
 example=json.loads((CONFIG_DIR/'paths.example.json').read_text(encoding='utf-8')); target=CONFIG_DIR/'paths.json'
 current=json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
 for key in example:
  old=str(current.get(key,example[key])).strip(); found=bool(old) and Path(os.path.expandvars(old)).expanduser().exists()
  print(f"{key}: {'FOUND' if found else 'MISSING'} {old}")
  if not found and sys.stdin.isatty():
   value=input(f"New path for {key} [Enter keeps current]: ").strip()
   if value:
    candidate=Path(os.path.expandvars(value)).expanduser()
    if not candidate.exists(): print(f"Not found; keeping {old}"); value=old
    current[key]=value
  else: current.setdefault(key,old)
 target.write_text(json.dumps(current,indent=2)+'\n',encoding='utf-8')
 from engine.health import main as health
 return health()
if __name__=='__main__': raise SystemExit(main())
