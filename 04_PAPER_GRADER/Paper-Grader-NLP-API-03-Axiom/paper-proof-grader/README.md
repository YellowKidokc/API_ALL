# Paper Proof Grader

This workflow is the planned intake for Genesis to Quantum and other formal papers.

## Intended Flow

```text
paper in
-> text extraction
-> raw metrics
-> section detection
-> claim extraction
-> 7QS forward/reverse analysis
-> DeBERTa zero-shot scoring
-> axiom proof snapshot
-> polished HTML / Markdown / JSON / Excel report
-> vectorized report summary
```

## Main Inputs

Drop papers here in local workflow mode:

```text
X:\brain\00_WORKFLOWS\paper-proof-grader\DROP_PAPERS_HERE
```

Supported first-pass formats:

```text
.txt
.md
.html
.htm
```

Planned formats:

```text
.pdf
.docx
```

## Main Outputs

Workflow outputs:

```text
X:\brain\00_WORKFLOWS\paper-proof-grader\OUTPUT
```

Archived originals:

```text
X:\brain\00_WORKFLOWS\paper-proof-grader\ARCHIVE
```

Readable report copies:

```text
O:\Vault\AI Chats\Paper Proof Grader Reports
```

Vector collection:

```text
Qdrant: http://192.168.1.177:6333
collection: paper_proof_grader
```

## Existing Tools To Reuse

```text
D:\brain\03_DEBERTA
D:\brain\08_CLAIMS
X:\brain\00_WORKFLOWS\link-pull-drop
```

## Build Order

1. Deterministic raw metrics.
2. Claim extractor bridge.
3. DeBERTa scoring labels for paper/axiom/7QS review.
4. Markdown and JSON report.
5. Polished HTML report.
6. Excel export.
7. Vectorized report summary.
