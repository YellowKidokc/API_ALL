from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import epistemic_intake_v2 as engine


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: repair_epistemic_v2_packet.py RUN_ID")
    run_id = sys.argv[1]
    output_dir = engine.OUTBOX / run_id
    process_dir = engine.PROCESS / run_id
    json_files = list(output_dir.glob("*.epistemic.json"))
    receipts = list(process_dir.glob("*.receipt.json"))
    if len(json_files) != 1 or len(receipts) != 1:
        raise RuntimeError("repair currently requires exactly one packet and receipt in the run")
    json_path, receipt_path = json_files[0], receipts[0]
    packet = json.loads(json_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    moved = Path(receipt["processed_original"])
    payload = moved.read_bytes()
    digest = engine.sha256_bytes(payload)
    if digest != receipt["source_sha256"]:
        raise RuntimeError("processed original no longer matches the receipt")

    backup = process_dir / "PRE_NORMALIZATION_BACKUP"
    backup.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("*.epistemic.*"):
        shutil.copy2(old, backup / old.name)
    shutil.copy2(receipt_path, backup / receipt_path.name)

    extraction, evaluation, synthesis = packet["call_1"], packet["call_2"], packet["call_3"]
    engine.normalize_scorecard(evaluation, synthesis)
    base = engine.slug(extraction.get("document_title") or extraction.get("governing_question") or moved.stem)
    new_json = output_dir / f"{base}.epistemic.json"
    new_md = output_dir / f"{base}.epistemic.md"
    original_source_path = Path(receipt["source_original_path"])
    new_md.write_text(
        engine.render_markdown(original_source_path, digest, payload.decode("utf-8", errors="replace"), extraction, evaluation, synthesis, run_id),
        encoding="utf-8",
    )
    new_json.write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")
    if json_path != new_json:
        json_path.unlink()
    old_md = Path(receipt["markdown_output"])
    if old_md != new_md and old_md.exists():
        old_md.unlink()
    receipt["markdown_output"] = str(new_md)
    receipt["json_output"] = str(new_json)
    receipt["score_normalization"] = "ten dimensions normalized to 0-10; raw=sum; final=raw*integrity_factor"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"REPAIRED={new_md}")
    print(f"BACKUP={backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
