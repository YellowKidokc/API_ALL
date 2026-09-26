from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.station_runner import legacy_main
if __name__ == "__main__":
    raise SystemExit(legacy_main("34","34_EVIDENCE_SERIES_SYNTHESIS","legacy_evidence","series_grand_synthesizer.py"))
