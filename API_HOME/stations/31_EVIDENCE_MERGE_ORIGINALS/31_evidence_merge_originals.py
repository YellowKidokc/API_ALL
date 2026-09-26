from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.station_runner import legacy_main
if __name__ == "__main__":
    raise SystemExit(legacy_main("31","31_EVIDENCE_MERGE_ORIGINALS","legacy_evidence","api_original_merge.py"))
