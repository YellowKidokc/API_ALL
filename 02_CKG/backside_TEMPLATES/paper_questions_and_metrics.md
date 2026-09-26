# Paper analysis question and metric inventory

Source: `X:\Python API` · 114 Python files · 36 focused producer scripts.

Each field below is source-declared. A blank, fallback, or prompt-only result must stay blank in the paper atom. Scores based on wording or similarity are text signals, not proof.

## Text And Readability

### text_analyzer.py — WIRED

- **Question:** How many words, paragraphs, keywords, and reading-grade estimates does the paper have?
- **Declared output keys:** `automated_readability`, `avg_paragraph_words`, `coleman_liau`, `dale_chall`, `flesch_kincaid_grade`, `flesch_reading_ease`, `gunning_fog`, `header_count`, `keybert_keywords`, `lexicon_count`, `paragraph_count`, `reading_time_min`, `sentence_count`, `smog_index`, `syllable_count`, `text_standard`, `top_bigrams`, `top_trigrams`, `unique_word_count`, `vocab_richness`, `word_count`, `yake_keywords`

### linguistic_analyzer.py — WIRED

- **Question:** How complex are the sentences, vocabulary, and syntax?
- **Declared output keys:** `lr_cttr`, `lr_error`, `lr_hdd`, `lr_mattr`, `lr_mtld`, `lr_rttr`, `lr_terms`, `lr_ttr`, `lr_words`, `textdescriptives_status`

### idea_density_analyzer.py — WIRED

- **Question:** What is the text's estimated idea density?
- **Declared output keys:** `idea_density_error`, `idea_density_level`, `idea_density_max`, `idea_density_mean`, `idea_density_min`, `idea_density_status`, `idea_density_std`, `idea_paragraphs_analyzed`, `idea_total_propositions`

### paper_analyzer.py — WIRED

- **Question:** What are the paper's structural, grammatical, argument, flow, and link metrics?
- **Declared output keys:** `adj_pct`, `adv_pct`, `argument_grade`, `assertive_verb_count`, `avg_dependency_depth`, `avg_sentences_per_paragraph`, `avg_words_per_sentence`, `claim_count`, `claim_density_per1k`, `cognitive_load`, `cognitive_load_error`, `coherence_flag`, `compression_ratio`, `cross_domain_bridges`, `density_label`, `evidence_count`, `evidence_density_per1k`, `evidence_to_claim_ratio`, `external_links`, `falsifiability_markers`, `flesch_kincaid_grade`, `flow_label`, `fluff_flag`, `gunning_fog`, `header_count`, `internal_external_ratio`, `internal_links`, `link_citation`, `link_concept`, `link_density_per1k`, `link_dependency`, `link_evidence`, `link_navigation`, `link_quality_score`, `max_dependency_depth`, `modal_verb_count`, `modal_vs_assertive_ratio`, `noun_pct`, `overlink_flag`, `paragraph_count`, `passive_pct`, `passive_voice_count`, `pos_note`, `prep_pct`, `readability_note`, `reading_time_min`, `semantic_error`, `semantic_note`, `sentence_count`, `signal_noise_ratio`, `smog_index`, `stopword_ratio`, `text_standard`, `topic_drift_avg`, `topic_drift_max`, `topic_drift_scores`, `total_links`, `transition_count`, `transition_density_pct`, `trigram_redundancy`, `ttr`, `underlink_flag`, `unique_word_count`, `verb_pct`, `weight_signal`, `word_count`

### nlp_analyzer.py — WIRED

- **Question:** Which entities, topics, and key sentences are detected?
- **Declared output keys:** `entity_concepts`, `entity_count`, `entity_orgs`, `entity_people`, `entity_types_found`, `topic_count`

## Academic Claims Evidence

### academic_scorer.py — WIRED

- **Question:** What academic claims, citations, and overstatements does the paper contain?
- **Declared output keys:** `absolute_claim_count`, `absolute_density_per1k`, `academic_grade`, `academic_rubric_grade`, `academic_rubric_total`, `academic_signal_count`, `academic_signal_density`, `author_year_citation_count`, `citation_count`, `citation_density_per1k`, `claim_candidate_1`, `claim_candidate_2`, `claim_candidate_3`, `claim_density_per1k`, `claim_marker_count`, `counterargument_count`, `definition_marker_count`, `doi_references`, `equation_count`, `equation_density_per1k`, `evidence_candidate_1`, `evidence_candidate_2`, `evidence_density_per1k`, `evidence_marker_count`, `evidence_to_claim_ratio`, `external_theories`, `external_theory_count`, `falsifiability_density_per1k`, `falsifiability_marker_count`, `footnote_count`, `has_abstract`, `has_conclusion`, `has_discussion`, `has_introduction`, `has_methodology`, `has_references_section`, `has_results`, `heading_count`, `hedge_count`, `hedge_density_per1k`, `hedge_to_absolute_ratio`, `limitation_count`, `novelty_marker_count`, `numeric_citation_count`, `quantitative_marker_count`, `reference_entry_count`, `rubric_claim_points`, `rubric_falsifiability_points`, `rubric_grounding_points`, `rubric_quantitative_points`, `rubric_structure_points`, `structure_score`, `title_detected`, `url_references`

### claim_inventory.py — INVENTORY_ONLY

- **Question:** What exact assertions are candidates for claim review?

### evidence_map.py — INVENTORY_ONLY

- **Question:** Which evidence statements are linked to which claims?

### kill_conditions.py — INVENTORY_ONLY

- **Question:** What would defeat each exact claim?

### equation_audit.py — INVENTORY_ONLY

- **Question:** What equations and assumptions need mathematical review?

### assumption_stack.py — INVENTORY_ONLY

- **Question:** Which assumptions does each argument require?

### overstatement_detector.py — INVENTORY_ONLY

- **Question:** Where does wording exceed the available evidence?

### coherence_score.py — INVENTORY_ONLY

- **Question:** What consistency analysis is proposed for the text?

## Framework And Truth Heuristics

### theophysics_scorer.py — WIRED

- **Question:** Which framework terms appear, as lexical signals only?
- **Declared output keys:** `anti_fruits_composite`, `anti_fruits_detail`, `chi_score`, `chi_status`, `ckg_raw`, `ckg_tier`, `cross_domain_bridges`, `dominant_anti_fruit`, `dominant_fruit`, `fruits_composite`, `fruits_detail`, `fruits_net_score`, `knowledge_score`, `me_avg_score`, `me_dominant_variable`, `scripture_refs`, `wisdom_score`, `wk_ratio`, `wk_status`

### truth_runner.py — INVENTORY_ONLY

- **Question:** Which scanner metrics are returned for the document?

### truth_coherence_scanner.py — INVENTORY_ONLY

- **Question:** Which text markers does the heuristic scanner label?
- **Schema fields:** `ClaimRecord.absolute_overreach`, `ClaimRecord.claim_index`, `ClaimRecord.claim_kind`, `ClaimRecord.claim_score`, `ClaimRecord.claim_status`, `ClaimRecord.claim_text`, `ClaimRecord.dependency_present`, `ClaimRecord.evidence_present`, `ClaimRecord.falsifiability_present`, `ClaimRecord.hedge_present`, `ClaimRecord.local_contradiction`, `ClaimRecord.paragraph_index`, `ClaimRecord.precision_present`, `ClaimRecord.sentence_index`, `ClaimRecord.source`, `ClaimRecord.support_status`, `DocumentRecord.absolute_pressure`, `DocumentRecord.anchored_claims`, `DocumentRecord.anti_fruit_pressure`, `DocumentRecord.anti_fruits_vector`, `DocumentRecord.character_attributes`, `DocumentRecord.character_posture`, `DocumentRecord.character_profile`, `DocumentRecord.claim_count`, `DocumentRecord.coherence_score`, `DocumentRecord.combined_score`, `DocumentRecord.contradiction_flags`, `DocumentRecord.contradictory_claims`, `DocumentRecord.discipline_score`, `DocumentRecord.evidence_density`, `DocumentRecord.falsifiability_density`, `DocumentRecord.falsifiable_claims`, `DocumentRecord.fruit_integrity_score`, `DocumentRecord.fruits_vector`, `DocumentRecord.hedge_density`, `DocumentRecord.integrity_profiles`, `DocumentRecord.overstated_claims`, `DocumentRecord.paragraph_count`, `DocumentRecord.rhetorical_force`, `DocumentRecord.section_count`, `DocumentRecord.sentence_count`, `DocumentRecord.source`, `DocumentRecord.source_type`, `DocumentRecord.speculative_claims`, `DocumentRecord.title`, `DocumentRecord.top_risky_sentences`, `DocumentRecord.top_supported_sentences`, `DocumentRecord.truth_score`, `DocumentRecord.under_supported_claims`, `DocumentRecord.warmth_score`, `SentenceScore.absolute_pressure`, `SentenceScore.claim_strength`, `SentenceScore.contradiction_pressure`, `SentenceScore.dependency_signal`, `SentenceScore.evidence_anchor`, `SentenceScore.falsifiability_signal`, `SentenceScore.hedge_pressure`, `SentenceScore.index`, `SentenceScore.precision_signal`, `SentenceScore.text`, `SentenceScore.truth_score`, `SentenceScore.truth_status`

### chi_computation.py — INVENTORY_ONLY

- **Question:** Which inputs would a chi calculation require?
- **Schema fields:** `ChiTimeSeries.C_CRIT`, `ChiTimeSeries.a_values`, `ChiTimeSeries.chi_values`, `ChiTimeSeries.dchi_dt`, `ChiTimeSeries.lambda_values`, `ChiTimeSeries.pi_values`, `ChiTimeSeries.years`, `DomainData.metrics`, `DomainData.name`, `DomainData.triad`, `DomainData.values`, `DomainData.years`, `TriadScore.domains`, `TriadScore.name`, `TriadScore.values`, `TriadScore.years`

### heartbeat_analyzer.py — WIRED

- **Question:** What structural motifs recur across the paper?
- **Declared output keys:** `chi`, `chi_composite`, `chi_dominant`, `chi_keys`, `chi_max`, `chi_mean`, `chi_min`, `chi_std`, `combined`, `combined_mean`, `combined_std`, `critique_words`, `defense_words`, `excluded_sections`, `fruit_composite`, `fruit_dominant`, `fruit_keys`, `fruit_max`, `fruit_mean`, `fruit_min`, `fruit_std`, `fruits`, `grade`, `heartbeat`, `heartbeat_error`, `idx`, `index`, `interpretation`, `negative_hits`, `normalized_score`, `peak_score`, `peak_sentence`, `peak_text`, `positive_hits`, `score`, `section`, `section_boundaries`, `section_idx`, `sentence_count`, `structural`, `structural_net`, `summary`, `theory_words`, `tier`, `total_score`, `v2_structural`, `valley_score`, `valley_sentence`, `valley_text`, `word_count`

### word_level_mapper.py — INVENTORY_ONLY

- **Question:** Which words or sentences match supplied anchor sets?

## Emotion And Fruit Text Signals

### emotion_analyzer.py — WIRED

- **Question:** Which emotion terms or model labels appear in the text?
- **Declared output keys:** `anti_emo_composite`, `betrayal`, `conflict`, `corruption`, `cruelty`, `despair`, `emo_dominant`, `emo_sentence_count`, `emo_top_5`, `faithfulness`, `fruit_emo_composite`, `fruit_emo_net`, `fruit_emo_strongest`, `fruit_emo_weakest`, `gentleness`, `goemotions_status`, `goodness`, `harshness`, `hatred`, `impatience`, `indulgence`, `joy`, `kindness`, `love`, `nrc_status`, `nrc_top_emotions`, `patience`, `peace`, `self_control`

### heartbeat_analyzer.py — WIRED

- **Question:** What structural motifs recur across the paper?
- **Declared output keys:** `chi`, `chi_composite`, `chi_dominant`, `chi_keys`, `chi_max`, `chi_mean`, `chi_min`, `chi_std`, `combined`, `combined_mean`, `combined_std`, `critique_words`, `defense_words`, `excluded_sections`, `fruit_composite`, `fruit_dominant`, `fruit_keys`, `fruit_max`, `fruit_mean`, `fruit_min`, `fruit_std`, `fruits`, `grade`, `heartbeat`, `heartbeat_error`, `idx`, `index`, `interpretation`, `negative_hits`, `normalized_score`, `peak_score`, `peak_sentence`, `peak_text`, `positive_hits`, `score`, `section`, `section_boundaries`, `section_idx`, `sentence_count`, `structural`, `structural_net`, `summary`, `theory_words`, `tier`, `total_score`, `v2_structural`, `valley_score`, `valley_sentence`, `valley_text`, `word_count`

### word_level_mapper.py — INVENTORY_ONLY

- **Question:** Which words or sentences match supplied anchor sets?

## Corpus And Graph

### graph_builder.py — INVENTORY_ONLY

- **Declared output keys:** `betweenness`, `centrality`, `chi_score`, `cluster`, `cluster_count`, `combined_score`, `degree`, `dominant_variable`, `edge_count`, `edges`, `label`, `most_central`, `node_count`, `node_data`, `nodes`, `stats`, `target`, `topic_1`, `truth_score`, `truth_tier`, `weight`, `wk_ratio`, `word_count`

### co_term_density.py — INVENTORY_ONLY

- **Question:** Which concepts co-occur within a chosen text window?

### cooccurrence_analyzer.py — INVENTORY_ONLY

- **Question:** Which concepts co-occur across the indexed corpus?

### correlation_engine.py — INVENTORY_ONLY

- **Question:** What cross-document term correspondence is suggested?

### paper_compare.py — INVENTORY_ONLY

- **Question:** How do two or more papers differ on measured features?
- **Schema fields:** `PaperStats.chars`, `PaperStats.citations`, `PaperStats.concepts`, `PaperStats.domains`, `PaperStats.equations`, `PaperStats.integration_order`, `PaperStats.lines`, `PaperStats.paper_id`, `PaperStats.path`, `PaperStats.sections`, `PaperStats.title`, `PaperStats.words`

### run_series_analytics.py — INVENTORY_ONLY

- **Question:** What patterns emerge across a paper series?

## Physics And Theory

### physics.py — INVENTORY_ONLY

- **Question:** Which physics analogies and kill tests are proposed?

### physics_comparison.py — INVENTORY_ONLY

- **Question:** What claimed physics mapping needs a boundary check?

### matter_analysis.py — INVENTORY_ONLY

- **Question:** What matter-related analysis does the script define?

### novelty_classification.py — INVENTORY_ONLY

- **Question:** Which claims are new relative to the reviewed corpus?

### overlap_calculator.py — INVENTORY_ONLY

- **Question:** How much do two supplied proposition sets overlap?

## Schema And Review

### snapshot_schema.py — INVENTORY_ONLY

- **Schema fields:** `AssumptionStack.causal`, `AssumptionStack.explicit`, `AssumptionStack.implicit`, `AssumptionStack.imported`, `AssumptionStack.measurement`, `AssumptionStack.philosophical`, `AssumptionStack.scientific`, `AssumptionStack.theological`, `CitationNode.cited`, `CitationNode.confidence`, `CitationNode.relation`, `Claim.claim`, `Claim.claim_type`, `Claim.evidence_present`, `Claim.importance`, `Claim.needs_citation`, `Claim.notes`, `Claim.risk_level`, `Claim.testability`, `CoherenceScore.ai_confidence`, `CoherenceScore.citation_adequacy`, `CoherenceScore.claim_discipline`, `CoherenceScore.definition_clarity`, `CoherenceScore.domain_separation`, `CoherenceScore.equation_coherence`, `CoherenceScore.falsifiability`, `CoherenceScore.reader_burden`, `CoherenceScore.review_readiness`, `CoherenceScore.scope_control`, `EquationEntry.dimensional_status`, `EquationEntry.equation`, `EquationEntry.issues`, `EquationEntry.operational_status`, `EquationEntry.purpose`, `EquationEntry.role`, `EquationEntry.variable_definitions`, `EquationEntry.variables_defined`, `EvidenceEntry.claim`, `EvidenceEntry.counterevidence_needed`, `EvidenceEntry.evidence_quality`, `EvidenceEntry.evidence_type`, `EvidenceEntry.gap`, `EvidenceEntry.supporting_evidence`, `KillCondition.claim`, `KillCondition.current_status`, `KillCondition.kill_condition`, `KillCondition.severity`, `KillCondition.test_method`, `NoveltyClassification.honest_label`, `NoveltyClassification.novelty_levels`, `NoveltyClassification.overstated_novelty_flags`, `NoveltyClassification.primary_novelty`, `OverstatementDetector.delta`, `OverstatementDetector.evidence_strength_index`, `OverstatementDetector.overstated_passages`, `OverstatementDetector.rhetorical_strength_index`, `OverstatementDetector.severity`, `PaperIdentity.author`, `PaperIdentity.date`, `PaperIdentity.domain`, `PaperIdentity.paper_id`, `PaperIdentity.paper_type`, `PaperIdentity.series`, `PaperIdentity.title`, `PaperIdentity.version`, `PhysicsComparison.category_confusion_risk`, `PhysicsComparison.difference`, `PhysicsComparison.does_paper_outperform`, `PhysicsComparison.nearest_theory`, `PhysicsComparison.similarity`, `ProofExplorerSnapshot.assumptions`, `ProofExplorerSnapshot.citations`, `ProofExplorerSnapshot.claim_inventory`, `ProofExplorerSnapshot.coherence`, `ProofExplorerSnapshot.equations`, `ProofExplorerSnapshot.evidence_map`, `ProofExplorerSnapshot.generated_at`, `ProofExplorerSnapshot.identity`, `ProofExplorerSnapshot.kill_conditions`, `ProofExplorerSnapshot.novelty`, `ProofExplorerSnapshot.overstatement`, `ProofExplorerSnapshot.paper_id`, `ProofExplorerSnapshot.physics_comparison`, `ProofExplorerSnapshot.pipeline_metrics`, `ProofExplorerSnapshot.revision`, `ProofExplorerSnapshot.schema_version`, `ProofExplorerSnapshot.spine_analysis`, `ProofExplorerSnapshot.theophysics`, `ProofExplorerSnapshot.thesis`, `RevisionPlan.best_next_test`, `RevisionPlan.must_fix_before_publication`, `RevisionPlan.needs_expert_review`, `RevisionPlan.strongest_part`, `RevisionPlan.weakest_part`, `TheophysicsOverlay.ckg_score`, `TheophysicsOverlay.decision_tree_status`, `TheophysicsOverlay.declared_axioms`, `TheophysicsOverlay.fruits_score`, `TheophysicsOverlay.lean_file_path`, `TheophysicsOverlay.seven_q_grid`, `TheophysicsOverlay.spine_mappings`, `TheophysicsOverlay.swap_test`, `Thesis.ai_confidence`, `Thesis.one_sentence`

### snapshot_merge.py — INVENTORY_ONLY

- Contract requires direct review; no paper metric was statically confirmed.

### validation_scaffold.py — INVENTORY_ONLY

- **Question:** Which indexed claims still lack validation?
- **Declared output keys:** `analogy`, `contradicts`, `related`, `supports`

### spine_analysis.py — INVENTORY_ONLY

- **Question:** What thesis and dependency spine does the paper present?
- **Declared output keys:** `content`, `role`, `section`, `type`

### revision_plan.py — INVENTORY_ONLY

- **Question:** What revisions would address identified gaps?

## Word-level channel families

### word_level_mapper.py

- **GOEMOTIONS_LABELS (28):** admiration, amusement, anger, annoyance, approval, caring, confusion, curiosity, desire, disappointment, disapproval, disgust, embarrassment, excitement, fear, gratitude, grief, joy, love, nervousness, optimism, pride, realization, relief, remorse, sadness, surprise, neutral
- **FRUIT_BLEND (9):** love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, self_control
- **ANTI_FRUIT_MAP (9):** hatred, despair, conflict, impatience, cruelty, corruption, betrayal, harshness, indulgence

### canonical_anchors.py

- **PROPERTIES_24 (24):** P04_simple, P05_consistent, P12_true, P13_rational, P23_generative, P24_judging, P01_necessary, P02_eternal, P03_immutable, P06_universal, P07_immaterial, P08_foundational, P09_self_existent, P10_infinite, P11_perfect, P14_order_giving, P15_law_giving, P16_intelligible, P17_necessary_for_knowledge, P18_invariant, P19_non_local, P20_transcendent, P21_objective, P22_unified
- **LAWS_CONSTRUCTIVE (10):** L01_gravitation_grace, L02_motion_grace_force, L03_electromagnetism_truth, L04_strong_force_love, L05_thermodynamics_harvest, L06_information_logos, L07_quantum_faith, L08_relativity_eternal_frame, L09_cosmology_omega, L10_coherence_christ
- **LAWS_DESTRUCTIVE (10):** L01_gravitation_sin, L02_motion_sin_nature, L03_electromagnetism_deception, L04_strong_force_captivity, L05_thermodynamics_judgment, L06_information_chaos, L07_quantum_false_observation, L08_relativity_frame_lock, L09_cosmology_heat_death, L10_decoherence
- **FRUITS_PHYSICS (9):** fruit_love, fruit_joy, fruit_peace, fruit_patience, fruit_kindness, fruit_goodness, fruit_faithfulness, fruit_gentleness, fruit_self_control
- **ANTI_FRUITS_PHYSICS (9):** anti_love, anti_joy, anti_peace, anti_patience, anti_kindness, anti_goodness, anti_faithfulness, anti_gentleness, anti_self_control
- **ARMOR (6):** armor_belt_truth, armor_breastplate_righteousness, armor_shoes_peace, armor_shield_faith, armor_helmet_salvation, armor_sword_spirit
- **BEATITUDES (8):** beat_poor_spirit, beat_mourn, beat_meek, beat_hunger_righteousness, beat_merciful, beat_pure_heart, beat_peacemakers, beat_persecuted
- **GIFTS (9):** gift_wisdom, gift_knowledge, gift_faith, gift_healing, gift_miracles, gift_prophecy, gift_discernment, gift_tongues, gift_interpretation
- **COUPLINGS (8):** coupling_faith, coupling_mercy, coupling_hope, coupling_wisdom, coupling_covenant, coupling_salvation, coupling_worship, coupling_conscience

### heartbeat_analyzer.py

- **FRUIT_ANCHORS (9):** love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, self_control
- **CHI_ANCHORS (10):** G, M, E, S, T, K, R, Q, F, C
- **STRUCTURAL_PATTERNS (11):** definition, derivation, scope_bound, prediction, evidence, equation, edge_case, modularity, steelman, overclaim, cross_domain

## Additional word-level questions

The word-level mapper declares channels A–N. Its source includes 28 GoEmotions labels including neutral, while the comment calls the channel 27. The counts below use the actual declared labels. Values are aligned to word positions but several are computed at sentence level and copied to those positions.

- Which emotion model labels are assigned to each sentence/word position?
- Which nine fruit and nine anti-fruit blends are calculated from those model labels?
- Which semantic similarities are assigned for nine fruit anchors and ten χ variables?
- Which of 11 structural patterns appear at each position?
- Which of 24 properties, ten constructive laws, and ten destructive laws are closest to each sentence?
- Which Fruits-as-Physics and anti-fruit anchors, six Armor pieces, eight Beatitudes, nine Gifts, and eight Couplings are closest?
- If OpenAI scoring was explicitly run, what sentence type, bridge score, logic score, falsifiability, axiom dependency count, theory count, and objection marker were returned?
- Which channel values were unavailable, model fallback, or copied from a sentence rather than measured for that exact word?

## Remaining scripts by role

These scripts are included for completeness. A source writer, renderer, fixture, or orchestrator is not automatically a per-paper measurement.

### Candidate Analysis Or Helper

- `academic_scorer_v2.py`
- `analyze_coherence.py` — How consistent are concepts across a paper series?
- `analyze_paper.py` — What does the local paper analyzer report?
- `check_and_fix_assembled.py`
- `check_missing_sections.py`
- `cosmic_fate_curves.py`
- `deep_workbook.py`
- `destroy.py`
- `dns_calculator.py` — How does the defined semantic novelty formula score an input?
- `duplicate_finder.py` — Which indexed notes may be duplicates?
- `engine.py`
- `extract_missing_sections.py`
- `extract_text.py` — What visible paper text can be extracted without changing the source?
- `law1_visualizations.py`
- `llm_bridge.py`
- `master_equation_network.py` — Which master equation variables are referenced or mapped?
- `obsidian_pipeline.py`
- `obsidian_writer.py`
- `paper_atom_api.py`
- `paper_metric_inventory.py`
- `prompts_smoketest.py`
- `quick_stats.py` — What counts exist in a specified vault?
- `scorer.py` — How does the defined 7Q scoring model combine supplied inputs?
- `seven_q_runner.py`
- `smart_breakthrough_detector.py` — Which passages are candidate breakthroughs for human review?

### Fixture Or Helper

- `_run_boundary_question.py`
- `_runner.py`
- `_test_fixture.py`

### Identity Schema Or Validation

- `canonical_anchors.py` — Which canonical anchors are relevant for review?
- `id_system.py`
- `uid_generator.py`

### Llm Or Prompt

- `ollama_7q_runner.py`
- `openai_8_prompts.py`
- `openai_mda_two_lane.py`
- `openai_paper_intel.py`
- `openai_sentence_scorer.py`

### Orchestrator Or Intake

- `app.py`
- `docker_entrypoint.py`
- `intake.py`
- `main.py`
- `pipeline.py`
- `pipeline_101124.py`
- `pipeline_legacy.py`
- `run_baseline.py`
- `run_brain_alignment.py`
- `run_convergence_batch.py`
- `run_drop_zone.py`
- `run_full_series_suite.py`
- `run_obsidian_brain.py`
- `run_pipeline.py`

### Renderer Or Generator

- `build_all_paper_mappings.py`
- `build_mermaid.py`
- `concept_hub_generator.py`
- `dashboard_generator.py`
- `generate_paper4_visualizations.py`
- `generate_report.py`
- `html_report.py`
- `paper_i_filler.py`
- `render_integrated_information.py`
- `render_soul_field_potential.py`
- `render_three_stage_collapse.py`
- `render_three_stage_collapse_v2.py`
- `render_yukawa_coupling.py`
- `template_filler.py`

### Source Or Vault Mutation

- `add_all_missing_sections.py`
- `add_missing_sections_final.py`
- `add_yaml_frontmatter.py`
- `auto_linker.py`
- `clean_concepts.py`
- `consolidate_p01.py`
- `consolidate_papers.py`
- `create_master_1-14.py`
- `create_remaining_sections.py`
- `grace_vault_manager.py`
- `promotion_pass.py`
- `sync_to_postgres.py`
- `toolkit_manager.py`
- `vault_refresh.py`

## Field-by-field API questions

These questions are generated from source-declared field keys. The field may be absent at runtime, so every answer needs a status and method.

- `text_analyzer.py` · `automated_readability` — What value, method, and status does text_analyzer.py report for automated_readability on this paper?
- `text_analyzer.py` · `avg_paragraph_words` — What value, method, and status does text_analyzer.py report for avg_paragraph_words on this paper?
- `text_analyzer.py` · `coleman_liau` — What value, method, and status does text_analyzer.py report for coleman_liau on this paper?
- `text_analyzer.py` · `dale_chall` — What value, method, and status does text_analyzer.py report for dale_chall on this paper?
- `text_analyzer.py` · `flesch_kincaid_grade` — What value, method, and status does text_analyzer.py report for flesch_kincaid_grade on this paper?
- `text_analyzer.py` · `flesch_reading_ease` — What value, method, and status does text_analyzer.py report for flesch_reading_ease on this paper?
- `text_analyzer.py` · `gunning_fog` — What value, method, and status does text_analyzer.py report for gunning_fog on this paper?
- `text_analyzer.py` · `header_count` — What value, method, and status does text_analyzer.py report for header_count on this paper?
- `text_analyzer.py` · `keybert_keywords` — What value, method, and status does text_analyzer.py report for keybert_keywords on this paper?
- `text_analyzer.py` · `lexicon_count` — What value, method, and status does text_analyzer.py report for lexicon_count on this paper?
- `text_analyzer.py` · `paragraph_count` — What value, method, and status does text_analyzer.py report for paragraph_count on this paper?
- `text_analyzer.py` · `reading_time_min` — What value, method, and status does text_analyzer.py report for reading_time_min on this paper?
- `text_analyzer.py` · `sentence_count` — What value, method, and status does text_analyzer.py report for sentence_count on this paper?
- `text_analyzer.py` · `smog_index` — What value, method, and status does text_analyzer.py report for smog_index on this paper?
- `text_analyzer.py` · `syllable_count` — What value, method, and status does text_analyzer.py report for syllable_count on this paper?
- `text_analyzer.py` · `text_standard` — What value, method, and status does text_analyzer.py report for text_standard on this paper?
- `text_analyzer.py` · `top_bigrams` — What value, method, and status does text_analyzer.py report for top_bigrams on this paper?
- `text_analyzer.py` · `top_trigrams` — What value, method, and status does text_analyzer.py report for top_trigrams on this paper?
- `text_analyzer.py` · `unique_word_count` — What value, method, and status does text_analyzer.py report for unique_word_count on this paper?
- `text_analyzer.py` · `vocab_richness` — What value, method, and status does text_analyzer.py report for vocab_richness on this paper?
- `text_analyzer.py` · `word_count` — What value, method, and status does text_analyzer.py report for word_count on this paper?
- `text_analyzer.py` · `yake_keywords` — What value, method, and status does text_analyzer.py report for yake_keywords on this paper?
- `linguistic_analyzer.py` · `lr_cttr` — What value, method, and status does linguistic_analyzer.py report for lr_cttr on this paper?
- `linguistic_analyzer.py` · `lr_error` — What value, method, and status does linguistic_analyzer.py report for lr_error on this paper?
- `linguistic_analyzer.py` · `lr_hdd` — What value, method, and status does linguistic_analyzer.py report for lr_hdd on this paper?
- `linguistic_analyzer.py` · `lr_mattr` — What value, method, and status does linguistic_analyzer.py report for lr_mattr on this paper?
- `linguistic_analyzer.py` · `lr_mtld` — What value, method, and status does linguistic_analyzer.py report for lr_mtld on this paper?
- `linguistic_analyzer.py` · `lr_rttr` — What value, method, and status does linguistic_analyzer.py report for lr_rttr on this paper?
- `linguistic_analyzer.py` · `lr_terms` — What value, method, and status does linguistic_analyzer.py report for lr_terms on this paper?
- `linguistic_analyzer.py` · `lr_ttr` — What value, method, and status does linguistic_analyzer.py report for lr_ttr on this paper?
- `linguistic_analyzer.py` · `lr_words` — What value, method, and status does linguistic_analyzer.py report for lr_words on this paper?
- `linguistic_analyzer.py` · `textdescriptives_status` — What value, method, and status does linguistic_analyzer.py report for textdescriptives_status on this paper?
- `idea_density_analyzer.py` · `idea_density_error` — What value, method, and status does idea_density_analyzer.py report for idea_density_error on this paper?
- `idea_density_analyzer.py` · `idea_density_level` — What value, method, and status does idea_density_analyzer.py report for idea_density_level on this paper?
- `idea_density_analyzer.py` · `idea_density_max` — What value, method, and status does idea_density_analyzer.py report for idea_density_max on this paper?
- `idea_density_analyzer.py` · `idea_density_mean` — What value, method, and status does idea_density_analyzer.py report for idea_density_mean on this paper?
- `idea_density_analyzer.py` · `idea_density_min` — What value, method, and status does idea_density_analyzer.py report for idea_density_min on this paper?
- `idea_density_analyzer.py` · `idea_density_status` — What value, method, and status does idea_density_analyzer.py report for idea_density_status on this paper?
- `idea_density_analyzer.py` · `idea_density_std` — What value, method, and status does idea_density_analyzer.py report for idea_density_std on this paper?
- `idea_density_analyzer.py` · `idea_paragraphs_analyzed` — What value, method, and status does idea_density_analyzer.py report for idea_paragraphs_analyzed on this paper?
- `idea_density_analyzer.py` · `idea_total_propositions` — What value, method, and status does idea_density_analyzer.py report for idea_total_propositions on this paper?
- `paper_analyzer.py` · `adj_pct` — What value, method, and status does paper_analyzer.py report for adj_pct on this paper?
- `paper_analyzer.py` · `adv_pct` — What value, method, and status does paper_analyzer.py report for adv_pct on this paper?
- `paper_analyzer.py` · `argument_grade` — What value, method, and status does paper_analyzer.py report for argument_grade on this paper?
- `paper_analyzer.py` · `assertive_verb_count` — What value, method, and status does paper_analyzer.py report for assertive_verb_count on this paper?
- `paper_analyzer.py` · `avg_dependency_depth` — What value, method, and status does paper_analyzer.py report for avg_dependency_depth on this paper?
- `paper_analyzer.py` · `avg_sentences_per_paragraph` — What value, method, and status does paper_analyzer.py report for avg_sentences_per_paragraph on this paper?
- `paper_analyzer.py` · `avg_words_per_sentence` — What value, method, and status does paper_analyzer.py report for avg_words_per_sentence on this paper?
- `paper_analyzer.py` · `claim_count` — What value, method, and status does paper_analyzer.py report for claim_count on this paper?
- `paper_analyzer.py` · `claim_density_per1k` — What value, method, and status does paper_analyzer.py report for claim_density_per1k on this paper?
- `paper_analyzer.py` · `cognitive_load` — What value, method, and status does paper_analyzer.py report for cognitive_load on this paper?
- `paper_analyzer.py` · `cognitive_load_error` — What value, method, and status does paper_analyzer.py report for cognitive_load_error on this paper?
- `paper_analyzer.py` · `coherence_flag` — What value, method, and status does paper_analyzer.py report for coherence_flag on this paper?
- `paper_analyzer.py` · `compression_ratio` — What value, method, and status does paper_analyzer.py report for compression_ratio on this paper?
- `paper_analyzer.py` · `cross_domain_bridges` — What value, method, and status does paper_analyzer.py report for cross_domain_bridges on this paper?
- `paper_analyzer.py` · `density_label` — What value, method, and status does paper_analyzer.py report for density_label on this paper?
- `paper_analyzer.py` · `evidence_count` — What value, method, and status does paper_analyzer.py report for evidence_count on this paper?
- `paper_analyzer.py` · `evidence_density_per1k` — What value, method, and status does paper_analyzer.py report for evidence_density_per1k on this paper?
- `paper_analyzer.py` · `evidence_to_claim_ratio` — What value, method, and status does paper_analyzer.py report for evidence_to_claim_ratio on this paper?
- `paper_analyzer.py` · `external_links` — What value, method, and status does paper_analyzer.py report for external_links on this paper?
- `paper_analyzer.py` · `falsifiability_markers` — What value, method, and status does paper_analyzer.py report for falsifiability_markers on this paper?
- `paper_analyzer.py` · `flesch_kincaid_grade` — What value, method, and status does paper_analyzer.py report for flesch_kincaid_grade on this paper?
- `paper_analyzer.py` · `flow_label` — What value, method, and status does paper_analyzer.py report for flow_label on this paper?
- `paper_analyzer.py` · `fluff_flag` — What value, method, and status does paper_analyzer.py report for fluff_flag on this paper?
- `paper_analyzer.py` · `gunning_fog` — What value, method, and status does paper_analyzer.py report for gunning_fog on this paper?
- `paper_analyzer.py` · `header_count` — What value, method, and status does paper_analyzer.py report for header_count on this paper?
- `paper_analyzer.py` · `internal_external_ratio` — What value, method, and status does paper_analyzer.py report for internal_external_ratio on this paper?
- `paper_analyzer.py` · `internal_links` — What value, method, and status does paper_analyzer.py report for internal_links on this paper?
- `paper_analyzer.py` · `link_citation` — What value, method, and status does paper_analyzer.py report for link_citation on this paper?
- `paper_analyzer.py` · `link_concept` — What value, method, and status does paper_analyzer.py report for link_concept on this paper?
- `paper_analyzer.py` · `link_density_per1k` — What value, method, and status does paper_analyzer.py report for link_density_per1k on this paper?
- `paper_analyzer.py` · `link_dependency` — What value, method, and status does paper_analyzer.py report for link_dependency on this paper?
- `paper_analyzer.py` · `link_evidence` — What value, method, and status does paper_analyzer.py report for link_evidence on this paper?
- `paper_analyzer.py` · `link_navigation` — What value, method, and status does paper_analyzer.py report for link_navigation on this paper?
- `paper_analyzer.py` · `link_quality_score` — What value, method, and status does paper_analyzer.py report for link_quality_score on this paper?
- `paper_analyzer.py` · `max_dependency_depth` — What value, method, and status does paper_analyzer.py report for max_dependency_depth on this paper?
- `paper_analyzer.py` · `modal_verb_count` — What value, method, and status does paper_analyzer.py report for modal_verb_count on this paper?
- `paper_analyzer.py` · `modal_vs_assertive_ratio` — What value, method, and status does paper_analyzer.py report for modal_vs_assertive_ratio on this paper?
- `paper_analyzer.py` · `noun_pct` — What value, method, and status does paper_analyzer.py report for noun_pct on this paper?
- `paper_analyzer.py` · `overlink_flag` — What value, method, and status does paper_analyzer.py report for overlink_flag on this paper?
- `paper_analyzer.py` · `paragraph_count` — What value, method, and status does paper_analyzer.py report for paragraph_count on this paper?
- `paper_analyzer.py` · `passive_pct` — What value, method, and status does paper_analyzer.py report for passive_pct on this paper?
- `paper_analyzer.py` · `passive_voice_count` — What value, method, and status does paper_analyzer.py report for passive_voice_count on this paper?
- `paper_analyzer.py` · `pos_note` — What value, method, and status does paper_analyzer.py report for pos_note on this paper?
- `paper_analyzer.py` · `prep_pct` — What value, method, and status does paper_analyzer.py report for prep_pct on this paper?
- `paper_analyzer.py` · `readability_note` — What value, method, and status does paper_analyzer.py report for readability_note on this paper?
- `paper_analyzer.py` · `reading_time_min` — What value, method, and status does paper_analyzer.py report for reading_time_min on this paper?
- `paper_analyzer.py` · `semantic_error` — What value, method, and status does paper_analyzer.py report for semantic_error on this paper?
- `paper_analyzer.py` · `semantic_note` — What value, method, and status does paper_analyzer.py report for semantic_note on this paper?
- `paper_analyzer.py` · `sentence_count` — What value, method, and status does paper_analyzer.py report for sentence_count on this paper?
- `paper_analyzer.py` · `signal_noise_ratio` — What value, method, and status does paper_analyzer.py report for signal_noise_ratio on this paper?
- `paper_analyzer.py` · `smog_index` — What value, method, and status does paper_analyzer.py report for smog_index on this paper?
- `paper_analyzer.py` · `stopword_ratio` — What value, method, and status does paper_analyzer.py report for stopword_ratio on this paper?
- `paper_analyzer.py` · `text_standard` — What value, method, and status does paper_analyzer.py report for text_standard on this paper?
- `paper_analyzer.py` · `topic_drift_avg` — What value, method, and status does paper_analyzer.py report for topic_drift_avg on this paper?
- `paper_analyzer.py` · `topic_drift_max` — What value, method, and status does paper_analyzer.py report for topic_drift_max on this paper?
- `paper_analyzer.py` · `topic_drift_scores` — What value, method, and status does paper_analyzer.py report for topic_drift_scores on this paper?
- `paper_analyzer.py` · `total_links` — What value, method, and status does paper_analyzer.py report for total_links on this paper?
- `paper_analyzer.py` · `transition_count` — What value, method, and status does paper_analyzer.py report for transition_count on this paper?
- `paper_analyzer.py` · `transition_density_pct` — What value, method, and status does paper_analyzer.py report for transition_density_pct on this paper?
- `paper_analyzer.py` · `trigram_redundancy` — What value, method, and status does paper_analyzer.py report for trigram_redundancy on this paper?
- `paper_analyzer.py` · `ttr` — What value, method, and status does paper_analyzer.py report for ttr on this paper?
- `paper_analyzer.py` · `underlink_flag` — What value, method, and status does paper_analyzer.py report for underlink_flag on this paper?
- `paper_analyzer.py` · `unique_word_count` — What value, method, and status does paper_analyzer.py report for unique_word_count on this paper?
- `paper_analyzer.py` · `verb_pct` — What value, method, and status does paper_analyzer.py report for verb_pct on this paper?
- `paper_analyzer.py` · `weight_signal` — What value, method, and status does paper_analyzer.py report for weight_signal on this paper?
- `paper_analyzer.py` · `word_count` — What value, method, and status does paper_analyzer.py report for word_count on this paper?
- `nlp_analyzer.py` · `entity_concepts` — What value, method, and status does nlp_analyzer.py report for entity_concepts on this paper?
- `nlp_analyzer.py` · `entity_count` — What value, method, and status does nlp_analyzer.py report for entity_count on this paper?
- `nlp_analyzer.py` · `entity_orgs` — What value, method, and status does nlp_analyzer.py report for entity_orgs on this paper?
- `nlp_analyzer.py` · `entity_people` — What value, method, and status does nlp_analyzer.py report for entity_people on this paper?
- `nlp_analyzer.py` · `entity_types_found` — What value, method, and status does nlp_analyzer.py report for entity_types_found on this paper?
- `nlp_analyzer.py` · `topic_count` — What value, method, and status does nlp_analyzer.py report for topic_count on this paper?
- `academic_scorer.py` · `absolute_claim_count` — What value, method, and status does academic_scorer.py report for absolute_claim_count on this paper?
- `academic_scorer.py` · `absolute_density_per1k` — What value, method, and status does academic_scorer.py report for absolute_density_per1k on this paper?
- `academic_scorer.py` · `academic_grade` — What value, method, and status does academic_scorer.py report for academic_grade on this paper?
- `academic_scorer.py` · `academic_rubric_grade` — What value, method, and status does academic_scorer.py report for academic_rubric_grade on this paper?
- `academic_scorer.py` · `academic_rubric_total` — What value, method, and status does academic_scorer.py report for academic_rubric_total on this paper?
- `academic_scorer.py` · `academic_signal_count` — What value, method, and status does academic_scorer.py report for academic_signal_count on this paper?
- `academic_scorer.py` · `academic_signal_density` — What value, method, and status does academic_scorer.py report for academic_signal_density on this paper?
- `academic_scorer.py` · `author_year_citation_count` — What value, method, and status does academic_scorer.py report for author_year_citation_count on this paper?
- `academic_scorer.py` · `citation_count` — What value, method, and status does academic_scorer.py report for citation_count on this paper?
- `academic_scorer.py` · `citation_density_per1k` — What value, method, and status does academic_scorer.py report for citation_density_per1k on this paper?
- `academic_scorer.py` · `claim_candidate_1` — What value, method, and status does academic_scorer.py report for claim_candidate_1 on this paper?
- `academic_scorer.py` · `claim_candidate_2` — What value, method, and status does academic_scorer.py report for claim_candidate_2 on this paper?
- `academic_scorer.py` · `claim_candidate_3` — What value, method, and status does academic_scorer.py report for claim_candidate_3 on this paper?
- `academic_scorer.py` · `claim_density_per1k` — What value, method, and status does academic_scorer.py report for claim_density_per1k on this paper?
- `academic_scorer.py` · `claim_marker_count` — What value, method, and status does academic_scorer.py report for claim_marker_count on this paper?
- `academic_scorer.py` · `counterargument_count` — What value, method, and status does academic_scorer.py report for counterargument_count on this paper?
- `academic_scorer.py` · `definition_marker_count` — What value, method, and status does academic_scorer.py report for definition_marker_count on this paper?
- `academic_scorer.py` · `doi_references` — What value, method, and status does academic_scorer.py report for doi_references on this paper?
- `academic_scorer.py` · `equation_count` — What value, method, and status does academic_scorer.py report for equation_count on this paper?
- `academic_scorer.py` · `equation_density_per1k` — What value, method, and status does academic_scorer.py report for equation_density_per1k on this paper?
- `academic_scorer.py` · `evidence_candidate_1` — What value, method, and status does academic_scorer.py report for evidence_candidate_1 on this paper?
- `academic_scorer.py` · `evidence_candidate_2` — What value, method, and status does academic_scorer.py report for evidence_candidate_2 on this paper?
- `academic_scorer.py` · `evidence_density_per1k` — What value, method, and status does academic_scorer.py report for evidence_density_per1k on this paper?
- `academic_scorer.py` · `evidence_marker_count` — What value, method, and status does academic_scorer.py report for evidence_marker_count on this paper?
- `academic_scorer.py` · `evidence_to_claim_ratio` — What value, method, and status does academic_scorer.py report for evidence_to_claim_ratio on this paper?
- `academic_scorer.py` · `external_theories` — What value, method, and status does academic_scorer.py report for external_theories on this paper?
- `academic_scorer.py` · `external_theory_count` — What value, method, and status does academic_scorer.py report for external_theory_count on this paper?
- `academic_scorer.py` · `falsifiability_density_per1k` — What value, method, and status does academic_scorer.py report for falsifiability_density_per1k on this paper?
- `academic_scorer.py` · `falsifiability_marker_count` — What value, method, and status does academic_scorer.py report for falsifiability_marker_count on this paper?
- `academic_scorer.py` · `footnote_count` — What value, method, and status does academic_scorer.py report for footnote_count on this paper?
- `academic_scorer.py` · `has_abstract` — What value, method, and status does academic_scorer.py report for has_abstract on this paper?
- `academic_scorer.py` · `has_conclusion` — What value, method, and status does academic_scorer.py report for has_conclusion on this paper?
- `academic_scorer.py` · `has_discussion` — What value, method, and status does academic_scorer.py report for has_discussion on this paper?
- `academic_scorer.py` · `has_introduction` — What value, method, and status does academic_scorer.py report for has_introduction on this paper?
- `academic_scorer.py` · `has_methodology` — What value, method, and status does academic_scorer.py report for has_methodology on this paper?
- `academic_scorer.py` · `has_references_section` — What value, method, and status does academic_scorer.py report for has_references_section on this paper?
- `academic_scorer.py` · `has_results` — What value, method, and status does academic_scorer.py report for has_results on this paper?
- `academic_scorer.py` · `heading_count` — What value, method, and status does academic_scorer.py report for heading_count on this paper?
- `academic_scorer.py` · `hedge_count` — What value, method, and status does academic_scorer.py report for hedge_count on this paper?
- `academic_scorer.py` · `hedge_density_per1k` — What value, method, and status does academic_scorer.py report for hedge_density_per1k on this paper?
- `academic_scorer.py` · `hedge_to_absolute_ratio` — What value, method, and status does academic_scorer.py report for hedge_to_absolute_ratio on this paper?
- `academic_scorer.py` · `limitation_count` — What value, method, and status does academic_scorer.py report for limitation_count on this paper?
- `academic_scorer.py` · `novelty_marker_count` — What value, method, and status does academic_scorer.py report for novelty_marker_count on this paper?
- `academic_scorer.py` · `numeric_citation_count` — What value, method, and status does academic_scorer.py report for numeric_citation_count on this paper?
- `academic_scorer.py` · `quantitative_marker_count` — What value, method, and status does academic_scorer.py report for quantitative_marker_count on this paper?
- `academic_scorer.py` · `reference_entry_count` — What value, method, and status does academic_scorer.py report for reference_entry_count on this paper?
- `academic_scorer.py` · `rubric_claim_points` — What value, method, and status does academic_scorer.py report for rubric_claim_points on this paper?
- `academic_scorer.py` · `rubric_falsifiability_points` — What value, method, and status does academic_scorer.py report for rubric_falsifiability_points on this paper?
- `academic_scorer.py` · `rubric_grounding_points` — What value, method, and status does academic_scorer.py report for rubric_grounding_points on this paper?
- `academic_scorer.py` · `rubric_quantitative_points` — What value, method, and status does academic_scorer.py report for rubric_quantitative_points on this paper?
- `academic_scorer.py` · `rubric_structure_points` — What value, method, and status does academic_scorer.py report for rubric_structure_points on this paper?
- `academic_scorer.py` · `structure_score` — What value, method, and status does academic_scorer.py report for structure_score on this paper?
- `academic_scorer.py` · `title_detected` — What value, method, and status does academic_scorer.py report for title_detected on this paper?
- `academic_scorer.py` · `url_references` — What value, method, and status does academic_scorer.py report for url_references on this paper?
- `theophysics_scorer.py` · `anti_fruits_composite` — What value, method, and status does theophysics_scorer.py report for anti_fruits_composite on this paper?
- `theophysics_scorer.py` · `anti_fruits_detail` — What value, method, and status does theophysics_scorer.py report for anti_fruits_detail on this paper?
- `theophysics_scorer.py` · `chi_score` — What value, method, and status does theophysics_scorer.py report for chi_score on this paper?
- `theophysics_scorer.py` · `chi_status` — What value, method, and status does theophysics_scorer.py report for chi_status on this paper?
- `theophysics_scorer.py` · `ckg_raw` — What value, method, and status does theophysics_scorer.py report for ckg_raw on this paper?
- `theophysics_scorer.py` · `ckg_tier` — What value, method, and status does theophysics_scorer.py report for ckg_tier on this paper?
- `theophysics_scorer.py` · `cross_domain_bridges` — What value, method, and status does theophysics_scorer.py report for cross_domain_bridges on this paper?
- `theophysics_scorer.py` · `dominant_anti_fruit` — What value, method, and status does theophysics_scorer.py report for dominant_anti_fruit on this paper?
- `theophysics_scorer.py` · `dominant_fruit` — What value, method, and status does theophysics_scorer.py report for dominant_fruit on this paper?
- `theophysics_scorer.py` · `fruits_composite` — What value, method, and status does theophysics_scorer.py report for fruits_composite on this paper?
- `theophysics_scorer.py` · `fruits_detail` — What value, method, and status does theophysics_scorer.py report for fruits_detail on this paper?
- `theophysics_scorer.py` · `fruits_net_score` — What value, method, and status does theophysics_scorer.py report for fruits_net_score on this paper?
- `theophysics_scorer.py` · `knowledge_score` — What value, method, and status does theophysics_scorer.py report for knowledge_score on this paper?
- `theophysics_scorer.py` · `me_avg_score` — What value, method, and status does theophysics_scorer.py report for me_avg_score on this paper?
- `theophysics_scorer.py` · `me_dominant_variable` — What value, method, and status does theophysics_scorer.py report for me_dominant_variable on this paper?
- `theophysics_scorer.py` · `scripture_refs` — What value, method, and status does theophysics_scorer.py report for scripture_refs on this paper?
- `theophysics_scorer.py` · `wisdom_score` — What value, method, and status does theophysics_scorer.py report for wisdom_score on this paper?
- `theophysics_scorer.py` · `wk_ratio` — What value, method, and status does theophysics_scorer.py report for wk_ratio on this paper?
- `theophysics_scorer.py` · `wk_status` — What value, method, and status does theophysics_scorer.py report for wk_status on this paper?
- `heartbeat_analyzer.py` · `chi` — What value, method, and status does heartbeat_analyzer.py report for chi on this paper?
- `heartbeat_analyzer.py` · `chi_composite` — What value, method, and status does heartbeat_analyzer.py report for chi_composite on this paper?
- `heartbeat_analyzer.py` · `chi_dominant` — What value, method, and status does heartbeat_analyzer.py report for chi_dominant on this paper?
- `heartbeat_analyzer.py` · `chi_keys` — What value, method, and status does heartbeat_analyzer.py report for chi_keys on this paper?
- `heartbeat_analyzer.py` · `chi_max` — What value, method, and status does heartbeat_analyzer.py report for chi_max on this paper?
- `heartbeat_analyzer.py` · `chi_mean` — What value, method, and status does heartbeat_analyzer.py report for chi_mean on this paper?
- `heartbeat_analyzer.py` · `chi_min` — What value, method, and status does heartbeat_analyzer.py report for chi_min on this paper?
- `heartbeat_analyzer.py` · `chi_std` — What value, method, and status does heartbeat_analyzer.py report for chi_std on this paper?
- `heartbeat_analyzer.py` · `combined` — What value, method, and status does heartbeat_analyzer.py report for combined on this paper?
- `heartbeat_analyzer.py` · `combined_mean` — What value, method, and status does heartbeat_analyzer.py report for combined_mean on this paper?
- `heartbeat_analyzer.py` · `combined_std` — What value, method, and status does heartbeat_analyzer.py report for combined_std on this paper?
- `heartbeat_analyzer.py` · `critique_words` — What value, method, and status does heartbeat_analyzer.py report for critique_words on this paper?
- `heartbeat_analyzer.py` · `defense_words` — What value, method, and status does heartbeat_analyzer.py report for defense_words on this paper?
- `heartbeat_analyzer.py` · `excluded_sections` — What value, method, and status does heartbeat_analyzer.py report for excluded_sections on this paper?
- `heartbeat_analyzer.py` · `fruit_composite` — What value, method, and status does heartbeat_analyzer.py report for fruit_composite on this paper?
- `heartbeat_analyzer.py` · `fruit_dominant` — What value, method, and status does heartbeat_analyzer.py report for fruit_dominant on this paper?
- `heartbeat_analyzer.py` · `fruit_keys` — What value, method, and status does heartbeat_analyzer.py report for fruit_keys on this paper?
- `heartbeat_analyzer.py` · `fruit_max` — What value, method, and status does heartbeat_analyzer.py report for fruit_max on this paper?
- `heartbeat_analyzer.py` · `fruit_mean` — What value, method, and status does heartbeat_analyzer.py report for fruit_mean on this paper?
- `heartbeat_analyzer.py` · `fruit_min` — What value, method, and status does heartbeat_analyzer.py report for fruit_min on this paper?
- `heartbeat_analyzer.py` · `fruit_std` — What value, method, and status does heartbeat_analyzer.py report for fruit_std on this paper?
- `heartbeat_analyzer.py` · `fruits` — What value, method, and status does heartbeat_analyzer.py report for fruits on this paper?
- `heartbeat_analyzer.py` · `grade` — What value, method, and status does heartbeat_analyzer.py report for grade on this paper?
- `heartbeat_analyzer.py` · `heartbeat` — What value, method, and status does heartbeat_analyzer.py report for heartbeat on this paper?
- `heartbeat_analyzer.py` · `heartbeat_error` — What value, method, and status does heartbeat_analyzer.py report for heartbeat_error on this paper?
- `heartbeat_analyzer.py` · `idx` — What value, method, and status does heartbeat_analyzer.py report for idx on this paper?
- `heartbeat_analyzer.py` · `index` — What value, method, and status does heartbeat_analyzer.py report for index on this paper?
- `heartbeat_analyzer.py` · `interpretation` — What value, method, and status does heartbeat_analyzer.py report for interpretation on this paper?
- `heartbeat_analyzer.py` · `negative_hits` — What value, method, and status does heartbeat_analyzer.py report for negative_hits on this paper?
- `heartbeat_analyzer.py` · `normalized_score` — What value, method, and status does heartbeat_analyzer.py report for normalized_score on this paper?
- `heartbeat_analyzer.py` · `peak_score` — What value, method, and status does heartbeat_analyzer.py report for peak_score on this paper?
- `heartbeat_analyzer.py` · `peak_sentence` — What value, method, and status does heartbeat_analyzer.py report for peak_sentence on this paper?
- `heartbeat_analyzer.py` · `peak_text` — What value, method, and status does heartbeat_analyzer.py report for peak_text on this paper?
- `heartbeat_analyzer.py` · `positive_hits` — What value, method, and status does heartbeat_analyzer.py report for positive_hits on this paper?
- `heartbeat_analyzer.py` · `score` — What value, method, and status does heartbeat_analyzer.py report for score on this paper?
- `heartbeat_analyzer.py` · `section` — What value, method, and status does heartbeat_analyzer.py report for section on this paper?
- `heartbeat_analyzer.py` · `section_boundaries` — What value, method, and status does heartbeat_analyzer.py report for section_boundaries on this paper?
- `heartbeat_analyzer.py` · `section_idx` — What value, method, and status does heartbeat_analyzer.py report for section_idx on this paper?
- `heartbeat_analyzer.py` · `sentence_count` — What value, method, and status does heartbeat_analyzer.py report for sentence_count on this paper?
- `heartbeat_analyzer.py` · `structural` — What value, method, and status does heartbeat_analyzer.py report for structural on this paper?
- `heartbeat_analyzer.py` · `structural_net` — What value, method, and status does heartbeat_analyzer.py report for structural_net on this paper?
- `heartbeat_analyzer.py` · `summary` — What value, method, and status does heartbeat_analyzer.py report for summary on this paper?
- `heartbeat_analyzer.py` · `theory_words` — What value, method, and status does heartbeat_analyzer.py report for theory_words on this paper?
- `heartbeat_analyzer.py` · `tier` — What value, method, and status does heartbeat_analyzer.py report for tier on this paper?
- `heartbeat_analyzer.py` · `total_score` — What value, method, and status does heartbeat_analyzer.py report for total_score on this paper?
- `heartbeat_analyzer.py` · `v2_structural` — What value, method, and status does heartbeat_analyzer.py report for v2_structural on this paper?
- `heartbeat_analyzer.py` · `valley_score` — What value, method, and status does heartbeat_analyzer.py report for valley_score on this paper?
- `heartbeat_analyzer.py` · `valley_sentence` — What value, method, and status does heartbeat_analyzer.py report for valley_sentence on this paper?
- `heartbeat_analyzer.py` · `valley_text` — What value, method, and status does heartbeat_analyzer.py report for valley_text on this paper?
- `heartbeat_analyzer.py` · `word_count` — What value, method, and status does heartbeat_analyzer.py report for word_count on this paper?
- `emotion_analyzer.py` · `anti_emo_composite` — What value, method, and status does emotion_analyzer.py report for anti_emo_composite on this paper?
- `emotion_analyzer.py` · `betrayal` — What value, method, and status does emotion_analyzer.py report for betrayal on this paper?
- `emotion_analyzer.py` · `conflict` — What value, method, and status does emotion_analyzer.py report for conflict on this paper?
- `emotion_analyzer.py` · `corruption` — What value, method, and status does emotion_analyzer.py report for corruption on this paper?
- `emotion_analyzer.py` · `cruelty` — What value, method, and status does emotion_analyzer.py report for cruelty on this paper?
- `emotion_analyzer.py` · `despair` — What value, method, and status does emotion_analyzer.py report for despair on this paper?
- `emotion_analyzer.py` · `emo_dominant` — What value, method, and status does emotion_analyzer.py report for emo_dominant on this paper?
- `emotion_analyzer.py` · `emo_sentence_count` — What value, method, and status does emotion_analyzer.py report for emo_sentence_count on this paper?
- `emotion_analyzer.py` · `emo_top_5` — What value, method, and status does emotion_analyzer.py report for emo_top_5 on this paper?
- `emotion_analyzer.py` · `faithfulness` — What value, method, and status does emotion_analyzer.py report for faithfulness on this paper?
- `emotion_analyzer.py` · `fruit_emo_composite` — What value, method, and status does emotion_analyzer.py report for fruit_emo_composite on this paper?
- `emotion_analyzer.py` · `fruit_emo_net` — What value, method, and status does emotion_analyzer.py report for fruit_emo_net on this paper?
- `emotion_analyzer.py` · `fruit_emo_strongest` — What value, method, and status does emotion_analyzer.py report for fruit_emo_strongest on this paper?
- `emotion_analyzer.py` · `fruit_emo_weakest` — What value, method, and status does emotion_analyzer.py report for fruit_emo_weakest on this paper?
- `emotion_analyzer.py` · `gentleness` — What value, method, and status does emotion_analyzer.py report for gentleness on this paper?
- `emotion_analyzer.py` · `goemotions_status` — What value, method, and status does emotion_analyzer.py report for goemotions_status on this paper?
- `emotion_analyzer.py` · `goodness` — What value, method, and status does emotion_analyzer.py report for goodness on this paper?
- `emotion_analyzer.py` · `harshness` — What value, method, and status does emotion_analyzer.py report for harshness on this paper?
- `emotion_analyzer.py` · `hatred` — What value, method, and status does emotion_analyzer.py report for hatred on this paper?
- `emotion_analyzer.py` · `impatience` — What value, method, and status does emotion_analyzer.py report for impatience on this paper?
- `emotion_analyzer.py` · `indulgence` — What value, method, and status does emotion_analyzer.py report for indulgence on this paper?
- `emotion_analyzer.py` · `joy` — What value, method, and status does emotion_analyzer.py report for joy on this paper?
- `emotion_analyzer.py` · `kindness` — What value, method, and status does emotion_analyzer.py report for kindness on this paper?
- `emotion_analyzer.py` · `love` — What value, method, and status does emotion_analyzer.py report for love on this paper?
- `emotion_analyzer.py` · `nrc_status` — What value, method, and status does emotion_analyzer.py report for nrc_status on this paper?
- `emotion_analyzer.py` · `nrc_top_emotions` — What value, method, and status does emotion_analyzer.py report for nrc_top_emotions on this paper?
- `emotion_analyzer.py` · `patience` — What value, method, and status does emotion_analyzer.py report for patience on this paper?
- `emotion_analyzer.py` · `peace` — What value, method, and status does emotion_analyzer.py report for peace on this paper?
- `emotion_analyzer.py` · `self_control` — What value, method, and status does emotion_analyzer.py report for self_control on this paper?
- `graph_builder.py` · `betweenness` — What value, method, and status does graph_builder.py report for betweenness on this paper?
- `graph_builder.py` · `centrality` — What value, method, and status does graph_builder.py report for centrality on this paper?
- `graph_builder.py` · `chi_score` — What value, method, and status does graph_builder.py report for chi_score on this paper?
- `graph_builder.py` · `cluster` — What value, method, and status does graph_builder.py report for cluster on this paper?
- `graph_builder.py` · `cluster_count` — What value, method, and status does graph_builder.py report for cluster_count on this paper?
- `graph_builder.py` · `combined_score` — What value, method, and status does graph_builder.py report for combined_score on this paper?
- `graph_builder.py` · `degree` — What value, method, and status does graph_builder.py report for degree on this paper?
- `graph_builder.py` · `dominant_variable` — What value, method, and status does graph_builder.py report for dominant_variable on this paper?
- `graph_builder.py` · `edge_count` — What value, method, and status does graph_builder.py report for edge_count on this paper?
- `graph_builder.py` · `edges` — What value, method, and status does graph_builder.py report for edges on this paper?
- `graph_builder.py` · `label` — What value, method, and status does graph_builder.py report for label on this paper?
- `graph_builder.py` · `most_central` — What value, method, and status does graph_builder.py report for most_central on this paper?
- `graph_builder.py` · `node_count` — What value, method, and status does graph_builder.py report for node_count on this paper?
- `graph_builder.py` · `node_data` — What value, method, and status does graph_builder.py report for node_data on this paper?
- `graph_builder.py` · `nodes` — What value, method, and status does graph_builder.py report for nodes on this paper?
- `graph_builder.py` · `stats` — What value, method, and status does graph_builder.py report for stats on this paper?
- `graph_builder.py` · `target` — What value, method, and status does graph_builder.py report for target on this paper?
- `graph_builder.py` · `topic_1` — What value, method, and status does graph_builder.py report for topic_1 on this paper?
- `graph_builder.py` · `truth_score` — What value, method, and status does graph_builder.py report for truth_score on this paper?
- `graph_builder.py` · `truth_tier` — What value, method, and status does graph_builder.py report for truth_tier on this paper?
- `graph_builder.py` · `weight` — What value, method, and status does graph_builder.py report for weight on this paper?
- `graph_builder.py` · `wk_ratio` — What value, method, and status does graph_builder.py report for wk_ratio on this paper?
- `graph_builder.py` · `word_count` — What value, method, and status does graph_builder.py report for word_count on this paper?
- `validation_scaffold.py` · `analogy` — What value, method, and status does validation_scaffold.py report for analogy on this paper?
- `validation_scaffold.py` · `contradicts` — What value, method, and status does validation_scaffold.py report for contradicts on this paper?
- `validation_scaffold.py` · `related` — What value, method, and status does validation_scaffold.py report for related on this paper?
- `validation_scaffold.py` · `supports` — What value, method, and status does validation_scaffold.py report for supports on this paper?
- `spine_analysis.py` · `content` — What value, method, and status does spine_analysis.py report for content on this paper?
- `spine_analysis.py` · `role` — What value, method, and status does spine_analysis.py report for role on this paper?
- `spine_analysis.py` · `section` — What value, method, and status does spine_analysis.py report for section on this paper?
- `spine_analysis.py` · `type` — What value, method, and status does spine_analysis.py report for type on this paper?
