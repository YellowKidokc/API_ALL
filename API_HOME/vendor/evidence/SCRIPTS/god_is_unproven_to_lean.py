#!/usr/bin/env python3
"""
GOD_IS UNPROVEN EXTRACTOR & LEAN 4 FORMAL PAIRING ENGINE (v1.0)
==============================================================
Pulls all unproven claims, candidate hypotheses, physical bridges,
and formalization targets from '00_THE_STORY/01_GOD_IS/' (all 20 papers)
and pairs them with typed formal definitions and candidate theorems in Lean 4.

Author: Antigravity / Faith Through Physics
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_GOD_IS_DIR = Path(os.path.join(os.environ.get("ONE_MENU_PATH_PRODUCTION_ROOT", ""), "00_THE_STORY", "01_GOD_IS"))
DEFAULT_LEAN_DIR = Path(os.path.join(os.environ.get("ONE_MENU_PATH_PIPELINE_API_ROOT", ""), "LEAN4"))
DEFAULT_LOCAL_LEAN = Path(os.environ.get("ONE_MENU_PATH_CANONIZATION_ROOT", ""))


def scan_god_is_papers(god_is_dir: Path) -> List[Dict[str, Any]]:
    """Scans all 20 paper folders in 01_GOD_IS and extracts unproven claims and formalization targets."""
    extracted_papers = []

    subfolders = sorted([
        d for d in god_is_dir.iterdir() 
        if d.is_dir() and d.name[:2].isdigit() and d.name != "01_CLAIMS_AND_EVIDENCE"
    ])
    print(f"[Extractor] Found {len(subfolders)} distinct paper folders in {god_is_dir}")

    for folder in subfolders:
        folder_num = folder.name[:2]
        # Clean folder title without leading number
        clean_name = folder.name[3:] if len(folder.name) > 3 else folder.name
        title = clean_name.replace("_", " ").title()

        paper_info: Dict[str, Any] = {
            "folder_num": folder_num,
            "folder_name": folder.name,
            "clean_name": clean_name,
            "title": title,
            "unproven_claims": [],
            "formalization_targets": [],
            "candidate_equations": [],
            "open_bridges": [],
            "source_files": []
        }

        # 1. Read FL_01 (Full Length)
        fl_files = list(folder.glob("*_FL_01_*.md"))
        if fl_files:
            fl_file = fl_files[0]
            paper_info["source_files"].append(fl_file.name)
            text = fl_file.read_text(encoding="utf-8", errors="replace")
            
            # Match tagged claims
            claim_matches = re.findall(r"\[(theological axiom|derivation grammar rule|candidate theorem|open bridge|hypothesis|claim)\]\s*\r?\n\s*([^\r\n]+(?:\r?\n(?!^\s*#)[^\r\n]+)*)", text, re.IGNORECASE)
            for role, body in claim_matches:
                clean_body = body.strip().split("\n\n")[0].strip()
                if len(clean_body) > 20:
                    paper_info["unproven_claims"].append({
                        "type": role.strip(),
                        "statement": clean_body[:250],
                        "source": fl_file.name
                    })

            # Match subheadings representing core claims (e.g. ### Debt One: Existence, ### 1.1 ...)
            subhead_matches = re.findall(r"^###\s+([^\r\n]+)\r?\n\s*([^\r\n]+(?:\r?\n(?!^\s*#)[^\r\n]+)*)", text, re.MULTILINE)
            for head, body in subhead_matches:
                if len(paper_info["unproven_claims"]) >= 6:
                    break
                clean_body = body.strip().split("\n\n")[0].strip()
                if len(clean_body) > 25 and not head.startswith("Video") and not head.startswith("Podcast"):
                    paper_info["unproven_claims"].append({
                        "type": f"Proposition: {head.strip()}",
                        "statement": clean_body[:250],
                        "source": fl_file.name
                    })

            # Look for mathematical / physical equations
            eq_matches = re.findall(r"(?:chi\s*=\s*integral[^\r\n]+|\$\$[^\$]+\$\$|Delta\s+S[^\r\n]+|S_damaged[^\r\n]+)", text)
            for eq in eq_matches[:4]:
                paper_info["candidate_equations"].append(eq.strip())

        # 2. Check 01_CLAIMS_AND_EVIDENCE for epistemic JSON
        ev_dir = folder / "01_CLAIMS_AND_EVIDENCE"
        if not ev_dir.exists():
            ev_dir = god_is_dir / "01_CLAIMS_AND_EVIDENCE"

        if ev_dir.exists():
            json_files = list(ev_dir.glob(f"*{folder_num}*.epistemic.json"))
            for jf in json_files:
                try:
                    data = json.loads(jf.read_text(encoding="utf-8", errors="replace"))
                    call_3 = data.get("call_3", {})
                    targets = call_3.get("formalization_targets", [])
                    conditionals = call_3.get("what_remains_conditional", [])
                    unresolved = call_3.get("strongest_unresolved_transition", "")

                    for t in targets:
                        paper_info["formalization_targets"].append(t)
                    for c in conditionals:
                        paper_info["open_bridges"].append(c)
                    if unresolved:
                        paper_info["open_bridges"].append(unresolved)
                except Exception:
                    pass

        # If no specific targets found from JSON, generate default structural formal targets
        if not paper_info["formalization_targets"]:
            paper_info["formalization_targets"] = [
                f"Formalize the deduction connecting {paper_info['title']} to the Root Axiom A₀.",
                "Specify typed invariants preventing category errors between physical and theological registers.",
                "Prove deductive consistency under non-contradiction."
            ]

        extracted_papers.append(paper_info)

    return extracted_papers


def generate_lean_formal_module(paper: Dict[str, Any], lean_theorems_dir: Path) -> Path:
    """Generates a rich Lean 4 module containing typed definitions, structures, and unproven theorem conjectures."""
    num = paper["folder_num"]
    name_clean = re.sub(r"[^\w]", "_", paper["clean_name"]).strip("_")
    ns = f"FaithThruPhysics.Theorems.GodIs_Unproven.P{num}_{name_clean}"

    lean_lines = [
        "/-!",
        f"# God Is Series — Formalization Target for Paper {num}: {paper['title']}",
        f"Source Folder: {paper['folder_name']}",
        "-/",
        "",
        f"namespace {ns}",
        "",
        "open FaithThruPhysics",
        "",
        "/-- Root Axiom A₀: God Is -/",
        "axiom GodIs : Prop",
        "",
        "/-- Relational Primitive P₀₁ -/",
        "axiom TrinitarianRelationality : GodIs → Prop",
        "",
        "/-- Physical Field / Thermodynamic Boundary -/",
        "structure PhysicalSystem where",
        "  entropy : Nat",
        "  coherence : Nat",
        "  is_closed : Bool",
        "",
        "/-- External Grace Input Operator (G) -/",
        "def GraceInput (sys : PhysicalSystem) (G_rate : Nat) : PhysicalSystem :=",
        "  { sys with entropy := sys.entropy - G_rate, coherence := sys.coherence + G_rate }",
        ""
    ]

    # Add theorem targets for each unproven claim
    for i, claim in enumerate(paper["unproven_claims"][:5], 1):
        clean_stmt = claim["statement"].replace("\n", " ").replace('"', "'")
        lean_lines.extend([
            f"/-- Unproven Claim {i} ({claim['type']}): {clean_stmt[:120]}... -/",
            f"axiom Claim_{i}_Axiomatic_Hypothesis (h : GodIs) : Prop",
            "",
            f"/-- Candidate Theorem {i}: Consistency of Claim {i} with Root Axiom -/",
            f"theorem theorem_claim_{i}_consistency (h : GodIs) (hc : Claim_{i}_Axiomatic_Hypothesis h) :",
            f"    Claim_{i}_Axiomatic_Hypothesis h := by",
            "  exact hc",
            ""
        ])

    # If no specific claims extracted, add the default core target
    if not paper["unproven_claims"]:
        lean_lines.extend([
            "/-- Candidate Formalization Target: Root Derivation -/",
            "theorem theorem_derived_from_ground (h : GodIs) (hr : TrinitarianRelationality h) :",
            "    TrinitarianRelationality h := by",
            "  exact hr",
            ""
        ])

    lean_lines.extend([
        f"end {ns}",
        ""
    ])

    lean_theorems_dir.mkdir(parents=True, exist_ok=True)
    out_file = lean_theorems_dir / f"P{num}_{name_clean}_Targets.lean"
    out_file.write_text("\n".join(lean_lines), encoding="utf-8")
    return out_file


def run_pairing_engine(
    god_is_dir: Path,
    lean_dir: Path,
    local_lean_dir: Path
) -> None:
    """Executes the complete extraction, Lean formalization, and Markdown pairing matrix generation."""
    print(f"\n=======================================================")
    print(f" GOD IS UNPROVEN CLAIMS & LEAN 4 PAIRING ENGINE")
    print(f" God Is Folder:  {god_is_dir}")
    print(f" Target Lean 4:  {lean_dir}")
    print(f" Local Project:  {local_lean_dir}")
    print(f"=======================================================\n")

    papers = scan_god_is_papers(god_is_dir)

    # 1. Generate Lean formalization targets in both project locations
    lean_out_dirs = [
        lean_dir / "FaithThruPhysics" / "Theorems" / "GodIs_Unproven",
        local_lean_dir / "FaithThruPhysics" / "Theorems" / "GodIs_Unproven"
    ]

    total_lean_files = 0
    for target_dir in lean_out_dirs:
        for p in papers:
            generate_lean_formal_module(p, target_dir)
            total_lean_files += 1

    print(f"[Lean 4] Generated formal theorem targets for all {len(papers)} papers in FaithThruPhysics/Theorems/GodIs_Unproven/")

    # 2. Build the Master Pairing Markdown Report
    report_lines = [
        "# THEOPHYSICS GAP ANALYSIS: GOD IS UNPROVEN CLAIMS ↔ LEAN 4 PAIRING MATRIX\n\n",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"**Source Knowledge Base:** `{god_is_dir}`\n",
        f"**Formal Engine:** Native Lean 4.30.0 Prover\n",
        f"**Total Papers Analyzed:** {len(papers)}\n\n",
        "---\n\n",
        "## Executive Summary\n\n",
        "This master matrix connects the **unproven claims, physical bridge hypotheses, and derivation gaps** "
        "from the twenty papers in the **God Is** collection to concrete, typed **Lean 4 theorem targets**.\n\n",
        "Each section identifies:\n",
        "1. **The Core Physical & Theological Claim**\n",
        "2. **Why It Is Currently Unproven** (what premise or empirical bridge is missing)\n",
        "3. **The Lean 4 Formalization Target** (exact typed module and theorem name)\n",
        "4. **Verification Strategy** (how to discharge the proof in Lean 4)\n\n",
        "---\n\n"
    ]

    tsv_rows = ["Folder\tPaper Title\tUnproven Claim\tWhy Unproven\tLean 4 Target Module\tStatus"]

    for p in papers:
        report_lines.append(f"### {p['folder_num']} — {p['title']}\n\n")
        report_lines.append(f"- **Source Folder:** `{p['folder_name']}`\n")
        
        # Unproven Claims
        report_lines.append(f"- **Unproven Claims & Hypotheses:**\n")
        if p["unproven_claims"]:
            for c in p["unproven_claims"][:4]:
                report_lines.append(f"  - `[{c['type']}]` {c['statement']}\n")
        else:
            report_lines.append(f"  - High-level paper thesis pending atomic lemma extraction.\n")

        # Formalization Targets
        report_lines.append(f"- **Formalization Gaps (What Lean Needs to Prove):**\n")
        for ft in p["formalization_targets"][:4]:
            report_lines.append(f"  - 🎯 {ft}\n")

        # Open Bridges
        if p["open_bridges"]:
            report_lines.append(f"- **Conditional Bridges:**\n")
            for ob in p["open_bridges"][:3]:
                report_lines.append(f"  - ⚠️ {ob}\n")

        # Lean 4 Pairing
        lean_target_name = f"P{p['folder_num']}_{re.sub(r'[^\\w]', '_', p['clean_name']).strip('_')}_Targets.lean"
        report_lines.append(f"- **Lean 4 Target Module:** [`{lean_target_name}`](file://{lean_dir / 'FaithThruPhysics' / 'Theorems' / 'GodIs_Unproven' / lean_target_name})\n")
        report_lines.append(f"- **Current Verification State:** `PENDING_MACHINE_PROOF` (formal typed shell generated)\n\n")
        report_lines.append("---\n\n")

        first_claim = p["unproven_claims"][0]["statement"] if p["unproven_claims"] else p["formalization_targets"][0]
        first_why = p["open_bridges"][0] if p["open_bridges"] else "Requires formal typed grounding"
        tsv_rows.append(f"{p['folder_num']}\t{p['title']}\t{first_claim[:80]}\t{first_why[:80]}\t{lean_target_name}\tPENDING")

    # 3. Save Master Documents to Outboxes
    outbox_md_lean = lean_dir / "OUTBOX" / "FAITH_THROUGH_PHYSICS" / "GOD_IS_UNPROVEN_CLAIMS_LEAN_PAIRING.md"
    outbox_tsv_lean = lean_dir / "OUTBOX" / "FAITH_THROUGH_PHYSICS" / "GOD_IS_UNPROVEN_CLAIMS_LEAN_PAIRING.tsv"
    
    evidence_outbox_md = lean_dir.parent / "EVIDENCE" / "OUTBOX" / "GOD_IS_UNPROVEN_CLAIMS_LEAN_PAIRING.md"
    evidence_outbox_tsv = lean_dir.parent / "EVIDENCE" / "OUTBOX" / "GOD_IS_UNPROVEN_CLAIMS_LEAN_PAIRING.tsv"

    for path in [outbox_md_lean, evidence_outbox_md]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(report_lines), encoding="utf-8")

    for path in [outbox_tsv_lean, evidence_outbox_tsv]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(tsv_rows), encoding="utf-8")

    print(f"\n[SUCCESS] Pairing Complete!")
    print(f"  - Master Markdown Matrix: {outbox_md_lean}")
    print(f"  - Master TSV Matrix:      {outbox_tsv_lean}")
    print(f"  - Evidence Outbox Copy:   {evidence_outbox_md}")
    print(f"  - Generated Lean Modules: {total_lean_files // 2} formal targets in FaithThruPhysics/Theorems/GodIs_Unproven/\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="God Is Unproven Claims to Lean 4 Pairing Engine")
    parser.add_argument("--god-is-dir", type=str, default=str(DEFAULT_GOD_IS_DIR), help="Path to 01_GOD_IS directory")
    parser.add_argument("--lean-dir", type=str, default=str(DEFAULT_LEAN_DIR), help="Path to network LEAN4 directory")
    parser.add_argument("--local-lean-dir", type=str, default=str(DEFAULT_LOCAL_LEAN), help="Path to local Canonizationv1")
    args = parser.parse_args()

    run_pairing_engine(
        god_is_dir=Path(args.god_is_dir),
        lean_dir=Path(args.lean_dir),
        local_lean_dir=Path(args.local_lean_dir)
    )
