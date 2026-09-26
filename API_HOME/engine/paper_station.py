from __future__ import annotations
import argparse,html,json,re,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from . import llm
from .focus import append,compose
from .output import dated_run_dir,sha256_file,write_bundle
from .papers import discover
from .paths import API_HOME

def arguments(label):
 p=argparse.ArgumentParser(prog=label); p.add_argument('items',nargs='*'); p.add_argument('--limit',type=int); p.add_argument('--workers',type=int,default=30); p.add_argument('--provider',default='deepseek'); p.add_argument('--model',default='deepseek-chat'); p.add_argument('--focus',default=''); p.add_argument('--redo',action='store_true'); return p.parse_args()
def source(paper):
 meta=json.loads((paper/'paper.json').read_text(encoding='utf-8')); path=paper/'00_SOURCE'/meta['source_file']; return meta,path,path.read_text(encoding='utf-8',errors='replace')
def ai_bundle(paper:Path,label:str,prompts:list[tuple[str,str]],args):
 meta,path,text=source(paper); focus,focus_hash=compose(API_HOME/'stations'/label,paper,args.focus); src_hash=sha256_file(path); llm.configure(args.workers)
 checkpoint={"source_hash":src_hash,"prompt_version":"1","model":args.model,"focus_hash":focus_hash}
 if not args.redo:
  for prior in sorted((paper/"02_RUNS"/label).glob("*/"+label+".run.json"),reverse=True):
   saved=json.loads(prior.read_text(encoding="utf-8"))
   if all(saved.get(k)==v for k,v in checkpoint.items()) and not saved.get("errors"):
    print(f"SKIP completed {paper}: {prior.parent}"); return
 def one(entry):
  name,instruction=entry; prompt=append(instruction+'\n\nSOURCE DOCUMENT:\n'+text,focus); result=llm.call([{'role':'user','content':prompt}],provider=args.provider,model=args.model); return name,result,prompt
 gathered={}; receipts=[]
 with ThreadPoolExecutor(max_workers=min(args.workers,len(prompts))) as pool:
  futures=[pool.submit(one,p) for p in prompts]
  for f in as_completed(futures):
   name,result,prompt=f.result(); gathered[name]=result.text if not result.error else {'error':result.error}; receipts.append(llm.receipt(result,source_hash=src_hash,prompt_version='1',focus_text=focus,focus_hash=focus_hash,part=name))
 out=dated_run_dir(paper,label); receipt={'source_hash':src_hash,'model':args.model,'provider':args.provider,'prompt_version':'1','focus_text':focus,'focus_hash':focus_hash,'tokens':sum(r['tokens'] for r in receipts),'time_seconds':sum(r['elapsed_seconds'] for r in receipts),'errors':[r['error'] for r in receipts if r['error']],'calls':receipts}
 body='<h1>'+html.escape(label)+'</h1>'+''.join(f'<section><h2>{html.escape(k)}</h2><pre>{html.escape(v if isinstance(v,str) else json.dumps(v,indent=2))}</pre></section>' for k,v in gathered.items()); write_bundle(out,label,gathered,'<!doctype html><meta charset="utf-8">'+body,receipt,[{'part':k,'result':v if isinstance(v,str) else json.dumps(v)} for k,v in gathered.items()])
 meta.setdefault('stations_run',[]).append({'station':label,'run':str(out.relative_to(paper))}); (paper/'paper.json').write_text(json.dumps(meta,indent=2),encoding='utf-8'); print(out)

def run_ai(label,prompts):
 args=arguments(label); papers=[x for x in discover(args.items,args.limit) if x.is_dir()]
 for paper in papers:
  try: ai_bundle(paper,label,prompts,args)
  except Exception as exc: print(f'{paper}: {type(exc).__name__}: {exc}')
