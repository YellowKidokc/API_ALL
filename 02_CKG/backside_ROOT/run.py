from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'_BACKSIDE'))
from workbench.ckg import main
sys.argv[1:1]=['--root',str(root)]
main()
