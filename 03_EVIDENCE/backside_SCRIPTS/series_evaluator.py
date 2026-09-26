"""
SERIES EVALUATOR & ARC GRADER (v1.0)
=====================================
Reads every paper in a series, then evaluates the SERIES AS A WHOLE:
  - Narrative arc: does it build? Does each paper earn the next?
  - Ordering: is the sequence optimal? Would reordering improve it?
  - Progressive complexity: does difficulty/depth increase appropriately?
  - Dependency chain: does each paper depend on prior ones? Are there orphans?
  - Redundancy detection: do any papers repeat claims from earlier ones?
  - Gap detection: are there missing steps in the argument chain?
  - Voice consistency: does the tone/register stay consistent?
  - Claim escalation audit: are claims properly graded as they build?
  - Story quality: is it well-told? Does it compel? Does it flow?
  - Series-level evidence score: aggregate of individual evidence balances

Output:
  - SERIES_ARC_REPORT.md in the series folder
  - SERIES_SCORECARD.md with numeric grades
  - SERIES_REORDER_RECOMMENDATION.md if ordering changes suggested

Runs DeepSeek by default, 12 papers per parallel batch.
Can also run OpenRouter (Gemini Flash) or OpenAI as fallback.

Usage:
  python series_evaluator.py --series 01_GOD_IS
  python series_evaluator.py --all
  python series_evaluator.py --series 01_GOD_IS --provider deepseek --model deepseek-chat
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
OUTBOX_DIR = ROOT_DIR / "OUTBOX"
SERIES_OUT_DIR = OUTBOX_DIR / "BY_SERIES"

# ─── API CONFIG ───────────────────────────────────────────────

def get_api_config(provider: str, model: str | None = None) -> dict:
    """Return url, model, headers for the chosen provider."""
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()

    configs = {
        "deepseek": {
            "url": "https://api.deepseek.com/chat/completions",
            "model": model or "deepseek-chat",
            "headers": {
                "Authorization": f"Bearer {deepseek_key}",
                "Content-Type": "application/json"
            },
            "available": bool(deepseek_key)
        },
        "openrouter": {
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "model": model or "google/gemini-2.5-flash",
            "headers": {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://faiththruphysics.com",
                "X-OpenRouter-Title": "Faith Through Physics Series Evaluator"
            },
            "available": bool(openrouter_key)
        },
        "openai": {
            "url": "https://api.openai.com/v1/chat/completions",
            "model": model or "gpt-4o",
            "headers": {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            },
            "available": bool(openai_key)
        }
    }

    if provider == "auto":
        for p in ["deepseek", "openrouter", "openai"]:
            if configs[p]["available"]:
                return configs[p]
        raise RuntimeError("No API keys found.")

    if not configs[provider]["available"]:
        raise RuntimeError(f"No API key for {provider}.")
    return configs[provider]


def call_llm(prompt: str, system_prompt: str, config: dict, max_tokens: int = 8192) -> str:
    """Call the LLM with retry."""
    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.15,
        "max_tokens": max_tokens
    }
    for attempt in range(1, 4):
        try:
            resp = requests.post(config["url"], json=payload,
                                 headers=config["headers"], timeout=300)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  [attempt {attempt}] Error: {e}")
            if attempt < 3:
                time.sleep(5 * attempt)
    return "[ERROR] All LLM attempts failed."


# ─── FILE LOADING ─────────────────────────────────────────────

def load_series_papers(series_name: str) -> list[dict]:
    """Load all paper markdown files for a series, sorted by filename."""
    series_dir = SERIES_OUT_DIR / series_name
    if not series_dir.exists():
        raise FileNotFoundError(f"Series folder not found: {series_dir}")

    papers = []
    for f in sorted(series_dir.glob("*.md")):
        # Skip synthesis/notebook files
        if f.name.startswith("00_") or f.name.startswith("01_THE_STORY"):
            continue
        content = f.read_text(encoding="utf-8", errors="replace")
        papers.append({
            "filename": f.name,
            "path": str(f),
            "content": content,
            "size": len(content)
        })
    return papers


def extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter fields we care about."""
    fm = {}
    yaml_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        return fm

    yaml_text = yaml_match.group(1)

    for key in ["title", "clean_title", "one_sentence_finding", "paper_rating",
                 "evd_support", "evd_counter", "evd_balance", "evd_families",
                 "governing_question", "chapter", "series", "domain_primary",
                 "formal_status", "canon_status"]:
        match = re.search(rf'^{key}:\s*["\']?(.+?)["\']?\s*$', yaml_text, re.MULTILINE)
        if match:
            fm[key] = match.group(1).strip().strip('"').strip("'")

    # Extract claim_ids count
    claims_match = re.search(r'claim_ids:\s*\[(.*?)\]', yaml_text, re.DOTALL)
    if claims_match:
        fm["claim_count"] = len([c for c in claims_match.group(1).split(",") if c.strip()])

    return fm


# ─── EVALUATION PROMPTS ──────────────────────────────────────

SYSTEM_PROMPT_INDIVIDUAL = """You are grading a single paper within a larger series.
For this paper, evaluate and return JSON (no markdown fences):
{
  "title": "paper title",
  "narrative_score": 1-10,
  "argument_clarity": 1-10,
  "builds_on_previous": true/false/first,
  "required_by_next": true/false/last,
  "key_claim": "one sentence",
  "key_weakness": "one sentence",
  "redundant_with": "filename or null",
  "voice_register": "declaration/canon/mixed",
  "ordering_note": "fine / should come earlier / should come later / could be cut"
}
Be rigorous. A 7 is good. A 9 is exceptional. Do not inflate."""

SYSTEM_PROMPT_SERIES = """You are the Master Series Evaluator for the Theophysics Research Initiative.
You are evaluating an entire series of papers as a SERIES — not individually, but as a connected arc.

Grade the following dimensions (1-10 each, be rigorous, a 7 is good, 9 is exceptional):

1. NARRATIVE ARC — Does it build? Does each paper earn the next? Is there a beginning, development, and culmination?
2. ORDERING — Is the sequence optimal? Would any reordering improve the flow?
3. PROGRESSIVE COMPLEXITY — Does depth increase appropriately? Or does it plateau or spike randomly?
4. DEPENDENCY CHAIN — Does each paper depend on prior ones? Are there orphan papers that don't connect?
5. REDUNDANCY — Do any papers repeat material from earlier ones without adding new substance?
6. GAP DETECTION — Are there missing arguments? Places where the reader needs a step that isn't provided?
7. VOICE CONSISTENCY — Does the tone stay consistent across the series?
8. CLAIM ESCALATION — Are claims properly graded? Does it avoid overclaiming early?
9. STORY QUALITY — Is it well-told? Compelling? Does a reader want to continue?
10. HONESTY — Are limitations, open questions, and failure points visible? Or are they hidden?

Return JSON (no markdown fences):
{
  "series_name": "name",
  "paper_count": N,
  "scores": {
    "narrative_arc": N,
    "ordering": N,
    "progressive_complexity": N,
    "dependency_chain": N,
    "redundancy": N,
    "gap_detection": N,
    "voice_consistency": N,
    "claim_escalation": N,
    "story_quality": N,
    "honesty": N,
    "overall": N
  },
  "best_paper": "filename",
  "weakest_paper": "filename",
  "biggest_gap": "description of what's missing",
  "reorder_suggestion": "description or 'none needed'",
  "redundancies_found": ["list of pairs"],
  "one_paragraph_verdict": "honest overall assessment",
  "what_holds": "strongest surviving claims across the series",
  "what_breaks": "weakest points or overclaims",
  "what_to_fix_first": "single highest-priority fix"
}"""


# ─── PARALLEL INDIVIDUAL GRADING ─────────────────────────────

def grade_individual_paper(paper: dict, paper_index: int, total: int,
                           prev_title: str | None, next_title: str | None,
                           config: dict) -> dict:
    """Grade a single paper for its role in the series."""
    context = f"Paper {paper_index}/{total} in the series."
    if prev_title:
        context += f" Previous paper: '{prev_title}'."
    if next_title:
        context += f" Next paper: '{next_title}'."

    # Truncate content if needed to fit context window
    content = paper["content"][:12000]

    prompt = f"""{context}

FILENAME: {paper['filename']}

CONTENT:
{content}

Grade this paper for its role in the series. Return JSON only."""

    result_text = call_llm(prompt, SYSTEM_PROMPT_INDIVIDUAL, config, max_tokens=2048)

    # Parse JSON from response
    try:
        # Strip any markdown fences
        cleaned = re.sub(r'```json?\s*', '', result_text)
        cleaned = re.sub(r'```\s*$', '', cleaned).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": result_text[:500], "filename": paper["filename"]}


def grade_all_papers_parallel(papers: list[dict], config: dict,
                               max_workers: int = 12) -> list[dict]:
    """Grade all papers in parallel batches."""
    results = [None] * len(papers)
    titles = [extract_frontmatter(p["content"]).get("clean_title", p["filename"]) for p in papers]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, paper in enumerate(papers):
            prev_t = titles[i-1] if i > 0 else None
            next_t = titles[i+1] if i < len(papers)-1 else None
            f = executor.submit(grade_individual_paper, paper, i+1, len(papers),
                                prev_t, next_t, config)
            futures[f] = i

        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
                print(f"  ✓ Graded paper {idx+1}/{len(papers)}: {papers[idx]['filename'][:50]}...")
            except Exception as e:
                results[idx] = {"error": str(e), "filename": papers[idx]["filename"]}
                print(f"  ✗ Failed paper {idx+1}: {e}")

    return results


# ─── SERIES-LEVEL EVALUATION ─────────────────────────────────

def evaluate_series(series_name: str, papers: list[dict],
                     individual_grades: list[dict], config: dict) -> dict:
    """Run the series-level evaluation using individual grades + paper summaries."""

    # Build a compact representation of the series
    series_summary = f"SERIES: {series_name}\nPAPER COUNT: {len(papers)}\n\n"

    for i, (paper, grade) in enumerate(zip(papers, individual_grades)):
        fm = extract_frontmatter(paper["content"])
        series_summary += f"--- PAPER {i+1}: {paper['filename']} ---\n"
        series_summary += f"Title: {fm.get('clean_title', 'unknown')}\n"
        series_summary += f"Finding: {fm.get('one_sentence_finding', 'unknown')}\n"
        series_summary += f"Rating: {fm.get('paper_rating', '?')}\n"
        series_summary += f"Evidence Balance: {fm.get('evd_balance', '?')}\n"
        series_summary += f"Claims: {fm.get('claim_count', '?')}\n"
        if isinstance(grade, dict) and "error" not in grade:
            series_summary += f"Narrative Score: {grade.get('narrative_score', '?')}\n"
            series_summary += f"Argument Clarity: {grade.get('argument_clarity', '?')}\n"
            series_summary += f"Builds on Previous: {grade.get('builds_on_previous', '?')}\n"
            series_summary += f"Key Claim: {grade.get('key_claim', '?')}\n"
            series_summary += f"Key Weakness: {grade.get('key_weakness', '?')}\n"
            series_summary += f"Ordering Note: {grade.get('ordering_note', '?')}\n"
        series_summary += "\n"

    prompt = f"""Evaluate this complete series as a SERIES — the arc, the build, the cohesion.

{series_summary}

Return JSON only with your complete series evaluation."""

    result_text = call_llm(prompt, SYSTEM_PROMPT_SERIES, config, max_tokens=4096)

    try:
        cleaned = re.sub(r'```json?\s*', '', result_text)
        cleaned = re.sub(r'```\s*$', '', cleaned).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": result_text[:1000]}


# ─── REPORT GENERATION ────────────────────────────────────────

def generate_reports(series_name: str, papers: list[dict],
                      individual_grades: list[dict], series_grade: dict):
    """Write the three output files."""
    series_dir = SERIES_OUT_DIR / series_name

    # ── SCORECARD ──
    scorecard_path = series_dir / "SERIES_SCORECARD.md"
    scores = series_grade.get("scores", {})
    sc = f"# SERIES SCORECARD: {series_name}\n"
    sc += f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    sc += f"Papers evaluated: {len(papers)}\n\n"
    sc += "## SERIES SCORES (1-10)\n\n"
    sc += f"| Dimension | Score |\n|---|---|\n"
    for dim, score in scores.items():
        sc += f"| {dim.replace('_', ' ').title()} | {score} |\n"
    sc += f"\n**Overall: {scores.get('overall', '?')}/10**\n"
    sc += f"\n**Best Paper:** {series_grade.get('best_paper', '?')}\n"
    sc += f"**Weakest Paper:** {series_grade.get('weakest_paper', '?')}\n"
    sc += f"**Biggest Gap:** {series_grade.get('biggest_gap', '?')}\n"
    sc += f"**Fix First:** {series_grade.get('what_to_fix_first', '?')}\n"
    scorecard_path.write_text(sc, encoding="utf-8")
    print(f"  → Wrote {scorecard_path}")

    # ── ARC REPORT ──
    arc_path = series_dir / "SERIES_ARC_REPORT.md"
    ar = f"# SERIES ARC REPORT: {series_name}\n"
    ar += f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    ar += f"## VERDICT\n\n{series_grade.get('one_paragraph_verdict', 'No verdict generated.')}\n\n"
    ar += f"## WHAT HOLDS\n\n{series_grade.get('what_holds', '?')}\n\n"
    ar += f"## WHAT BREAKS\n\n{series_grade.get('what_breaks', '?')}\n\n"
    ar += f"## REDUNDANCIES\n\n"
    for r in series_grade.get("redundancies_found", []):
        ar += f"- {r}\n"
    ar += f"\n## INDIVIDUAL PAPER GRADES\n\n"
    ar += f"| # | Filename | Narrative | Clarity | Builds | Key Weakness | Order |\n"
    ar += f"|---|---|---|---|---|---|---|\n"
    for i, (paper, grade) in enumerate(zip(papers, individual_grades)):
        if isinstance(grade, dict) and "error" not in grade:
            ar += (f"| {i+1} | {paper['filename'][:40]}... "
                   f"| {grade.get('narrative_score', '?')} "
                   f"| {grade.get('argument_clarity', '?')} "
                   f"| {grade.get('builds_on_previous', '?')} "
                   f"| {grade.get('key_weakness', '?')[:40]}... "
                   f"| {grade.get('ordering_note', '?')} |\n")
        else:
            ar += f"| {i+1} | {paper['filename'][:40]}... | ERROR | — | — | — | — |\n"
    arc_path.write_text(ar, encoding="utf-8")
    print(f"  → Wrote {arc_path}")

    # ── REORDER RECOMMENDATION ──
    reorder = series_grade.get("reorder_suggestion", "none needed")
    if reorder and reorder.lower() != "none needed":
        reorder_path = series_dir / "SERIES_REORDER_RECOMMENDATION.md"
        ro = f"# REORDER RECOMMENDATION: {series_name}\n\n{reorder}\n"
        reorder_path.write_text(ro, encoding="utf-8")
        print(f"  → Wrote {reorder_path}")


# ─── MAIN ─────────────────────────────────────────────────────

def run_series(series_name: str, provider: str, model: str | None,
               max_workers: int):
    """Full evaluation pipeline for one series."""
    print(f"\n{'='*60}")
    print(f"EVALUATING SERIES: {series_name}")
    print(f"{'='*60}")

    config = get_api_config(provider, model)
    print(f"Provider: {provider} | Model: {config['model']}")

    # Load papers
    papers = load_series_papers(series_name)
    print(f"Loaded {len(papers)} papers")

    if not papers:
        print("  No papers found. Skipping.")
        return

    # Phase 1: Individual grading (parallel)
    print(f"\nPhase 1: Grading {len(papers)} papers individually (max {max_workers} parallel)...")
    individual_grades = grade_all_papers_parallel(papers, config, max_workers)

    # Phase 2: Series-level evaluation
    print(f"\nPhase 2: Evaluating series arc...")
    series_grade = evaluate_series(series_name, papers, individual_grades, config)

    # Phase 3: Generate reports
    print(f"\nPhase 3: Writing reports...")
    generate_reports(series_name, papers, individual_grades, series_grade)

    # Print summary
    scores = series_grade.get("scores", {})
    overall = scores.get("overall", "?")
    print(f"\n{'─'*40}")
    print(f"SERIES OVERALL: {overall}/10")
    print(f"Best: {series_grade.get('best_paper', '?')}")
    print(f"Fix first: {series_grade.get('what_to_fix_first', '?')}")
    print(f"{'─'*40}\n")


def main():
    parser = argparse.ArgumentParser(description="Series Evaluator & Arc Grader")
    parser.add_argument("--series", type=str, help="Series folder name (e.g., 01_GOD_IS)")
    parser.add_argument("--all", action="store_true", help="Evaluate all series")
    parser.add_argument("--provider", type=str, default="deepseek",
                        choices=["deepseek", "openrouter", "openai", "auto"])
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--workers", type=int, default=12,
                        help="Max parallel API calls")
    args = parser.parse_args()

    if args.all:
        for series_dir in sorted(SERIES_OUT_DIR.iterdir()):
            if series_dir.is_dir():
                run_series(series_dir.name, args.provider, args.model, args.workers)
    elif args.series:
        run_series(args.series, args.provider, args.model, args.workers)
    else:
        print("Specify --series <name> or --all")
        sys.exit(1)


if __name__ == "__main__":
    main()
