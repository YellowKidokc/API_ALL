# Implementation Plan

## Phase 1 - Static Prototype

1. Create `paper-snapshot-prototype.html`.
2. Match the black/gold Proof Explorer style.
3. Hardcode the FP-005 snapshot object.
4. Include all nine snapshot boxes.
5. Make the 7Q panel expandable.

## Phase 2 - Integrate With FP-005

1. Open `fp-005-enhanced.html`.
2. Parse existing `theophysics-structure` JSON.
3. Insert a `Paper Snapshot` section near the top, before the long proof stack.
4. Populate fields from JSON plus fallback snapshot defaults.
5. Preserve existing navigation, fonts, colors, analytics, and metadata.

## Phase 3 - Make Reusable

1. Extract CSS classes for snapshot cards/chips/badges.
2. Extract rendering JS into a small reusable function.
3. Use the same function for axiom pages and ISO pages.
4. Add per-page JSON snapshot blocks.

## Phase 4 - Paper Grader Bridge

1. Have `paper-proof-grader` emit `snapshot.json`.
2. Have HTML report consume `snapshot.json`.
3. Store same snapshot in Excel workbook tab `00_Snapshot`.
4. Vectorize the snapshot summary into Qdrant collection `paper_proof_grader`.
