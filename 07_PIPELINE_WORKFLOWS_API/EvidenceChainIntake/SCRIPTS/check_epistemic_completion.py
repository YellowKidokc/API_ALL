from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "INBOX"
CHECKPOINTS = ROOT / "SCRIPTS" / "PROCESS" / "EPISTEMIC_INTAKE_V2" / "CHECKPOINTS"
LOGS = ROOT / "SCRIPTS" / "LOGS"
ALLOWED = {".md", ".txt", ".html", ".htm"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(record: dict) -> tuple[str, str]:
    if record.get("stage") == "COMPLETE" and record.get("receipt"):
        return "COMPLETE", "none"
    if not isinstance(record.get("call_1"), dict):
        return "INCOMPLETE", "CALL_1"
    if not isinstance(record.get("call_2"), dict):
        return "INCOMPLETE", "CALL_2"
    if not isinstance(record.get("call_3"), dict):
        return "INCOMPLETE", "CALL_3"
    return "INCOMPLETE", "FINAL_ASSEMBLY"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit restart-safe epistemic completion")
    parser.add_argument("--input", type=Path, default=INBOX)
    args = parser.parse_args()
    base = args.input
    files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in ALLOWED)
    LOGS.mkdir(parents=True, exist_ok=True)
    rows = []
    for source in files:
        sha = digest(source)
        checkpoint = CHECKPOINTS / f"{sha}.json"
        record = json.loads(checkpoint.read_text(encoding="utf-8")) if checkpoint.exists() else {}
        status, missing = classify(record)
        rows.append({
            "source": str(source), "sha256": sha, "status": status, "missing_stage": missing,
            "checkpoint_stage": record.get("stage", "NEVER_STARTED"),
            "last_error": record.get("error", ""), "checkpoint": str(checkpoint) if checkpoint.exists() else ""
        })
        print(f"[{status}] {source.name}: missing={missing}; checkpoint={record.get('stage', 'NEVER_STARTED')}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report = LOGS / f"epistemic-completion-{stamp}.csv"
    with report.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys() if rows else ["source", "status"])
        writer.writeheader(); writer.writerows(rows)
    print(f"Report: {report}")
    return 1 if any(row["status"] != "COMPLETE" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
