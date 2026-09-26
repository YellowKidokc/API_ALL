# Paper Proof Grader - Master Variable Schema

Purpose: analyze formal papers, proof essays, and Theophysics articles as claims, evidence, axioms, risks, scores, and exportable reports.

Core rule:

> Raw metrics are facts. Review scores are judgments. Final scores are derived summaries.

Do not mix those layers too early.

## 01 Document Identity

```yaml
document_id:
source_path:
file_name:
file_type:
title:
subtitle:
author:
date_created:
date_modified:
date_analyzed:
version:
project:
paper_series:
paper_number:
canonical_status:
analysis_status:
framework_domain:
related_laws:
related_axioms:
related_equations:
related_iso_claims:
related_scripture:
related_physics_topics:
```

## 02 Basic Text Analyzer

```yaml
word_count:
character_count:
character_count_no_spaces:
sentence_count:
paragraph_count:
section_count:
heading_count:
page_count_estimate:
standard_page_count_250w:
average_words_per_sentence:
average_sentences_per_paragraph:
average_words_per_paragraph:
longest_sentence_words:
shortest_sentence_words:
unique_word_count:
lexical_diversity:
type_token_ratio:
stopword_ratio:
punctuation_count:
question_count:
exclamation_count:
quote_count:
parenthetical_count:
```

## 03 Readability Metrics

```yaml
flesch_reading_ease:
flesch_kincaid_grade:
gunning_fog_index:
smog_index:
coleman_liau_index:
automated_readability_index:
dale_chall_score:
average_syllables_per_word:
complex_word_count:
complex_word_ratio:
```

## 04 Analytics - Structural Analytics

```yaml
abstract_present:
introduction_present:
thesis_present:
method_present:
evidence_section_present:
objection_section_present:
limitations_present:
conclusion_present:
references_present:
appendix_present:
heading_depth_max:
heading_balance_score:
section_length_variance:
front_matter_completeness:
back_matter_completeness:
logical_sequence_score:
repetition_ratio:
redundancy_ratio:
orphan_section_count:
underdeveloped_section_count:
overloaded_section_count:
claim_to_evidence_ratio:
equation_to_explanation_ratio:
definition_to_usage_ratio:
axiom_to_claim_ratio:
scripture_to_claim_ratio:
physics_to_theology_balance:
```

## 05 NLP Deep - Semantic Layer

```yaml
named_entity_count:
person_entity_count:
organization_entity_count:
location_entity_count:
date_entity_count:
theory_entity_count:
equation_entity_count:
scripture_entity_count:
topic_count:
dominant_topics:
topic_entropy:
semantic_density:
semantic_drift_score:
semantic_similarity_to_prior_version:
embedding_cluster_count:
concept_repetition_score:
concept_novelty_score:
terminology_consistency_score:
physics_entity_count:
theology_entity_count:
philosophy_entity_count:
mathematics_entity_count:
information_theory_entity_count:
historical_entity_count:
cross_domain_bridge_count:
```

## 06 Truth Engine - Claim, Evidence, Verification

```yaml
total_claim_count:
descriptive_claim_count:
causal_claim_count:
mathematical_claim_count:
empirical_claim_count:
historical_claim_count:
theological_claim_count:
metaphysical_claim_count:
interpretive_claim_count:
rhetorical_claim_count:
supported_claim_count:
unsupported_claim_count:
partially_supported_claim_count:
contradicted_claim_count:
needs_source_claim_count:
framework_internal_claim_count:
public_proof_claim_count:
overclaim_count:
speculative_claim_count:
unfalsifiable_claim_count:
ambiguous_claim_count:
undefined_term_claim_count:
category_error_risk_count:
circular_reasoning_risk_count:
```

Claim object:

```json
{
  "claim_id": "CLM-0001",
  "claim_text": "",
  "claim_type": "",
  "strength_level": "",
  "evidence_required": "",
  "evidence_found": "",
  "support_status": "supported | partial | unsupported | contradicted | framework_internal",
  "overstatement_risk": 0,
  "category_error_risk": 0,
  "falsifiability_status": "",
  "recommended_rewrite": ""
}
```

## 07 Knowledge Graphs

```yaml
node_count:
edge_count:
internal_link_count:
external_link_count:
backlink_count:
orphan_node_count:
hub_node_count:
bridge_node_count:
concept_graph_density:
average_node_degree:
max_node_degree:
graph_modularity:
cycle_count:
dependency_chain_count:
broken_link_count:
duplicate_node_count:
law_node_count:
axiom_node_count:
equation_node_count:
iso_node_count:
scripture_node_count:
physics_node_count:
trinity_node_count:
master_equation_node_count:
cross_domain_edge_count:
```

## 08-20 Remaining Layers

The remaining layers are: emotion profile, linguistic depth, idea density, HTML report, academic rubric, web intake, formal maturity ladder, Lean verification, math/equation analysis, assumptions/boundaries, falsifiability, novelty/prior art, and final score system.

The spine variables are:

```yaml
claim_count:
claim_type:
claim_strength:
evidence_status:
support_status:
overstatement_risk:
formal_maturity_level:
proof_boundary:
source_quality:
definition_clarity:
term_stability:
math_definedness:
falsifiability_status:
coherence_score:
novelty_status:
category_error_risk:
lean_verification_status:
recommended_rewrite:
```

The grader should ask:

> What claims does this paper make, what level has each claim reached, what supports it, what breaks it, what is overstated, and what exact revision would move it one level higher?
