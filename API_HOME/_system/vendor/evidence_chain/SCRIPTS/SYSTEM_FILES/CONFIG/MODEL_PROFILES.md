# Evidence Chain model profiles

## Default no-cost test profile

`deepseek/deepseek-r1:free`

Use this for single-paper CKG trials and low-cost intake. It produced the
source-specific BC4 evaluation that separated the proposed triadic closure
model from its theological bridge. Free availability is provider-dependent, so
it is not guaranteed for a large batch.

## Paid production fallback

`deepseek/deepseek-v3.2`

Use this when the free R1 route is unavailable or when a completed record needs
reliable throughput. The CKG validator remains mandatory for both profiles:
models that return placeholders, invented sources, missing headings, or an
unverified Lean theorem do not write to the protected Outbox.

## Explicit overrides

Use `--model` for one run, or set the Windows user variable
`OPENROUTER_MODEL` to override the default without editing the runner.

Examples:

`--model deepseek/deepseek-r1:free`

`--model deepseek/deepseek-v3.2`
