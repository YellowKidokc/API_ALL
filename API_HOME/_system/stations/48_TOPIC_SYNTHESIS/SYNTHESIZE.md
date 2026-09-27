You receive one cross-referenced ARGUMENT CLUSTER: the same argument as it appears in several sources (each member names
its source key, quote or timestamp, and who the source attributes it to). Write the strongest honest version of it.
- title: a short name for the argument
- strongest_form: one paragraph, the best formulation any member supports
- steps: the premises in their strongest order
- lineage: who holds it, ONLY from the members' attributed_to and source keys; relation = source | parallel | develops | contrasts.
  If you add a scholar from general knowledge, put it in uncertain_citations with "verify": true, never in lineage.
- objections: the strongest objections (from members first, then general knowledge marked "from general knowledge"),
  each with best_reply and reply_strength 0-5
- evidence_strength 0-5 and rigor 0-5, with one line why
- one_line: the argument in one sentence a reader will remember
Do not write citations; the report builds them from the source keys.

Return: {"title": "", "strongest_form": "", "steps": [], "lineage": [{"who": "", "source_key": "", "relation": ""}],
 "objections": [{"objection": "", "origin": "members|general knowledge", "best_reply": "", "reply_strength": 0}],
 "evidence_strength": 0, "rigor": 0, "why": "", "uncertain_citations": [{"who": "", "what": "", "verify": true}],
 "one_line": "", "focus_findings": []}
