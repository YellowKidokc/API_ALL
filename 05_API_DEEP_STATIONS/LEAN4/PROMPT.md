# LEAN4 Station Prompt

**Station ID:** `lean4`  
**Purpose:** Identify formalization opportunities and map paper claims to existing Lean 4 declarations.  
**Input:** One original paper plus its `paper_uuid` and extracted atoms/axiom nodes.  
**Output:** `lean4.json` — formal verification candidate packets.  

---

## Task

For each mathematically or formally relevant claim in the paper, either:

1. Find an existing Lean 4 declaration that corresponds to it, or
2. Propose a formalization target with definitions, assumptions, and a precise proposition.

Use the **Formal Packet — {{claim ID}}** template (`00_FULL_LEAN_TEMPLATE.md`) as the output shape for each formal candidate.

---

## Output schema

```json
{
  "station": "lean4",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "template": "00_FULL_LEAN_TEMPLATE.md",
  "formal_candidates": [
    {
      "identity": {
        "claim_id": "<atom_uuid>",
        "candidate_uuid": "<uuid>"
      },
      "source_selection": {
        "exact_source_expression": "",
        "selection_disposition": "FORMALIZE|REFERENCE|NOT_FORMALIZABLE",
        "reason": ""
      },
      "formal_object": {
        "object_type": "DEFINITION|THEOREM|LEMMA|AXIOM|CONJECTURE",
        "exact_proposed_statement": "",
        "fully_qualified_declaration": "",
        "project_root": "",
        "module": ""
      },
      "symbol_table": [
        {
          "term": "",
          "formal_definition": "",
          "reader_meaning": "",
          "source_correspondence": ""
        }
      ],
      "assumptions_and_dependencies": {
        "explicit_premises": [],
        "custom_axioms": [],
        "theological_starting_premises": "",
        "non_vacuity_requirement": ""
      },
      "verification_controls": [
        {
          "check": "module compilation|declaration inspection|axiom dependency|proof escape|non-vacuity|negative control|countermodel|ablation|independent encoding",
          "command_or_evidence": "",
          "status": "NOT_RUN|PASS|FAIL|NOT_APPLICABLE",
          "interpretation": ""
        }
      ],
      "result_and_boundary": {
        "verification_status": "NOT_ATTEMPTED|CANDIDATE|IN_PROGRESS|LEAN_CERTIFIED|FAILED",
        "what_is_established": "",
        "what_remains_open": "",
        "encoding_fidelity_review": "",
        "interpretive_connections": ""
      },
      "reproduction_receipt": {
        "run_id": "",
        "timestamp": "",
        "source_hashes": {},
        "commands": [],
        "exit_codes": [],
        "log_paths": [],
        "declarations_checked": []
      },
      "corpus_links": {
        "human_companion": "",
        "corpus_claim_register": "",
        "supporting_summaries": []
      }
    }
  ],
  "existing_matches": [
    {
      "claim_id": "<atom_uuid>",
      "declaration_name": "",
      "module": "",
      "build_result": "BUILT_OK|BUILD_FAILED|NOT_BUILT",
      "trust_status": "CLEAN|CONTAINS_SORRY|...",
      "correspondence": "EXACT|PARTIAL|MODEL_ONLY|PROPOSED|DISPUTED"
    }
  ],
  "notes": ""
}
```

---

## Rules

1. Do not invent a theorem from a missing-document routing question.
2. Lack of an attached proof is not evidence that no proof exists in the corpus.
3. Distinguish `NOT_SEARCHED` from `NOT_FOUND_IN_SEARCHED_SCOPE`.
4. A successful build does not establish physical, historical, or theological premises.
5. Record the exact Lean declaration name, module, repository revision, and toolchain version when a match exists.
6. Every formal candidate must state what it does **not** establish.
