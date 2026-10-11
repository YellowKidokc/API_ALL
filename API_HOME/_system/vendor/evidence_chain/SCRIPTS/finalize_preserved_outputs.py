from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import organize_and_retake_folders as organizer


HERE = Path(__file__).resolve().parent
PROCESS = HERE / "PROCESS" / "EPISTEMIC_INTAKE_V2"
CHECKPOINTS = PROCESS / "CHECKPOINTS"


def digest(path: Path) -> str:
    with open(organizer.unc_path(path), "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def exists(path: Path) -> bool:
    return os.path.exists(organizer.unc_path(path))


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def frontmatter_value(text: str, key: str, fallback: str = "") -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+)$", text)
    if not match:
        return fallback
    raw = match.group(1).strip()
    try:
        value = json.loads(raw)
        return str(value or fallback)
    except json.JSONDecodeError:
        return raw.strip("\"'") or fallback


def finalize(source_hash: str) -> Path:
    checkpoint_path = CHECKPOINTS / f"{source_hash}.json"
    state = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    markdown_path = Path(state["markdown_output"])
    json_path = Path(state["json_output"])
    processed_path = Path(state["processed_original"])
    staged_path = Path(state["source_original_path"])

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    if packet.get("source_integrity", {}).get("sha256") != source_hash:
        raise RuntimeError("packet source hash mismatch")
    if not exists(processed_path) or digest(processed_path) != source_hash:
        raise RuntimeError("processed original is missing or changed")

    organization = organizer.organize_all(
        dry_run=False, source_paths=[markdown_path], write_receipt=False
    )
    if organization.get("processed_count") != 1:
        raise RuntimeError("routing did not return one record")
    record = organization["records"][0]
    routed = [
        record["original_structure_dest"],
        *record["categorized_dests"],
        *record["discovery_facet_dests"],
    ]
    output_hash = digest(markdown_path)
    bad = [path for path in routed if not exists(Path(path)) or digest(Path(path)) != output_hash]
    if bad:
        details = "\n".join(
            f"{path} (exists={exists(Path(path))}, hash={digest(Path(path)) if exists(Path(path)) else 'missing'})"
            for path in bad
        )
        raise RuntimeError(f"routing verification failed for {len(bad)} destination(s):\n{details}")

    text = markdown_path.read_text(encoding="utf-8")
    run_id = frontmatter_value(text, "run_id", markdown_path.parent.name)
    title = frontmatter_value(text, "title", markdown_path.stem)
    provider = frontmatter_value(text, "provider", "openrouter")
    model = frontmatter_value(text, "model", "unknown")
    receipt = {
        "status": "success",
        "run_id": run_id,
        "source_original_path": str(staged_path),
        "source_sha256": source_hash,
        "markdown_output": str(markdown_path),
        "json_output": str(json_path),
        "processed_original": str(processed_path),
        "final_title": title,
        "routed_outputs": routed,
        "provider": provider,
        "model": model,
        "usage": "preserved from original completed calls",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "finalization_note": "Existing verified AI packet rerouted and finalized without repeating API calls.",
    }
    receipt_path = PROCESS / run_id / f"{markdown_path.stem.removesuffix('.epistemic')}.receipt.json"
    atomic_json(receipt_path, receipt)

    history = list(state.get("history") or [])
    history.append({"stage": "COMPLETE", "at": receipt["completed_at"]})
    state.update(
        {
            "stage": "COMPLETE",
            "updated_at": receipt["completed_at"],
            "history": history,
            "receipt": str(receipt_path),
            "routed_outputs": routed,
        }
    )
    atomic_json(checkpoint_path, state)

    if staged_path.exists():
        if digest(staged_path) != source_hash:
            raise RuntimeError("staged duplicate hash mismatch; refusing removal")
        staged_path.unlink()
    return receipt_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hashes", nargs="+")
    args = parser.parse_args()
    for source_hash in args.hashes:
        print(finalize(source_hash))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
