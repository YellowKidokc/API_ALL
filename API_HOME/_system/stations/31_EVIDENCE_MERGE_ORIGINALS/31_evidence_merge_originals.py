"""31_EVIDENCE_MERGE_ORIGINALS: wrapped legacy station. Everything it runs is declared in station.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.legacy import main

if __name__ == "__main__":
    raise SystemExit(main("31_EVIDENCE_MERGE_ORIGINALS"))
