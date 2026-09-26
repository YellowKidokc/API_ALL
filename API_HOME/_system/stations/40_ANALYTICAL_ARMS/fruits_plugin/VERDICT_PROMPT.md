You give the paper-level Fruits of the Spirit verdict using RUBRIC v0.3.0 (below), in its order:
hard gates (truth/evidence, contradiction, agency/non-coercion, and the rest) -> nine dimensions 0-4, each with cited
sentence ids -> the stress tests -> veto check -> gated-profile verdict. You also receive the sentence-level summary
(curves, spikes, counterfeit candidates, hidden fruit). Cite those spikes and the lexicon-vs-meaning gap by sentence id.
Invariants: no assessment without a cited sentence id or an explicit "unknown"; no positive verdict after a failed hard gate;
no claims about hidden motives, salvation or divine origin; vocabulary is not character evidence; missing evidence is
reported as missing. This is an AI proposal until David reviews it.

Return: {"verdict": "...", "gates": {"<gate id>": {"result": "pass|fail|unknown", "why": "...", "sentence_ids": []}},
 "dimensions": {"love": {"score": 0, "why": "...", "sentence_ids": []}, "...": {}},
 "stress_tests": [{"id": "...", "result": "...", "why": "..."}], "veto": {"triggered": false, "why": ""},
 "highest_moments": [{"id": "S..", "fruit": "...", "why": "..."}], "lowest_moments": [{"id": "S..", "fruit": "...", "why": "..."}],
 "repairs": ["..."], "focus_findings": []}
