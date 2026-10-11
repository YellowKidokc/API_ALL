You are writing the formal record of a Lean 4 source (or a claim written for Lean) for David Lowe's Theophysics work,
for readers who know Lean and formal verification. The source is below, whole, with line numbers (L1, L2, ...), and
its assumptions have already been listed (ASSUMPTIONS, ids A1 ...).

Pick the declarations that carry the source's argument (at most 12) as CLAIMS. Every other declaration goes in
"other_declarations" by name only.

Return one JSON object:
{"claims": [{"claim_id": "C1", "title": "short name",
             "source_expression": "the exact source text the claim formalizes (quote)",
             "disposition": "FORMALIZE | REFERENCE | NOT_FORMALIZABLE", "disposition_reason": "",
             "object_type": "DEFINITION | THEOREM | LEMMA | AXIOM | CONJECTURE",
             "statement": "the exact Lean statement (quote the source when it exists; otherwise the proposed statement)",
             "declaration": "fully qualified name", "module": "",
             "symbols": [{"term": "", "formal_definition": "", "reader_meaning": ""}],
             "controls": [{"check": "module compilation | axiom dependency | proof escape | non-vacuity | negative control | countermodel | independent encoding",
                           "command_or_evidence": "the command to run, or the line in the source that records a result",
                           "status": "NOT_RUN | PASS | FAIL | NOT_APPLICABLE", "interpretation": ""}],
             "verification_status": "NOT_ATTEMPTED | CANDIDATE | IN_PROGRESS | FAILED",
             "established": "what the claim establishes IF it compiles, stated narrowly",
             "open": "what remains open",
             "fidelity": "does the formal statement say what the prose claim says? where does it differ?",
             "uses_assumptions": ["A1", "A3"]}],
 "other_declarations": ["name", ...]}

Rules:
1. Do not restate the assumptions inside a claim: point to them by id in uses_assumptions only.
2. You have not compiled anything. A control is PASS only when the source itself records the result, and then
   command_or_evidence must cite the line (e.g. "L88: #print axioms ... shows no sorryAx").
3. LEAN_CERTIFIED is never yours to give; the compiler gives it later.
4. A successful build would not establish physical, historical or theological premises: say so in "open" when relevant.
