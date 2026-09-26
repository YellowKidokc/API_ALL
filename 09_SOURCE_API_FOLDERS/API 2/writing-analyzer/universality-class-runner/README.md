# Universality Class Runner

Applies the universality class test (prompt 11) against MDA and GTQ corpora.
Compares DeepSeek and OpenAI O3 responses side by side.

## What this tests

The correct mathematical classification of the cross-domain findings:
- NOT isomorphism (domains are not isomorphic to each other)
- NOT analogy (too weak, no formal content)
- CORRECT: Each domain is an independent MODEL of the same formal THEORY T

T has 10 axioms (the 10 laws). A domain passes when it satisfies 7+ axioms with textual evidence.

## How to run

From the writing-analyzer directory:
  RUN_UNIVERSALITY.bat

## Output files

  run_TIMESTAMP/
    mda_deepseek.md       — MDA corpus × DeepSeek
    mda_o3.md             — MDA corpus × OpenAI O3
    gtq_deepseek.md       — GTQ corpus × DeepSeek
    gtq_o3.md             — GTQ corpus × OpenAI O3
    summary.md            — Side-by-side comparison of key findings
