# MASTER_EQUATION Station Prompt

**Station ID:** `master_equation`  
**Purpose:** Extract, validate, or relate the paper's mathematical structure to the project's master equation framework.  
**Input:** One original paper plus its `paper_uuid` and extracted atoms.  
**Output:** `master_equation.json` — master equation analysis.  

---

## Task

Identify equations, mathematical objects, and quantitative claims in the paper. Determine whether they instantiate, approximate, contradict, or are independent of the master equation. Record symbols, units, dimensional checks, and boundaries.

---

## Output schema

```json
{
  "station": "master_equation",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "master_equation_analysis": {
    "references_master_equation": false,
    "reference_spans": [],
    "relationship": "instantiates|approximates|contradicts|independent|not_assessable",
    "reason": ""
  },
  "equations": [
    {
      "equation_id": "<uuid>",
      "exact_expression": "",
      "plain_meaning": "",
      "symbols": [
        {"symbol": "", "definition": "", "units_or_type": "", "scope": ""}
      ],
      "types_domain_codomain": "",
      "units": "",
      "premises_and_boundary_conditions": "",
      "status": "proposed|defined|derived|checked|open",
      "dimensional_check": "PASS|FAIL|NOT_RUN|NOT_APPLICABLE",
      "source_span": "",
      "atom_uuids": ["<uuid>"]
    }
  ],
  "symbol_dictionary": [
    {"symbol": "", "definition": "", "scope": "", "alternative_uses": [], "definition_link": "<uuid>"}
  ],
  "dimensional_issues": [],
  "notes": ""
}
```

---

## Rules

1. Preserve exact equations; do not normalize away notation that carries meaning.
2. Every symbol must have a declared definition and scope.
3. Dimensional checks are mandatory for physical quantities.
4. A reference to the master equation must cite the exact span; do not infer relationship from vague similarity.
5. Mark `not_assessable` when the paper lacks enough mathematical content.
