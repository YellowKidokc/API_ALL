# CKG Atom — Fully Explained Template

This document explains every section and rule of the CKG companion format.

## Purpose

A CKG companion is a structured, machine-readable review of a single source
document. It is produced by the runner in stages and stored in
`OUTBOX/01_ALL_PAPERS/<paper_uuid>.md`. The companion is a candidate AI
analysis, not a formal verification or admission of truth.

## Map stage

The map gives a high-level structural overview of the source:

- `title` — the document title or the best available label.
- `domain` — the primary knowledge domain (e.g. Mathematics, Theology, Physics).
- `project` — the collection or project the document belongs to.
- `purpose` — the kind of document: paper, note, draft, objection, evidence,
  or synthesis.
- `summary` — a one-paragraph summary of the document.
- `keywords` — a list of searchable keywords.
- `objects` — extracted atomic objects (claims, definitions, axioms, evidence,
  objections). Each object may quote the source verbatim.
- `unmapped` — important content that does not fit the object schema.

### Object rules

- `key` is a short stable identifier such as `C1`, `D1`, `A1`.
- `type` is one of `CLAIM`, `DEFINITION`, `AXIOM`, `EVIDENCE`, `OBJECTION`.
- `register` names the epistemic register (e.g. `FORMAL_MATHEMATICAL`).
- `quote` must be a verbatim substring of the source. Empty quotes are allowed
  when the object is inferred rather than directly quoted.
- `statement` restates the object in the companion's own terms.
- `reason` explains the classification.

## Sections S01 through S10

Each section elaborates one analytical dimension. The default meaning is:

1. **S01 · Core Finding** — the single most important conclusion.
2. **S02 · Axiom / Definition Spine** — the foundational definitions and axioms
   the document relies on.
3. **S03 · Argument Chain** — the step-by-step reasoning.
4. **S04 · Evidence and Sources** — empirical, textual, or formal evidence.
5. **S05 · Objections and Counterarguments** — internal tensions or external
   objections.
6. **S06 · Translation Layer** — rendering ideas across domains or audiences.
7. **S07 · Formal and Mathematical Layer** — equations, proofs, and formalisms.
8. **S08 · Bridge Integrity** — checks that cross-domain bridges hold.
9. **S09 · Falsification and Open Questions** — what could disprove the claims
   and what remains unresolved.
10. **S10 · Consilience Summary** — how the document fits the larger project.

Each section returns `status`, `reason`, `markdown`, and `object_keys`.

## Audit stage

The audit reviews the companion for consistency:

- Are all non-empty quotations exact substrings of the source?
- Are status labels consistent with the content?
- Are unsupported claims explicitly flagged?
- Is any placeholder text left in the output?

## General rules

1. **Source-grounded quotes only.** The runner rejects invented quotations.
2. **AI-proposed status.** Every `status` value is an AI proposal, never a
   runner-attested fact.
3. **No empty sections.** Sections with empty `markdown` are rejected.
4. **No silent truncation.** Sources over 100,000 characters are rejected.
5. **Resume from checkpoints.** Saved stages are reused when the source,
   template, model, and prompt are unchanged.
6. **One runner at a time.** The lockfile prevents simultaneous runners.
