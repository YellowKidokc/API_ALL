from pathlib import Path
import sys

root = Path(__file__).resolve().parents[4] / "CKG"
backside = root.parent / "_BACKSIDE" / "CKG"
sys.path.insert(0, str(backside))
from workbench.series_tools import main

sys.argv[1:1] = ["--root", str(root)]
main()
