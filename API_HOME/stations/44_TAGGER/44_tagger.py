from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.papers import discover
from engine.tagger import tag_item

def main():
 p=argparse.ArgumentParser(); p.add_argument('items',nargs='*'); p.add_argument('--limit',type=int); p.add_argument('--focus',default=''); p.add_argument('--workers',type=int); p.add_argument('--provider'); p.add_argument('--model'); p.add_argument('--redo',action='store_true'); a=p.parse_args()
 for item in discover(a.items,a.limit):
  if item.is_dir():
   meta=json.loads((item/'paper.json').read_text()); source=item/'00_SOURCE'/meta['source_file']; text=source.read_text(encoding='utf-8',errors='replace'); values=tag_item(meta['id'],'paper',item,text); meta['tags']={x['tag']:x for x in values}; (item/'paper.json').write_text(json.dumps(meta,indent=2),encoding='utf-8'); print(item)
  else: print(f'Skipping non-paper item: {item}',file=sys.stderr)
if __name__=='__main__': main()
