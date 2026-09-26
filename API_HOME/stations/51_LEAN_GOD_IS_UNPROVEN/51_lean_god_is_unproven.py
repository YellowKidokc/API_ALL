"""51_LEAN_GOD_IS_UNPROVEN: wrapped legacy station. Everything it runs is declared in station.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.legacy import main

if __name__ == "__main__":
    raise SystemExit(main("51_LEAN_GOD_IS_UNPROVEN"))
