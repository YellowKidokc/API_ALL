---
type: dashboard
title: "Evidence Dashboard — Vault-Wide"
template_version: "v0.3"
tags: [dashboard, theophysics]
---

# Evidence Dashboard — Vault-Wide
**POF 2828 | The corpus at a glance**
*Every note with `type: evidence-sheet` rolls up here. Sorted so the weakest load-bearing claim with the most riding on it is on top. This page reads frontmatter only — it cannot tell you a claim is true; it tells you which sheet to open next.*

---

## 🔥 Gated — resolve first

Papers with a verified counterexample open. These are your fires.

```dataview
TABLE WITHOUT ID
  file.link AS Paper,
  clean_title AS Title,
  domain AS Domain,
  evd_weakest_claim AS "Gated / weakest",
  evd_support AS Support,
  evd_counter AS Counter,
  evd_families AS Families,
  paper_rating AS Rating
FROM ""
WHERE type = "evidence-sheet" AND evd_gated = true
SORT evd_counter DESC
```

---

## ⚠️ Unscored — coverage below floor

Papers still at UNSCORED. How much of the question bank got answered?

```dataview
TABLE WITHOUT ID
  file.link AS Paper,
  clean_title AS Title,
  domain AS Domain,
  round(evd_coverage * 100) + "%" AS Coverage,
  evd_unassessed AS "Unassessed / stale",
  evd_families AS Families,
  content_type AS Type
FROM ""
WHERE type = "evidence-sheet" AND evd_state = "UNSCORED"
SORT evd_coverage DESC
```

---

## ✅ Scored — by weakest load-bearing claim

Scored papers, sorted worst-first. The one most likely to break is on top.

```dataview
TABLE WITHOUT ID
  file.link AS Paper,
  clean_title AS Title,
  domain AS Domain,
  evd_balance AS Balance,
  evd_weakest_claim AS "Weakest claim",
  choice(evd_stable, "stable", "FLIPS") AS Robustness,
  evd_families AS Families,
  round(evd_coverage * 100) + "%" AS Coverage,
  coherence AS Coherence,
  paper_rating AS Rating
FROM ""
WHERE type = "evidence-sheet" AND evd_state = "SCORED"
SORT evd_balance ASC
```

---

## ⚖️ Scoring-dependent verdicts

Papers whose verdict FLIPS under ±25% weights or cap ±1. These results depend on how we chose to score, not on the evidence.

```dataview
TABLE WITHOUT ID
  file.link AS Paper,
  clean_title AS Title,
  evd_balance AS Balance,
  evd_weakest_claim AS "Weakest claim",
  domain AS Domain
FROM ""
WHERE type = "evidence-sheet" AND evd_state = "SCORED" AND evd_stable = false
SORT evd_balance ASC
```

---

## 🤖 Machine-only assessments

No human appears in the assessor list. Nothing here is admissible until a human ruling is recorded.

```dataview
TABLE WITHOUT ID
  file.link AS Paper,
  clean_title AS Title,
  domain AS Domain,
  evd_assessors AS Assessors,
  paper_rating AS Rating,
  rating_awarded_by AS "Awarded by"
FROM ""
WHERE type = "evidence-sheet" AND !contains(evd_assessors, "David")
SORT paper_rating DESC
```

---

## 📊 Coherence vs Evidence

Two axes kept apart. High coherence + low balance = well-built argument with no evidence. Low coherence + high balance = evidence without a structure to carry it.

```dataview
TABLE WITHOUT ID
  file.link AS Paper,
  clean_title AS Title,
  coherence AS Coherence,
  evd_balance AS Balance,
  evd_state AS State,
  domain AS Domain
FROM ""
WHERE type = "evidence-sheet" AND coherence != null
SORT coherence DESC, evd_balance ASC
```

---

## 📈 Status roll-up

```dataview
TABLE WITHOUT ID
  status AS Status,
  length(rows) AS Sheets,
  round(sum(rows.evd_families)) AS "Total families"
FROM ""
WHERE type = "evidence-sheet"
GROUP BY status
```

---

## 🗂️ By Domain

```dataview
TABLE WITHOUT ID
  domain AS Domain,
  length(rows) AS Papers,
  round(average(rows.paper_rating), 1) AS "Avg rating",
  min(rows.evd_balance) AS "Weakest balance",
  round(average(rows.evd_coverage) * 100) + "%" AS "Avg coverage"
FROM ""
WHERE type = "evidence-sheet"
GROUP BY domain
SORT length(rows) DESC
```

### Physics
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, evd_balance AS Balance,
  paper_rating AS Rating, evd_state AS State
FROM "" WHERE type = "evidence-sheet" AND domain = "Physics"
SORT evd_balance ASC
```

### Theology
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, evd_balance AS Balance,
  paper_rating AS Rating, evd_state AS State
FROM "" WHERE type = "evidence-sheet" AND domain = "Theology"
SORT evd_balance ASC
```

### Ontological
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, evd_balance AS Balance,
  paper_rating AS Rating, evd_state AS State
FROM "" WHERE type = "evidence-sheet" AND domain = "Ontological"
SORT evd_balance ASC
```

### Mathematics
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, evd_balance AS Balance,
  paper_rating AS Rating, evd_state AS State
FROM "" WHERE type = "evidence-sheet" AND domain = "Mathematics"
SORT evd_balance ASC
```

### Consciousness
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, evd_balance AS Balance,
  paper_rating AS Rating, evd_state AS State
FROM "" WHERE type = "evidence-sheet" AND domain = "Consciousness"
SORT evd_balance ASC
```

### Information Theory
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, evd_balance AS Balance,
  paper_rating AS Rating, evd_state AS State
FROM "" WHERE type = "evidence-sheet" AND domain = "Information Theory"
SORT evd_balance ASC
```

### Philosophy
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, evd_balance AS Balance,
  paper_rating AS Rating, evd_state AS State
FROM "" WHERE type = "evidence-sheet" AND domain = "Philosophy"
SORT evd_balance ASC
```

### Cosmology
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, evd_balance AS Balance,
  paper_rating AS Rating, evd_state AS State
FROM "" WHERE type = "evidence-sheet" AND domain = "Cosmology"
SORT evd_balance ASC
```

<!-- Add more domain sections as the closed vocabulary finalizes -->

---

## 📋 By Content Type

```dataview
TABLE WITHOUT ID
  content_type AS "Content Type",
  length(rows) AS Papers,
  round(average(rows.paper_rating), 1) AS "Avg rating"
FROM ""
WHERE type = "evidence-sheet"
GROUP BY content_type
SORT length(rows) DESC
```

---

## 🎯 By Chapter (ONE_STORY)

```dataview
TABLE WITHOUT ID
  chapter AS Chapter,
  length(rows) AS Papers,
  round(average(rows.paper_rating), 1) AS "Avg rating",
  sum(rows.evd_families) AS "Total families",
  round(average(rows.evd_coverage) * 100) + "%" AS "Avg coverage"
FROM ""
WHERE type = "evidence-sheet" AND chapter != null
GROUP BY chapter
SORT chapter ASC
```

---

## 🔬 Formal status

```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, formal_status AS "Formal status",
  lean_receipts AS Receipts, domain AS Domain
FROM ""
WHERE type = "evidence-sheet" AND formal_status != "NOT_ESTABLISHED"
SORT formal_status DESC
```

---

## 📉 Negative ratings (failed tests — never deleted)

```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, paper_rating AS Rating,
  rating_awarded_by AS "Awarded by", domain AS Domain,
  evd_weakest_claim AS "Weakest claim"
FROM ""
WHERE type = "evidence-sheet" AND paper_rating < 0
SORT paper_rating ASC
```

---

## 🏆 Highest rated

```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, paper_rating AS Rating,
  rating_awarded_by AS "Awarded by", domain AS Domain,
  formal_status AS "Formal", evd_state AS State
FROM ""
WHERE type = "evidence-sheet" AND paper_rating > 0
SORT paper_rating DESC
LIMIT 25
```

---

## 🔍 Custom filters

### Papers with Lean receipts
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, lean_receipts AS Receipts,
  paper_rating AS Rating
FROM ""
WHERE type = "evidence-sheet" AND length(lean_receipts) > 0
SORT paper_rating DESC
```

### Papers with no claims extracted
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, domain AS Domain,
  evd_coverage AS Coverage
FROM ""
WHERE type = "evidence-sheet" AND length(claim_ids) = 0
```

### Recently processed
```dataview
TABLE WITHOUT ID
  file.link AS Paper, clean_title AS Title, processed_date AS Processed,
  semantic_model AS Model, domain AS Domain
FROM ""
WHERE type = "evidence-sheet" AND processed_date != null
SORT processed_date DESC
LIMIT 20
```

---

## Corpus totals

```dataview
TABLE WITHOUT ID
  "Total papers" AS Metric, length(rows) AS Value
FROM ""
WHERE type = "evidence-sheet"
GROUP BY true
```

```dataview
TABLE WITHOUT ID
  "Avg coverage" AS Metric,
  round(average(rows.evd_coverage) * 100) + "%" AS Value
FROM ""
WHERE type = "evidence-sheet"
GROUP BY true
```

```dataview
TABLE WITHOUT ID
  "Avg rating" AS Metric,
  round(average(rows.paper_rating), 1) AS Value
FROM ""
WHERE type = "evidence-sheet"
GROUP BY true
```

---

_The dashboard reads frontmatter only. It cannot tell you a claim is true; it tells you which sheet to open next._

_POF 2828 · not a probability of truth · human ruling required_
