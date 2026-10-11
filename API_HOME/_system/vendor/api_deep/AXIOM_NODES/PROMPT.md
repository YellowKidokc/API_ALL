# AXIOM_NODES Station Prompt

**Station ID:** `axiom_nodes`  
**Purpose:** Map paper content to registered axiom nodes and produce axiom-candidate packets compatible with the Consilience Atlas / Nerve Sync API `/api/axioms` intake.  
**Input:** One original paper plus its `paper_uuid` and any already-extracted claim atoms.  
**Output:** `axiom_nodes.json` — identified axiom nodes and candidate packets.  

---

## Task

Identify which axiom nodes from the registered axiom framework (Iron Chain spine, Theophysics axioms, etc.) the paper invokes, supports, challenges, extends, or ignores. For each node, produce or reference an **axiom-candidate-packet** conforming to `axiom-packet.schema.json`.

---

## Output schema

```json
{
  "station": "axiom_nodes",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "schema_reference": "axiom-packet.schema.json",
  "axiom_nodes": [
    {
      "packet_type": "axiom-candidate-packet",
      "schema_version": "1.0",
      "identity": {
        "canonical_id": "A1.0",
        "uuid": "<uuid>",
        "atlas_object_type": "AXIOM",
        "domain": "THEOLOGY|PHYSICS|MATHEMATICS|...",
        "status": "CANDIDATE"
      },
      "meaning_block": {
        "formal_definition": "",
        "common_sense_meaning": "",
        "governing_questions": {
          "question_answered": "",
          "problem_solved": "",
          "kill_condition": "",
          "downstream_license": "",
          "unresolved": ""
        },
        "candidate_canon_boundary": "CANDIDATE"
      },
      "dependency_spine": {
        "upstream": [],
        "downstream": [],
        "blast_radius": "INERT|LOCAL|STRUCTURAL"
      },
      "warrant": {
        "claim": "",
        "evidence": [],
        "kill_conditions": [],
        "assumptions": []
      },
      "relationship_to_paper": {
        "relation": "invokes|supports|challenges|extends|ignores|not_applicable",
        "source_spans": ["span1"],
        "atom_uuids": ["<uuid>"],
        "confidence": "high|medium|low",
        "notes": ""
      },
      "admission": {
        "state": "candidate_draft"
      }
    }
  ],
  "unmapped_claims": ["<atom_uuid>"],
  "notes": ""
}
```

---

## Rules

1. Only map to registered axiom node IDs. Do not invent new canonical IDs.
2. `ignores` requires evidence that the paper had reason to address the node but did not.
3. `not_applicable` requires a reason.
4. Link each node mapping to specific source spans and extracted atoms when available.
5. Produce a full axiom-candidate packet only when the paper contributes a new axiom candidate. Otherwise reference the existing node.
6. Report unmapped claims so the curator can propose new nodes or definitions.
