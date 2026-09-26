# FRUITS Station Prompt

**Station ID:** `fruits`
**Purpose:** Evaluate the paper's alignment with the Fruits of the Spirit framework.
**Input:** One original paper plus its paper_uuid.
**Output:** `fruits.json` — fruits-of-the-spirit assessment.

---

## Task

Assess how the paper embodies or fails to embody the Fruits of the Spirit (love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, self-control). This is an interpretive review, not a truth verification. Report honest negatives and positives.

## Output schema

```json
{
  "station": "fruits",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "status": "NOT_ASSESSED|ASSESSED|NOT_APPLICABLE",
  "not_applicable_reason": "",
  "fruits": [
    {
      "fruit": "love|joy|peace|patience|kindness|goodness|faithfulness|gentleness|self-control",
      "assessment": "present|absent|mixed|not_assessable",
      "source_spans": ["span1"],
      "reasons": ["..."],
      "cautions": ["..."]
    }
  ],
  "summary": "...",
  "notes": ""
}
```

## Rules

1. Framework alignment is not evidence of truth or spiritual standing.
2. If the paper is not in the theological domain, mark `NOT_APPLICABLE` with reason.
3. Every judgment must cite source spans.
4. Do not inflate positives to protect the author or inflate negatives to attack.
