# Paper analysis prompt pack

Use one prompt per folder. Supply the original paper text, paper ID, SHA-256, and the exact registry section. Return JSON under that paper ID. Quote exact source spans for claims and mark every unanswered field `null` with a reason. Distinguish extraction, heuristic text signal, mathematical derivation, empirical observation, Lean receipt, and theological interpretation. Never infer truth, proof, or spiritual condition from a lexical or emotion score.

## Text and readability
Count visible words, letters, paragraphs, estimated sentences, unique terms, length distributions, and grade estimates. State cleaning rules and formula names. Provide counts separately from interpretations.

## Academic claims and evidence
List exact claim spans. For each, give lane, physics claim type if relevant, defense class, evidence needed/present/gap, proof boundary, and kill condition. A citation marker is not verified evidence.

## Framework and truth heuristics
Identify explicit master-equation variables, axioms, coherence definitions, and Fruits language. Separate quotations and term hits from proposed mappings. Do not assign a truth or spiritual score without an explicit reviewed measurement contract.

## Emotion and fruit text signals
Report model labels as labels about text. Include model/version and any fallback. Do not treat labels as measurements of a person or as evidence of spiritual fruit.

## Corpus and graph
Compare papers only when both source identities and hashes are supplied. Return suggested links with span, relation, and confidence; do not promote shared terms to corroboration.

## Physics and theory
Identify each established theory, model, hypothesis, or analogy. State its source, domain, equation, scope, evidence burden, and what would break the proposed bridge. Keep mainstream status separate from the paper's interpretation.

## Schema and review
Populate the paper snapshot with explicit nulls for missing data. Preserve original text and hash, attach provenance for each node, and keep candidate admission status until human review.
