from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
DEFAULT_CONFIG = {
    "canon_status": "candidate_draft",
    "preserve_input_in_place": True,
    "append_complete_source": True,
    "ask_when_confidence_below": 0.65,
    "semantic_provider": "deepseek",
    "allowed_extensions": [".md", ".txt", ".html", ".htm"],
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return clean[:100] or "untitled"


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def infer_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        candidate = line.strip().lstrip("#").strip()
        if candidate and len(candidate) <= 180:
            if candidate.lower().startswith(("title:", "status:", "---")):
                continue
            return candidate
    return path.stem.replace("_", " ").replace("-", " ").strip().title()


def infer_type(text: str) -> tuple[str, float, list[str]]:
    lower = text.lower()
    signals: list[str] = []
    scores = {"conversation": 0, "article": 0, "system": 0, "research_synthesis": 0}

    if re.search(r"(?m)^(user|assistant|human|codex|claude):", lower):
        scores["conversation"] += 4
        signals.append("speaker labels")
    if lower.count("## ") >= 3:
        scores["article"] += 2
        scores["research_synthesis"] += 2
        signals.append("sectioned long-form text")
    if any(term in lower for term in ("what the evidence", "original paper", "negative control", "unresolved question")):
        scores["research_synthesis"] += 4
        signals.append("evidence and boundary analysis")
    if any(term in lower for term in ("system model", "architecture", "pipeline", "framework", "emerging ladder")):
        scores["system"] += 3
        signals.append("system or framework language")
    if len(text.split()) > 1200:
        scores["article"] += 1
        signals.append("long-form source")

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_type, best_score = ranked[0]
    runner_up = ranked[1][1]
    confidence = 0.45 if best_score == 0 else min(0.95, 0.58 + 0.08 * (best_score - runner_up))
    return best_type if best_score else "source_record", round(confidence, 2), signals


def infer_tags(text: str) -> list[str]:
    vocabulary = {
        "consciousness": ("conscious", "sentience", "subjective experience"),
        "watcher": ("watcher", "question-sensitive", "state alone"),
        "artificial-intelligence": (" ai ", "artificial intelligence"),
        "dishbrain": ("dishbrain", "pong", "neuronal culture"),
        "lean4": ("lean", "formal theorem"),
        "theology": ("theological", "christian", "god", "personhood"),
        "systems": ("system", "closed-loop", "framework"),
    }
    padded = f" {text.lower()} "
    return sorted(tag for tag, terms in vocabulary.items() if any(term in padded for term in terms))


def section_outline(text: str) -> list[str]:
    headings = []
    for line in text.splitlines():
        match = re.match(r"^#{1,4}\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(1))
    return headings[:40]


def render_record(metadata: dict, text: str) -> str:
    tags = ", ".join(yaml_quote(tag) for tag in metadata["tags"])
    outline = metadata["source_outline"]
    outline_md = "\n".join(f"- {heading}" for heading in outline) or "- No explicit headings detected"
    return f'''---
type: {metadata["inferred_type"]}
title: {yaml_quote(metadata["title"])}
status: CANDIDATE_DRAFT
canon_status: {metadata["canon_status"]}
semantic_status: pending_review
source_file: {yaml_quote(metadata["source_file"])}
source_sha256: {metadata["source_sha256"]}
captured_at: {metadata["captured_at"]}
tags: [{tags}]
---

# {metadata["title"]}

> **CANDIDATE_DRAFT — NOT ADMITTED.** The source is preserved below. Structured semantic
> sections remain pending until an AI or human completes the accompanying analysis prompt.

## Intake assessment

- Inferred type: `{metadata["inferred_type"]}`
- Routing confidence: `{metadata["routing_confidence"]}`
- Signals: {", ".join(metadata["routing_signals"]) or "none"}
- Original words: `{metadata["word_count"]}`
- Original SHA-256: `{metadata["source_sha256"]}`

## Source outline

{outline_md}

## At a glance

Pending semantic extraction.

## Central claim

Pending semantic extraction.

## Best concise argument

Pending semantic extraction.

## System or model

Pending semantic extraction.

## Evidence chain

Pending semantic extraction.

## Best evidence and sources

Pending semantic extraction.

## Strongest objection and negative controls

Pending semantic extraction.

## What survives

Pending semantic extraction.

## What this does not establish

Pending semantic extraction.

## Corrections and revisions

Pending semantic extraction.

## Implications

Pending semantic extraction.

## Formal or testable path

Pending semantic extraction.

## Open questions and next actions

Pending semantic extraction.

## Recommended classification and relationships

Pending semantic extraction.

## Complete preserved source

<!-- BEGIN EXACT SOURCE PROJECTION; authoritative bytes are preserved in ARCHIVE -->

{text}

<!-- END EXACT SOURCE PROJECTION -->
'''


def load_hash_index() -> dict[str, dict]:
    index: dict[str, dict] = {}
    process_dir = SCRIPTS_DIR / "PROCESS"
    if not process_dir.exists():
        return index
    for receipt_path in process_dir.glob("*.intake.json"):
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            digest = receipt.get("source_sha256")
            if digest:
                index[digest] = {
                    "receipt": str(receipt_path),
                    "record": receipt.get("knowledge_record"),
                    "source": receipt.get("source_file"),
                }
        except (OSError, json.JSONDecodeError):
            continue
    return index


def process_file(path: Path, run_id: str, config: dict, known_hashes: dict[str, dict]) -> dict:
    payload = path.read_bytes()
    digest = sha256(payload)
    expected_prompt = SCRIPTS_DIR / "PROCESS" / f"{slug(path.stem)}.analysis-prompt.md"
    if digest in known_hashes and expected_prompt.exists():
        prior = known_hashes[digest]
        return {
            "source": str(path),
            "sha256": digest,
            "status": "exact_duplicate_skipped",
            "duplicate_of": prior.get("source"),
            "record": prior.get("record"),
            "receipt": prior.get("receipt"),
        }
    text = payload.decode("utf-8", errors="replace")
    inferred_type, confidence, signals = infer_type(text)
    title = infer_title(path, text)
    metadata = {
        "title": title,
        "inferred_type": inferred_type,
        "routing_confidence": confidence,
        "routing_signals": signals,
        "canon_status": config["canon_status"],
        "source_file": str(path.resolve()),
        "source_sha256": digest,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "word_count": len(text.split()),
        "tags": infer_tags(text),
        "source_outline": section_outline(text),
    }

    originals = SCRIPTS_DIR / "ORIGINALS" / run_id
    output = SCRIPTS_DIR / "PROCESS"
    ready = ROOT / "OUTBOX" / "00_ALL_PROCESSED_ARTICLES"
    questions = SCRIPTS_DIR / "QUESTIONS"
    for directory in (originals, output, ready, questions):
        directory.mkdir(parents=True, exist_ok=True)

    source_copy = originals / path.name
    if source_copy.exists() and sha256(source_copy.read_bytes()) != digest:
        source_copy = originals / f"{path.stem}-{digest[:8]}{path.suffix}"
    if not source_copy.exists():
        shutil.copy2(path, source_copy)
    base = slug(path.stem)
    record_path = ready / f"{base}.knowledge.md"
    receipt_path = output / f"{base}.intake.json"
    prompt_path = output / f"{base}.analysis-prompt.md"
    if receipt_path.exists():
        try:
            old_digest = json.loads(receipt_path.read_text(encoding="utf-8")).get("source_sha256")
        except (OSError, json.JSONDecodeError):
            old_digest = None
        if old_digest != digest:
            base = f"{base}-{digest[:8]}"
            record_path = ready / f"{base}.knowledge.md"
            receipt_path = output / f"{base}.intake.json"
            prompt_path = output / f"{base}.analysis-prompt.md"

    record_path.write_text(render_record(metadata, text), encoding="utf-8")
    receipt = {**metadata, "preserved_source": str(source_copy), "knowledge_record": str(record_path)}
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    prompt_template = (SCRIPTS_DIR / "SYSTEM_FILES" / "PROMPTS" / "knowledge_record.md").read_text(encoding="utf-8")
    prompt_path.write_text(
        prompt_template.replace("{{METADATA}}", json.dumps(metadata, indent=2, ensure_ascii=False)).replace("{{SOURCE}}", text),
        encoding="utf-8",
    )

    question_path = None
    if confidence < float(config["ask_when_confidence_below"]):
        question_path = questions / f"{base}.question.md"
        question_path.write_text(
            f"# Human routing question\n\nWhat should `{path.name}` primarily become?\n\n"
            "- [ ] Conversation record\n- [ ] Article\n- [ ] System/framework record\n"
            "- [ ] Research synthesis\n- [ ] Source record only\n\n"
            f"Automatic guess: `{inferred_type}` at confidence `{confidence}`.\n",
            encoding="utf-8",
        )

    return {
        "source": str(path),
        "sha256": metadata["source_sha256"],
        "inferred_type": inferred_type,
        "confidence": confidence,
        "record": str(record_path),
        "prompt": str(prompt_path),
        "question": str(question_path) if question_path else None,
        "preserved_source": str(source_copy),
        "status": "prepared_for_semantic_analysis",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Preserve sources and build reviewable meaning records.")
    parser.add_argument("--input", type=Path, default=ROOT / "INBOX")
    parser.add_argument("--files", type=Path, nargs="+", default=[],
                        help="Prepare only these explicit source files; leaves INBOX and every other paper untouched.")
    parser.add_argument("--config", type=Path, default=ROOT / "SYSTEM_FILES" / "CONFIG" / "config.json")
    args = parser.parse_args()

    config = dict(DEFAULT_CONFIG)
    config_path = args.config if args.config.exists() else ROOT / "SYSTEM_FILES" / "CONFIG" / "config.example.json"
    if config_path.exists():
        config.update(json.loads(config_path.read_text(encoding="utf-8")))

    for name in (
        "INBOX", "PROCESS", "OUTBOX/00_ALL_PROCESSED_ARTICLES",
        "OUTBOX/02_SORTED_READY_TO_TRANSFER", "OUTBOX/03_TRANSFERRED",
        "OUTBOX/99_HOLD", "QUESTIONS", "ORIGINALS", "TRANSFER", "LOGS"
    ):
        (ROOT / name).mkdir(parents=True, exist_ok=True)

    allowed = {value.lower() for value in config["allowed_extensions"]}
    if args.files:
        inputs = sorted(args.files)
        missing = [str(path) for path in inputs if not path.is_file()]
        if missing:
            raise SystemExit("Missing explicit source file(s): " + ", ".join(missing))
        unsupported = [str(path) for path in inputs if path.suffix.lower() not in allowed]
        if unsupported:
            raise SystemExit("Unsupported explicit source file(s): " + ", ".join(unsupported))
    else:
        inputs = sorted(path for path in args.input.rglob("*") if path.is_file() and path.suffix.lower() in allowed)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    results = []
    known_hashes = load_hash_index()
    for path in inputs:
        try:
            result = process_file(path, run_id, config, known_hashes)
            results.append(result)
            if result.get("status") == "prepared_for_semantic_analysis":
                known_hashes[result["sha256"]] = {
                    "receipt": str(ROOT / "PROCESS" / f"{Path(result['prompt']).name.removesuffix('.analysis-prompt.md')}.intake.json"),
                    "record": result.get("record"),
                    "source": result.get("source"),
                }
        except Exception as exc:
            results.append({"source": str(path), "error": str(exc)})
    log = {"run_id": run_id, "input_count": len(inputs), "results": results}
    (ROOT / "LOGS" / f"{run_id}.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    duplicates = sum(result.get("status") == "exact_duplicate_skipped" for result in results)
    prepared = sum(result.get("status") == "prepared_for_semantic_analysis" for result in results)
    print(
        f"Evidence Chain Intake examined {len(inputs)} source(s): "
        f"{prepared} new, {duplicates} exact duplicate(s) skipped; run {run_id}"
    )
    return 1 if any("error" in result for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
