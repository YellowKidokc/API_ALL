# TASK: claim extraction and evaluation

The INPUT is one chunk of a YouTube transcript with [mm:ss] timestamps. It may
start or end mid-sentence because chunks overlap. Skip claims that are cut off.

Extract every substantive claim (factual, scientific, historical, theological,
or philosophical). Skip filler, jokes, and self-promotion. Quote the claim
as close to verbatim as the transcript allows.

Repeat this block for each claim, using the rating scales from HOME:

## CLAIM
> [quote]

- source: [video ID] @ [mm:ss]
- speaker: [name if clear, else "unknown"]
- category: [scientific | historical | theological | philosophical | biblical | other]
- support: [demonstrated-formal | demonstrated-empirical | defensible | asserted | unclear]
- falsifiable: [yes | no | not-assessed]
- confidence: [low | medium | high]
- reasoning: [2–4 sentences. Name what is established, what is disputed, and what is missing.]
- theophysics: [mapping to the root axiom or a defined node, labeled speculative / defensible / Lean-checked; or "none"]

If the chunk has no substantive claims, write `## CLAIM` once with `- none`.

## FOLLOW-UPS
- [specific checks, sources to look up, or glossary terms you needed; or "none"]
