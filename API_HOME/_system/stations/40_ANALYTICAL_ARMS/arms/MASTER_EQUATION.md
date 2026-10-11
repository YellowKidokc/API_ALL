MASTER_EQUATION station V2, Part A: what in this paper plays the role of the master equation?
This is subjective; answer carefully and say where it is subjective.

REFERENCE: chi_total = integral over t and Omega of G*M*E*S_eff*T*K*R*Q*F*C (ME-EQ-001); locally chi = G*M*E*S_eff*T*K*R*Q*F*C (ME-EQ-002).
The factors multiply: if any required factor is zero, the whole collapses (zero-collapse, ME-EQ-006).
SLOTS (meanings below).

1. The paper's own core relation: one sentence stating what everything else depends on (may be verbal); quote the closest span.
2. Product test (weighted most heavily): if one ingredient is zero or missing, does the conclusion fail entirely
   (multiplicative), only weaken (additive), flip past a threshold (threshold), or is it unclear? Quote the evidence.
3. Slot mapping: for each of the 10 slots, what plays that role, with a quoted span and sentence id, fit =
   direct | analogous | stretched | absent. Absent is a normal answer. Do not fill slots to look complete.
4. Where it breaks: slots the paper treats as optional, factors it adds that have no slot.
5. Overall: analog strength 0-5, confidence low|medium|high, one-line statement. Always an analogy proposal, never a derivation.
Part B only if the paper contains equations: list each (exact expression, symbols, relation to chi:
instantiates | approximates | contradicts | independent).

Return: {"core_relation": {"sentence": "", "quote": "", "sentence_id": ""},
 "product_test": {"answer": "multiplicative|additive|threshold|unclear", "quote": "", "reason": ""},
 "slots": [{"slot": "G", "plays_role": "", "quote": "", "sentence_id": "", "fit": "direct|analogous|stretched|absent"}],
 "breaks": [], "extra_factors": [], "analog_strength": 0, "confidence": "low", "one_line": "",
 "equations": [], "focus_findings": []}
