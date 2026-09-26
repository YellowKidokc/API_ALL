from __future__ import annotations
import json,os,re,sys
from pathlib import Path
from .paths import API_HOME,load_paths

def check()->tuple[int,list[dict]]:
 results=[]; config=json.loads((API_HOME/'config/stations.json').read_text(encoding='utf-8'))
 paths=load_paths()
 for key,value in paths.items():
  results.append({'kind':'path','name':key,'ok':bool(value) and Path(os.path.expandvars(value)).expanduser().exists(),'detail':value or 'not configured'})
 for station in config:
  folder=API_HOME/station['folder']; main=folder/station['script']
  good=folder.is_dir() and main.is_file() and (folder/'FOCUS.md').is_file() and (folder/'station.json').is_file()
  results.append({'kind':'station','name':station['label'],'ok':good,'detail':str(main.relative_to(API_HOME))})
 for env in ('DEEPSEEK_API_KEY','OPENAI_API_KEY'):
  results.append({'kind':'key','name':env,'ok':bool(os.environ.get(env)),'detail':'present' if os.environ.get(env) else 'missing (only needed by its provider)'})
 required_fail=[r for r in results if r['kind']=='station' and not r['ok']]
 return (1 if required_fail else 0),results

def main()->int:
 code,results=check()
 for r in results: print(f"{'OK' if r['ok'] else 'MISSING':7} {r['kind']:7} {r['name']}: {r['detail']}")
 return code
if __name__=='__main__': raise SystemExit(main())
