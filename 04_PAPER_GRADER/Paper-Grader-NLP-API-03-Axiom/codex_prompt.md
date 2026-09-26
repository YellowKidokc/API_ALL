# Prompt For Online Codex

You are working on the Faith Through Physics Proof Explorer pages.

Build a reusable **Paper Snapshot** section for the black/gold Proof Explorer UI.

The snapshot is one-screen scientific triage, not a marketing page. It must answer:

```text
What is being claimed?
What kind of claim is it?
What supports it?
What would break it?
Why should a physicist keep reading?
```

Use these required boxes:

```text
1. Paper ID / Identity Strip
2. One-Sentence Claim
3. Claim Maturity Level
4. FACTS Snapshot
5. 7Q Mini Grid
6. Forward / Reverse Test
7. Evidence Bar
8. Kill Conditions
9. Not Claimed
```

Claim maturity ladder:

```text
1 Metaphor
2 Analogy
3 Structural Correspondence
4 Formal Model
5 Machine-Checked Theorem
6 Empirical Support
7 Public Proof Claim
```

Implementation requirements:

- Match the existing black/gold Proof Explorer style.
- Keep the closed view compact and scannable.
- Make the 7Q panel collapsible and closed by default.
- Keep kill conditions visible by default.
- Show proof boundary without requiring a click.
- Do not imply that physics proves theology unless the actual claim says that.
- Preserve existing metadata, analytics, fonts, and navigation.

First target page:

```text
X:\proof-explorer\fp-005-enhanced.html
```

That page already has an embedded JSON block:

```html
<script type="application/json" id="theophysics-structure">
```

Use that as the initial data source where possible. Add fallback snapshot fields where the existing JSON is incomplete.

Also create or update a prototype page:

```text
X:\proof-explorer\paper-snapshot-prototype.html
```

The final result should feel like a scientific claim audit card: clear, falsifiable, honest, and hard to misread.
