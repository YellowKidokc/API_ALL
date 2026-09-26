from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.papers import discover
from engine.report import build
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('items',nargs='*');p.add_argument('--limit',type=int);a=p.parse_args()
 for paper in [x for x in discover(a.items,a.limit) if x.is_dir()]: print(*build(paper))
