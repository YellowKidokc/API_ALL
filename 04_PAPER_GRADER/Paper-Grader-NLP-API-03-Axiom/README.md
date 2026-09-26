# Paper Snapshot / Proof Explorer Package

This package gives Online Codex the exact build target for the Paper Snapshot layer.

## Goal

Add a one-screen scientific triage snapshot to the black Proof Explorer / Axiom pages.

The snapshot answers:

```text
What is being claimed?
What kind of claim is it?
What supports it?
What would break it?
Why should a physicist keep reading?
```

## Files

```text
codex_prompt.md
snapshot_schema.json
snapshot_ui_spec.md
implementation_plan.md
```

## Existing Local Context

Current local pages:

```text
X:\proof-explorer\index.html
X:\proof-explorer\fp-005.html
X:\proof-explorer\fp-005-enhanced.html
X:\proof-explorer\axioms-layer-0-core.html
X:\proof-explorer\axioms-layer-2-derived.html
X:\proof-explorer\axioms-layer-3-extended.html
X:\proof-explorer\axioms-closure.html
```

Current workflow schema:

```text
X:\brain\00_WORKFLOWS\paper-proof-grader\MASTER_VARIABLE_SCHEMA.md
X:\brain\00_WORKFLOWS\paper-proof-grader\PAPER_SNAPSHOT_SCHEMA.md
```

## Desired First Build

Create a reusable `PaperSnapshot` component or vanilla HTML section matching the existing black/gold Proof Explorer style.

Then add it to:

```text
fp-005-enhanced.html
```

Use the JSON block already embedded in that file as the first data source.
