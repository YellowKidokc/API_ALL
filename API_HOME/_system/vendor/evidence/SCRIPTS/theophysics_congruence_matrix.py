"""
THEOPHYSICS CONGRUENCE & GAP PAIRING ENGINE (v0.5)
==================================================
Tri-partite pairing engine that connects:
1. One Story Axioms & Truth Predicates (Theological / Conceptual)
2. Evidence Layer (Empirical / Philosophical Support vs Missing Gaps)
3. Lean 4 Formal Verification (Machine-Proven vs Pending)

Generates:
- OUTBOX/THEOPHYSICS_CONGRUENCE_MATRIX.md
- OUTBOX/THEOPHYSICS_CONGRUENCE_MATRIX.tsv
"""

from __future__ import annotations
import os  # ONE_MENU

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_ROOT") or (SCRIPTS_DIR if SCRIPTS_DIR.name == "_____pipeline-workflows-main" else SCRIPTS_DIR.parent))

if (ROOT_DIR / "EVIDENCE_CHAIN_INTAKE" / "OUTBOX").exists():
    OUTBOX_DIR = ROOT_DIR / "EVIDENCE_CHAIN_INTAKE" / "OUTBOX"
elif (ROOT_DIR / "OUTBOX").exists():
    OUTBOX_DIR = ROOT_DIR / "OUTBOX"
else:
    OUTBOX_DIR = SCRIPTS_DIR.parent / "OUTBOX"

FOR_SUBSTACK_DIR = OUTBOX_DIR / "FOR_SUBSTACK"
LEAN_RECEIPTS_DIR = OUTBOX_DIR / "LEAN_RECEIPTS"
DEFAULT_DB_PATH = Path(os.path.join(os.environ.get("ONE_MENU_PATH_CANONIZATION_ROOT", ""), "theophysics_pipeline.db"))

def run_pairing_analysis(db_path: Path = DEFAULT_DB_PATH) -> Path:
    print("\n=======================================================")
    print("THEOPHYSICS CONGRUENCE & GAP PAIRING ENGINE")
    print("=======================================================\n")

    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    matrix_md = OUTBOX_DIR / "THEOPHYSICS_CONGRUENCE_MATRIX.md"
    matrix_tsv = OUTBOX_DIR / "THEOPHYSICS_CONGRUENCE_MATRIX.tsv"

    # 1. Load Lean receipts
    verified_lean_papers = set()
    if LEAN_RECEIPTS_DIR.exists():
        for rf in LEAN_RECEIPTS_DIR.glob("*.json"):
            try:
                data = json.loads(rf.read_text(encoding="utf-8"))
                if data.get("status") == "PROVEN":
                    # ONE_MENU fix: one PROVEN receipt used to mark EVERY paper proven.
                    for key in ("paper_id", "slug", "paper", "source", "title"):
                        if data.get(key):
                            verified_lean_papers.add(re.sub(r"[^\w]", "_", str(data[key])).strip("_").lower())
                    verified_lean_papers.add(re.sub(r"[^\w]", "_", rf.stem).strip("_").lower())
            except Exception:
                pass

    # Also check Lean 4 Theorems directory
    lean_theorems_dir = ROOT_DIR.parent / "LEAN_FLOOR" / "FaithThruPhysics" / "Theorems"
    existing_lean_files = set()
    if lean_theorems_dir.exists():
        for lf in lean_theorems_dir.glob("*.lean"):
            existing_lean_files.add(lf.stem.lower())

    # 2. Collect paper companions
    companion_files = []
    if FOR_SUBSTACK_DIR.exists():
        companion_files = list(FOR_SUBSTACK_DIR.glob("*.md"))

    records = []
    for cf in sorted(companion_files, key=lambda p: p.name):
        text = cf.read_text(encoding="utf-8", errors="replace")
        
        title_m = re.search(r'title:\s*["\']?([^"\n\r]+)["\']?', text)
        title = title_m.group(1).strip() if title_m else cf.stem

        slug_m = re.search(r'paper_id:\s*["\']?([^"\n\r]+)["\']?', text)
        slug = slug_m.group(1).strip() if slug_m else cf.stem
        slug_clean = re.sub(r"[^\w]", "_", slug).strip("_").lower()

        score_m = re.search(r'paper_rating:\s*([0-9\.]+)', text)
        score = float(score_m.group(1)) if score_m else 7.0

        weak_m = re.search(r'evd_weakest_claim:\s*["\']?([^"\n\r]+)["\']?', text)
        weakest = weak_m.group(1).strip() if weak_m else "Formal Lean receipt pending"

        # Evidence status
        support_count = len(re.findall(r'evidence_type:', text))  # ONE_MENU fix: `or 4` made every paper SUPPORTED
        evidence_status = "SUPPORTED" if support_count >= 3 else "WEAK_EVIDENCE"

        # Lean status
        has_lean = (slug_clean in existing_lean_files) or (slug_clean in verified_lean_papers)
        lean_status = "PROVEN" if has_lean else "PENDING_LEAN"

        # Action needed
        actions = []
        if "pending" in weakest.lower() or "formal" in weakest.lower():
            actions.append("Formalize Lean 4 invariant")
        if "mathematical mapping" in weakest.lower():
            actions.append("Add explicit Master Equation units")
        if not actions:
            actions.append("Ready for +8 admission")

        records.append({
            "slug": slug,
            "title": title,
            "score": score,
            "evidence_status": evidence_status,
            "lean_status": lean_status,
            "weakest": weakest,
            "action": " & ".join(actions)
        })

    # Write TSV
    with open(matrix_tsv, "w", encoding="utf-8") as tf:
        tf.write("paper_id\tclean_title\tstanding\tevidence_status\tlean4_status\tweakest_gap\taction_required\n")
        for r in records:
            tf.write(f"{r['slug']}\t{r['title']}\t{r['score']}\t{r['evidence_status']}\t{r['lean_status']}\t{r['weakest']}\t{r['action']}\n")

    # Write Markdown Report
    lines = [
        "# 📐 Theophysics Congruence Matrix: Axioms ⟷ Evidence ⟷ Lean 4",
        f"**Total Papers Mapped:** {len(records)} | **Lean 4 Status:** Native Machine Verification Active",
        "\n---\n",
        "## 1. Tri-Partite Congruence Table\n",
        "| # | Chapter / Paper | Standing | Evidence Layer | Lean 4 Prover | Missing Gap / Weak Link | Action Required |",
        "|---|---|---|---|---|---|---|"
    ]

    for i, r in enumerate(records, 1):
        evd_badge = f"`{r['evidence_status']}`"
        lean_badge = f"**`{r['lean_status']}`**" if r['lean_status'] == "PROVEN" else "`PENDING`"
        lines.append(f"| {i} | **[[{r['title']}]]** | `+{r['score']}/8.0` | {evd_badge} | {lean_badge} | {r['weakest']} | {r['action']} |")

    lines.extend([
        "\n---\n",
        "## 2. Priority Upgrade Targets (Gaps to Pair Up)",
        "1. **Formalization Gaps:** Any paper where formal Lean 4 theorems need deep algebraic properties rather than propositional groundings.",
        r"2. **Thermodynamic Grounding:** Papers on Cost, Evil, and Grace need explicit Landauer-limit dissipation formulas ($\Delta Q \ge kT \ln 2 \cdot \Delta I$).",
        "3. **Relational Invariants:** Ensure the Trinitarian $A_0$ relationality axiom flows directly into physics parameters ($G, M, E, S, T, K, R, Q, F, C$).",
        "\n---\n",
        f"_Generated by Faith Through Physics Congruence Engine · Database: {db_path}_"
    ])

    matrix_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SUCCESS] Congruence Matrix generated:")
    print(f"  - Markdown Report: {matrix_md}")
    print(f"  - TSV Matrix:      {matrix_tsv}\n")

    return matrix_md

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Theophysics Congruence Pairing Engine")
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Path to SQLite DB")
    args = parser.parse_args()
    run_pairing_analysis(Path(args.db))
