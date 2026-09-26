# Portable API workspace

This directory is the filesystem contract for paper-processing stations. Paths
are relative to this directory so the workspace can be moved as a unit.

## Complete Grading Bundle

A paper grade is one bundle, not six optional jobs. The mandatory stations are:

1. `COHERENCE`
2. `MASTER_EQUATION`
3. `ATOMS`
4. `COHERENCE_SCORE`
5. `AXIOM_NODES`
6. `FRUITS`

`COHERENCE` and `COHERENCE_SCORE` remain distinct until their contracts prove
otherwise. All six station attempts share one `paper_id`, `run_id`, frozen
source file, SHA-256, output folder, and bundle status. They may execute in
parallel. The coordinator preserves successful station results and retries only
failed stations, but the completion barrier is absolute: **six valid results or
no completed grade**.

Only after all six results validate may the coordinator run Excel calculations,
combine findings, ask Fruits to supply the front page, assemble final HTML,
Excel, JSON, Markdown, and receipts, and move the source to `PROCESSED/`.
A partial bundle is `INCOMPLETE`; it must not publish final artifacts and must
not call the paper graded.

The machine-readable contract is
`_BACKSIDE/CONFIG/grading_bundle.example.json`.

## Bundle lifecycle folders

- `INBOX/` — unclaimed source papers, organized by scheduling lane.
- `PROCESSING/` — atomically claimed bundles. A claim freezes the source and
  records its SHA-256 before any station runs.
- `RETRY/` — incomplete bundles waiting for failed stations only.
- `OUTBOX/` — fully assembled, validated bundle output.
- `RECEIPTS/` — append-only completion and station receipts.
- `REVIEW/` — work explicitly routed for human review.
- `ERRORS/` — terminal or operator-actionable failures; never finished output.
- `PROCESSED/` — source papers moved here only after the completion barrier and
  final assembly succeed.

Station folders hold station-specific code and artifacts. A station must not
move the shared source to `PROCESSED/`; only the bundle coordinator owns that
transition.

## Inbox lanes

Every `INBOX/` uses the same ordered lanes:

```text
INBOX/
├── 00_HOLD_NEVER_PROCESS/
├── 01_PRIORITY/
├── 02_SERIES/
└── 03_GENERAL/
```

- `00_HOLD_NEVER_PROCESS/` is safe storage. Discovery must ignore the entire
  subtree. Files remain untouched until a person moves them to a runnable lane.
- `01_PRIORITY/` is always selected before every other runnable lane.
- `02_SERIES/` keeps related papers together. Put each series in a named child
  folder; discovery is recursive and preserves that relative grouping.
- `03_GENERAL/` contains non-series work. Named child folders may still group
  related material; discovery is recursive and preserves the relative path.

Discovery is recursive inside all three runnable lanes. Folder order is a
scheduling rule, not permission to split a Complete Grading Bundle.

## Document state history

Every API or station transition appends a timestamped event to the document's
state history. Markdown places the history immediately after YAML frontmatter;
HTML places it at the start of `<body>` (after any serialized metadata). The
canonical JSON and run receipt carry the same events. Existing events are never
rewritten or silently removed.

Each event records at least:

```yaml
pipeline_history:
  - station: FRUITS
    state: COMPLETED
    entered_at: 2026-09-24T12:00:00Z
    exited_at: 2026-09-24T12:04:31Z
    paper_id: paper-name
    run_id: 01K...
    source_sha256: <64 lowercase hex characters>
    result: VALID
```

Allowed bundle states are `QUEUED`, `CLAIMED`, `RUNNING`, `INCOMPLETE`,
`ASSEMBLING`, `COMPLETED`, and `ERROR`. Station events may add attempt number,
provider, model, artifact paths, validation outcome, and error details. Times
are UTC ISO 8601 values. The shared identifiers and hash must remain unchanged
throughout a run.

See `_BACKSIDE/DOCS/document-state-history.md` for placement and validation
rules.
