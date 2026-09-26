#!/usr/bin/env python3
"""
AXIOM ONE-PAGE COMPILER & LEDGER EXTRACTOR (v1.0)
=================================================
Transforms all 191 Axiom Node Markdown companions in '21_AXIOM NODES'
into high-density, ~55-70 line One-Page Axiom Pages.

Simultaneously extracts and consolidates:
1. COMMENTARY ARCHIVE: §2 (Six-Layer Explanatory Lens) + §5 (Dynamics) per node
2. BRIDGE LEDGER: §6 (Orientation) + §7 (Bridges) + §8 (Reality Mirror) across all 191 nodes
3. MACHINE LEDGER: §0C/§0D (Crosswalks/Nabla) + §9 (Receipts/SHAs) across all 191 nodes

Author: Antigravity / Faith Through Physics
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def parse_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
    """Extract YAML frontmatter dictionary and remaining markdown body."""
    meta: Dict[str, str] = {}
    body = content
    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = fm_match.group(2)
        for line in fm_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                meta[k] = v
    return meta, body


def split_sections(body: str) -> Dict[str, str]:
    """Split markdown body into major numbered sections (0 through 10)."""
    sections: Dict[str, str] = {}
    
    # Matches top-level headings like '## 0. Front Identity Layer', '## 1. Atom Meaning Block', etc.
    header_pattern = re.compile(r"^(##\s+(\d+)\.[^\r\n]*)", re.MULTILINE)
    matches = list(header_pattern.finditer(body))
    
    if not matches:
        return {"all": body}
        
    # Content before first ## section (Title block, initial alerts)
    sections["preamble"] = body[:matches[0].start()].strip()
    
    for i, m in enumerate(matches):
        sec_num = m.group(2)
        sec_title = m.group(1).strip()
        start_idx = m.start()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sec_content = body[start_idx:end_idx].strip()
        sections[sec_num] = sec_content
        sections[f"title_{sec_num}"] = sec_title
        
    return sections


def parse_table_kv(text: str) -> Dict[str, str]:
    """Parses standard markdown 2-column key-value tables into a dict."""
    kv: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 2:
            key = parts[0].lower().replace("`", "").strip()
            val = parts[1].strip()
            if key and key != "field" and key != "warrant field" and key != "bridge field":
                kv[key] = val
    return kv


def extract_math_blocks(sec1_text: str) -> List[str]:
    """Extract all math callout blocks from Section 1."""
    blocks = []
    # Match > [!math] ... up to the next non-quoted section or heading
    pattern = re.compile(r"(>\s*\[!math\][^\n]*\n(?:>[^\n]*\n*)+)", re.MULTILINE)
    for m in pattern.finditer(sec1_text):
        blocks.append(m.group(1).strip())
    return blocks


def extract_where_and_boundary(sec1_text: str) -> Tuple[str, str]:
    """Extract 'Where:' variable definitions and 'Boundary:' quote."""
    where_text = ""
    boundary_text = ""
    
    # Where:
    where_match = re.search(r"(?:^|\n)(Where:\s*\n(?:\s*-\s*[^\n]+\n*)+)", sec1_text, re.MULTILINE)
    if where_match:
        where_text = where_match.group(1).strip()
        
    # Boundary:
    boundary_match = re.search(r"(?:^|\n)(Boundary:\s*\n>\s*[^\n]+(?:\n>[^\n]+)*)", sec1_text, re.MULTILINE)
    if boundary_match:
        boundary_text = boundary_match.group(1).strip()
        
    return where_text, boundary_text


def extract_governing_questions(sec1_text: str) -> Dict[int, str]:
    """Extract answers to Governing Questions 1-5."""
    gq: Dict[int, str] = {}
    # Pattern matching: 1. **What question...** \n answer
    pattern = re.compile(r"(\d+)\.\s*\*\*(.*?)\*\*\s*\r?\n\s*([^\r\n]+(?:\r?\n(?!^\s*\d+\.\s*\*\*)[^\r\n]+)*)", re.MULTILINE)
    for m in pattern.finditer(sec1_text):
        q_num = int(m.group(1))
        ans = m.group(3).strip()
        gq[q_num] = ans
    return gq


def extract_not_claiming(text: str) -> List[str]:
    """Extract 'Not claiming:' bullet points."""
    bullets = []
    m = re.search(r"Not claiming:\s*\n((?:\s*-\s*[^\n]+\n*)+)", text, re.MULTILINE)
    if m:
        for line in m.group(1).splitlines():
            line = line.strip()
            if line.startswith("-"):
                bullets.append(line)
    return bullets


def compile_one_page_axiom(
    filepath: Path,
    meta: Dict[str, str],
    sections: Dict[str, str]
) -> str:
    """Compiles a tight, high-density ~55-70 line One-Page Axiom Page."""
    canonical_id = meta.get("canonical_id", "")
    legacy_id = meta.get("legacy_id", "")
    mode = meta.get("mode", "AX_CORE")
    status = meta.get("epistemic_status", "primitive")
    position = meta.get("production_position", "")
    strict_status = meta.get("strict_core_status", "")
    source_record = meta.get("source_generated_record", "")
    sealed_auth = meta.get("sealed_chain_authority", "")
    sha256 = meta.get("source_sha256", "")
    
    # Extract Human Label from title or first heading
    title_m = re.search(r"#\s*([A-Z0-9\.]+)\s*[—\-]\s*([^\r\n]+)", sections.get("preamble", ""))
    if title_m:
        human_label = title_m.group(2).strip()
    else:
        human_label = meta.get("title", filepath.stem).replace(" - Atom Meaning Block", "").strip()

    sec0 = sections.get("0", "")
    sec1 = sections.get("1", "")
    sec3 = sections.get("3", "")
    sec4 = sections.get("4", "")
    sec10 = sections.get("10", "")

    # Parse 0A/0B identity info
    sec0_kv = parse_table_kv(sec0)
    tier = sec0_kv.get("tier", "Tier 0: Root Foundation")
    domain = sec0_kv.get("domain", "Primordial")

    # Formal definition (first paragraph of §1 Formal Definition)
    fd_match = re.search(r"### Formal Definition\s*\r?\n\s*([^\r\n]+(?:\r?\n(?!\r?\n)[^\r\n]+)*)", sec1)
    formal_def = fd_match.group(1).strip() if fd_match else "Formal definition not extracted."
    # Clean out redundant disclaimer if accidentally captured
    formal_def = re.sub(r"\n\s*Within this framework, the admitted root is God.*", "", formal_def, flags=re.DOTALL).strip()

    # Math Core & Self-Refutation
    math_blocks = extract_math_blocks(sec1)
    where_text, boundary_text = extract_where_and_boundary(sec1)

    # Governing Questions
    gq = extract_governing_questions(sec1)
    q3_breaks = gq.get(3, "Structural failure across downstream dependencies.")
    q4_pays_for = gq.get(4, "Enables downstream differentiation and definition grounding.")
    q5_unresolved = gq.get(5, "Richer metaphysical and specific empirical structures.")

    # Warrant info (§4)
    sec4_kv = parse_table_kv(sec4)
    warrant_claim = sec4_kv.get("claim", formal_def)
    warrant_type = sec4_kv.get("warrant type", sec4_kv.get("native grade", mode))
    kill_condition = sec4_kv.get("kill condition", "Demonstrate that absolute non-being is coherent and stable.")
    assumptions = sec4_kv.get("assumptions", "Reality is intelligible and domain is nonempty.")

    # Dependencies (§3 & §10)
    up_m = re.search(r"### Direct Upstream\s*\r?\n\s*([^\r\n]+)", sec3)
    upstream_raw = up_m.group(1).strip() if up_m else "None (Foundational Primitive)"
    upstream = re.sub(r"^\s*-\s*(?:Production generated record:\s*)?", "", upstream_raw).strip()
    if not upstream or upstream.lower() == "none":
        upstream = "∅ (Foundational Primitive)"
    
    down_m = re.search(r"### Direct Downstream[^\r\n]*\r?\n\s*([^\r\n]+)", sec3)
    downstream_raw = down_m.group(1).strip() if down_m else "Next sequential node"
    downstream = re.sub(r"^\s*-\s*(?:Sequence navigation points next to [^:]+:\s*)?", "", downstream_raw).strip()

    # Enables list from §3 or §0C
    enables_m = re.search(r"### v2\.3 Early Dependents[^\r\n]*\r?\n\s*((?:- [^\r\n]+\r?\n*)+)", sec3)
    enables_summary = ""
    if enables_m:
        enables_items = [re.sub(r"\s*\[.*?\]", "", line).strip("- ").strip() for line in enables_m.group(1).splitlines() if line.strip()]
        enables_summary = ", ".join(enables_items[:6])
    if not enables_summary:
        enables_summary = sec0_kv.get("enables list", "Downstream derivation spine")

    # Not claiming bullets
    not_claiming = extract_not_claiming(sec0)
    if not not_claiming:
        not_claiming = extract_not_claiming(sec1)
    if not not_claiming:
        not_claiming = [
            "- Not a standalone secular deduction of the full doctrine of God from this symbol alone.",
            "- Not a claim that physical or empirical ontologies are exhausted by this primitive."
        ]

    # Assemble One-Page Document
    out = []
    
    # 1. Frontmatter
    out.append("---")
    out.append(f'title: "{canonical_id} {human_label} - Axiom Node"')
    out.append(f'canonical_id: "{canonical_id}"')
    out.append(f'legacy_id: "{legacy_id}"')
    out.append(f'human_label: "{human_label}"')
    out.append(f'mode: "{mode}"')
    out.append(f'status: "{status}"')
    out.append(f'production_position: "{position}"')
    out.append(f'tier: "{tier}"')
    out.append(f'source_generated_record: "{source_record}"')
    out.append(f'sealed_chain_authority: "{sealed_auth}"')
    out.append(f'source_sha256: "{sha256}"')
    out.append("---")
    out.append("")
    
    # 2. Header & Root Confession / Canon Boundary
    out.append(f"# {canonical_id} — {human_label}")
    out.append("")
    out.append(f"> **ID:** `{canonical_id}` | **Legacy:** `{legacy_id}` | **Mode:** `{mode}` | **Status:** `{status}` | **Position:** {position}")
    out.append("")
    out.append("> [!danger] Canon Boundary & Root Confession")
    out.append(f"> Within this framework, **God is the admitted ontological root**. `{canonical_id}` establishes the formal floor of this node; it does not carry the full doctrine of God, creation, or Trinity by itself alone.")
    out.append("")
    out.append("---")
    out.append("")
    
    # 3. Section 1: Formal Articulation & Math Core
    out.append("## 1. Formal Articulation & Mathematical Core")
    out.append("")
    out.append(formal_def)
    out.append("")
    if math_blocks:
        for mb in math_blocks:
            out.append(mb)
            out.append("")
    if where_text:
        out.append(where_text)
        out.append("")
    if boundary_text:
        out.append(boundary_text)
        out.append("")
        
    out.append("---")
    out.append("")
    
    # 4. Section 2: What This Pays For (The Engine)
    out.append("## 2. What This Pays For")
    out.append("")
    out.append(f"> **Downstream Yield:** {q4_pays_for}")
    out.append("")
    out.append(f"Without `{canonical_id}`, the framework cannot establish `{enables_summary}`. This node supplies the necessary inferential baseline for subsequent axiomatic layers.")
    out.append("")
    out.append("---")
    out.append("")
    
    # 5. Section 3: Warrant & Defeat Boundary
    out.append("## 3. Warrant & Defeat Boundary")
    out.append("")
    out.append(f"- **Warrant Form:** {warrant_type} | **Kill Condition:** {kill_condition}")
    out.append(f"- **Defeat Impact (What Breaks):** {q3_breaks}")
    out.append(f"- **Unresolved Boundary:** {q5_unresolved}")
    out.append("- **Not Claiming:**")
    for nc in not_claiming:
        out.append(f"  {nc}")
    out.append("")
    out.append("---")
    out.append("")
    
    # 6. Section 4: Dependency Spine & Authority Links
    out.append("## 4. Dependency Spine & Authority Links")
    out.append("")
    out.append(f"- **Upstream Dependencies:** {upstream}")
    out.append(f"- **Enables / Dependents:** {enables_summary}")
    out.append(f"- **Next Node:** {downstream}")
    out.append(f"- **Full Generated Record:** {source_record}")
    out.append(f"- **Sealed Authority:** {sealed_auth}")
    out.append("")
    
    return "\n".join(out)


def extract_node_commentary(
    filepath: Path,
    meta: Dict[str, str],
    sections: Dict[str, str]
) -> str:
    """Extracts §2 (Six-Layer Explanatory Lens) and §5 (Dynamics) into a dedicated commentary record."""
    canonical_id = meta.get("canonical_id", "")
    legacy_id = meta.get("legacy_id", "")
    title_m = re.search(r"#\s*([A-Z0-9\.]+)\s*[—\-]\s*([^\r\n]+)", sections.get("preamble", ""))
    human_label = title_m.group(2).strip() if title_m else filepath.stem

    sec2 = sections.get("2", "## 2. Six-Layer Explanatory Lens\n\nNo explanatory lens extracted.")
    sec5 = sections.get("5", "## 5. Dynamics Panel\n\nNo dynamics panel extracted.")
    
    out = []
    out.append("---")
    out.append(f'title: "{canonical_id} {human_label} - Support Commentary"')
    out.append(f'canonical_id: "{canonical_id}"')
    out.append(f'target_axiom_node: "[[{filepath.name}]]"')
    out.append('type: "SUPPORT_COMMENTARY"')
    out.append("---")
    out.append("")
    out.append(f"# Commentary: {canonical_id} — {human_label}")
    out.append("")
    out.append(f"> Reference companion commentary for Axiom Node: [[{filepath.name}]]")
    out.append("")
    out.append("---")
    out.append("")
    out.append(sec2)
    out.append("")
    out.append("---")
    out.append("")
    out.append(sec5)
    out.append("")
    return "\n".join(out)


def run_transformation(
    vault_dir: Path,
    output_dir: Path,
    commentary_dir: Path,
    bridge_ledger_file: Path,
    machine_ledger_file: Path,
    in_place: bool = False,
    backup_dir: Optional[Path] = None,
    limit: Optional[int] = None
) -> None:
    """Executes the complete transformation across all 191 axiom node files."""
    files = sorted(vault_dir.glob("*.md"))
    if not files:
        print(f"[ERROR] No markdown files found in {vault_dir}")
        return

    if limit:
        files = files[:limit]

    print(f"\n=======================================================")
    print(f" AXIOM ONE-PAGE COMPILER & LEDGER EXTRACTOR")
    print(f" Source Nodes:     {vault_dir} ({len(files)} files)")
    print(f" Output 1-Page:    {output_dir}")
    print(f" Commentaries:     {commentary_dir}")
    print(f" Bridge Ledger:    {bridge_ledger_file}")
    print(f" Machine Ledger:   {machine_ledger_file}")
    print(f" In-Place Overwrite: {in_place}")
    print(f"=======================================================\n")

    output_dir.mkdir(parents=True, exist_ok=True)
    commentary_dir.mkdir(parents=True, exist_ok=True)

    if in_place and backup_dir:
        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Backup] Creating full backup of {len(files)} files in: {backup_dir}")
        for f in files:
            shutil.copy2(f, backup_dir / f.name)

    bridge_ledger_entries = [
        "# THEOPHYSICS CONSOLIDATED BRIDGE LEDGER (191 NODES)\n\n"
        "Consolidates §6 (Orientation Panel), §7 (Bridges), and §8 (Reality Mirror) across the entire axiomatic spine.\n\n"
        "---\n\n"
    ]
    
    machine_ledger_entries = [
        "# THEOPHYSICS CONSOLIDATED MACHINE & CROSSWALK LEDGER (191 NODES)\n\n"
        "Consolidates §0C/§0D (Pending Crosswalks & Nabla Positions) and §9 (Receipts/Runs/SHAs) across the entire axiomatic spine.\n\n"
        "---\n\n"
    ]

    transformed_count = 0
    line_counts = []

    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(content)
        sections = split_sections(body)

        # 1. Compile crisp One-Page Axiom
        one_page_content = compile_one_page_axiom(f, meta, sections)
        line_count = len(one_page_content.splitlines())
        line_counts.append(line_count)

        target_axiom_path = f if in_place else output_dir / f.name
        target_axiom_path.write_text(one_page_content, encoding="utf-8")

        # 2. Extract Commentary
        commentary_content = extract_node_commentary(f, meta, sections)
        commentary_file = commentary_dir / f"COMMENTARY_{f.name}"
        commentary_file.write_text(commentary_content, encoding="utf-8")

        # 3. Append to Bridge Ledger
        cid = meta.get("canonical_id", f.stem)
        sec6 = sections.get("6", "")
        sec7 = sections.get("7", "")
        sec8 = sections.get("8", "")
        bridge_ledger_entries.append(
            f"## [{cid}] {f.stem}\n\n"
            f"{sec6}\n\n---\n\n{sec7}\n\n---\n\n{sec8}\n\n---\n\n"
        )

        # 4. Append to Machine Ledger
        sec0 = sections.get("0", "")
        sec9 = sections.get("9", "")
        # Extract 0C and 0D from sec0
        c_d_text = ""
        c_m = re.search(r"(### 0C\.[^\n]*\n.*)", sec0, re.DOTALL)
        if c_m:
            c_d_text = c_m.group(1).strip()
        machine_ledger_entries.append(
            f"## [{cid}] {f.stem}\n\n"
            f"{c_d_text}\n\n---\n\n{sec9}\n\n---\n\n"
        )

        transformed_count += 1
        if transformed_count % 25 == 0 or transformed_count == len(files):
            print(f"  [Progress] Processed {transformed_count}/{len(files)} nodes (Current avg lines: {sum(line_counts)//len(line_counts)})")

    # Write Master Ledgers
    bridge_ledger_file.write_text("".join(bridge_ledger_entries), encoding="utf-8")
    machine_ledger_file.write_text("".join(machine_ledger_entries), encoding="utf-8")

    avg_lines = sum(line_counts) // len(line_counts) if line_counts else 0
    print(f"\n[SUCCESS] Completed Transformation of {transformed_count} Axiom Nodes:")
    print(f"  - Target Axiom Nodes Avg Line Count: {avg_lines} lines (Target: 55-70 lines)")
    print(f"  - Generated 1-Page Files: {target_axiom_path.parent}")
    print(f"  - Generated Support Commentaries: {commentary_dir}")
    print(f"  - Consolidated Bridge Ledger: {bridge_ledger_file} ({bridge_ledger_file.stat().st_size // 1024} KB)")
    print(f"  - Consolidated Machine Ledger: {machine_ledger_file} ({machine_ledger_file.stat().st_size // 1024} KB)\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Axiom One-Page Compiler & Ledger Extractor")
    parser.add_argument(
        "--vault-dir",
        type=str,
        default=r"C:\Users\David\Documents\faiththruphysics.com\00_ Production\00_ Production\21_AXIOM NODES",
        help="Path to 21_AXIOM NODES directory"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=r"C:\Users\David\Documents\faiththruphysics.com\00_ Production\00_ Production\21_AXIOM_NODES_ONE_PAGE",
        help="Output directory for 1-page axiom nodes"
    )
    parser.add_argument(
        "--commentary-dir",
        type=str,
        default=r"C:\Users\David\Documents\faiththruphysics.com\00_ Production\00_ Production\21_AXIOM_COMMENTARIES",
        help="Output directory for node support commentary"
    )
    parser.add_argument(
        "--bridge-ledger",
        type=str,
        default=r"C:\Users\David\Documents\faiththruphysics.com\00_ Production\00_ Production\BRIDGE_LEDGER.md",
        help="Path for master bridge ledger"
    )
    parser.add_argument(
        "--machine-ledger",
        type=str,
        default=r"C:\Users\David\Documents\faiththruphysics.com\00_ Production\00_ Production\MACHINE_LEDGER.md",
        help="Path for master machine ledger"
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite original files in 21_AXIOM NODES (creates timestamped backup automatically)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit execution to first N files for testing"
    )

    args = parser.parse_args()

    v_dir = Path(args.vault_dir)
    o_dir = Path(args.output_dir)
    c_dir = Path(args.commentary_dir)
    b_ledger = Path(args.bridge_ledger)
    m_ledger = Path(args.machine_ledger)

    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    b_dir = v_dir.parent / f"21_AXIOM_NODES_BACKUP_{now_str}" if args.in_place else None

    run_transformation(
        vault_dir=v_dir,
        output_dir=o_dir,
        commentary_dir=c_dir,
        bridge_ledger_file=b_ledger,
        machine_ledger_file=m_ledger,
        in_place=args.in_place,
        backup_dir=b_dir,
        limit=args.limit
    )
