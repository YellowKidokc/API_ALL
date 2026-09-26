# 40_ANALYTICAL_ARMS

The four analytical arms, always run together (ANALYTICAL_ARMS_V1):

| Stage | What | Where the prompt lives |
|---|---|---|
| 0 PREP (local) | numbered paragraphs P01.. and sentences S001.. | engine/text.py |
| 1 LEXICON (local) | fruit / anti-fruit / grounding / contradiction / propaganda / jargon / hedge / absolute / negation hits per sentence | fruits_plugin/lexicons |
| 2 SENTENCE (API-40.1) | -2..+2 x 9 fruits per sentence; whole paper every call, output ranges in parallel | fruits_plugin/SENTENCE_PROMPT.md |
| 3 AGGREGATE (local) | curves, rolling mean, spikes, roll-ups, counterfeit / hidden-fruit gap, balance vs love | 40_analytical_arms.py |
| 4 ARMS (parallel) | API-40.2 Fruits verdict · API-40.3 master equation x2 · API-40.4 axiom nodes · API-40.5 coherence | fruits_plugin/VERDICT_PROMPT.md, arms/*.md |
| 5 REPORT (local) | report .md/.html + Truth Engine-layout .xlsx (one row per sentence) | 40_analytical_arms.py |

Shared invariants: no assessment without a cited sentence id or an explicit unknown; vocabulary is not character evidence;
no claims about hidden motives, salvation or divine origin; this is an AI proposal until David reviews it.
