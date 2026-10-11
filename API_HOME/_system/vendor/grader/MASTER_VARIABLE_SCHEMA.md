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

Paper-level metrics:

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

## 08 Emotion Profile

```yaml
emotional_intensity_score:
certainty_score:
humility_score:
urgency_score:
accusatory_language_score:
defensive_language_score:
awe_language_score:
moral_language_score:
conflict_language_score:
hope_language_score:
fear_language_score:
anger_language_score:
trust_language_score:
rhetorical_overheat_flag:
apologetic_balance_flag:
polemic_density:
prophetic_tone_score:
academic_tone_score:
public_audience_tone_score:
```

## 09 Linguistic Depth

```yaml
lexical_depth_score:
abstract_word_ratio:
concrete_word_ratio:
technical_term_count:
defined_term_count:
undefined_term_count:
metaphor_count:
analogy_count:
isomorphism_claim_count:
compression_line_count:
transition_quality_score:
sentence_variety_score:
paragraph_flow_score:
conceptual_load_score:
term_stability_score:
```

## 10 Idea Density

```yaml
core_idea_count:
unique_idea_count:
repeated_idea_count:
idea_density_per_1000_words:
claim_density_per_1000_words:
evidence_density_per_1000_words:
equation_density_per_1000_words:
definition_density_per_1000_words:
compression_line_count:
compression_line_quality_score:
novel_connection_count:
cross_domain_mapping_count:
signal_to_noise_ratio:
redundancy_penalty:
conceptual_compression_score:
standard_pages:
info_density_per_page:
signal_per_page:
noise_per_page:
claim_per_page:
evidence_per_page:
```

## 11 HTML Report

Report sections:

```yaml
executive_summary:
top_strengths:
top_weaknesses:
overstatement_report:
claim_inventory:
evidence_map:
source_quality_report:
math_structure_report:
coherence_report:
readability_report:
knowledge_graph_summary:
recommended_revisions:
json_export:
excel_export:
html_export:
markdown_export:
```

HTML panels:

```yaml
score_card_panel:
claim_table_panel:
evidence_table_panel:
risk_flags_panel:
graph_preview_panel:
revision_suggestions_panel:
source_quality_panel:
```

## 12 Academic Rubric Layer

```yaml
thesis_clarity_score:
argument_structure_score:
evidence_quality_score:
source_quality_score:
citation_quality_score:
method_clarity_score:
definition_clarity_score:
originality_score:
coherence_score:
organization_score:
style_score:
grammar_score:
limitations_score:
counterargument_score:
conclusion_strength_score:
```

## 13 Web Intake

```yaml
source_url:
source_type:
download_date:
scrape_date:
author_detected:
publisher_detected:
publication_date_detected:
doi_detected:
citation_metadata_detected:
pdf_text_extracted:
ocr_required:
html_cleaned:
main_content_extracted:
references_extracted:
links_extracted:
images_extracted:
tables_extracted:
equations_extracted:
source_domain:
source_authority_score:
peer_reviewed_status:
institutional_source_flag:
primary_source_flag:
secondary_source_flag:
blog_or_opinion_flag:
fringe_source_flag:
dead_link_flag:
archive_url:
```

## 14 Formal Maturity Ladder

```yaml
formal_maturity_level:
  - metaphor
  - analogy
  - structural_correspondence
  - formal_model
  - machine_checked_theorem
  - empirical_support
  - public_proof_claim
current_level:
next_level_required:
proof_boundary:
overclaim_if_stated_as:
safe_public_wording:
```

## 15 Lean 4 / Formal Verification Layer

```yaml
lean_file_present:
lean_theorem_count:
lean_definition_count:
lean_axiom_count:
sorry_count:
admitted_proof_count:
kernel_verified_count:
failed_proof_count:
formalization_status:
maps_to_claim_ids:
claim_has_lean_definition:
claim_has_lean_theorem:
claim_is_kernel_verified:
claim_exceeds_lean_boundary:
```

## 16 Math / Equation Layer

```yaml
equation_count:
unique_symbol_count:
variable_count:
undefined_variable_count:
defined_variable_count:
unit_count:
missing_unit_count:
dimensional_consistency_flag:
equation_reference_count:
equation_explanation_score:
derivation_present:
boundary_conditions_present:
assumptions_present:
falsification_conditions_present:
chi_symbol_count:
master_equation_reference_count:
G_count:
M_count:
E_count:
S_count:
T_count:
K_count:
R_count:
Q_count:
F_count:
C_count:
veto_property_present:
product_form_present:
ratio_form_present:
lagrangian_form_present:
```

## 17 Assumption / Boundary Layer

```yaml
explicit_assumption_count:
implicit_assumption_count:
unstated_dependency_count:
boundary_condition_count:
scope_limit_count:
category_boundary_count:
domain_transfer_count:
unsupported_domain_transfer_count:
physics_to_theology_transfer_count:
theology_to_physics_transfer_count:
information_to_morality_transfer_count:
math_to_metaphysics_transfer_count:
```

## 18 Falsifiability / Kill-Switch Layer

```yaml
falsifiable_claim_count:
non_falsifiable_claim_count:
testable_prediction_count:
kill_condition_count:
failed_test_count:
passed_test_count:
expected_fail_count:
warning_count:
replication_needed_count:
what_would_disprove_this:
what_would_weaken_this:
what_would_strengthen_this:
what_is_only_internal_to_framework:
```

## 19 Novelty / Prior Art Layer

```yaml
novel_claim_count:
known_claim_count:
unclear_novelty_count:
prior_art_match_count:
citation_overlap_count:
uncredited_similarity_risk:
original_synthesis_score:
new_term_count:
new_equation_count:
new_mapping_count:
```

## 20 Final Score System

```yaml
master_score_10000:
academic_score_1000:
truth_engine_score_1000:
coherence_score_1000:
evidence_score_1000:
math_score_1000:
formal_verification_score_1000:
writing_score_1000:
novelty_score_1000:
risk_control_score_1000:
graph_integration_score_1000:
score_band:
primary_failure_points:
```

## Core Database Tables

Full build:

```text
papers
paper_versions
paper_sections
paper_metrics_raw
paper_scores
claims
claim_scores
evidence_items
sources
equations
definitions
axioms
lean_links
knowledge_nodes
knowledge_edges
risk_flags
review_reports
exports
```

MVP:

```text
papers
paper_sections
claims
evidence_items
metrics
scores
reports
```

## MVP Build Order

```text
1. PDF / DOCX / HTML / Markdown intake
2. Basic text metrics
3. Section detector
4. Claim extractor
5. Evidence mapper
6. Overstatement detector
7. Academic rubric scorer
8. Formal maturity classifier
9. HTML / Markdown report
10. Excel / JSON export
```

Then:

```text
11. Knowledge graph
12. Lean 4 linkage
13. Theophysics-specific scoring
14. Web intake
15. Postgres dashboard
```

## Spine Variables

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

