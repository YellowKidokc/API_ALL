# CKG Atom Master Template

This document is the runner's current prompt contract. It defines the CKG
pipeline stages and the JSON schema each stage must return. Keep it aligned
with `02_FULLY_EXPLAINED_TEMPLATE.md`.

## Pipeline stages

The runner executes one call per stage, in order:

1. `map` — structural overview of the source document.
2. `S01` through `S10` — ten analytical sections.
3. `audit` — final review and consistency check.

## Stage: `map`

Read the source document and return a single JSON object matching this schema:

```json
{
  "title": "string — document title or best label",
  "domain": "string — primary knowledge domain",
  "project": "string — collection or project name",
  "purpose": "string — paper | note | draft | objection | evidence | synthesis",
  "summary": "string — one-paragraph summary",
  "keywords": ["string"],
  "objects": [
    {
      "key": "C1",
      "type": "CLAIM | DEFINITION | AXIOM | EVIDENCE | OBJECTION",
      "register": "string — e.g. FORMAL_MATHEMATICAL, THEOLOGICAL, EMPIRICAL",
      "quote": "exact substring from the source, or empty",
      "statement": "paraphrased or formal statement",
      "reason": "why the object is classified this way"
    }
  ],
  "unmapped": ["string — important content not captured above"]
}
```

**Rule:** Every non-empty `quote` must be a verbatim substring of the source
text. The runner rejects invented quotations.

## Stages: `S01` through `S10`

For each section, return a single JSON object:

```json
{
  "status": "AI_PROPOSED",
  "reason": "string — concise rationale for the section content",
  "markdown": "string — the section content in GitHub-Flavored Markdown",
  "object_keys": ["C1", "C2"]
}
```

**Rule:** `markdown` must be non-empty. The runner rejects empty sections.

Suggested section focus (configurable per project):

- `S01` — Core finding and one-sentence claim.
- `S02` — Axiom/definition spine.
- `S03` — Argument chain.
- `S04` — Evidence and sources.
- `S05` — Objections and counterarguments.
- `S06` — Theological/philosophical translation.
- `S07` — Formal and mathematical layer.
- `S08` — Bridge integrity and cross-domain checks.
- `S09` — Open questions and falsification boundaries.
- `S10` — Consilience summary and next steps.

## Stage: `audit`

Return a single JSON object:

```json
{
  "status": "AI_PROPOSED",
  "reason": "string — summary of what was checked",
  "markdown": "string — audit report in GitHub-Flavored Markdown"
}
```

The audit should verify that:

- All quoted text appears in the source.
- Status labels are consistent with the content.
- Unsupported claims are flagged explicitly.
- No placeholder text remains.

## Output contract

- Each stage response must be valid JSON.
- The provider response content is parsed as JSON; raw text is wrapped in a
  fallback schema.
- All results are candidate AI analysis, never admission or proof verification.
