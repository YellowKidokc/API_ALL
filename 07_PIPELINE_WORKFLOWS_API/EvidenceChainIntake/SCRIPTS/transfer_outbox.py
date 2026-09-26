from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy completed evidence records to an approved folder.")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    config_path = ROOT / "SYSTEM_FILES" / "CONFIG" / "transfer.json"
    configured = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    destination = args.destination or (Path(configured["destination"]) if configured.get("destination") else None)
    if destination is None:
        print("No transfer destination configured.")
        print(f"Create transfer.json from transfer.example.json: {config_path}")
        return 2
    destination.mkdir(parents=True, exist_ok=True)
    receipt = {"timestamp": datetime.now().isoformat(), "destination": str(destination), "files": []}
    transfer_ready = ROOT / "OUTBOX" / "02_SORTED_READY_TO_TRANSFER"
    for source in sorted(transfer_ready.rglob("*.md")):
        target = destination / source.relative_to(transfer_ready)
        target.parent.mkdir(parents=True, exist_ok=True)
        status = "skipped_existing"
        if not target.exists() or args.replace:
            shutil.copy2(source, target)
            status = "copied"
        receipt["files"].append({"source": str(source), "target": str(target), "sha256": digest(source), "status": status})
    log = ROOT / "LOGS" / f"transfer-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    log.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    transferred = ROOT / "OUTBOX" / "03_TRANSFERRED"
    transferred.mkdir(parents=True, exist_ok=True)
    shutil.copy2(log, transferred / log.name)
    print(f"Transfer checked {len(receipt['files'])} file(s). Receipt: {log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
