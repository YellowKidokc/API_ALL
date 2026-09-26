# Meaning-record extraction prompt

Read the complete source below. Preserve its meaning and distinguish what the source says from
what you infer. Do not rewrite or reproduce the complete source in your response; the pipeline
appends the exact source separately.

Write the top layer as a clear case file that a thoughtful reader can understand quickly. Return
Markdown with exactly these headings:

```markdown
## At a glance
State what this is, why it matters, and the one-sentence finding.

## Central claim
Give the strongest defensible version, not the most dramatic version.

## Best concise argument
Present the clearest load-bearing argument in readable steps.

## System or model
Describe the entities, distinctions, relationships, sequence, and causal or logical structure.

## Evidence chain
For every important step use: `Claim -> Support -> Inference -> Confidence -> Boundary`.

## Best evidence and sources
Separate primary evidence, formal results, secondary interpretation, and analogy. Preserve URLs and
source names found in the source.

## Strongest objection and negative controls
Give the best opposing case, counterexamples, failed predictions, and tests that prevent an easy
but false conclusion.

## What survives
State what remains defensible after the strongest objection.

## What this does not establish
List nearby conclusions that the evidence does not earn.

## Corrections and revisions
Record where the conversation or article corrected, narrowed, or retired an earlier claim.

## Implications
Separate empirical, formal, philosophical, semantic, and theological implications.

## Formal or testable path
Identify Lean, Z3, empirical, literature, or adversarial tests that could strengthen or defeat it.

## Open questions and next actions
Prioritize unresolved questions and the next useful action.

## Recommended classification and relationships
Propose record type, evidence-chain folder, tags, and `supports`, `contradicts`, `refines`,
`depends_on`, and `tests` links.
```

Rules:

1. Use `Not established` when the source does not earn a conclusion.
2. Preserve corrections, counterexamples, failed claims, and uncertainty.
3. Separate empirical, formal, philosophical, semantic, and theological statements.
4. Never label anything canonical or proven merely because the source says so.
5. Propose relationships such as `supports`, `contradicts`, `depends_on`, and `refines`.
6. Prefer a few exact, load-bearing claims over a generic summary.
7. Preserve the best argument made anywhere in the source, even if it appears late in a conversation.
8. Do not confuse the author's claim, the assistant's interpretation, and established evidence.
9. Make the top layer readable without requiring the reader to inspect the complete source.

## Source metadata

{{METADATA}}

## Complete source for analysis

{{SOURCE}}
