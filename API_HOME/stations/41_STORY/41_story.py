from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.paper_station import run_ai
if __name__=='__main__':
 run_ai('41_STORY',[
 ('paper_pass','Evaluate hook, sequence, narrative causality, transitions, payoff, coherence, and specific repairs for this complete paper.'),
 ('series_pass','Identify series-level placement and dependencies using only series context present in the paper metadata/source; mark unavailable context explicitly.'),
 ('memorable_lines','Gate each paragraph on coherence. Only for coherent paragraphs, propose at most one memorable line; cite paragraph or sentence ID. Return no line for a failed gate.')])
