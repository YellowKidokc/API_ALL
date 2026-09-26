# Paper Snapshot Schema

Purpose: one-screen scientific triage for a paper, axiom page, proof page, or ISO page.

The snapshot is not the whole paper, the whole proof explorer, or a public marketing page. It answers:

> What is being claimed, what kind of claim is it, what supports it, what would break it, and why should a physicist keep reading?

## Required Boxes

1. Paper ID / Identity Strip
2. One-Sentence Claim
3. Claim Maturity Level
4. FACTS Snapshot
5. 7Q Mini Grid
6. Forward / Reverse Test
7. Evidence Bar
8. Kill Conditions
9. Not Claimed

All boxes should be scannable when closed. Deeper details can be expandable.

## Claim Maturity Ladder

```text
1 Metaphor
2 Analogy
3 Structural Correspondence
4 Formal Model
5 Machine-Checked Theorem
6 Empirical Support
7 Public Proof Claim
```

## JSON Shape

```json
{
  "snapshot": {
    "paper_id": "FP-005",
    "title": "The Turtles and the Floor",
    "type": "Foundational Paper",
    "domain": ["Physics", "Theology", "Information Theory"],
    "status": "Published",
    "version": "1.0",
    "word_count": 910,
    "last_updated": "2026-04-26",
    "one_sentence_claim": "This paper argues that the Cross/Pentecost sequence can be modeled as irreversible coupling-architecture modification, with stated formal, empirical, and theological constraints.",
    "maturity": {
      "level": 4,
      "label": "Formal Model",
      "boundary": "Lean verifies internal structure only; empirical and theological claims remain separately tested."
    },
    "facts": {
      "frame": "The anomaly is missing composition, not a missing component.",
      "admit": "Dual-substrate model is speculative; key parameter derivation is incomplete; categorical construction is incomplete.",
      "claim": "The sequence is structurally coherent under irreversible coupling modification.",
      "test": "Check symmetry-breaking, energy accounting, parameter derivation, EM invisibility, historical discontinuity.",
      "snap": "One fatal kill condition breaks the model; multiple prediction failures collapse it."
    },
    "seven_q": {
      "q0_posture": "Structural correspondence is tested, not assumed.",
      "q1_identity": "The object is a claimed substrate-transition model.",
      "q2_domain": "Physics <-> Theology.",
      "q3_claim": "Irreversible coupling modification explains the sequence.",
      "q4_support": "Formal structure, analogy class, evidence hooks.",
      "q5_dependencies": "Requires prior framework layers and valid physical operation.",
      "q6_consequences": "If true, theology and physics share constrained architecture.",
      "q7_kill_conditions": "Reversibility, failed conservation, failed parameter derivation, categorical contradiction."
    },
    "forward_reverse": {
      "forward": "Physics predicts theological structure.",
      "reverse": "Theology predicts physical constraint."
    },
    "evidence": {
      "formal": ["Lean4 theorem compiled"],
      "physics": ["SSB / irreversible coupling model", "Thermodynamic audit pending"],
      "empirical": ["Historical discontinuity claim", "EM invisibility check"],
      "theological": ["Cross/Pentecost sequence"]
    },
    "kill_conditions": {
      "fatal": [
        "SSB reversible in required limit",
        "Energy non-conserved across full arc",
        "Key parameter derivation fails",
        "Unexpected EM signature appears",
        "Categorical contradiction found"
      ],
      "wounding": [
        "Historical record contradicts P1",
        "Auxiliary object shown unnecessary"
      ]
    },
    "not_claimed": [
      "Physics proves theology.",
      "The model is empirically complete.",
      "Lean proves the external reality of the event."
    ]
  }
}
```

## UI Rule

The closed view must fit on one screen at desktop size. The expanded view may reveal:

- Full 7Q fields
- Full kill-condition test descriptions
- Evidence table
- Dependency chain
- Lean file links
- Claim audit rows

## Tone Rule

For physicists, the snapshot should lead with structure, falsifiability, and proof boundary. It should not lead with persuasion.


