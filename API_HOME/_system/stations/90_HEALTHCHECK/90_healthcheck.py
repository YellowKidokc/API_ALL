"""90_HEALTHCHECK: every station, path key and API key; verifies options against each script's real --help."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.health import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
