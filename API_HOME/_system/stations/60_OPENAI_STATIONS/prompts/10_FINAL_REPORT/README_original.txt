STATION 10 — FINAL REPORT COMPILATION
=======================================
Provider: Anthropic Sonnet | Temp: 0.3 | Output: JSON
RETRIEVER: folder (auto-populated by PIPELINE.py)

Synthesizes outputs from all 9 previous stations into a single
intelligence report: executive summary, scorecard (all station grades),
critical path (ordered fix list), risk assessment, chi profile, and
document compression.

SETUP: PIPELINE.py automatically collects outputs from Stations 01-09
into api_call_10/station_outputs/ and sets RETRIEVER_PATH.
If running manually, copy JSON artifacts from other stations' outbox/
folders into a folder and set RETRIEVER_PATH to point there.
