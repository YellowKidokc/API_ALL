"""Build the axiom-node mapping prompt from AXIOMS_PART1_MODE_CLASSIFICATION.md."""

from __future__ import annotations

import json
from pathlib import Path


def _load_axiom_nodes() -> list[dict]:
    """Parse the axiom classification markdown into a compact node list."""
    source = Path(__file__).resolve().parents[1] / "AXIOMS_PART1_MODE_CLASSIFICATION.md"
    if not source.exists():
        return []
    text = source.read_text(encoding="utf-8")
    nodes: list[dict] = []
    current_mode = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") and "(" in stripped:
            current_mode = stripped.split("(")[1].split(")")[0].strip()
            continue
        if stripped.startswith("- `") and "|" in stripped:
            parts = stripped.split("|")
            if len(parts) >= 2:
                node_id = parts[0].strip().strip("- `")
                name = parts[1].strip()
                nodes.append({"node_id": node_id, "name": name, "mode": current_mode})
    return nodes


def build_axiom_prompt(source_text: str) -> str:
    nodes = _load_axiom_nodes()
    if not nodes:
        raise RuntimeError("Could not load axiom nodes from AXIOMS_PART1_MODE_CLASSIFICATION.md")

    node_list = "\n".join(f"- {n['node_id']}: {n['name']} ({n['mode']})" for n in nodes)

    schema = {
        "paper_uuid": "stable id derived from source path",
        "title": "document title",
        "summary": "one-paragraph summary of how the paper relates to the axiom system",
        "primary_mode": "AX_CORE | AX_DERIVED | AX_SCAFFOLD | FW_EXTENDED | HY_EVIDENCE | DROP_DUPLICATE | mixed",
        "axiom_nodes": [
            {
                "node_id": "e.g. A1.1",
                "name": "human-readable node name",
                "mode": "AX_CORE | AX_DERIVED | AX_SCAFFOLD | FW_EXTENDED | HY_EVIDENCE | DROP_DUPLICATE",
                "alignment": "directly_asserted | supported | contested | relevant_but_not_asserted | absent",
                "evidence_quote": "exact substring from the source, or empty",
                "confidence": "high | medium | low",
                "notes": "optional explanation"
            }
        ]
    }

    instructions = f"""
You are an axiom-node mapping engine for the Faith Through Physics / Theophysics canon.

The canonical axiom nodes below are drawn from AXIOMS_PART1_MODE_CLASSIFICATION.md.
For each node, decide how the SOURCE text relates to it.

Alignment rules:
- directly_asserted: the source explicitly states this axiom/claim.
- supported: the source agrees with or builds on this node without explicitly stating it.
- contested: the source argues against or challenges this node.
- relevant_but_not_asserted: the node is nearby conceptually but the source does not take a stand.
- absent: the node is not relevant to the source.

CRITICAL: Only include nodes where the source clearly engages the concept. Do NOT list every node that is vaguely related. Omit absent and weakly-related nodes entirely. Keep the response compact.

If a quote is used, it must be copied EXACTLY from the source text.

CANONICAL AXIOM NODES:
{node_list}

Return ONLY a JSON object matching the schema below. No markdown fences, no commentary.
"""

    return (
        f"{instructions}\n\n"
        f"SCHEMA:\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n\n"
        f"SOURCE:\n{source_text}\n"
    )
