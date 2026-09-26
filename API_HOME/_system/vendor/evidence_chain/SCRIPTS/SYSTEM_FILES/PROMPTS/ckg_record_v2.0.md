# CKG_RECORD_V2.0

This is the fixed completion contract for a source-pinned CKG knowledge record.
Return the required fourteen `##` headings in exactly the supplied order. Do
not reproduce the preserved source. Do not use placeholders such as `[OPEN]`
or `not run`. Every answer must be grounded in the supplied source, and must
distinguish a source statement from an inference, a formal consequence, an
empirical claim, or a philosophical/theological interpretation.

## Universal epistemic ledger rules

* **What survives** states the narrowest claim that remains defensible after
  the strongest objection. Name the supporting basis; do not simply repeat the
  central claim.
* **What this does not establish** sets hard boundaries. State nearby claims
  that are not earned, including the difference between a formal result, an
  empirical result, and a philosophical or theological interpretation. A proof
  of encoded premises is not proof that those premises describe the world.
* **Formal or testable path** says what could change the atom's standing. It
  must use exactly these labeled subsections: `### Lean / formal checks`,
  `### Empirical / literature checks`, and `### Adversarial checks`.

In the Lean section, include a compact table with: proposed theorem or
invariant; definitions and premises to encode; status (`likely structurally
provable`, `requires new axioms or definitions`, or `not yet formalizable from
source`); reader meaning / analogy; and exactly what a passing result
establishes. A Lean proof verifies encoded definitions and premises only. It
does not establish physical instantiation or theological identity. The other
two sections give empirical, literature, and counterexample tests with a
pass/fail condition where possible.

## Reader bridge rule

In **System or model**, include a `### Terms and plain-language bridge`
subsection. Define every source term, symbol, operator, or equation needed to
understand the claim that is likely above a ninth-grade reading level. For each,
give: exact role in this source; plain-language meaning; and one common-sense
analogy or concrete example. An analogy may clarify structure but is never
evidence or proof.

## Classification rule

The final classification section must identify all applicable domains, subjects
and tags, claim type, evidence type, and formal status. Many-to-many
classification is expected: do not force a cross-domain source into a single
folder. Classification is navigation, not canon admission or proof of truth.
