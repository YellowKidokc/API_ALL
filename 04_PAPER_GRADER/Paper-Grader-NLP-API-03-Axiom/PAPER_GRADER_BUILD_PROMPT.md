# Prompt For Online Codex - Paper Grader Build

You are building the Paper Grader / NLP API / Axiom Snapshot system.

The goal is a workflow that takes one formal paper and produces:

```text
1. raw deterministic metrics
2. readability metrics
3. section/heading analysis
4. claim inventory
5. evidence map
6. 7Q forward/reverse analysis
7. DeBERTa zero-shot percentage scores
8. formal maturity classification
9. axiom proof snapshot
10. Excel workbook
11. JSON export
12. Markdown report
13. polished HTML report
14. vectorized summary
```

Use the schemas in:

```text
paper-proof-grader/MASTER_VARIABLE_SCHEMA.md
PAPER_SNAPSHOT_SCHEMA.md
snapshot_schema.json
```

## Core Principle

Raw metrics are facts. Review scores are judgments. Final scores are derived summaries.

Do not mix those layers too early.

## First Implementation Target

Build an MVP pipeline that supports:

```text
input: .txt, .md, .html
output: JSON, Markdown, HTML, Excel
```

The first version should work without DeBERTa, Ollama, or external models. Add deterministic metrics first.

## Required Excel Workbook Tabs

```text
00_Dashboard
01_Document_ID
02_Raw_Text_Metrics
03_Readability
04_Structure
05_Claims
06_Evidence_Map
07_7QS
08_Axiom_Proof
09_DeBERTa_Scores
10_Risk_Flags
11_Final_Scores
12_Report_Export
```

## Required Snapshot Boxes

```text
1. Paper ID / Identity Strip
2. One-Sentence Claim
3. Claim Maturity Level
4. FACTS Snapshot
5. 7Q Mini Grid
6. Forward / Reverse Test
7. Evidence Bar
8. Kill Conditions
9. Not Claimed
```

## Docker Requirement

Design the app so NLP model weights are not committed to Git.

Use environment variables for optional services:

```text
QDRANT_URL
INFINITY_URL
OLLAMA_URL
HF_HOME
TRANSFORMERS_CACHE
```

## Build Order

1. Create Python package layout.
2. Implement text extraction for txt/md/html.
3. Implement deterministic raw metrics.
4. Implement simple section detector.
5. Implement claim candidate extraction.
6. Emit JSON report.
7. Emit Markdown report.
8. Emit Excel workbook.
9. Emit HTML report using the snapshot UI style.
10. Add optional vectorization hook.
11. Add optional DeBERTa hook.
12. Add optional Ollama review hook.

Keep the first version simple, testable, and honest.
