#!/usr/bin/env python3
"""
nlp_multimethod_router.py - Multi-Method NLP Dispatcher & Dossier Generator
===========================================================================
Lenses Supported:
  - Lens 1: THEOPHYSICS (Formal Epistemic, Triune Ontology, Master Equation, 10-Law Rubric)
  - Lens 2: INVESTIGATION (Forensic Timeline, Actor/Entity Network, Anomalies, Contradictions)
  - Lens 3: DYNAMICS / CROSS-DOMAIN (Coherence Metric dC/dt, SEM/SOM/EDU Entropies, Collapse Signatures)

Designed for David Lowe's Theophysics Vault & Brain pipeline ecosystem.
100% self-relative path resolution.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ============================================================
# PATH RESOLUTION (100% Self-Relative)
# ============================================================
HERE = Path(__file__).resolve().parent
WORKFLOW_ROOT = HERE.parent if HERE.name.lower() == "scripts" else HERE
INBOX = WORKFLOW_ROOT / "INBOX"
OUTBOX = WORKFLOW_ROOT / "OUTBOX"
PROCESSED = WORKFLOW_ROOT / "PROCESSED"
LOGS = WORKFLOW_ROOT / "LOGS"

for d in (INBOX, OUTBOX, PROCESSED, LOGS):
    d.mkdir(parents=True, exist_ok=True)

# Lexicon Intake Path
VAULT_INTAKE_CSV = Path(r"Z:\Theophysics_Vault\07_System_and_Operations\AG_Lexicon_Intake\AG_SORTING_TERMS_INTAKE.csv")

# ============================================================
# LOGGING
# ============================================================
def log(msg: str) -> None:
    stamp = datetime.now().isoformat(timespec="seconds")
    line = f"[{stamp}] {msg}"
    print(line)
    try:
        log_file = LOGS / f"nlp_router_{datetime.now():%Y%m%d}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ============================================================
# LEXICON INTAKE HELPER
# ============================================================
def record_lexicon_terms(terms: list[dict[str, str]]) -> None:
    if not terms or not VAULT_INTAKE_CSV.parent.exists():
        return
    try:
        write_header = not VAULT_INTAKE_CSV.exists()
        with open(VAULT_INTAKE_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "term", "category", "pattern_used", "source_folder",
                    "source_file", "confidence", "reason", "proposed_sheet", "status"
                ])
            for t in terms:
                writer.writerow([
                    t.get("term", ""),
                    t.get("category", ""),
                    t.get("pattern_used", ""),
                    t.get("source_folder", ""),
                    t.get("source_file", ""),
                    t.get("confidence", "0.9"),
                    t.get("reason", "nlp_router_discovery"),
                    t.get("proposed_sheet", "Lexicon"),
                    "candidate"
                ])
    except Exception as e:
        log(f"Notice: Could not write to Lexicon intake: {e}")

# ============================================================
# LLM CLIENT (DeepSeek API with heuristic fallback)
# ============================================================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()

def call_llm(prompt: str, system_prompt: str, max_tokens: int = 4000, temperature: float = 0.2) -> str:
    if not DEEPSEEK_API_KEY:
        log("WARN: DEEPSEEK_API_KEY not found. Running in heuristic mode.")
        return ""
    
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
    except Exception as exc:
        log(f"LLM Call Error: {exc}")
        return ""

# ============================================================
# ROUTING & CLASSIFICATION LOGIC
# ============================================================
def inspect_header_and_lens(content: str) -> tuple[str, str]:
    """
    Returns (lens_name, clean_content).
    Lenses: THEOPHYSICS | INVESTIGATION | DYNAMICS
    """
    first_few_lines = [l.strip() for l in content.splitlines()[:10] if l.strip()]
    header_str = " ".join(first_few_lines).upper()

    # 1. Explicit Header Override
    if any(k in header_str for k in ["NLP: THEOPHYSICS", "NLP:THEOPHYSICS", "NLP: THEO", "NLP: AXIOM", "NLP: LOGOS"]):
        return "THEOPHYSICS", content
    if any(k in header_str for k in ["NLP: INVESTIGATION", "NLP:INVESTIGATION", "NLP: DOSSIER", "NLP: CONSPIRACY", "NLP: FORENSIC"]):
        return "INVESTIGATION", content
    if any(k in header_str for k in ["NLP: DYNAMICS", "NLP:DYNAMICS", "NLP: CROSS-DOMAIN", "NLP: COHERENCE", "NLP: COLLAPSE", "NLP: CDC"]):
        return "DYNAMICS", content

    # 2. Content Heuristics / Keyword scoring
    text_lower = content.lower()
    
    # Keyword scores
    theo_words = ["theophysics", "master equation", "landauer", "triune", "christ", "logos", "god", "theology", "grace", "ontology", "axiom"]
    invest_words = ["charlie kirk", "candace", "shooter", "suspect", "fbi", "police", "surveillance", "alibi", "witness", "assassination", "investigation", "turning point", "tpusa", "tyler robinson"]
    dyn_words = ["entropy", "coherence", "phase transition", "collapse", "somatic", "semantic entropy", "institutional trust", "attractor", "thermodynamic", "dC/dt"]

    theo_score = sum(text_lower.count(w) for w in theo_words)
    invest_score = sum(text_lower.count(w) for w in invest_words) * 1.5
    dyn_score = sum(text_lower.count(w) for w in dyn_words) * 1.2

    log(f"Auto-classification scores: THEOPHYSICS={theo_score}, INVESTIGATION={invest_score}, DYNAMICS={dyn_score}")

    if invest_score > theo_score and invest_score > dyn_score and invest_score >= 5:
        return "INVESTIGATION", content
    if dyn_score > theo_score and dyn_score >= 5:
        return "DYNAMICS", content
    if theo_score >= 3:
        return "THEOPHYSICS", content

    # Default fallback for podcasts / speech transcripts
    if "candace" in text_lower or "kirk" in text_lower or "interview" in text_lower or "show" in text_lower:
        return "INVESTIGATION", content

    return "THEOPHYSICS", content

# ============================================================
# LENS 1: THEOPHYSICS PROMPT
# ============================================================
SYSTEM_THEOPHYSICS = """You are the Lead Epistemic Auditor for Theophysics and the Consilience Atlas.
Your goal is to parse the input text and extract formal theophysical propositions, mathematical invariants, and ontological alignments.

Output a comprehensive, rigorous Markdown Dossier with these exact sections:
# THEOPHYSICAL EPISTEMIC DOSSIER: [Document Title]

## 1. Executive Summary & Foundational Ontology
- Core Triune alignment (Father/Field, Logos/Form-Coherence, Spirit/Grace-Action)
- Epistemic Truth Kernel status

## 2. Mathematical & Formal Invariants
- Master Equation relations identified (dC/dt = O * G(1-C) - S * C, Landauer bound, Noether charge, conservation)
- Information-theoretic or thermodynamic mappings

## 3. Load-Bearing Claims & 10-Rubric Evaluation
Extract key claims with scores (1-10) for:
- Mathematical Rigor
- Internal Consistency
- Empirical Anchoring
- Falsifiability
- Theological Orthodoxy

## 4. Quoted Anchors & Verbatim Evidence
List 5-10 exact verbatim quotes from the source text that support the evaluation.

## 5. Lexicon & Emerging Axiomatic Terms
List key terminology in table format: | Term | Category | Definition | Proposed Action |
"""

# ============================================================
# LENS 2: INVESTIGATION PROMPT
# ============================================================
SYSTEM_INVESTIGATION = """You are a Master Forensic Intelligence Analyst and Investigative Dossier Creator.
Your job is to analyze real-world investigative transcripts, speeches, or investigative journalism (e.g. Candace Owens on Charlie Kirk events, institutional cover-ups, geopolitical anomalies).

You MUST extract and reconstruct the objective timeline, identify all actors, map power/money pressure flows, catalog contradictions, and isolate anomalies.

Output a rigorous, clear Markdown Intelligence Dossier with these exact sections:
# INVESTIGATIVE DOSSIER: [Subject / Episode Title]

## 1. Executive Summary
- Primary Investigative Hypothesis
- High-level finding & confidence rating

## 2. Forensic Timeline (Chronological Reconstruction)
Reconstruct all specific times, dates, and sequences mentioned in the source (e.g., timestamps, departure times, phone calls, announcements).
Format as:
- **[Time / Date]**: [Event Description] | *Source Quote / Reference*

## 3. Key Actors & Power-Network Matrix
Map all individuals, organizations, and entities mentioned:
| Entity / Actor | Affiliation / Role | Actions / Assertions | Motive / Pressure Vectors |
| --- | --- | --- | --- |

## 4. Official Narrative vs. Speaker Claims (Contradiction Grid)
| Issue / Event | Official Account | Source / Speaker Assertion | Evidence / Conflict Analysis |
| --- | --- | --- | --- |

## 5. Unresolved Anomalies & Falsification Checklist
- What questions remain completely unanswered?
- What testable factual evidence (e.g. flight logs, phone records, CCTV) would prove or disprove the claims?

## 6. Key Quoted Anchors (Verbatim Evidence)
Provide 5-10 verbatim quotes with exact spoken language for evidentiary citation.

## 7. Emerging Entities & Terms for Lexicon
List any new code names, groups, or phrases in table format: | Term | Category | Context |
"""

# ============================================================
# LENS 3: CROSS-DOMAIN COHERENCE PROMPT
# ============================================================
SYSTEM_CROSS_DOMAIN = """You are the Senior Systems Theorist for the Cross-Domain Coherence Project.
Your framework models civilizational and systemic collapse using the invariant equation:
dC/dt = O * G(1 - C) - S * C
and the Coherence Metric: chi = Integral(Psi x Phi x Lambda dV), where Psi is consciousness/intent, Phi is physical action, and Lambda is structural constraint.

Analyze the input text through the lens of Triadic Invariant Entropy:
1. Semantic Entropy (SEM) - decay of shared vocabulary and truthful meaning
2. Somatic Entropy (SOM) - biological, neural, and physical degradation
3. Educational / Institutional Entropy (EDU) - breakdown of knowledge transmission and trust

Output a structured Markdown Dossier with these exact sections:
# CROSS-DOMAIN COHERENCE AUDIT: [Title]

## 1. Systemic Diagnosis & Phase State
- System Coherence State (Coherent, Metasynchronous, Degraded, Critical Collapse)
- Dominant Entropy Driver (SEM, SOM, or EDU)

## 2. Invariant Dynamic Equation Analysis
- Identification of Observer term (O), Grace/External Negentropy (G), and Dissipative Entropy (S)
- Quantification/Trajectory of dC/dt

## 3. The Triadic Entropy Breakdown
- **Semantic Entropy (SEM)**: Language manipulation, euphemisms, loss of consensus reality
- **Somatic Entropy (SOM)**: Physical impacts, stress, health, violence
- **Institutional / Education Entropy (EDU)**: Institutional betrayal, loss of trust, transmission failure

## 4. Actionable Restorative Levers (Negentropic Injections)
How can external coherence (G) be restored to halt system decay?

## 5. Verbatim Empirical Anchors
Direct quotes from the source demonstrating the dynamics.
"""

# ============================================================
# RUN PROCESSOR ON FILE
# ============================================================
def process_file(file_path: Path, force_lens: str | None = None) -> Path:
    log(f"Processing input file: {file_path.name}")
    raw_text = file_path.read_text(encoding="utf-8", errors="replace")
    
    # Determine Lens
    if force_lens:
        lens = force_lens.upper()
    else:
        lens, _ = inspect_header_and_lens(raw_text)
    
    log(f"Routed to Lens: [{lens}]")

    # Select system prompt
    if lens == "INVESTIGATION":
        sys_prompt = SYSTEM_INVESTIGATION
    elif lens == "DYNAMICS":
        sys_prompt = SYSTEM_CROSS_DOMAIN
    else:
        sys_prompt = SYSTEM_THEOPHYSICS

    # Send first 24,000 characters to DeepSeek (plenty for high-density extraction)
    sample_text = raw_text[:28000]
    prompt = f"Analyze the following source document according to your required format:\n\n=== SOURCE TEXT START ===\n{sample_text}\n=== SOURCE TEXT END ==="

    dossier_text = call_llm(prompt, sys_prompt)

    # Heuristic fallback if API key is missing or call failed
    if not dossier_text:
        dossier_text = f"# {lens} AUDIT: {file_path.stem}\n\n*Heuristic Mode (No LLM response)*\n\nTotal length: {len(raw_text)} chars.\n\n### Source Excerpt\n```\n{raw_text[:2000]}\n```"

    # Build output artifact
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"DOSSIER_{lens}_{stamp}_{file_path.stem}.md"
    out_file = OUTBOX / out_name

    full_output = f"""---
lens: "{lens}"
source_file: "{file_path.name}"
processed_at: "{datetime.now(timezone.utc).isoformat()}"
char_count: {len(raw_text)}
router_version: "1.0.0"
---

{dossier_text}

---
<details>
<summary><b>Source Information & Provenance</b></summary>

- **Original File:** `{file_path.name}`
- **MD5:** `{hashlib.md5(raw_text.encode('utf-8')).hexdigest()}`
- **Processed By:** `NLPRouter (Lens: {lens})`
</details>
"""
    out_file.write_text(full_output, encoding="utf-8")
    log(f"Generated output dossier: {out_file}")

    # Extract any emerging terms table to record in lexicon
    emerging_terms = []
    for line in dossier_text.splitlines():
        if "|" in line and not line.strip().startswith("| ---"):
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if len(cols) >= 2 and cols[0].lower() not in ("term", "entity / actor", "entity"):
                emerging_terms.append({
                    "term": cols[0],
                    "category": cols[1] if len(cols) > 1 else lens,
                    "pattern_used": f"lens_{lens.lower()}",
                    "source_folder": str(file_path.parent),
                    "source_file": file_path.name,
                })
    if emerging_terms:
        record_lexicon_terms(emerging_terms[:10])

    return out_file

# ============================================================
# MAIN DISPATCHER
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Multi-Method NLP Router")
    parser.add_argument("--file", "-f", help="Direct path to input file to process")
    parser.add_argument("--lens", "-l", choices=["THEOPHYSICS", "INVESTIGATION", "DYNAMICS"], help="Force specific NLP lens")
    parser.add_argument("--sweep-inbox", action="store_true", help="Process all files in INBOX/")
    args = parser.parse_args()

    if args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"Error: File not found: {p}")
            sys.exit(1)
        res = process_file(p, force_lens=args.lens)
        print(f"\n[SUCCESS] Dossier generated: {res}")
        return

    # Sweep INBOX (check local INBOX first, then check parent _inbox if present)
    target_inbox = INBOX
    inputs = [p for p in target_inbox.iterdir() if p.is_file() and not p.name.startswith(".")]
    
    parent_inbox = WORKFLOW_ROOT.parent / "_inbox"
    if not inputs and parent_inbox.exists() and parent_inbox.is_dir():
        parent_inputs = [p for p in parent_inbox.iterdir() if p.is_file() and not p.name.startswith(".")]
        if parent_inputs:
            log(f"Found {len(parent_inputs)} inputs in Front Door _inbox: {parent_inbox}")
            target_inbox = parent_inbox
            inputs = parent_inputs

    if not inputs:
        print(f"No files found to process.")
        print(f"  Checked: {INBOX}")
        if parent_inbox.exists():
            print(f"  Checked: {parent_inbox}")
        print("Drop files into either inbox or run with: python nlp_multimethod_router.py --file <path>")
        return

    for inp in inputs:
        try:
            res = process_file(inp, force_lens=args.lens)
            # Move to PROCESSED
            shutil.move(str(inp), str(PROCESSED / inp.name))
            print(f"Finished {inp.name} -> {res.name}")
        except Exception as e:
            log(f"Failed processing {inp.name}: {e}")

if __name__ == "__main__":
    main()
