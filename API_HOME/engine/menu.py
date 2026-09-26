from __future__ import annotations
import argparse,json,os,shlex,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
if __package__ in (None,''):
 sys.path.insert(0,str(Path(__file__).resolve().parents[1])); from engine.paths import API_HOME,ensure_runtime_dirs
else: from .paths import API_HOME,ensure_runtime_dirs

def load(name): return json.loads((API_HOME/'config'/name).read_text(encoding='utf-8'))
def registry(): return {x['number']:x for x in load('stations.json')}
def display(all_items=False):
 rows=sorted(registry().values(),key=lambda x:x['rank']); rows=rows if all_items else rows[:20]
 print('\nONE_MENU — stations\n')
 for x in rows: print(f" {x['number']}  {x['name']:<32} rank {x['rank']}")
 print('\nM = show all · Enter = repeat last run · number(s) or routine letter')
def resolve(tokens):
 routines=load('routines.json'); reg=registry(); out=[]
 for token in tokens:
  key=token.upper()
  nums=routines[key]['stations'] if key in routines else [token.zfill(2) if token.isdigit() else token]
  for n in nums:
   if n not in reg: raise SystemExit(f'Unknown station or routine: {token}')
   if n not in out: out.append(n)
 return out
def estimate(numbers,limit):
 settings=load('settings.json'); count=limit or 1; tokens=count*len(numbers)*settings['estimated_tokens_per_item']; workers=settings['max_concurrent_calls']; seconds=max(1,round(tokens/1500/max(1,workers)))
 return tokens,seconds
def parse(argv=None):
 p=argparse.ArgumentParser(description='One front door for every API pipeline')
 p.add_argument('selection',nargs='*'); p.add_argument('--item',action='append',default=[],help='input item/path forwarded to each selected station'); p.add_argument('--turbo',nargs='?',const='high',choices=('low','normal','high')); p.add_argument('--workers',type=int); p.add_argument('--limit',type=int); p.add_argument('--provider'); p.add_argument('--model'); p.add_argument('--redo',action='store_true'); p.add_argument('--focus',default=''); p.add_argument('--yes',action='store_true'); p.add_argument('--dry-run',action='store_true'); p.add_argument('--min',dest='minimum',type=int,default=5); return p.parse_args(argv)
def search(tag,minimum):
 from engine.tagger import find
 rows=find(tag,minimum)
 for item,kind,name,score,reason,quote,path in rows: print(f'{score:2} {kind:7} {item} | {path}\n   {reason}\n   {quote}')
 print(f'{len(rows)} result(s)'); return 0
def run(argv=None):
 ensure_runtime_dirs(); args=parse(argv)
 if args.selection and args.selection[0].lower()=='find':
  if len(args.selection)<2: raise SystemExit('Usage: ONE_MENU.bat find TAG --min 5')
  return search(' '.join(args.selection[1:]),args.minimum)
 state=API_HOME/'STATE'/'last_run.json'
 if not args.selection and not sys.stdin.isatty(): raise SystemExit('A station number or routine is required in non-interactive mode')
 if not args.selection:
  display(); raw=input('\n1 What to run? ').strip()
  if raw.upper()=='M': display(True); raw=input('\n1 What to run? ').strip()
  if not raw and state.exists(): args.selection=json.loads(state.read_text())['selection']
  else: args.selection=shlex.split(raw)
  args.turbo=input('2 Turbo [low/normal/high, Enter=normal]? ').strip().lower() or None
  amount=input('  How many items [all]? ').strip(); args.limit=int(amount) if amount else None
  args.provider=input('  Provider [deepseek]? ').strip() or 'deepseek'
  args.redo=input('  Redo finished items [N]? ').strip().lower() in ('y','yes')
  args.focus=input('3 Extra focus [0=none]? ').strip(); args.focus='' if args.focus=='0' else args.focus
 numbers=resolve(args.selection); settings=load('settings.json'); workers=args.workers or settings['turbo_presets'].get(args.turbo or 'normal',settings['max_concurrent_calls']); provider=args.provider or settings['default_provider']; model=args.model or settings['models'].get(provider)
 est_tokens,est_seconds=estimate(numbers,args.limit)
 plan={'selection':args.selection,'stations':numbers,'limit':args.limit,'workers':workers,'provider':provider,'model':model,'redo':args.redo,'focus':args.focus,'items':args.item,'estimated_tokens':est_tokens,'estimated_seconds':est_seconds}
 print('\n4 Confirm exact plan\n'+json.dumps(plan,indent=2))
 if sys.stdin.isatty() and not args.yes and input('Run [Y/n]? ').strip().lower() in ('n','no'): return 1
 state.write_text(json.dumps(plan,indent=2),encoding='utf-8'); reg=registry(); started=time.monotonic(); results=[]
 # Stations run in routine order. Each station owns item parallelism; this prevents cross-station multiplication.
 for n in numbers:
  s=reg[n]; accepted=set(s['options']); cmd=[sys.executable,str(API_HOME/s['folder']/s['script']),*args.item]
  for flag,value in [('limit',args.limit),('workers',workers),('provider',provider),('model',model),('focus',args.focus)]:
   if flag in accepted and value not in (None,''): cmd += [f'--{flag}',str(value)]
  if args.redo and 'redo' in accepted: cmd.append('--redo')
  if args.dry_run: cmd.append('--dry-run') if n not in {'44','46','47','90','91'} else None
  print(f"\n[{n}] {s['name']}\n$ {' '.join(shlex.quote(x) for x in cmd)}")
  completed=subprocess.run(cmd,cwd=API_HOME); results.append({'station':s['label'],'returncode':completed.returncode})
 elapsed=time.monotonic()-started; record={**plan,'started_at':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':elapsed,'results':results}
 log=API_HOME/'LOGS'/f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}.json"; log.write_text(json.dumps(record,indent=2),encoding='utf-8')
 print(f"done={sum(r['returncode']==0 for r in results)} failed={sum(r['returncode']!=0 for r in results)} tokens=see receipts elapsed={elapsed:.1f}s log={log}")
 return 1 if any(r['returncode'] for r in results) else 0
if __name__=='__main__': raise SystemExit(run())
