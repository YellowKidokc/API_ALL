# ATOMS Station Prompt

**Station ID:** `atoms`  
**Purpose:** Extract independently reviewable claim atoms from a source paper using the Claim Atom Expansion AI Intake Template v1.1.  
**Input:** One original paper (markdown or plain text) plus its `paper_uuid`.  
**Output:** `atoms.json` — a list of candidate atom packets.  

---

## Task

Read the source paper and decompose it into independently gradable objects. Each object must have exactly one primary type:

- `CLAIM` — asserts a proposition
- `EVIDENCE` — bears on one or more propositions
- `PROOF` — derives an exact conclusion under premises
- `PROCESS` — describes a versioned operation

Use the **Claim Atom Expansion — AI Intake Template v1.1** (`CLAIM_ATOM_EXPANSION_AI_INTAKE_TEMPLATE_v1_1.md`) as the output shape for each atom.

---

## Output schema

```json
{
  "station": "atoms",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "schema_reference": "_schema/atom_envelope_v1_1.schema.json",
  "intake_template": "CLAIM_ATOM_EXPANSION_AI_INTAKE_TEMPLATE_v1_1.md",
  "atoms": [
    {
      "identity": {
        "object_type": "CLAIM|EVIDENCE|PROOF|PROCESS",
        "version": "0.1.0-candidate",
        "content_hash": "<sha256 of normalized content>"
      },
      "provenance": {
        "raw_statement": "exact source text",
        "source_uri": "<paper_uuid>",
        "source_span": "heading/paragraph/line range",
        "source_hash": "<sha256>",
        "ai_contribution_declared": "YES",
        "ai_contribution_role": "extraction"
      },
      "admission": {
        "graph": "candidate",
        "human_ruling": "pending"
      },
      "discovery": {
        "referent": "",
        "identities": [],
        "distinctions": [],
        "relations": [],
        "operations": [],
        "dependencies": [],
        "constraints": [],
        "invariants": [],
        "collapse_conditions": [],
        "consequences": [],
        "representation_ladder": [],
        "formalization_boundary": ""
      },
      "classification": {
        "emergent_labels": [],
        "inherited_labels": [],
        "reconciliation_status": "OPEN",
        "axes": {
          "lifecycle_state": "INTAKE",
          "proof_class": "",
          "register": "HISTORY|PHYSICS|MATHEMATICS|THEOLOGY|BRIDGE|...",
          "ic_grade": "",
          "why_outcome": ""
        }
      },
      "ai_completion_report": {
        "proposed_object_count": 1,
        "source_preserved": "YES",
        "source_hash_present": "YES",
        "independently_failing_components_separated": "YES",
        "selected_object_type": "",
        "selected_register": "",
        "required_native_fields_complete": "",
        "discovery_status": "STRUCTURALLY_OPENED|DISCOVERY_INCOMPLETE"
      }
    }
  ]
}
```

---

## Rules

1. One atom = one assertion that can be graded independently.
2. Preserve raw source text exactly; do not silently rewrite it.
3. Start with nondiscriminatory discovery (Section 1 of the intake template) before choosing a domain or register.
4. Choose exactly one `object_type`. If a sentence mixes types, split it.
5. Keep only the matching register anatomy and object extension; delete competing blank blocks before output.
6. Mark status as `candidate` / `pending` for all extracted atoms. Never auto-admit.
7. Do not invent evidence, proofs, measurements, theorem receipts, or sources.
8. Use `OPEN`, `UNKNOWN`, or `NOT_APPLICABLE` for unresolved fields rather than guessing.
9. Include AI contribution provenance: provider, model, role, receipt.

## What to report if nothing atom-shaped is found

Return an empty `atoms` array with a `notes` field explaining why (e.g., `INSUFFICIENT_SOURCE`, `ROUTING_QUESTIONNAIRE`).
