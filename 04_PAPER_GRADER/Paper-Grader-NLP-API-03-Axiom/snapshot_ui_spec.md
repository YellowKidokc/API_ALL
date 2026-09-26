# Snapshot UI Spec

## Visual Direction

Match the existing Proof Explorer pages:

- Black background
- Dark charcoal panels
- Fine borders
- Gold accents
- Compact scientific layout
- Badges for maturity, status, evidence, and kill conditions
- Expandable details

Avoid:

- Marketing hero copy
- Emotional persuasion
- Large decorative sections
- Hiding kill conditions
- Claiming more than the proof boundary allows

## Closed One-Screen Layout

```text
Identity Strip
One-Sentence Claim

[Maturity Badge] [Proof Boundary]

FACTS Row:
Frame | Admit | Claim | Test | Snap

Forward / Reverse Test

Evidence Bar

Fatal Kill Conditions

Not Claimed

[Expandable: 7Q Snapshot]
```

## Required Interactions

- 7Q Snapshot is collapsed by default.
- Kill conditions are visible by default.
- Evidence chips are grouped in this order:
  1. Formal / Mathematical
  2. Physics / Empirical
  3. Historical / Textual
  4. Theological / Interpretive
- Maturity level must show both number and label.
- Proof boundary must be visible without a click.

## Data Source

First pass can use a static JS object or embedded JSON.

Better pass:

- Read existing `<script type="application/json" id="theophysics-structure">`.
- Derive snapshot fields from it where possible.
- Allow manual fallback fields for missing data.
