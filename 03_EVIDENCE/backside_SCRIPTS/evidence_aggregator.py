"""
EVIDENCE AGGREGATOR & UPGRADE ENGINE (v0.5)
===========================================
Aggregates evidence sheets, claims, and vulnerabilities from all paper companions in OUTBOX/
and generates an actionable upgrade blueprint to strengthen candidate claims to +8 standing.

Outputs:
- OUTBOX/EVIDENCE_UPGRADE_REPORT.md
- OUTBOX/EVIDENCE_DASHBOARD_SUMMARY.tsv
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
OUTBOX_DIR = ROOT_DIR / "OUTBOX"
FOR_SUBSTACK_DIR = OUTBOX_DIR / "FOR_SUBSTACK"

def parse_companion_evidence(filepath: Path) -> dict[str, Any]:
    text = filepath.read_text(encoding="utf-8", errors="replace")
    
    title_m = re.search(r'title:\s*["\']?([^"\n\r]+)["\']?', text)
    title = title_m.group(1).strip() if title_m else filepath.stem

    score_m = re.search(r'paper_rating:\s*([0-9\.]+)', text) or re.search(r'score:\s*([0-9\.]+)', text)
    score = float(score_m.group(1)) if score_m else 7.0

    domain_m = re.search(r'domain_primary:\s*["\']?([a-zA-Z0-9_\-]+)["\']?', text)
    domain = domain_m.group(1).title() if domain_m else "Theology"

    weak_m = re.search(r'evd_weakest_claim:\s*["\']?([^"\n\r]+)["\']?', text)
    weakest_claim = weak_m.group(1).strip() if weak_m else "Formal Lean receipt pending"

    # Extract S04 Claims & Evidence
    claims_block = ""
    claims_m = re.search(r'(## S04 · Evidence & Support[\s\S]*?)(?=## S05|\Z)', text)
    if claims_m:
        claims_block = claims_m.group(1).strip()

    # Extract S03 Truth Predicates Table
    pred_count = len(re.findall(r'\| P\d+ \|', text))

    return {
        "filename": filepath.name,
        "title": title,
        "score": score,
        "domain": domain,
        "weakest_claim": weakest_claim,
        "claims_block": claims_block,
        "pred_count": pred_count,
        "text_sample": text[:2000]
    }

def run_evidence_aggregation() -> Path:
    print("\n=== AGGREGATING EVIDENCE & UPGRADE DIAGNOSES ===")
    
    companion_files = []
    if FOR_SUBSTACK_DIR.exists():
        companion_files.extend(list(FOR_SUBSTACK_DIR.glob("*.md")))

    if not companion_files and (OUTBOX_DIR / "00_UNTOUCHED").exists():
        companion_files.extend(list((OUTBOX_DIR / "00_UNTOUCHED").glob("*.md")))

    print(f"Found {len(companion_files)} companion document(s) to analyze.")
    if not companion_files:
        print("No companions found in OUTBOX.")
        return OUTBOX_DIR / "EVIDENCE_UPGRADE_REPORT.md"

    records = [parse_companion_evidence(f) for f in companion_files]
    
    # Sort by score ascending (lowest score / most urgent upgrade first)
    records = sorted(records, key=lambda r: r["score"])

    report_path = OUTBOX_DIR / "EVIDENCE_UPGRADE_REPORT.md"
    tsv_path = OUTBOX_DIR / "EVIDENCE_DASHBOARD_SUMMARY.tsv"

    # Write TSV
    with open(tsv_path, "w", encoding="utf-8") as tf:
        tf.write("title\tdomain\tstanding\tpredicates_count\tweakest_claim\tfilename\n")
        for r in records:
            tf.write(f"{r['title']}\t{r['domain']}\t{r['score']}\t{r['pred_count']}\t{r['weakest_claim']}\t{r['filename']}\n")

    # Generate Markdown Report
    lines = [
        "# 🛡️ Evidence Aggregation & +8 Upgrade Action Blueprint",
        f"**Generated:** {len(records)} Total Papers Evaluated | **Target Standing:** +8.0 Unassailable",
        "\n---\n",
        "## 1. Evidence Inventory & Vulnerability Index\n",
        "| # | Paper Title | Domain | Current Standing | Predicates | Weakest Load-Bearing Point / Action Item |",
        "|---|---|---|---|---|---|"
    ]

    for i, r in enumerate(records, 1):
        lines.append(f"| {i} | **[[{r['title']}]]** | {r['domain']} | `+{r['score']}/8.0` | {r['pred_count']} | {r['weakest_claim']} |")

    lines.extend([
        "\n---\n",
        "## 2. Priority Upgrade Diagnoses (How to Make the Evidence Better)\n",
        "To elevate all papers from candidate standing (+7.0) to an unassailable +8.0, apply the following 4-dimensional reinforcements:\n",
        "### 🏛️ A. Formal & Mathematical Rigor",
        "- **Explicit Boundary Conditions:** Ensure every Master Equation variable ($G, M, E, S, T, K, R, Q, F, C$) has defined units, tensor dimensions, and operational domains.",
        "- **Lean 4 Proof Invariants:** Formulate candidate theorems as machine-checkable Lean 4 propositions (`theorem reality_is_relational : ...`).\n",
        "### 🔬 B. Empirical & Information-Theoretic Alignment",
        "- **Landauer Limit Integration:** Formulate cost-bearing ($C$) explicitly as thermodynamic dissipation $\Delta Q \ge kT \ln 2 \cdot \Delta I$.",
        "- **Negentropy Invariant:** Ground Grace as an explicit open-system negentropic flow ($-\Delta S_{external}$) reversing local entropy accumulation.\n",
        "### 📜 C. Classical Intellectual History Anchoring",
        "- Cross-link theological propositions with classical anchors (Aquinas' *actus purus*, Anselm's *id quo maius cogitari nequit*, Leibniz's *monadology/pre-established harmony*, and Gödel's *incompleteness*).\n",
        "### ⚔️ D. Falsification & Defeat Precision",
        "- Maintain the 4-step systemic advantage table so defeat conditions are clearly bounded rather than left ambiguous.",
        "\n---\n",
        "## 3. Detailed Per-Paper Evidence Extractions\n"
    ])

    for r in records:
        lines.append(f"### 📖 [[{r['title']}]] (`+{r['score']}/8.0`)")
        lines.append(f"- **Primary Domain:** {r['domain']}")
        lines.append(f"- **Weakest Claim Identified:** {r['weakest_claim']}")
        if r['claims_block']:
            lines.append(f"\n{r['claims_block']}\n")
        lines.append("\n---\n")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[SUCCESS] Evidence upgrade report generated at: {report_path}")
    print(f"[SUCCESS] Evidence TSV summary generated at: {tsv_path}")
    return report_path

if __name__ == "__main__":
    run_evidence_aggregation()
