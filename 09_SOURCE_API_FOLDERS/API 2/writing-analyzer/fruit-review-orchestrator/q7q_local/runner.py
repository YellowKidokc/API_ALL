"""7Q runner entry point."""

from __future__ import annotations

import argparse
import re
import logging
from pathlib import Path
import sys
from typing import List, Optional

try:
    from .core import INPUT_DIR, LOGS_DIR, OUTPUT_DIR, PROCESSED_DIR, load_config, QMode
    from .parser import extract_claims_for_paper, find_inputs, parse_input, read_input
    from .analyzer import analyze_evidence_mode, analyze_forward, analyze_reverse
    from .scorer import compute_scores
    from .auditor import audit_state
    from .exporter import export_json, export_markdown
    from .chievaluator import run_chi_evaluator
except ImportError:  # script execution fallback
    import os

    CURRENT = Path(__file__).resolve().parent
    if str(CURRENT) not in sys.path:
        sys.path.insert(0, str(CURRENT))
    from core import INPUT_DIR, LOGS_DIR, OUTPUT_DIR, PROCESSED_DIR, load_config, QMode  # type: ignore
    from parser import extract_claims_for_paper, find_inputs, parse_input, read_input  # type: ignore
    from analyzer import analyze_evidence_mode, analyze_forward, analyze_reverse  # type: ignore
    from scorer import compute_scores  # type: ignore
    from auditor import audit_state  # type: ignore
    from exporter import export_json, export_markdown  # type: ignore
    from chievaluator import run_chi_evaluator  # type: ignore


def _safe_tag(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "claim"


def _claim_output_path(base: Optional[Path], tag: str) -> Optional[Path]:
    if base is None:
        return None
    if base.suffix.lower() in {".json", ".md"}:
        return base.with_name(f"{base.stem}_{_safe_tag(tag)}{base.suffix}")
    return base


def run_text(content: str, claim_id: str = "", title: str = "Direct Input", cfg: dict | None = None, source_path: str = ""):
    config = cfg or load_config()
    state = parse_input(content)
    state.claim_id = claim_id
    state.paper_title = title
    state.paper_path = source_path

    mode = config.get("default_mode", QMode.FORWARD.value)
    if mode == QMode.REVERSE.value:
        state = analyze_reverse(state, config)
    elif mode == QMode.EVIDENCE.value:
        state = analyze_evidence_mode(state, config)
    else:
        state = analyze_forward(state, config)

    state = compute_scores(state, config)
    state = audit_state(state, config)
    state = run_chi_evaluator(state, config)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Run minimal 7Q forward pipeline.")
    parser.add_argument("input", nargs="?", default=None, help="Path to claim/paper file.")
    parser.add_argument("--mode", choices=[m.value for m in QMode], default=None, help="Run mode.")
    parser.add_argument("--out", type=Path, default=None, help="Optional markdown output path.")
    parser.add_argument("--json", type=Path, default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.StreamHandler(sys.stdout)],
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    log = logging.getLogger("7Q")

    config = load_config()
    if args.mode:
        config["default_mode"] = args.mode
    config["input_extensions"] = config.get("input_extensions", [".md", ".txt", ".json", ".yaml", ".html"])

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.input:
        input_paths = [Path(args.input)]
    else:
        input_paths = find_inputs(config)
    if not input_paths:
        log.info("No inputs found in %s", INPUT_DIR)
        return 0

    for path in input_paths:
        data = read_input(path)
        text = data["content"]
        claims = extract_claims_for_paper(text)

        for i, claim in enumerate(claims, start=1):
            claim_text = claim.get("statement", "").strip()
            if not claim_text:
                continue
            claim_id = f"{path.stem}::{claim.get('claim_id', f'claim-{i}')}"
            claim_title = claim.get("heading", "") or f"{path.stem} — Claim {i}"
            title = f"{path.stem} / {claim_title}"

            state = run_text(claim_text, claim_id=claim_id, title=title, cfg=config, source_path=str(path))

            json_path = export_json(state, _claim_output_path(args.json, claim.get("claim_id", f"claim-{i}")))
            md_path = export_markdown(state, _claim_output_path(args.out, claim.get("claim_id", f"claim-{i}")))

            log.info("Wrote JSON: %s", json_path)
            log.info("Wrote Markdown: %s", md_path)

        # Archive after processing
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        target = PROCESSED_DIR / path.name
        if target.exists():
            target = PROCESSED_DIR / f"{path.stem}_{path.stat().st_mtime_ns}{path.suffix}"
        path.rename(target)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
