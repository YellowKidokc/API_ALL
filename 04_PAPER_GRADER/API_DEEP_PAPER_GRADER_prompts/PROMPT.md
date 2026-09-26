# PAPER_GRADER Station Prompt

**Station ID:** `paper_grader`  
**Purpose:** Grade a paper across multiple dimensions using a declared rubric.  
**Input:** One original paper plus its `paper_uuid` and outputs from other stations (atoms, axiom_nodes, coherence, etc.).  
**Output:** `paper_grader.json` — rubric-based assessment.  

---

## Task

Assess the paper across the ten CKG sections plus framework alignment dimensions. Produce per-section grades with reasons, not numerical roll-ups unless a compatible rubric supports them.

---

## Output schema

```json
{
  "station": "paper_grader",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "status": "NOT_RUN|ASSESSED",
  "rubric_version": "1.0",
  "overall": {
    "summary": "",
    "strengths": [],
    "weaknesses": [],
    "open_questions": []
  },
  "section_results": [
    {
      "section": "S01 Classification|S02 Claim Definition|S03 Argument Structure|S04 Evidence|S05 Objections|S06 Boundaries|S07 Formal & Math|S08 Bridges|S09 Falsifiability|S10 Audit",
      "assessment": "NOT_ASSESSED|NOT_APPLICABLE|ASSESSED",
      "positive": "",
      "negative": "",
      "net": "",
      "ceiling": "",
      "reasons": [],
      "receipt": ""
    }
  ],
  "framework_alignment": {
    "master_equation": {"assessment": "", "reasons": []},
    "axiom_use": {"assessment": "", "reasons": []},
    "fruits_alignment": {"assessment": "", "reasons": []},
    "lean_applicability": {"assessment": "", "reasons": []},
    "internal_coherence": {"assessment": "", "reasons": []}
  },
  "scorecard": {
    "score_total": null,
    "score_ceiling": null,
    "coherence": null,
    "evidence_balance": null,
    "evidence_coverage": null
  },
  "improvement_path": [
    {"heading": "", "assessment": "", "reason": "", "next_improvement": ""}
  ],
  "notes": ""
}
```

---

## Rules

1. Default every section to `NOT_ASSESSED`. Do not fabricate zeros or grades.
2. Every grade must have reasons and a receipt pointing to the source span or station output.
3. Framework alignment is not evidence of truth.
4. Numerical scores require a declared compatible rubric; otherwise leave null.
5. Identify the weakest load-bearing link and affected conclusions.
