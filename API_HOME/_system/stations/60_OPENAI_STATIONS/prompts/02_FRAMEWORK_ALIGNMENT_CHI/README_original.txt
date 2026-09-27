STATION 02 — THESIS + CLAIM INVENTORY
======================================
Provider: Anthropic Sonnet (reasoning)
Temperature: 0.2
Output: JSON

PURPOSE:
Extracts and classifies every claim in the document:
- Stated thesis vs actual thesis (gap detection)
- Claims classified: load-bearing / suggestive / overreached / definitional
- Claim types: empirical, mathematical, theological, interpretive, structural, predictive
- Confidence levels the document itself uses
- Dependency chains between claims

Rubric drawn from: writing-analyzer/prompts/13_generate_claims_json.txt

INPUT: Drop any document into inbox/
OUTPUT: JSON with thesis analysis and classified claim inventory
