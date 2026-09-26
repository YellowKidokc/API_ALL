"""91_RELOCATE: same as RELOCATE.bat."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.relocate import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
