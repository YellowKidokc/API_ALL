STATION 01 — RAW METRICS
========================
Provider: DeepSeek (cheap)
Temperature: 0.1 (deterministic)
Output: JSON

PURPOSE:
Extracts raw numerical metrics from any document without interpretation:
- Word/sentence/paragraph/section counts
- Flesch reading ease and Kincaid grade level
- Vocabulary diversity (type-token ratio)
- Equation density (inline/display math, variable mentions)
- Citation markers (academic, data, scripture)
- Structural markers (definitions, claims, hedges, objections, transitions)
- Document type classification

This is the cheapest station — runs first, provides baseline numbers
that other stations can reference.

INPUT: Drop any .md, .txt, .html, or .json file into inbox/
OUTPUT: JSON metrics report in outbox/
