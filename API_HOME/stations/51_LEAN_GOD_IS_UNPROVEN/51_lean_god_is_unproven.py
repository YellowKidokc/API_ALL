from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.station_runner import legacy_main
if __name__ == "__main__":
    raise SystemExit(legacy_main("51","51_LEAN_GOD_IS_UNPROVEN","legacy_evidence","god_is_unproven_to_lean.py"))
