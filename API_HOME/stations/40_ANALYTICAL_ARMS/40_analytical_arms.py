from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.paper_station import run_ai
if __name__=='__main__':
 run_ai('40_ANALYTICAL_ARMS',[
 ('fruits','Score every sentence from -2 to +2 for love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, and self-control. Preserve full-document context and return sentence IDs. Identify counterfeit and hidden fruit. The rubric, prompt, and lexicons are replaceable plug-in files in this station.'),
 ('master_equation','Apply the complete analog method in PROMPT.md: identify what plays the role of a master equation, alternatives, assumptions, failure modes, and equations when present.'),
 ('axiom_nodes','Map claims to axiom nodes without choosing among unresolved canonical registries. State registry identifiers exactly as supplied by the source.'),
 ('coherence','Assess local and global coherence, contradictions, unsupported transitions, strongest links, and repair suggestions.'),
 ('cross_arm_disagreements','Compare the four requested analytical perspectives conceptually and list likely disagreements. Do not suppress any arm.')])
