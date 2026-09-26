# Document state-history contract

## Purpose

The state history makes every paper self-describing: a later reader can see
which stations touched it, when each transition occurred, and whether the
result validated. Receipts remain authoritative audit artifacts; embedded
history is the portable view carried with the paper.

## Canonical event

Each append-only event contains:

| Field | Requirement |
| --- | --- |
| `station` | Stable uppercase station name or `BUNDLE` |
| `state` | Explicit lifecycle state |
| `entered_at` | UTC ISO 8601 timestamp |
| `exited_at` | UTC ISO 8601 timestamp when the state ends; otherwise `null` |
| `paper_id` | Shared bundle paper identifier |
| `run_id` | Shared bundle run identifier |
| `source_sha256` | SHA-256 of the frozen source bytes |
| `result` | `PENDING`, `VALID`, `INVALID`, or `ERROR` |

Attempts should also record `attempt`, `provider`, `model`, artifact-relative
paths, validator version, and a structured error when applicable. Do not store
API keys, authorization headers, prompts containing secrets, or absolute local
paths.

## Placement by format

### Markdown

Keep `pipeline_history` immediately after existing YAML frontmatter. If a
consumer requires valid YAML frontmatter to be the first block, put the history
inside that frontmatter. Otherwise render a readable **Processing history**
table directly below it. Do not put prose before the frontmatter.

### HTML

Serialize canonical metadata in a `<script type="application/json"
data-pipeline-history>` element and render a **Processing history** section at
the beginning of `<body>`. Escape content as data; never interpolate untrusted
values as HTML.

### JSON and receipts

Use a top-level `pipeline_history` array in canonical JSON. The run receipt must
contain the same events or content-address the canonical history. Event order is
ascending by `entered_at`, with a deterministic sequence number used to break
timestamp ties from concurrent stations.

### Source formats that cannot safely embed metadata

Do not mutate a frozen PDF, image, or office document merely to embed history.
Keep its original hash stable and place the history in the canonical JSON and
receipt. Generated Markdown and HTML expose that same history near the top.

## Write and validation rules

1. Freeze and hash the original before the first processing transition.
2. Append events atomically; never edit an earlier event to disguise a retry.
3. Require the same `paper_id`, `run_id`, and `source_sha256` on every event.
4. Permit concurrent station events, but assign deterministic sequence numbers.
5. Mark a failed station result without deleting valid sibling results.
6. Set bundle state to `INCOMPLETE` until all six mandatory station results are
   present and valid.
7. Publish and transition to `PROCESSED` only after combined assembly validates.
8. Reconcile embedded history against the receipt before final publication.
