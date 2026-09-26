# LANE 4: FORMAL PROOF BREAKDOWN ENGINE (v1.0)
# =============================================
# Reads .lean files, sends each through DeepSeek with the
# Lane 4 template, logs every result to the FORMAL_PROOF_LEDGER,
# and outputs both markdown and JSON per file.
#
# Three outboxes:
#   01_WORKING/   — live results, editable
#   02_ARCHIVE/   — untouched copies, never edited
#   03_LEDGER/    — append-only cumulative log
#
# Usage:
#   python lane4_lean_breakdown.py
#   python lane4_lean_breakdown.py --provider deepseek
#   python lane4_lean_breakdown.py --file CandidateComparison.lean

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
LEAN4_DIR = ROOT_DIR / "LEAN4"
LEAN_THEOREMS_DIR = LEAN4_DIR / "FaithThruPhysics" / "Theorems"
LEAN_INBOX_DIR = LEAN4_DIR / "INBOX"
OUTBOX_DIR = ROOT_DIR / "OUTBOX"
LANE4_DIR = OUTBOX_DIR / "LANE4_FORMAL_PROOFS"
WORKING_DIR = LANE4_DIR / "01_WORKING"
ARCHIVE_DIR = LANE4_DIR / "02_ARCHIVE"
LEDGER_DIR = LANE4_DIR / "03_LEDGER"
LOGS_DIR = ROOT_DIR / "LOGS"
TEMPLATES_DIR = SCRIPTS_DIR / "TEMPLATES"

LEDGER_FILE = LEDGER_DIR / "FORMAL_PROOF_LEDGER.tsv"
LEDGER_COLUMNS = [
    "result_id", "timestamp", "lean_file", "lean_file_sha256",
    "theorem_name", "result_type", "one_line_plain", "one_line_technical",
    "proves", "does_not_prove", "axiom_dependency", "non_vacuous",
    "papers_affected", "contested_claims_hit", "claim_verdict",
    "supersedes", "trust_level", "provider", "model", "run_id"
]

def ensure_dirs():
    for d in [LEAN_INBOX_DIR, WORKING_DIR, ARCHIVE_DIR, LEDGER_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    if not LEDGER_FILE.exists():
        LEDGER_FILE.write_text("\t".join(LEDGER_COLUMNS) + "\n", encoding="utf-8")

def get_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def load_template() -> str:
    template_path = TEMPLATES_DIR / "06_LANE4_FORMAL_PROOFS_v1.1.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    # Fallback: use inline minimal template
    return "Analyze this Lean 4 file. For each theorem: state what it proves, what it assumes, what it does NOT prove. List all negative results. Output in JSON."


def call_api(prompt: str, system_prompt: str, max_tokens: int = 8192,
             provider: str = "auto", model: str | None = None) -> tuple[str, dict]:
    """Reuses the same multi-route API logic from turbo_pipeline_runner."""
    import requests

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()

    routes = []
    if deepseek_key:
        routes.append({
            "provider": "deepseek", "model": model or "deepseek-chat",
            "url": "https://api.deepseek.com/chat/completions",
            "headers": {"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"}
        })
    if openrouter_key:
        routes.append({
            "provider": "openrouter", "model": model or "deepseek/deepseek-r1:free",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://faiththruphysics.com",
                "X-OpenRouter-Title": "Lane 4 Formal Proofs Engine"
            }
        })
    if not routes:
        raise RuntimeError("No API keys found. Set DEEPSEEK_API_KEY or OPENROUTER_API_KEY.")

    for route in routes:
        payload = {
            "model": route["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": max_tokens
        }
        for attempt in range(1, 3):
            try:
                resp = requests.post(route["url"], json=payload, headers=route["headers"], timeout=180)
                resp.raise_for_status()
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    usage["_route"] = {"provider": route["provider"], "model": route["model"]}
                    return content, usage
            except Exception as e:
                print(f"  [Warning] {route['provider']}/{route['model']} attempt {attempt}: {e}")
                time.sleep(3)
    raise RuntimeError("All API routes exhausted.")


SYSTEM_PROMPT = (
    "You are a formal-methods analyst specializing in Lean 4 proof assistant code. "
    "You analyze .lean files and explain exactly what they prove, what they assume, "
    "and what they do NOT prove. You identify negative results (countermodels, "
    "ablated premises, failed theorems) as valuable discipline evidence. "
    "You write in two registers: plain English first (for everyday readers), "
    "then technical detail (for mathematicians/physicists). "
    "You output in the exact format specified by the template. "
    "Do not editorialize. Do not praise. Do not speculate beyond the code."
)

def append_ledger_row(row: dict):
    """Append one row to the TSV ledger."""
    values = [str(row.get(col, "")) for col in LEDGER_COLUMNS]
    line = "\t".join(values) + "\n"
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(line)

def process_lean_file(lean_path: Path, run_id: str, provider: str, model: str | None) -> dict:
    """Process one .lean file through the Lane 4 template."""
    print(f"\n  Processing: {lean_path.name}")
    start = time.time()

    lean_code = lean_path.read_text(encoding="utf-8", errors="replace")
    file_sha = get_sha256(lean_path)
    template = load_template()

    prompt = f"""LEAN 4 FILE TO ANALYZE:
Filename: {lean_path.name}
SHA-256: {file_sha}

```lean
{lean_code}
```

TEMPLATE (follow this format exactly — every section, in order):
{template}

OUTPUT the filled template now. Do not skip any section.
At the end, output a JSON block with key "ledger_rows" containing
an array of objects, one per formal result (theorem, countermodel,
ablation, negative control), each with these fields:
  theorem_name, result_type, one_line_plain, one_line_technical,
  proves, does_not_prove, axiom_dependency, non_vacuous,
  papers_affected, contested_claims_hit, claim_verdict, trust_level
"""

    result_text, usage = call_api(prompt, SYSTEM_PROMPT, max_tokens=8192,
                                   provider=provider, model=model)
    elapsed = round(time.time() - start, 2)
    route = usage.get("_route", {})
    used_provider = route.get("provider", "unknown")
    used_model = route.get("model", "unknown")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Save markdown result to WORKING
    working_file = WORKING_DIR / f"{lean_path.stem}_LANE4_RESULT.md"
    working_file.write_text(result_text, encoding="utf-8")

    # Save to ARCHIVE (with timestamp, never edited)
    archive_subdir = ARCHIVE_DIR / f"{lean_path.stem}_{timestamp[:10]}"
    archive_subdir.mkdir(parents=True, exist_ok=True)
    (archive_subdir / f"{lean_path.stem}_LANE4_RESULT.md").write_text(result_text, encoding="utf-8")
    shutil.copy2(str(lean_path), str(archive_subdir / lean_path.name))

    # Try to extract JSON ledger rows from the output
    ledger_rows_logged = 0
    json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', result_text)
    if not json_match:
        json_match = re.search(r'"ledger_rows"\s*:\s*\[[\s\S]*?\]', result_text)

    if json_match:
        try:
            raw_json = json_match.group(0)
            if not raw_json.startswith("{"):
                raw_json = "{" + raw_json + "}"
            parsed = json.loads(raw_json)
            rows = parsed.get("ledger_rows", [])
            for row in rows:
                ledger_entry = {
                    "result_id": f"{lean_path.stem}-{row.get('theorem_name', 'unknown')}-{timestamp[:10].replace('-', '')}",
                    "timestamp": timestamp,
                    "lean_file": lean_path.name,
                    "lean_file_sha256": file_sha,
                    "theorem_name": row.get("theorem_name", ""),
                    "result_type": row.get("result_type", "THEOREM_PASS"),
                    "one_line_plain": row.get("one_line_plain", ""),
                    "one_line_technical": row.get("one_line_technical", ""),
                    "proves": row.get("proves", ""),
                    "does_not_prove": row.get("does_not_prove", ""),
                    "axiom_dependency": row.get("axiom_dependency", "Lean standard only"),
                    "non_vacuous": row.get("non_vacuous", ""),
                    "papers_affected": row.get("papers_affected", ""),
                    "contested_claims_hit": row.get("contested_claims_hit", "NONE"),
                    "claim_verdict": row.get("claim_verdict", "NOT_ADDRESSED"),
                    "supersedes": "NONE",
                    "trust_level": row.get("trust_level", "MEDIUM"),
                    "provider": used_provider,
                    "model": used_model,
                    "run_id": run_id
                }
                append_ledger_row(ledger_entry)
                ledger_rows_logged += 1
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [Warning] Could not parse ledger JSON from output: {e}")

    # Save JSON result
    json_result = {
        "lean_file": lean_path.name,
        "file_sha256": file_sha,
        "timestamp": timestamp,
        "provider": used_provider,
        "model": used_model,
        "elapsed_seconds": elapsed,
        "ledger_rows_logged": ledger_rows_logged,
        "markdown_path": str(working_file),
        "archive_path": str(archive_subdir)
    }
    json_file = WORKING_DIR / f"{lean_path.stem}_LANE4_RESULT.json"
    json_file.write_text(json.dumps(json_result, indent=2), encoding="utf-8")

    print(f"  Done: {lean_path.name} | {elapsed}s | {ledger_rows_logged} ledger rows")
    return json_result


def collect_lean_files(single_file: str | None = None) -> list[Path]:
    """Collect .lean files to process."""
    files = []
    if single_file:
        p = Path(single_file)
        if p.exists():
            files.append(p)
        else:
            # Try relative to LEAN4 dir
            for search in [LEAN_THEOREMS_DIR, LEAN_INBOX_DIR, LEAN4_DIR]:
                candidate = search / single_file
                if candidate.exists():
                    files.append(candidate)
                    break
        return files

    # Collect from Theorems dir (per-paper files)
    if LEAN_THEOREMS_DIR.exists():
        files.extend(sorted(LEAN_THEOREMS_DIR.glob("*.lean")))

    # Collect from INBOX (new files)
    if LEAN_INBOX_DIR.exists():
        files.extend(sorted(LEAN_INBOX_DIR.glob("*.lean")))

    return files

def main():
    parser = argparse.ArgumentParser(description="Lane 4: Formal Proof Breakdown Engine")
    parser.add_argument("--file", type=str, default=None,
                        help="Process a single .lean file (name or path)")
    parser.add_argument("--provider", type=str, default="auto",
                        choices=["auto", "deepseek", "openrouter"],
                        help="API provider preference")
    parser.add_argument("--model", type=str, default=None,
                        help="Model override (e.g. deepseek/deepseek-r1:free)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List files without processing")
    args = parser.parse_args()

    ensure_dirs()
    run_id = f"lane4_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    print("=" * 60)
    print("LANE 4: FORMAL PROOF BREAKDOWN ENGINE v1.0")
    print(f"Run ID: {run_id}")
    print(f"Provider: {args.provider} | Model: {args.model or 'default'}")
    print(f"Lean dir: {LEAN4_DIR}")
    print(f"Ledger: {LEDGER_FILE}")
    print("=" * 60)

    files = collect_lean_files(args.file)
    print(f"\nFound {len(files)} .lean file(s) to process.")

    if not files:
        print("No .lean files found. Place files in LEAN4/FaithThruPhysics/Theorems/ or LEAN4/INBOX/")
        return 0

    if args.dry_run:
        for f in files:
            print(f"  [DRY RUN] Would process: {f.name}")
        return 0

    results = []
    errors = 0
    for i, lean_file in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] {lean_file.name}")
        try:
            result = process_lean_file(lean_file, run_id, args.provider, args.model)
            results.append(result)
        except Exception as e:
            errors += 1
            print(f"  [ERROR] {lean_file.name}: {e}")
            log_file = LOGS_DIR / f"lane4_error_{lean_file.stem}_{int(time.time())}.log"
            import traceback
            log_file.write_text(traceback.format_exc(), encoding="utf-8")

    # Summary
    total_ledger = sum(r.get("ledger_rows_logged", 0) for r in results)
    print("\n" + "=" * 60)
    print(f"LANE 4 COMPLETE")
    print(f"  Files processed: {len(results)}")
    print(f"  Errors: {errors}")
    print(f"  Ledger rows appended: {total_ledger}")
    print(f"  Working dir: {WORKING_DIR}")
    print(f"  Archive dir: {ARCHIVE_DIR}")
    print(f"  Ledger: {LEDGER_FILE}")
    print("=" * 60)

    # Write run summary
    summary = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_processed": len(results),
        "errors": errors,
        "ledger_rows_total": total_ledger,
        "results": results
    }
    summary_file = WORKING_DIR / f"RUN_SUMMARY_{run_id}.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
