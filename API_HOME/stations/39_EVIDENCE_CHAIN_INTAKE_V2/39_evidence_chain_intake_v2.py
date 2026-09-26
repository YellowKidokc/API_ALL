from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.station_runner import legacy_main
if __name__ == "__main__":
    raise SystemExit(legacy_main("39","39_EVIDENCE_CHAIN_INTAKE_V2","legacy_evidence","epistemic_intake_v2.py"))
