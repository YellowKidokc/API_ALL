from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.papers import create

def main():
 p=argparse.ArgumentParser(); p.add_argument('sources',nargs='+'); p.add_argument('--title'); p.add_argument('--id'); p.add_argument('--series',default=''); a=p.parse_args()
 for source in a.sources: print(create(Path(source),title=a.title,paper_id=a.id,series=a.series))
if __name__=='__main__': main()
