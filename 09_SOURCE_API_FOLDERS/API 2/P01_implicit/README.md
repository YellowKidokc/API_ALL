# 13 — Implicit (Collaborative Filtering)

**Library:** `implicit` (pip installed, 3.8k GitHub stars)
**Type:** Item recommendation via matrix factorization (ALS, BPR, logistic MF)
**Use case:** "Files/apps David uses together" — if you open Obsidian after Claude, recommend Obsidian next time you're in Claude.
**Model size:** Tiny — sparse matrix of user-item interactions
**Status:** Installed, not yet wired

## How it connects to PPK

PPK routes files to stations. Implicit learns which stations co-occur — "David always runs claim-extractor THEN paper-proof-grader on the same file." It recommends the second station before David asks.

## Quick test
```python
import implicit
print("implicit ready")
```
