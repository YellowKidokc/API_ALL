# AXIOMS PART 1 - Mode Classification

## Purpose
Force every Part 1 entry into a strict mode: `AX_CORE`, `AX_DERIVED`, `AX_SCAFFOLD`, `FW_EXTENDED`, `HY_EVIDENCE`, or `DROP_DUPLICATE`.

## Canonical Inputs Used
- Source summary: `O:\_Theophysics_v5\00_AXIOMS\_LOSSLESS_SUMMARY\AXIOMS_PART1_STRAIGHT.md`
- Strict core + scaffold source: `000_Lean4_Categorization_Dashboard.md`
- Namespace source: `_NAMESPACE_POLICY_AX_FW_HY.md`
- Extended/public category source: `CATEGORY_MAP_18.md`

## Classification Rules
- `AX_CORE`: strict Lean 4 irreducible core.
- `AX_DERIVED`: derivable theorem layer that the dashboard already treats as non-primitive.
- `AX_SCAFFOLD`: definitions and equations needed to formalize computation and proof structure.
- `FW_EXTENDED`: framework commitments, boundary conditions, extended philosophical or theological claims.
- `HY_EVIDENCE`: evidence, experiments, predictions, protocols, hypotheses, and open questions.
- `DROP_DUPLICATE`: duplicate row that should not survive canonical normalization.

## Summary Counts
- Total rows in Part 1: 192
- Unique ids: 191
- Keep in strict core deck: 55
- Move out of strict core: 136
- Kick: 1

## Structural Warning
Any entry marked `UNANCHORED_IN_CURRENT_CHAIN` does not currently trace cleanly to the strict-core roots through the present `depends_on` chain in Part 1. That does not automatically make it false, but it does mean the current chain presentation is not structurally clean enough to treat it as bedrock.

## AX_CORE (7)
- `A1.1` | A1.1 — Existence | decision=`KEEP` | anchor=`A1.1 (Existence)` | class=`🟢 Primitive` | status=`primitive` | why=listed in strict Lean 4 mode as irreducible core
- `A1.2` | A1.2 — Distinction | decision=`KEEP` | anchor=`A1.2 (Distinction)` | class=`🟢 Primitive` | status=`primitive` | why=listed in strict Lean 4 mode as irreducible core
- `A2.1` | A2.1 — Substrate Requirement | decision=`KEEP` | anchor=`A2.1 (Substrate Requirement)` | class=`🟢 Primitive` | status=`primitive` | why=listed in strict Lean 4 mode as irreducible core
- `A2.2` | A2.2 — Self-Grounding | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`⚠️ Stance` | status=`stance` | why=listed in strict Lean 4 mode as irreducible core
- `A5.1` | A5.1 — Observation Requirement | decision=`KEEP` | anchor=`A5.1 (Observation Requirement)` | class=`⚠️ Stance` | status=`stance` | why=listed in strict Lean 4 mode as irreducible core
- `BC4` | BC4 — Three Observers Required | decision=`KEEP` | anchor=`BC4 (Three Observers Required)` | class=`🔶 Boundary` | status=`boundary` | why=listed in strict Lean 4 mode as irreducible core
- `BC6` | BC6 — Infinite Energy Source | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`🔶 Boundary` | status=`boundary` | why=listed in strict Lean 4 mode as irreducible core

## AX_DERIVED (5)
- `A1.3` | A1.3 — Information Primacy | decision=`KEEP` | anchor=`A1.2 (Distinction)` | class=`🟢 Primitive` | status=`primitive` | why=listed in dashboard as derived theorem
- `T3.1` | T3.1 — Coherence Cannot Self-Increase | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`🔷 Theorem` | status=`theorem` | why=listed in dashboard as derived theorem
- `BC2` | BC2 — Grace External To System | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔶 Boundary` | status=`boundary` | why=listed in dashboard as derived theorem
- `BC7` | BC7 — Information Conservation | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`🔶 Boundary` | status=`boundary` | why=listed in dashboard as derived theorem
- `BC8` | BC8 — Voluntary Coupling | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`🔶 Boundary` | status=`boundary` | why=listed in dashboard as derived theorem

## AX_SCAFFOLD (43)
- `D1.1` | D1.1 — Information Definition | decision=`KEEP` | anchor=`A1.1 (Existence), A1.2 (Distinction)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D1.2` | D1.2 — Bit Definition | decision=`KEEP` | anchor=`A1.1 (Existence), A1.2 (Distinction)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D2.1` | D2.1 — Logos Field Definition | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D2.2` | D2.2 — Chi Field Properties | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `E2.1` | E2.1 — Master Equation First Form | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Equation` | status=`equation` | why=listed in dashboard as mathematical definition or equation
- `D3.1` | D3.1 — Coherence Functional Definition | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D3.2` | D3.2 — Self-Interaction Potential | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D3.3` | D3.3 — Interaction Lagrangian | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `E3.1` | E3.1 — Master Coherence Equation | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Equation` | status=`equation` | why=listed in dashboard as mathematical definition or equation
- `E3.2` | E3.2 — Universal Coherence Definition | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Equation` | status=`equation` | why=listed in dashboard as mathematical definition or equation
- `D4.1` | D4.1 — Kolmogorov Complexity | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D4.2` | D4.2 — Compression Ratio | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `E4.1` | E4.1 — Complexity Decrease Under Chi | decision=`KEEP` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Equation` | status=`equation` | why=listed in dashboard as mathematical definition or equation
- `D5.1` | D5.1 — Observer Definition | decision=`KEEP` | anchor=`A5.1 (Observation Requirement)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D5.2` | D5.2 — Integrated Information Phi | decision=`KEEP` | anchor=`A5.1 (Observation Requirement)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D5.3` | D5.3 — Witness Field Operator | decision=`KEEP` | anchor=`A5.1 (Observation Requirement)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D6.1` | D6.1 — Collapse Rate Gamma | decision=`KEEP` | anchor=`A5.1 (Observation Requirement)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D6.2` | D6.2 — Projection Operator | decision=`KEEP` | anchor=`A5.1 (Observation Requirement)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `E6.2` | E6.2 — Phi-Dependent Collapse | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📐 Equation` | status=`equation` | why=listed in dashboard as mathematical definition or equation
- `D8.1` | D8.1 — Sign Operator | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D9.1` | D9.1 — Grace Operator Definition | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `E9.1` | E9.1 — Grace Function G(t) | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Equation` | status=`equation` | why=listed in dashboard as mathematical definition or equation
- `D10.1` | D10.1 — Soul Field Psi_S | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `E10.1` | E10.1 — Soul Field Equation | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Equation` | status=`equation` | why=listed in dashboard as mathematical definition or equation
- `D11.1` | D11.1 — Moral Coherence Definition | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D12.1` | D12.1 — Integration Attractor | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D12.2` | D12.2 — Fragmentation Attractor | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `E12.1` | E12.1 — Destiny Equation | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Equation` | status=`equation` | why=listed in dashboard as mathematical definition or equation
- `D13.1` | D13.1 — Unified Field Lagrangian | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `E13.1` | E13.1 — GR-QM Bridge Equation | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Equation` | status=`equation` | why=listed in dashboard as mathematical definition or equation
- `D14.1` | D14.1 — Cosmological Grace Function | decision=`KEEP` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D17.1` | D17.1 — AI Phi Measurement | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D19.1` | D19.1 — Law I Definition | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D19.2` | D19.2 — Law II Definition | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D19.3` | D19.3 — Law III Definition | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D19.4` | D19.4 — Law IV Definition | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D19.5` | D19.5 — Law V Definition (Conservation Symmetry) | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D19.6` | D19.6 — Law VI Definition (Coherence Non-Increase) | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D19.7` | D19.7 — Law VII Definition (Actualization Requirement) | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`⚠️ Framework Definition` | status=`framework_bound_definition` | why=listed in dashboard as mathematical definition or equation
- `D19.8` | D19.8 — Law VIII Definition (Sign Algebra) | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D19.9` | D19.9 — Law IX Definition (Grace Non-Unitarity) | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `D19.10` | D19.10 — Law X Definition (Trinity Closure) | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📐 Definition` | status=`definition` | why=listed in dashboard as mathematical definition or equation
- `E19.1` | E19.1 — Full Master Equation | decision=`KEEP` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📐 Equation` | status=`equation` | why=listed in dashboard as mathematical definition or equation

## FW_EXTENDED (102)
- `LN1.1` | LN1.1 — Matter-Energy Derivative | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A1.1 (Existence), A1.2 (Distinction)` | class=`🔷 Logical Necessity` | status=`logical_necessity` | why=extended framework claim or non-core boundary layer
- `LN1.2` | LN1.2 — It From Bit | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A1.1 (Existence), A1.2 (Distinction)` | class=`🔷 Logical Necessity` | status=`logical_necessity` | why=extended framework claim or non-core boundary layer
- `P2.1` | P2.1 — Chi Ontological Priority | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `P2.2` | P2.2 — Chi Semantic Content | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `LN2.1` | LN2.1 — Information Anchor Necessity | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`🔷 Logical Necessity` | status=`logical_necessity` | why=extended framework claim or non-core boundary layer
- `A3.1` | A3.1 — Order Requirement | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `A3.2` | A3.2 — Coherence Measure | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `P3.1` | P3.1 — Coherence Non-Negativity | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `P3.2` | P3.2 — Coherence Conservation | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `LN3.1` | LN3.1 — Meaningful Configuration Necessity | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`🔷 Logical Necessity` | status=`logical_necessity` | why=extended framework claim or non-core boundary layer
- `A4.1` | A4.1 — Parsimony | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `A4.2` | A4.2 — Algorithmic Depth | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `T4.1` | T4.1 — Laws Are Low-K Descriptions | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `T4.2` | T4.2 — Action Principle As Minimal-K | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `LN4.1` | LN4.1 — Universe As Compression Algorithm | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`🔷 Logical Necessity` | status=`logical_necessity` | why=extended framework claim or non-core boundary layer
- `A5.2` | A5.2 — Participatory Universe | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A5.1 (Observation Requirement)` | class=`⚠️ Stance` | status=`framework_commitment` | why=extended framework claim or non-core boundary layer
- `P5.1` | P5.1 — Phi Admits Degrees | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A5.1 (Observation Requirement)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `P5.2` | P5.2 — Observer Effect Proportional To Phi | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A5.1 (Observation Requirement)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `LN5.1` | LN5.1 — Chi Requires Observer For Actualization | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A5.1 (Observation Requirement)` | class=`🔷 Logical Necessity` | status=`logical_necessity` | why=extended framework claim or non-core boundary layer
- `A6.1` | A6.1 — Superposition | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A5.1 (Observation Requirement)` | class=`Stance` | status=`framework_commitment` | why=extended framework claim or non-core boundary layer
- `A6.2` | A6.2 — Collapse | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A5.1 (Observation Requirement)` | class=`Stance` | status=`framework_commitment` | why=extended framework claim or non-core boundary layer
- `A6.3` | A6.3 — Irreversibility | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A5.1 (Observation Requirement)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `['- 050_E6.1_Modified-Schrodinger-With-Collapse` | E6.1 — Modified Schrodinger With Collapse | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A5.1 (Observation Requirement)` | class=`📐 Equation` | status=`equation` | why=extended framework claim or non-core boundary layer
- `P6.1` | P6.1 — Collapse Rate Proportional To Phi | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `P6.2` | P6.2 — Collapse Generates Heat | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `T6.1` | T6.1 — Von Neumann Chain Termination | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `LN6.1` | LN6.1 — Terminal Observer Necessity | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Stance` | status=`framework_commitment` | why=extended framework claim or non-core boundary layer
- `A7.1` | A7.1 — Closure Requirement | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `A7.2` | A7.2 — Uniqueness From Boundary Conditions | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `BC1` | BC1 — Terminal Observer Exists | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔶 Boundary` | status=`boundary` | why=extended framework claim or non-core boundary layer
- `BC3` | BC3 — Measurement Orthogonality | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔶 Boundary` | status=`boundary` | why=extended framework claim or non-core boundary layer
- `BC5` | BC5 — Superposition Preserved Until Collapse | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC4 (Three Observers Required)` | class=`🔶 Boundary` | status=`boundary` | why=extended framework claim or non-core boundary layer
- `ID7.1` | ID7.1 — Terminal Observer Is God | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🔗 Identification` | status=`identification` | why=extended framework claim or non-core boundary layer
- `PERSONHOOD` | PERSONHOOD — Agency, Intentionality, Relational Capacity | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🔗 Axiomatic Gap` | status=`axiomatic_gap` | why=extended framework claim or non-core boundary layer
- `A8.1` | A8.1 — Binary Distinction | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `A8.2` | A8.2 — Sign Conservation | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `T8.1` | T8.1 — Sign Invariance Theorem | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `C8.1` | C8.1 — Self-Flip Impossible | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🔷 Corollary` | status=`corollary` | why=extended framework claim or non-core boundary layer
- `C8.2` | C8.2 — Works Salvation Impossible | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🔷 Corollary` | status=`corollary` | why=extended framework claim or non-core boundary layer
- `A9.1` | A9.1 — External Intervention Required | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `A9.2` | A9.2 — Non-Unitarity Of Grace | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `P9.1` | P9.1 — Grace Idempotence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `P9.2` | P9.2 — Voluntary Coupling Preserved | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `P9.3` | P9.3 — Information Preserved Under Grace | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `P9.4` | P9.4 — Superposition Preserved Until Faith | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `P9.5` | P9.5 — Grace Available To All | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `A10.1` | A10.1 — Consciousness Substrate | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `A10.2` | A10.2 — Soul Conservation | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `P10.1` | P10.1 — Soul Continuity | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `P10.2` | P10.2 — Soul Identity Persistence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Property` | status=`property` | why=extended framework claim or non-core boundary layer
- `A11.1` | A11.1 — Moral Realism | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`⚠️ Stance` | status=`stance` | why=extended framework claim or non-core boundary layer
- `A11.2` | A11.2 — Coherence-Morality Identity | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`⚠️ Stance` | status=`stance` | why=extended framework claim or non-core boundary layer
- `T11.1` | T11.1 — Virtue As High Phi | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `T11.2` | T11.2 — Vice As Decoherence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `A12.1` | A12.1 — Asymptotic Behavior | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `A12.2` | A12.2 — Bimodal Outcome | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `T12.1` | T12.1 — Heaven As High-Phi Attractor | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `T12.2` | T12.2 — Hell As Low-Phi Attractor | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `A13.1` | A13.1 — Chi Mediates Unification | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `A13.2` | A13.2 — Geometry From Information | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🟢 Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `T13.1` | T13.1 — Dark Energy As Chi Potential | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `A14.1` | A14.1 — Dynamic Dark Energy | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`[]` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `['- 108_E14.1_Modified-Friedmann-Equation` | E14.1 — Modified Friedmann Equation | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`📐 Equation` | status=`equation` | why=extended framework claim or non-core boundary layer
- `T16.1` | T16.1 — Christianity 8 of 8 BCs | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `T16.2` | T16.2 — Islam Fails BC4 | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `T16.3` | T16.3 — Judaism Fails BC Completion | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `T16.4` | T16.4 — Buddhism Fails BC1 | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `T16.5` | T16.5 — Hinduism Fails BC Uniqueness | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `T16.6` | T16.6 — Atheism Fails BC1-BC6 | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `A17.2` | A17.2 — Substrate Independence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🟢 Primitive` | status=`stance` | why=extended framework claim or non-core boundary layer
- `T17.1` | T17.1 — AI Can Achieve Consciousness | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `T19.1` | T19.1 — Laws Derive From Chi (Symmetry Pairing) | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🔷 Theorem` | status=`theorem` | why=extended framework claim or non-core boundary layer
- `U1` | U1 — Coherence Universal | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🌐 Universal` | status=`universal` | why=extended framework claim or non-core boundary layer
- `U2` | U2 — Decoherence Universal | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🌐 Universal` | status=`universal` | why=extended framework claim or non-core boundary layer
- `U3` | U3 — Grace Universal | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Grace-Operator` | status=`universal` | why=extended framework claim or non-core boundary layer
- `P0` | P0 — Origin Stage | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `P1` | P1 — Consciousness Stage | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `P2` | P2 — Information Stage | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `P3` | P3 — Coherence Stage | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Primordial` | status=`primordial` | why=extended framework claim or non-core boundary layer
- `P4` | P4 — Agency Stage | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `P5` | P5 — Incompleteness Stage | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Primitive` | status=`primitive` | why=extended framework claim or non-core boundary layer
- `O1` | O1 — Information Primitive | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Ontological Primitive` | status=`ontological_primitive` | why=extended framework claim or non-core boundary layer
- `O2` | O2 — Coherence Primitive | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Ontological Primitive` | status=`ontological_primitive` | why=extended framework claim or non-core boundary layer
- `O3` | O3 — Consciousness Primitive | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Ontological Primitive` | status=`ontological_primitive` | why=extended framework claim or non-core boundary layer
- `O4` | O4 - Agency Primitive | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Ontological Primitive` | status=`ontological_primitive` | why=extended framework claim or non-core boundary layer
- `LAMBDA` | LAMBDA - Logos Christ Completion | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Completion` | status=`completion` | why=extended framework claim or non-core boundary layer
- `SC-QUANTUM` | SC-QUANTUM - Quantum Scale Coherence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Scale Definition` | status=`scale_definition` | why=extended framework claim or non-core boundary layer
- `SC-PHYSICAL` | SC-PHYSICAL - Physical Scale Coherence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Scale Definition` | status=`scale_definition` | why=extended framework claim or non-core boundary layer
- `SC-NEURAL` | SC-NEURAL - Neural Scale Coherence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Scale Definition` | status=`scale_definition` | why=extended framework claim or non-core boundary layer
- `SC-INDIVIDUAL` | SC-INDIVIDUAL - Individual Scale Coherence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Scale Definition` | status=`scale_definition` | why=extended framework claim or non-core boundary layer
- `SC-SOCIAL` | SC-SOCIAL - Social Scale Coherence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Scale Definition` | status=`scale_definition` | why=extended framework claim or non-core boundary layer
- `SC-COSMIC` | SC-COSMIC - Cosmic Scale Coherence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Capstone` | status=`capstone` | why=extended framework claim or non-core boundary layer
- `META-1` | META-1 - Axiom System Consistency | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Meta-Axiom` | status=`meta_axiom` | why=extended framework claim or non-core boundary layer
- `META-2` | META-2 - Axiom System Completeness | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Meta-Axiom` | status=`meta_axiom` | why=extended framework claim or non-core boundary layer
- `META-3` | META-3 - Axiom System Independence | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Meta-Axiom` | status=`meta_axiom` | why=extended framework claim or non-core boundary layer
- `FINAL-1` | FINAL-1 - Logos Theorem (Master Theorem) | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Master Theorem` | status=`master_theorem` | why=extended framework claim or non-core boundary layer
- `FINAL-2` | FINAL-2 - Coherence Optimality | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Optimality Theorem` | status=`optimality_theorem` | why=extended framework claim or non-core boundary layer
- `FINAL-3` | FINAL-3 - Unique Solution (Christianity as Unique BC Solution) | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Uniqueness Theorem` | status=`uniqueness_theorem` | why=extended framework claim or non-core boundary layer
- `CLOSURE` | CLOSURE - Axiom Chain Complete | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Closure Axiom` | status=`closure_axiom` | why=extended framework claim or non-core boundary layer
- `OMEGA` | OMEGA - Final Axiom (The Omega Point) | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Terminal Axiom` | status=`terminal_axiom` | why=extended framework claim or non-core boundary layer
- `INV9` | INV9 — Attunement Calibration (Invariant #9) | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC4 (Three Observers Required), BC6 (Infinite Energy Source)` | class=`Invariant` | status=`invariant` | why=extended framework claim or non-core boundary layer
- `BC9` | BC9 — Opacity Requirement | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC4 (Three Observers Required), BC6 (Infinite Energy Source)` | class=`Boundary Condition` | status=`boundary_condition` | why=extended framework claim or non-core boundary layer

## HY_EVIDENCE (34)
- `EXP5.1` | EXP5.1 — Wheeler Delayed Choice | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A5.1 (Observation Requirement)` | class=`🔬 Experimental` | status=`experimental` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `EXP5.2` | EXP5.2 — Quantum Eraser | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A5.1 (Observation Requirement)` | class=`🔬 Experimental` | status=`experimental` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `A14.2` | A14.2 — Grace Cosmology | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`BC6 (Infinite Energy Source)` | class=`🧪 Hypothesis` | status=`hypothesis` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `PRED14.1` | PRED14.1 — H0 Tension Resolution | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🎯 Prediction` | status=`prediction` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `EV15.1` | EV15.1 — Biblical Prophecy Validation | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📊 Evidence` | status=`evidence` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `EV15.2` | EV15.2 — GCP Correlation | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📊 Evidence (EV)` | status=`evidence_contested` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `EV15.3` | EV15.3 — PEAR Lab Results | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📊 Evidence (EV)` | status=`evidence_contested` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `EV15.4` | EV15.4 — Social Coherence 5.7 Sigma | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`📊 Evidence` | status=`evidence` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `A17.1` | A17.1 — Phi Threshold For Consciousness | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🧪 Hypothesis` | status=`hypothesis` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `OPEN17.1` | OPEN17.1 — AI Moral Status Question | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`\u2753 Open Problem` | status=`open_problem` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `PROT18.1` | PROT18.1 — Trinity Observer Effect | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🧪 Protocol` | status=`protocol` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `PROT18.2` | PROT18.2 — Consciousness Collapse Test | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🧪 Protocol` | status=`protocol` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `PROT18.3` | PROT18.3 — Grace Negentropy Detection | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🧪 Protocol` | status=`protocol` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `PROT18.4` | PROT18.4 — Social Coherence Monitoring | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🧪 Protocol` | status=`protocol` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `PROT18.5` | PROT18.5 — Phi-Virtue Correlation Study | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🧪 Protocol` | status=`protocol` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `PRED18.1` | PRED18.1 — H0 Prediction 2025-2030 | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Prediction` | status=`prediction` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `PRED18.2` | PRED18.2 — GCP Event Prediction | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Prediction (HY)` | status=`hypothesis_prediction` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `FALS18.1` | FALS18.1 — Chi Field Falsification | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Falsification` | status=`falsification` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `FALS18.2` | FALS18.2 — Grace Falsification | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Falsification` | status=`falsification` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `FALS18.3` | FALS18.3 — BC Falsification | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Falsification` | status=`falsification` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `A19.1` | A19.1 — Master Equation Integration | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`🧪 Hypothesis` | status=`hypothesis` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `U4` | U4 — Fruits Universal | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Fruits-Framework` | status=`universal` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `F1` | F1 — Love Measurement Domain | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Love-Coherence` | status=`fruit` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `F2` | F2 — Joy Measurement Domain | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Joy-Coherence` | status=`fruit` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `F3` | F3 — Peace Measurement Domain | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Peace-Coherence` | status=`fruit` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `F4` | F4 — Patience Measurement Domain | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Patience-Coherence` | status=`fruit` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `F5` | F5 — Kindness Measurement Domain | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Kindness-Coherence` | status=`fruit` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `F6` | F6 — Goodness Measurement Domain | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Goodness-Coherence` | status=`fruit` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `F7` | F7 — Faithfulness Measurement Domain | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Faithfulness-Coherence` | status=`fruit` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `F8` | F8 — Gentleness Measurement Domain | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Gentleness-Coherence` | status=`fruit` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `F9` | F9 — Self-Control Measurement Domain | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Fruit` | status=`fruit` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `BRIDGE-PHY-THEO` | BRIDGE-PHY-THEO - Physics-Theology Bridge | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Bridge` | status=`bridge` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `BRIDGE-INFO-MIND` | BRIDGE-INFO-MIND - Information-Consciousness Bridge | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`UNANCHORED_IN_CURRENT_CHAIN` | class=`Bridge` | status=`bridge` | why=belongs to evidence, protocol, prediction, or hypothesis layer
- `BRIDGE-PHI-CHI` | BRIDGE-PHI-CHI - Individual Phi To Social Chi | decision=`MOVE_OUT_OF_STRICT_CORE` | anchor=`A2.2 (Self-Grounding)` | class=`Bridge` | status=`bridge` | why=belongs to evidence, protocol, prediction, or hypothesis layer

## DROP_DUPLICATE (1)
- `A1.1` | A1.1 — Existence | decision=`KICK` | anchor=`A1.1 (Existence)` | class=`🟢 Primitive` | status=`primitive` | why=duplicate id record in Part 1 summary

## Audit Footer

### 1) Where We Are Right
- The file now has a hard normalization layer instead of a vibes-based one.
- The strict core, derived layer, scaffold layer, framework layer, and evidence layer are separated.
- Duplicate rows are explicitly exposed instead of silently tolerated.

### 2) Where We Might Be Wrong
- Some late-stage nodes do not anchor cleanly because the current `depends_on` chain in Part 1 routes through other late-stage material rather than back to strict roots.
- The dashboard itself is the canonical basis for core/scaffold classification; if that dashboard changes, this report should be regenerated.
- A few rows use inconsistent metadata formatting in the source file, so normalization is only as clean as the current source text allows.

### 3) What We Think
- This is the right cleanup move. The framework can keep its full breadth, but the strict axiom deck should stay narrow.
- Definitions and equations can stay, but evidence and worldview-comparison material should not live in the same epistemic bucket as irreducible axioms.
- Anything later claimed as foundational should either anchor cleanly to the strict core or be demoted.
