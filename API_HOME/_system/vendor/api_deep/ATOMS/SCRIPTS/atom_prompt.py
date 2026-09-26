"""Build the atom-classification prompt from the Claim Atom Standard."""

from __future__ import annotations

import json


def build_atom_prompt(source_text: str) -> str:
    schema = {
        "paper_uuid": "stable id derived from source path",
        "title": "document title",
        "domainType": "physics | theology | mathematics | information | consciousness | psychology | history",
        "summary": "one-paragraph summary of the source",
        "atoms": [
            {
                "nodeType": "claim | paradigm | bridge | prediction | evidence | kill | paper | objection | translation | check | article | reach | result | question | series | raw",
                "stage": "00_inbox_working | 01_canonical | 02_paradigm | 03_synthesis | 04_hypothesis | 05_evidence | 06_falsification | 07_paper | 08_objections | 09_everyday | 10_worldcheck | 11_articles | 12_audience | 13_fulfilled",
                "name": "human-readable title",
                "statementTechnical": "technical statement (omit for evidence, result, kill if not applicable)",
                "statementPlain": "plain-language statement (omit for evidence, result, kill if not applicable)",
                "claimClass": "floor-axiom | definition | theorem | bridge | empirical-anchor | prediction | boundary (only for 01_canonical)",
                "falsificationCondition": "what would destroy this claim (required for claim nodes)",
                "verificationStatus": "machine-verified | informal | falsified",
                "challengeStatus": "unchallenged | challenged-open | challenged-survived | falsified | upstream-falsified",
                "edges": [
                    {
                        "type": "dependsOn | feedsInto | expands | bridgesTo | challenges | forksFrom",
                        "target": "nodeID or claimID of related atom (use IDs found in this document; empty if unknown)",
                        "grade": "structural_identity | structural_isomorphism | structural_analogy | metaphorical | independent",
                        "propagates": "true | false"
                    }
                ],
                "notes": "optional: anything else relevant"
            }
        ]
    }

    instructions = """
You are an atom-classification engine for the Faith Through Physics / Theophysics canon.

Read the SOURCE text below and emit a JSON object matching the schema exactly.

Rules:
1. Only 01_canonical stage nodes are true "claims" and receive a claimID (tp:DOMAIN/L#/C#). All other stages get nodeID only.
2. Every claim node MUST include a falsificationCondition. If the source does not state one, infer the strongest honest kill condition.
3. Evidence, kill, result, paper, article, reach nodes do NOT need statementTechnical/statementPlain.
4. Use the exact enums in the schema. Do not invent values.
5. For edges, prefer empty target over guessed IDs. Only link to atoms you actually extracted from this source.
6. If the source contains multiple distinct claims, extract multiple atoms.
7. If a section is raw or unclassifiable, emit a 00_inbox_working raw node.
"""

    return (
        f"{instructions}\n\n"
        f"SCHEMA:\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n\n"
        f"SOURCE:\n{source_text}\n\n"
        "Return ONLY the JSON object. No markdown fences, no commentary."
    )
