# COHERENCE_SCORE Station Prompt

**Station ID:** `coherence_score`
**Purpose:** Assess internal coherence among a paper's claims, definitions, and assumptions.
**Input:** One original paper plus its paper_uuid and extracted atoms.
**Output:** `coherence_score.json` — coherence assessment with structured reasons.

---

## Task

Evaluate how well the paper's claims, definitions, and assumptions work together without fighting. Identify contradictions, unresolved tensions, missing definitions, and inferential gaps. Produce both a qualitative assessment and, when possible, a quantitative score.

## Output schema

```json
{
  "station": "coherence_score",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "overall": {
    "score": null,
    "score_ceiling": 10,
    "status": "NOT_ASSESSED|ASSESSED",
    "summary": "one-sentence assessment"
  },
  "dimensions": [
    {
      "name": "internal_consistency|definitional_stability|inferential_connectedness|register_boundary_respect",
      "score": null,
      "reasons": ["..."],
      "affected_atom_uuids": ["<uuid>"]
    }
  ],
  "contradictions": [
    {
      "atoms": ["<uuid>", "<uuid>"],
      "description": "...",
      "severity": "definitional|local|structural"
    }
  ],
  "tensions": [...],
  "missing_definitions": [...],
  "notes": ""
}
```

## Rules

1. A high coherence score does not imply truth; a low score does not imply falsity.
2. Every score must be accompanied by reasons and affected atom UUIDs.
3. Distinguish real contradictions from mere tension or underdetermination.
4. Report missing definitions as open items, not as automatic defects.
