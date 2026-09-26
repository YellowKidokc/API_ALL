"""
SERIES GRAND SYNTHESIZER (v0.5)
===============================
Aggregates all individual paper companions in a series into a single, unified,
comprehensive Master Series Paper / Grand Narrative Overview.

Workflow:
1. Gathers all companions for a given series from OUTBOX/BY_SERIES/<SeriesName> or OUTBOX/FOR_SUBSTACK.
2. Extracts each chapter's:
   - Core Finding & Axiom
   - Section-by-section argument progression
   - Truth Predicates
   - Mathematical Formulations & Master Equation variables
   - 4-Step Systemic Advantage
3. Passes the full structured corpus to the LLM to braid into ONE cohesive Master Series Paper.
4. Generates:
   - OUTBOX/BY_SERIES/<SeriesName>/<SeriesName>_GRAND_SYNTHESIS_MASTER_PAPER.md
   - OUTBOX/FOR_SUBSTACK/<SeriesName>_COMPLETE_SERIES_OVERVIEW.md
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
OUTBOX_DIR = ROOT_DIR / "OUTBOX"
SERIES_OUT_DIR = OUTBOX_DIR / "BY_SERIES"
SUBSTACK_OUT_DIR = OUTBOX_DIR / "FOR_SUBSTACK"

SYSTEM_SYNTHESIS_PROMPT = (
    "You are the Master Intellectual Co-Author and Grand Architect of Faith Through Physics. "
    "Your mission is to synthesize an ENTIRE MULTI-CHAPTER SERIES into ONE UNIFIED, COMPREHENSIVE MASTER PAPER. "
    "Do NOT produce a superficial high-level summary. Weave a rigorous, exhaustive, chapter-by-chapter intellectual narrative "
    "that preserves every major axiom, truth predicate, mathematical operator, and physical-theological bridge. "
    "Connect the entire 20-chapter arc into a singular, unassailable, logically air-tight masterwork."
)

def call_llm(prompt: str, system_prompt: str, provider: str = "openrouter", model: str | None = None) -> str:
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()

    routes = []
    if provider in ("openrouter", "auto") and openrouter_key:
        routes.append({
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "model": model or "google/gemini-2.5-flash",
            "headers": {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://faiththruphysics.com",
                "X-OpenRouter-Title": "Faith Through Physics Grand Synthesizer"
            }
        })
    if provider in ("deepseek", "auto") and deepseek_key:
        routes.append({
            "url": "https://api.deepseek.com/chat/completions",
            "model": model or "deepseek-chat",
            "headers": {
                "Authorization": f"Bearer {deepseek_key}",
                "Content-Type": "application/json"
            }
        })
    if openai_key:
        routes.append({
            "url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4o",
            "headers": {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
        })

    if not routes:
        raise RuntimeError("No API keys found for Grand Synthesizer.")

    for route in routes:
        payload = {
            "model": route["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 8192
        }
        for attempt in range(1, 3):
            try:
                resp = requests.post(route["url"], json=payload, headers=route["headers"], timeout=180)
                resp.raise_for_status()
                res = resp.json()
                choices = res.get("choices") or []
                if choices:
                    return choices[0].get("message", {}).get("content", "")
            except Exception as e:
                print(f"[Warning] Synthesizer route {route['model']} attempt {attempt} failed: {e}")
                time.sleep(2)

    raise RuntimeError("All routes failed for Grand Synthesizer.")

def extract_companion_summary(filepath: Path) -> dict[str, Any]:
    text = filepath.read_text(encoding="utf-8", errors="replace")
    
    # Extract title
    title_m = re.search(r'title:\s*["\']?([^"\n\r]+)["\']?', text)
    title = title_m.group(1).strip() if title_m else filepath.stem

    # Extract clean title
    clean_title_m = re.search(r'clean_title:\s*["\']?([^"\n\r]+)["\']?', text)
    clean_title = clean_title_m.group(1).strip() if clean_title_m else title

    # Extract finding
    finding_m = re.search(r'one_sentence_finding:\s*["\']?([^"\n\r]+)["\']?', text)
    finding = finding_m.group(1).strip() if finding_m else ""

    # Extract score
    score_m = re.search(r'paper_rating:\s*([0-9\.]+)', text)
    score = score_m.group(1) if score_m else "7.0"

    # Extract The Six block
    the_six = ""
    the_six_m = re.search(r'(## The Six[\s\S]*?)(?=## S01|\Z)', text)
    if the_six_m:
        the_six = the_six_m.group(1).strip()

    # Extract Math & Physics Layer
    math_layer = ""
    math_m = re.search(r'(## S07 · Formal & Math[\s\S]*?)(?=## S08|\Z)', text)
    if math_m:
        math_layer = math_m.group(1).strip()

    # Extract Translation Table
    bridge_layer = ""
    bridge_m = re.search(r'(## S08 · Bridge Integrity[\s\S]*?)(?=## S09|\Z)', text)
    if bridge_m:
        bridge_layer = bridge_m.group(1).strip()

    # Extract Truth Predicates Table
    predicates = ""
    pred_m = re.search(r'(\| P# \|[\s\S]*?)(?=\n\n|\Z)', text)
    if pred_m:
        predicates = pred_m.group(1).strip()

    return {
        "filename": filepath.name,
        "clean_title": clean_title,
        "score": score,
        "finding": finding,
        "the_six": the_six,
        "math_layer": math_layer,
        "bridge_layer": bridge_layer,
        "predicates": predicates,
        "full_text_sample": text[:3500]
    }

def synthesize_series(series_name: str, provider: str = "openrouter", model: str | None = None) -> Path:
    print(f"\n=======================================================")
    print(f"GRAND SYNTHESIS ENGINE: Synthesizing Series [{series_name}]")
    print(f"=======================================================\n")

    # 1. Collect all companion files
    series_dir = SERIES_OUT_DIR / series_name
    substack_dir = SUBSTACK_OUT_DIR
    companion_files = []

    if series_dir.exists():
        companion_files = [f for f in series_dir.glob("*.md") if not f.name.startswith("00_") and "GRAND_SYNTHESIS" not in f.name]

    if not companion_files and substack_dir.exists():
        companion_files = [f for f in substack_dir.glob("*.md") if "COMPLETE_SERIES" not in f.name]

    if not companion_files:
        raise FileNotFoundError(f"No companion files found for series '{series_name}'.")

    # Sort files naturally
    companion_files = sorted(companion_files, key=lambda p: p.name)
    print(f"Found {len(companion_files)} chapter companions in series.")

    # 2. Extract structured chapter dossiers
    chapters_data = []
    for cf in companion_files:
        cd = extract_companion_summary(cf)
        chapters_data.append(cd)
        print(f"  - Ingested Chapter: [[{cd['clean_title']}]] (Standing: +{cd['score']}/8.0)")

    # 3. Build synthesis prompt
    chapters_prompt_block = ""
    for i, ch in enumerate(chapters_data, 1):
        chapters_prompt_block += f"""
### CHAPTER {i}: [[{ch['clean_title']}]]
- **Standing:** +{ch['score']}/8.0
- **Core Finding:** {ch['finding']}
- **The Six / Differentiating Advantage:**
{ch['the_six']}
- **Truth Predicates:**
{ch['predicates']}
- **Formal Mathematics & Master Equation Mapping:**
{ch['math_layer']}
- **Cross-Domain Translation:**
{ch['bridge_layer']}
---
"""

    prompt = f"""You are writing the definitive, exhaustive GRAND SYNTHESIS MASTER PAPER for the complete series: "{series_name}".

TOTAL CHAPTERS IN ARC: {len(chapters_data)}

CHAPTER DOSSIERS TO BRAID:
{chapters_prompt_block}

REQUIREMENTS FOR THE MASTER SYNTHESIS PAPER:
Produce a monumental, publication-ready Master Paper in GitHub-Flavored Markdown that unites all {len(chapters_data)} chapters into a continuous intellectual narrative without leaving out essential insights.

STRUCTURE:
# 🌌 The Grand Synthesis: {series_name.replace('_', ' ').title()}
## A Complete, Braided Exposition of the Trinitarian Axiom, Physical Law, and Redemptive Teleology

### 0. Executive Consilience Preamble & Epistemic Contract
- State the Singular Root Axiom ($A_0$: "God Is") and the Primitive Truth Predicates ($P_0$).
- Explain how this multi-chapter arc solves the core problem of fragmentation between physics, metaphysics, and theology.

### 1. The Continuous Chapter-by-Chapter Arc (Exhaustive Narrative Journey)
- Provide a rigorous, interconnected walkthrough of all {len(chapters_data)} chapters in sequence.
- For EVERY chapter:
  - Formulate its exact contribution to the growing spine.
  - Explain what the previous chapter proved that this chapter relies upon.
  - Explain what new physical law, mathematical operator, or theological truth it introduces.
  - Include explicit Obsidian/Substack wikilinks `[[Chapter Title]]`.

### 2. Consolidated Master Equation & Mathematical Formalism
- Synthesize all mathematical variables ($G, M, E, S, T, K, R, Q, F, C$), negentropy flows ($-\Delta S$), tensor/operator dynamics, and Lean 4 invariant proofs introduced across the chapters into one Master Equation framework table and narrative.

### 3. Master Truth Predicates Consolidated Matrix
- Build a comprehensive Markdown table uniting the key truth predicates (P01 through P30+) across all chapters with their Logical Modality, Source Chapter, and Physical/Metaphysical Ground.

### 4. The 4-Step Total Systemic Advantage vs. Rival Worldviews
1. The Unique Move of Faith Through Physics across the whole 20-chapter arc.
2. Where Rival Frameworks Collapse (Materialism, Deism, Classical Scholasticism without physical operators).
3. The Total Explanatory Power Unlocked (What can now be calculated, unified, and defended).
4. The Global Defeat Boundary (The strict falsification boundary of the unified system).

### 5. Architectural Map & Dependency Spine
- A clear Markdown diagram and dependency list showing how the chapters lock together into an unshakeable consilience atlas.

Deliver the complete, fully articulated text from top to bottom with zero omissions or placeholder text.
"""

    print("\nCalling LLM Grand Synthesizer (Braid Engine)...")
    synthesis_text = call_llm(prompt, SYSTEM_SYNTHESIS_PROMPT, provider=provider, model=model)

    # 4. Save to series outbox and substack outbox
    series_dir.mkdir(parents=True, exist_ok=True)
    substack_dir.mkdir(parents=True, exist_ok=True)

    master_series_file = series_dir / f"{series_name}_GRAND_SYNTHESIS_MASTER_PAPER.md"
    substack_series_file = substack_dir / f"{series_name}_COMPLETE_SERIES_GRAND_OVERVIEW.md"

    master_series_file.write_text(synthesis_text, encoding="utf-8")
    substack_series_file.write_text(synthesis_text, encoding="utf-8")

    print(f"\n[SUCCESS] Master Series Synthesis generated:")
    print(f"  - Series Outbox: {master_series_file}")
    print(f"  - Substack Outbox: {substack_series_file}")

    return master_series_file

def main():
    parser = argparse.ArgumentParser(description="Grand Series Synthesizer")
    parser.add_argument("--series", type=str, default="01_THE_STORY", help="Series name to synthesize")
    parser.add_argument("--provider", type=str, default="openrouter", choices=["auto", "openrouter", "deepseek"])
    parser.add_argument("--model", type=str, default=None)
    args = parser.parse_args()

    synthesize_series(args.series, provider=args.provider, model=args.model)
    return 0

if __name__ == "__main__":
    sys.exit(main())
