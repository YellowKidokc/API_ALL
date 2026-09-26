from pathlib import Path
import argparse,json,math,re,statistics,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.output import dated_run_dir,sha256_file,write_bundle
from engine.papers import discover

def main():
 p=argparse.ArgumentParser(); p.add_argument('items',nargs='*'); p.add_argument('--limit',type=int); p.add_argument('--workers',type=int); p.add_argument('--provider'); p.add_argument('--model'); p.add_argument('--focus',default=''); p.add_argument('--redo',action='store_true'); a=p.parse_args()
 for paper in [x for x in discover(a.items,a.limit) if x.is_dir()]:
  meta=json.loads((paper/'paper.json').read_text()); source=paper/'00_SOURCE'/meta['source_file']; text=source.read_text(encoding='utf-8',errors='replace'); words=re.findall(r"\b[\w'-]+\b",text); sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+',text) if s.strip()]; paragraphs=[p for p in re.split(r'\n\s*\n',text) if p.strip()]; lengths=[len(re.findall(r'\w+',s)) for s in sentences] or [0]
  metrics=[{'id':'word_count','family':'size','value':len(words),'method':'computed','academic_benchmark':False},{'id':'sentence_count','family':'size','value':len(sentences),'method':'computed','academic_benchmark':False},{'id':'paragraph_count','family':'size','value':len(paragraphs),'method':'computed','academic_benchmark':False},{'id':'mean_sentence_words','family':'readability','value':statistics.mean(lengths),'method':'computed','academic_benchmark':False},{'id':'sentence_words_sd','family':'rhythm','value':statistics.pstdev(lengths),'method':'computed','academic_benchmark':False},{'id':'lexical_diversity','family':'lexical','value':len({w.lower() for w in words})/max(1,len(words)),'method':'computed','academic_benchmark':False}]
  data={'schema_version':1,'metrics':metrics,'headline':metrics[:12],'specialized_charts':[],'coverage':{'expected_schema_variables':366,'emitted_here':len(metrics),'external_116_script_audit':'requires configured nas_brain on David machine'}}
  out=dated_run_dir(paper,'42_STATISTICS_WALL'); receipt={'source_hash':sha256_file(source),'model':'local','prompt_version':'1','focus_text':a.focus,'focus_hash':'','tokens':0,'time_seconds':0,'errors':[]}; html='<h1>Statistics wall data</h1><p>Use station 46 to render the approved matrix.</p>'; write_bundle(out,'42_STATISTICS_WALL',data,html,receipt,metrics); (paper/'03_REPORT'/'statistics.json').write_text(json.dumps(data,indent=2),encoding='utf-8'); print(out)
if __name__=='__main__': main()
