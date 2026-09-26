STATION 09 — SERIES CONTINUITY + CROSS-REFERENCE
==================================================
Provider: Anthropic Sonnet | Temp: 0.2 | Output: JSON
RETRIEVER: folder (set RETRIEVER_PATH to the series folder)

Cross-reference audit within a multi-article series: forward/backward
references, thread tracking, repeated introductions, contradictions,
ordering conflicts, arc contribution. Needs RETRIEVER_PATH pointed at
the series folder so it can pull sibling articles for context.

SETUP: Edit config.txt and set RETRIEVER_PATH to the series folder:
  RETRIEVER_PATH=D:\GitHub\faiththruphysics-site-data\mda
  RETRIEVER_PATH=D:\GitHub\faiththruphysics-site-data\gtq
Rubric drawn from: writing-analyzer/prompts/06_ONE_series_evaluation.txt
