from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from engine.station_runner import legacy_main
if __name__ == "__main__":
    raise SystemExit(legacy_main("04","04_YT_LENSES","legacy_youtube","lens_pass.py"))
