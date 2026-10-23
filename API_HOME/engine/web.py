"""Browser front end for ONE_MENU. Serves web/index.html on 127.0.0.1 and runs menu.py jobs."""
from __future__ import annotations
import json,os,shutil,socket,subprocess,sys,threading,uuid,webbrowser
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
if __package__ in (None,''):
 sys.path.insert(0,str(Path(__file__).resolve().parents[1])); from engine.paths import API_HOME,ensure_runtime_dirs
else: from .paths import API_HOME,ensure_runtime_dirs

PORT=8765; JOBS:dict[str,dict]={}; LOCK=threading.Lock()
def load(name): return json.loads((API_HOME/'config'/name).read_text(encoding='utf-8'))

def command(plan:dict)->list[str]:
 cmd=[sys.executable,'-u',str(API_HOME/'engine'/'menu.py'),*[str(x) for x in plan.get('selection',[])],'--yes']
 if plan.get('turbo'): cmd += ['--turbo',plan['turbo']]
 if plan.get('limit'): cmd += ['--limit',str(int(plan['limit']))]
 if plan.get('provider'): cmd += ['--provider',plan['provider']]
 if plan.get('focus'): cmd += ['--focus',plan['focus']]
 for item in plan.get('items',[]): cmd += ['--item',item]
 if plan.get('redo'): cmd.append('--redo')
 if plan.get('dry_run'): cmd.append('--dry-run')
 return cmd

def start(cmd:list[str],label:str='')->str:
 job_id=uuid.uuid4().hex[:8]
 proc=subprocess.Popen(cmd,cwd=API_HOME,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),text=True,encoding='utf-8',errors='replace',bufsize=1)
 job={'id':job_id,'label':label,'cmd':cmd,'log':'','status':'running','code':None,'proc':proc}
 with LOCK: JOBS[job_id]=job
 def pump():
  for line in proc.stdout:
   with LOCK: job['log']+=line
  code=proc.wait()
  with LOCK: job['code']=code; job['status']='done' if code==0 else ('stopped' if job['status']=='stopping' else 'failed')
 threading.Thread(target=pump,daemon=True).start(); return job_id

def paths()->dict:
 example=load('paths.example.json'); target=API_HOME/'config'/'paths.json'
 current=json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
 return {k:current.get(k,v) for k,v in example.items()}

def save_paths(values:dict)->dict:
 merged=paths(); bad=[]
 for k,v in values.items():
  if k not in merged: continue
  v=str(v).strip().strip('"')
  if v and not Path(os.path.expandvars(v)).expanduser().exists(): bad.append(k)
  merged[k]=v
 (API_HOME/'config'/'paths.json').write_text(json.dumps(merged,indent=2)+'\n',encoding='utf-8')
 return {'ok':True,'not_found':bad}

def save_keys(values:dict)->dict:
 for name in ('DEEPSEEK_API_KEY','OPENAI_API_KEY'):
  v=str(values.get(name,'')).strip()
  if not v: continue
  os.environ[name]=v
  if os.name=='nt': subprocess.run(['setx',name,v],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 return {'ok':True}

def health()->list[dict]:
 from engine.health import check
 return check()[1]

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a): pass
 def send(self,body,ctype='application/json',code=200):
  data=body if isinstance(body,bytes) else json.dumps(body).encode()
  self.send_response(code); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
 def do_GET(self):
  if self.path in ('/','/index.html'): return self.send((API_HOME/'web'/'index.html').read_bytes(),'text/html; charset=utf-8')
  if self.path=='/icon.png': return self.send((API_HOME/'web'/'icon.png').read_bytes(),'image/png')
  if self.path=='/api/config': return self.send({'stations':load('stations.json'),'routines':load('routines.json'),'settings':load('settings.json')})
  if self.path=='/api/health': return self.send(health())
  if self.path=='/api/paths': return self.send(paths())
  if self.path=='/api/jobs':
   with LOCK: return self.send([{k:v for k,v in j.items() if k not in ('proc','log')} for j in JOBS.values()])
  if self.path.startswith('/api/jobs/'):
   with LOCK: job=JOBS.get(self.path.rsplit('/',1)[1])
   if not job: return self.send({'error':'no such job'},code=404)
   with LOCK: return self.send({k:v for k,v in job.items() if k!='proc'})
  self.send({'error':'not found'},code=404)
 def do_POST(self):
  if self.headers.get('Origin') not in (None,f'http://127.0.0.1:{PORT}',f'http://localhost:{PORT}'): return self.send({'error':'forbidden'},code=403)
  body=json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
  if self.path=='/api/run':
   if not body.get('selection'): return self.send({'error':'pick at least one station'},code=400)
   return self.send({'id':start(command(body),' + '.join(map(str,body['selection'])))})
  if self.path=='/api/paths': return self.send(save_paths(body))
  if self.path=='/api/keys': return self.send(save_keys(body))
  if self.path=='/api/quit':
   self.send({'ok':True}); threading.Thread(target=self.server.shutdown,daemon=True).start(); return
  if self.path=='/api/stop':
   with LOCK: job=JOBS.get(body.get('id',''))
   if job and job['status']=='running':
    with LOCK: job['status']='stopping'
    job['proc'].terminate()
   return self.send({'ok':True})
  self.send({'error':'not found'},code=404)

def open_window(url:str)->None:
 """Open as a standalone app window (Edge/Chrome --app); fall back to the default browser."""
 candidates=[shutil.which(n) for n in ('msedge','chrome','google-chrome','chromium')]
 for base in (os.environ.get('ProgramFiles(x86)',''),os.environ.get('ProgramFiles',''),os.environ.get('LOCALAPPDATA','')):
  if base: candidates += [os.path.join(base,'Microsoft','Edge','Application','msedge.exe'),os.path.join(base,'Google','Chrome','Application','chrome.exe')]
 for exe in candidates:
  if exe and os.path.isfile(exe):
   subprocess.Popen([exe,f'--app={url}','--window-size=1400,950'],creationflags=getattr(subprocess,'DETACHED_PROCESS',0)); return
 webbrowser.open(url)

def running()->bool:
 with socket.socket() as s: return s.connect_ex(('127.0.0.1',PORT))==0

def main()->int:
 url=f'http://127.0.0.1:{PORT}/'; show='--no-browser' not in sys.argv
 if running():
  if show: open_window(url)
  return 0
 ensure_runtime_dirs(); server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
 print(f'ONE_MENU is open at {url}')
 if show: open_window(url)
 try: server.serve_forever()
 except KeyboardInterrupt: pass
 return 0
if __name__=='__main__': raise SystemExit(main())
