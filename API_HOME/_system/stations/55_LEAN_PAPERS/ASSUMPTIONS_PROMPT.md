You are listing every assumption a Lean 4 source (or a claim written for Lean) rests on, for David Lowe's
Theophysics formal work. The source is below, whole, with line numbers (L1, L2, ...).

This list is the ASSUMPTIONS PAPER: it is reviewed by David before anything is run, so it must be complete and exact.
An assumption is anything the conclusions need that the source does not prove:
- explicit_premise: a hypothesis argument or `variable` the theorems take
- custom_axiom: an `axiom` declared in this source
- imported_axiom: an axiom it relies on from elsewhere (propext, Classical.choice, Quot.sound, a project axiom ...)
- definition_choice: a `def`/`structure` whose chosen encoding decides the result (a different faithful encoding could change it)
- physical_premise / theological_premise: a claim about the world or about God that the formal statement stands in for
- hidden: needed but never stated (say why it is needed)
- non_vacuity: what must be shown so the hypotheses are not contradictory or empty
- proof_escape: `sorry`, `admit`, `native_decide` or similar that the result currently depends on

Return one JSON object:
{"assumptions": [{"id": "A1", "kind": "<one of the kinds above>", "statement": "the assumption, exact",
                  "where": "L12 (or L12-L15)", "load_bearing": true, "why": "what breaks without it (one sentence)"}],
 "assumptions_paper": "Markdown: a short paper that walks through the assumptions in order of importance, what each one
                       commits you to, and which are the weakest. Formal register. No verdicts on truth."}

Number the ids A1, A2, ... in order of appearance. Quote Lean exactly. Never say something was compiled or checked.
