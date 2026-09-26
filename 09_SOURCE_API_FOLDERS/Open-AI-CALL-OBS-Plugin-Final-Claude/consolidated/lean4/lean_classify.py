#!/usr/bin/env python3
"""
lean_classify.py — LLM-powered classification for LEAN_FLOOR OUTBOX

Uses provider_chain.py (OpenRouter free → DeepSeek fallback).
Classifies Lean results into the locked 12-domain / 30-topic / 6-role taxonomy.
Sorts into OUTBOX subfolders. Writes manifest.

Usage:
    python lean_classify.py                   # classify everything in OUTBOX
    python lean_classify.py --verified-only   # only 00_VERIFIED_RECEIPTS
"""
from __future__ import annotations
import csv, json, os, re, shutil, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from provider_chain import llm_call, current_provider, current_model

LEAN_ROOT = SCRIPT_DIR.parent.parent  # LEAN_FLOOR
OUTBOX = LEAN_ROOT / "OUTBOX"
LOGS = LEAN_ROOT / "OUTBOX" / "05_RESULTS_BY_FORMAL_STATUS" 
LOGS.mkdir(parents=True, exist_ok=True)

# ── Locked taxonomy (same as Evidence Chain) ──
APPROVED_DOMAINS = [
    "01_THEOLOGY", "02_BIBLICAL_STUDIES", "03_PHILOSOPHY", "04_ETHICS",
    "05_MATHEMATICS_AND_LOGIC", "06_PHYSICS", "07_INFORMATION_AND_SYSTEMS",
    "08_BIOLOGY_AND_LIFE", "09_MIND_AND_BEHAVIOR", "10_COMPUTING_AND_ENGINEERING",
    "11_HISTORY_AND_SOCIETY", "12_RESEARCH_METHODS_AND_KNOWLEDGE",
]
APPROVED_TOPICS = [
    "god-as-root", "trinity", "logos-and-christ", "creation-and-origins",
    "divine-attributes", "truth-and-knowledge", "love-and-relationship",
    "grace-and-repair", "justice-and-mercy", "evil-and-deception",
    "freedom-and-agency", "fruits-and-virtue", "salvation-and-resurrection",
    "consciousness-and-observers", "measurement", "time-and-causality",
    "information-and-meaning", "entropy-and-decay", "coherence-and-order",
    "life-and-carbon", "axiom-chain", "master-equation", "ten-laws",
    "isomorphism-and-duality", "formal-verification", "scripture-and-typology",
    "worldviews-and-objections", "institutions-and-culture",
    "corpus-and-canon", "ai-and-automation",
]
APPROVED_ROLES = [
    "01_ARGUMENT", "02_FORMALIZATION", "03_EVIDENCE_AND_SOURCES",
    "04_AUDIT_AND_OBJECTIONS", "05_EXPLANATION_AND_STORY", "06_METHOD_AND_TOOLS",
]

SYSTEM_PROMPT = f"""You are a document classifier for the Theophysics Research Initiative (POF 2828).

Given a Lean 4 formal verification file or its companion document, assign:

1. PRIMARY_DOMAIN: one from {json.dumps(APPROVED_DOMAINS)}
2. SECONDARY_DOMAINS: zero to two more from the same list
3. TOPICS: one to five from {json.dumps(APPROVED_TOPICS)}
4. PRIMARY_ROLE: one from {json.dumps(APPROVED_ROLES)}
5. LEAN_STATUS: one of VERIFIED (compiles, zero sorry), PARTIAL (compiles with sorry), UNTESTED, NOT_LEAN
6. TITLE: a clean human-readable title for this document

Respond ONLY with a JSON object. No markdown, no explanation. Example:
{{"primary_domain":"05_MATHEMATICS_AND_LOGIC","secondary_domains":["01_THEOLOGY"],"topics":["formal-verification","trinity"],"primary_role":"02_FORMALIZATION","lean_status":"VERIFIED","title":"Trinity Three-Person Isomorphism Proof"}}

If you cannot classify, respond: {{"error":"reason"}}
Choose ONLY from the approved lists. Do not invent categories."""


OUT_DOMAIN = OUTBOX / "01_BY_DOMAIN"
OUT_TOPIC  = OUTBOX / "02_BY_TOPIC"
OUT_ROLE   = OUTBOX / "03_BY_ROLE"
OUT_STATUS = OUTBOX / "04_BY_LEAN_STATUS"
OUT_VERIFIED = OUTBOX / "00_VERIFIED_RECEIPTS"


def scan_lean_files(verified_only: bool = False) -> list[Path]:
    seen: dict[str, Path] = {}
    scan = [OUT_VERIFIED] if verified_only else [OUTBOX]
    for d in scan:
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.suffix in (".lean", ".md") and not f.name.startswith("."):
                key = f.name.lower()
                if key not in seen:
                    seen[key] = f
    return sorted(seen.values(), key=lambda p: p.name.lower())


def safe_copy(src: Path, dst: Path) -> bool:
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"  WARN: {src.name} -> {dst}: {e}")
        return False


def classify_file(f: Path) -> dict[str, Any]:
    try:
        text = f.read_text(encoding="utf-8", errors="replace")[:6000]
    except Exception:
        text = f.name
    try:
        raw = llm_call(SYSTEM_PROMPT, f"Filename: {f.name}\n\nContent:\n{text}")
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
        if "error" in result:
            return {"file": f.name, "source": str(f), "error": result["error"]}
    except Exception as e:
        return {"file": f.name, "source": str(f), "error": str(e)[:200]}

    return {
        "file": f.name,
        "source": str(f),
        "title": result.get("title", f.stem),
        "primary_domain": result.get("primary_domain", "_uncategorized"),
        "secondary_domains": result.get("secondary_domains", []),
        "topics": result.get("topics", []),
        "primary_role": result.get("primary_role", "_uncategorized"),
        "lean_status": result.get("lean_status", "UNTESTED"),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--verified-only", action="store_true")
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"  LEAN FLOOR CLASSIFIER — POF 2828")
    print(f"  Provider: {current_provider()} / {current_model()}")
    print(f"{'='*70}\n")

    for d in [OUT_DOMAIN, OUT_TOPIC, OUT_ROLE, OUT_STATUS]:
        d.mkdir(parents=True, exist_ok=True)

    files = scan_lean_files(args.verified_only)
    print(f"  Found {len(files)} files to classify.\n")
    if not files:
        return 0

    manifest: list[dict] = []
    ok = err = 0

    for i, f in enumerate(files, 1):
        print(f"  [{i}/{len(files)}] {f.name}...", end=" ", flush=True)
        rec = classify_file(f)
        manifest.append(rec)

        if "error" in rec:
            print(f"ERROR: {rec['error'][:80]}")
            err += 1
            continue

        # Sort into folders
        for dom in [rec["primary_domain"]] + rec.get("secondary_domains", []):
            safe_copy(f, OUT_DOMAIN / dom / f.name)
        for top in rec.get("topics", []):
            safe_copy(f, OUT_TOPIC / top / f.name)
        safe_copy(f, OUT_ROLE / rec["primary_role"] / f.name)
        safe_copy(f, OUT_STATUS / rec["lean_status"] / f.name)

        print(f"{rec['lean_status']} | {rec['primary_domain']}")
        ok += 1

    # Write manifest
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    mf = LOGS / f"lean_classify_{ts}.json"
    mf.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    cf = LOGS / f"lean_classify_{ts}.csv"
    with open(cf, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "title", "primary_domain", "topics",
                     "primary_role", "lean_status"])
        for r in manifest:
            if "error" not in r:
                w.writerow([r["file"], r.get("title",""), r["primary_domain"],
                            "; ".join(r.get("topics",[])), r["primary_role"],
                            r["lean_status"]])

    dc, tc, sc = Counter(), Counter(), Counter()
    for r in manifest:
        if "error" not in r:
            dc[r["primary_domain"]] += 1
            for t in r.get("topics",[]): tc[t] += 1
            sc[r["lean_status"]] += 1

    print(f"\n{'='*70}")
    print(f"  DONE — {ok} classified, {err} errors")
    print(f"  Provider: {current_provider()} / {current_model()}")
    print(f"{'='*70}")
    print("\n  DOMAINS:")
    for k,v in dc.most_common(): print(f"    {k:40s} {v}")
    print("\n  LEAN STATUS:")
    for k,v in sc.most_common(): print(f"    {k:20s} {v}")
    print("\n  TOP TOPICS:")
    for k,v in tc.most_common(10): print(f"    {k:40s} {v}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
