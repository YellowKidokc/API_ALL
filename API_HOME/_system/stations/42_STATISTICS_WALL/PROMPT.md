# STATISTICS WALL V1: every number an academic or an Obsidian user could want, and then some

David, 2026-09-25: "so many statistics that it's a wall of numbers." Every metric an academic would ask for, every one an
Obsidian user would want, all computed and shown. The wall is the point: it signals thoroughness and invites checking.
A short headline strip sits on top for people who won't read the wall.

## What already exists (build on it, don't redo it)
- `04_PAPER_GRADER\Academic_paper-proof-grader_Jul\MASTER_VARIABLE_SCHEMA.md`: **366 variables in 20 layers**: identity, basic text,
  readability, structure, NLP semantic, truth engine (claims/evidence), knowledge graph, emotion, linguistic depth, idea density,
  academic rubric, web intake, formal maturity, Lean 4, math/equations, assumptions/boundaries, falsifiability, novelty, final scores.
- `\\192.168.2.50\brain\Python API` (X:\Python API): **116 metric scripts**, catalogued in `paper_metric_registry.json` with 296 metric
  questions (text_analyzer, linguistic_analyzer, idea_density_analyzer, academic_scorer, claim_inventory, evidence_map, kill_conditions,
  equation_audit, assumption_stack, overstatement_detector, coherence_score, chi_computation, heartbeat_analyzer, word_level_mapper
  (GoEmotions), emotion_analyzer, graph_builder, co_term_density, cooccurrence_analyzer, correlation_engine, novelty_classification ...).
- Analytical arms (`ANALYTICAL_ARMS_V1.md`): per-sentence fruit vectors, master-equation slots, axiom nodes, coherence.

**Step 1 for Codex:** run every existing script on one sample paper and list which of the 366 variables actually come out,
which are empty, and which scripts are broken. Report that before adding anything.

## What to add (grouped; L = local and free, A = needs the API)

**Readability, complete set (L).** Add LIX, RIX, Linsear Write, Spache, FORCAST, McAlpine EFLAW and text_standard consensus,
plus reading time and speaking time (at 238 and 150 wpm).

**Lexical richness (L).** MTLD, MATTR (window 50), HD-D, vocd-D, Yule's K, Simpson's D, Honoré's R, Brunet's W, Herdan's C, Maas.
Hapax legomena and dislegomena counts and ratios. Zipf slope + R², Heaps' law β.

**Syntax (L, spaCy).**
- Mean dependency distance, parse-tree depth, clauses per sentence, subordination index.
- Passive-voice ratio and nominalization ratio.
- POS proportions: noun, verb, adjective, adverb, pronoun, preposition, conjunction, determiner.
- Lexical density (content/function), mean word length, share of long words (7+ letters).

**Distribution stats for EVERY per-sentence series (L).** For sentence length, each fruit, sentiment, surprisal, and so on:
mean, median, SD, min, max, IQR, skew, kurtosis, Gini, burstiness, autocorrelation at lag 1, and the location (sentence id) of max and min.

**Cohesion, Coh-Metrix style (L).**
- Noun and argument overlap between adjacent sentences.
- Embedding similarity sentence→sentence and paragraph→paragraph (mean and SD), using the local M19 embeddings.
- Connectives per 1,000 words by type (causal, adversative, temporal, additive, conditional) and given/new ratio.
- Topic drift: cosine distance between the opening and the closing.

**Information theory (L), which fits Theophysics directly.**
- Shannon entropy (unigram and bigram), conditional entropy, redundancy.
- Compression ratio under gzip, bz2 and lzma (a Kolmogorov proxy).
- Mean and SD of surprisal and perplexity under a local LM.
- Mutual information of the top 20 key-term pairs.
- Information per sentence curve.

**Metadiscourse and stance, Hyland (L).** Hedges, boosters, attitude markers, self-mentions and engagement markers per 1,000 words,
the hedge:booster ratio, absolutes ("always/never/proves") per 1,000 words, and the certainty index.

**Emotion and affect (L).**
- VADER compound and positive/negative/neutral.
- NRC VAD (valence, arousal, dominance), NRC 8 emotions, GoEmotions 28 labels (existing word_level_mapper).
- Emotional-arc shape: the six Reagan arcs (rags-to-riches, tragedy, man-in-a-hole ...) with the fit score.

**Citations and sources (L, with A for classification).**
- Reference count, references per 1,000 words, DOI coverage %.
- Median reference year and Price index (% from the last 5 years).
- Source-type mix: peer-reviewed / book / web / scripture / self. Self-citation ratio.
- Citation density per section.
- Scripture references by book and by testament, OT:NT ratio.

**Argument structure (A, checked locally).**
- Claim:evidence ratio, % unsupported claims, % claims carrying their own caveat.
- Premise depth, longest inference chain, branching factor, objections raised vs answered, counter-argument ratio.
- Fallacy flags by type, overstatement count (existing detector).

**Semantics and corpus position (L, needs David's corpus embedded once).**
- Topic count and topic entropy (BERTopic).
- Semantic novelty: distance to the nearest paper in David's corpus. Centroid similarity to its series and to the whole corpus.
- Near-duplicate sentence pairs inside the paper and against the corpus.

**Knowledge graph extras (L, networkx).** PageRank top 10 terms, betweenness top 10, modularity, clustering coefficient,
diameter, and connected components.

**Obsidian and vault (L).**
- Wikilinks out, backlinks in, unresolved links, embeds, block references, aliases.
- Tags (count and list), frontmatter completeness %, heading depth and count, callouts, words per heading.
- Vault graph degree and orphan status. Last-modified age and revision count from git history where available.

**Analytical arms (from ANALYTICAL_ARMS_V1).** Per-fruit curve stats (distribution set above), lexicon-vs-meaning gap counts,
counterfeit and hidden-fruit counts, master-equation slot coverage (x/10) and product-test result, axiom nodes engaged by mode,
and coherence dimension scores.

**Reliability, which academics expect (A).** Run every API-derived score twice and report agreement: Cohen's κ for
categories, ICC for scores. Report 95% bootstrap confidence intervals over sentences for every per-sentence mean.

## The multiplier: context on every number (L)
For every metric, also compute:
- **corpus percentile**: rank among all of David's graded papers
- **series percentile**: rank within its series
- **delta vs the previous version** of the same paper, when one exists

This turns a few hundred numbers into well over a thousand. Each one is still meaningful: "Yule's K 142 (88th percentile of the corpus, +12 since v2)".

## Output
- `03_REPORT\statistics.xlsx`: one row per metric: group, metric, value, unit, corpus pct, series pct, Δ previous, method, source script, L/A, CI.
  Plus sheets per sentence and per paragraph with every series.
- `03_REPORT\statistics.html`: the **wall**, a dense multi-column grid of every metric grouped by layer, small type, tabular numbers,
  each cell showing value + percentile, with a hover tooltip giving the method. It stays on the page, not collapsed away.
  Above it, a **headline strip of 12 numbers** David picks.
- `02_RUNS\statistics\statistics.json`: canonical values, so the site and the combiner read one source.
- Every metric carries its method name and library version, so an academic can reproduce it.

## Libraries (local, free)
textstat, TextDescriptives (spaCy component: descriptive stats, readability, dependency distance, POS proportions, coherence,
information theory, quality), lexicalrichness, spaCy en_core_web_trf, vaderSentiment, NRC lexicons, networkx,
sentence-transformers (or David's M19 embeddings), BERTopic, zlib/bz2/lzma, scipy, numpy, pandas, openpyxl.

## Cost
Everything marked L is free and repeatable. The A items reuse outputs from the analytical arms and the claim extraction, except
the reliability re-run, which doubles those specific calls.

## Decisions for David
1. Which 12 numbers go in the headline strip.
2. Which corpus the percentiles use: all papers, or only canonical/published ones.
3. Whether the public HTML shows the whole wall or the wall plus a download of the xlsx.

## Visual prototype (2026-09-25)
`STATISTICS_MATRIX_PROTOTYPE.html` in this folder is the layout to build toward (demo data, single self-contained file):
headline strip of 12 → **the matrix** (one band per family, one circle per statistic: colour = good↔needs work on a
diverging blue/grey/red ramp, size = |z| from the norm, inner glyph = dot computed / diamond AI-judged / ring runs
disagreed, dashed = no academic benchmark; toggle corpus vs academic frame; sort weak→strong, most pronounced, A–Z)
→ **family map** (x = vs academic norm, y = vs David's corpus, filled core = share rated strong, a dashed lane for
families with no academic benchmark) → 15 specialised charts → the full wall. Feed it `statistics.json` instead of the
generated demo data; keep the encodings.
