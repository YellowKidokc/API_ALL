# Part B: Theophysics Paper Intelligence suite, code inventory (deep read 2026-09-26)

Source (David's NAS, not reachable from the cloud):
- `\\NAS\h_hp\Desktop\Folders\THEOPHYSICS_PAPER_INTELLIGENCE` (**A**, older)
- `...\THEOPHYSICS_PAPER_INTELLIGENCE (1)` (**B = current**)

**Bottom line**
- Every shared file is identical or newer in B.
- A has only a folder of planning docs (`08_SITE_TOPBAR_MANIFEST_BRIDGE`) plus one broken .bat file.
- No hard-coded API keys were found in any code file; keys are read from environment variables.

## What B adds over A
- `run_pipeline.py` (Aug 19): layers L8-L10, L12, L13 and L14, HTML scorecards, analytics packs, and the flags `--deepseek/--heartbeat/--goemotions/--nlp/--all-md`.
- `theophysics_scorer.py` (Aug 13): CHI × a discipline factor, plus `chi_keyword_score, canon_discipline_factor, unsupported_numeric_claims, proof_pressure_terms, falsifiability_markers`. The CKG score is capped when a paper has no citations.
- 7Q switched from OpenAI gpt-4o-mini to DeepSeek.
- `truth_runner.py` (Aug 16): a per-claim ledger `claim_records` with nearby evidence candidates.
- New folders 08-14:
  - `metric_registry.json` (**356 fields**: 334 verified in output, 16 in code only, 6 runtime).
  - `METRIC_REGISTRY.md`, `METRIC_CROSSWALK.xlsx`.
  - `ANALYTICS_QUESTIONS.md`: a proposed L15 "Atom analytics", not built.

## Orchestrator (`00_ORCHESTRATOR/run_pipeline.py`)
Flags: `--paper --series --output --deepseek(--openai alias) --heartbeat --goemotions --nlp --all-md`. Schema `2026.04.07-B`.

**Per paper:** identity fields (`paper_id` = `P-`+12 hex of sha1(path), `file, series_id, run_id, schema_version, source_path, analyzed_at, _layer_status`), then:
- L1 text
- L2 academic
- L3 theophysics
- L4 7Q (DeepSeek, opt-in)
- L5 NLP (opt-in)
- L6 truth engine
- L8 emotion (NRC; GoEmotions opt-in)
- L9 linguistic depth
- L10 idea density

Each layer is wrapped in try/except, and errors are recorded in `_layer_status`.

**Per series:** after all the papers:
- L7 graph
- L12 series analytics
- Excel output (SUMMARY + FULL_DATA)
- results JSON
- L11 HTML scorecards and analytics packs
- L13 analyst report (DeepSeek, opt-in)
- L14 heartbeat (opt-in)
- run_summary

**Defaults:** L1, L2, L3, L6, L8(NRC), L9 and L10 run by default; series runs add L7, L12 and L11. Opt-in only: L4, L5, GoEmotions, L13, L14.

## Modules (fields per module are listed in the flat list at the end)

| Layer | Module | Local / API | Notes and bugs |
|---|---|---|---|
| L1 | 01_TEXT_ANALYTICS `text_analyzer.py` | local: textstat, YAKE, KeyBERT (all-MiniLM-L6-v2) | `paper_analyzer.py` (8 sub-levels: grammar, drift, density, dependency depth, argument, flow, links) is **not wired in** |
| L2 | 02_ACADEMIC_STANDARD `academic_scorer.py` | regex; optional Semantic Scholar (no key; never enabled) | `has_discussion` is computed but not output |
| L3 | 03_THEOPHYSICS_METRICS `theophysics_scorer.py` | keyword counts | CHI, W/K ratio, 12 fruits, 10 ME variables (`me_G…me_C`), CKG tier |
| L4 | 04_OPENAI_7Q `seven_q_runner.py`, `promotion_pass`, `template_filler`, `paper_i_filler` | **DeepSeek** (`DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, default deepseek-chat), temp 0.3, JSON mode | **the paper is cut to its first 6,000 characters**, which breaks the whole-document rule; template paths point to `O:\_Theophysics_v4` |
| L5 | 05_NLP_DEEP `nlp_analyzer.py` | spaCy, sumy TextRank, gensim LDA | **bug:** `build_corpus_model()` is never called, so topics are always empty |
| L6 | 06_TRUTH_ENGINE `truth_runner.py`, `truth_coherence_scanner.py` | lexicons + spaCy NER | truth/coherence scores, 9 fruit + 9 anti-fruit, 8 character attributes × 6, 30 integrity profiles, claim ledger. **ISSUE-002:** anti-fruit lists have only 4 terms each |
| L7 | 07_KNOWLEDGE_GRAPHS `build_graph` | networkx, Louvain, pyvis | **stale:** edges depend on L6/L5 fields that no longer exist |
| L8 | 08_EMOTION_PROFILE `emotion_analyzer.py` | nrclex; GoEmotions `monologg/bert-base-cased-goemotions-original` | emotion → fruit/anti-fruit mapping; fruit fields are 0 unless GoEmotions is on |
| L9 | 09_LINGUISTIC_DEPTH `linguistic_analyzer.py` | spaCy, textdescriptives, lexicalrichness | MTLD, MATTR, HD-D, coherence, POS, LIX/RIX; the "quality" component is skipped (config bug) |
| L10 | 10_IDEA_DENSITY `idea_density_analyzer.py` | `ideadensity` (CPIDR) | **bug:** whitespace is collapsed before the paragraph split, so the paper is always 1 paragraph and std is 0 |
| L11 | 11_HTML_REPORT `generate_report.py`, `paper_pack.py` | Chart.js, openpyxl | per-paper HTML scorecard + a 12-page analytics pack (HTML + xlsx) |
| L12 | 04_ANALYTICS `pipeline_layer.py` | networkx, keyword lists | series concepts, domains, breakthroughs, atoms/molecules/hubs, Jaccard coherence matrix |
| L13 | 13_ANALYST_REPORT | **DeepSeek**, temp 0.25, 5k tokens | series editorial / historical / theological report; asks for a field that doesn't exist |
| L14 | 12_HEARTBEAT `heartbeat_analyzer.py` | MiniLM anchors (local) | sentence-by-sentence fruit + χ + structural "EKG" with peak and valley. Side tools not wired in: `word_level_mapper` (channels A-N), `openai_8_prompts` (o3), `openai_paper_intel` (o3), `openai_sentence_scorer` (gpt-4o-mini) |
| - | 14_LOCAL_API `server.py` | stdlib HTTP, loopback only, port 8765 | endpoints below; paid providers require `confirm_paid_provider:true` |

**14_LOCAL_API endpoints:**
- `GET /health`, `/metrics[?category=]`, `/jobs`, `/jobs/{id}`, `/jobs/{id}/results|log|artifacts|download/{rel}`
- `POST /runs/paper`, `/runs/project`, `/compare`, `/jobs/{id}/canonization-candidates` (labelled "CANDIDATE_DRAFT, NOT ADMITTED")

## The 7Q prompts (L4), verbatim structure

**System prompt:** "rigorous academic analyst… 7-Question Scientific Method… Your goal is NOT to validate claims, it is to STRENGTHEN the paper… Name real theories, real authors, real journals."

**FORWARD**
- Q0 POSTURE
- Q1 DOMAIN
- Q2 CLAIM
- Q3 EVIDENCE (what's missing)
- Q4 ASSUMPTIONS (load-bearing)
- Q5 FALSIFICATION
- Q6 INTEGRATION
- Q7 STRENGTH GAPS (real papers, authors, journals)
- then `summary` and `top_3_strengthening_actions`

**REVERSE**
- R1 state the claim
- R2 list the assumptions
- R3 challenge each one
- R4 the weakest link
- R5 the strongest counter-theory
- R6 does it survive?
- R7 what would settle it
- then `verdict` and `confidence_score`

**PROMOTION**
- P1 posture frameworks
- P2 A/B/C confidence gradient
- P3 structural vs analogical isomorphism
- P4 support literature
- P5 equivalent forms (physics / info / systems / math)
- P6 forward predictions
- P7 integration map
- then `infobox_fields`

**Template filler:** `t_score` 0-100, tier NEAR-CANONICAL ≥90 / STRONG ≥75 / PROVISIONAL ≥60 / WEAK, `deaths` (death tests survived out of 4), controversy score.

## Portability problems
- Paths are hard-coded to `O:\999_IGNORE\...Python_Backend` (KeyBERT cache), `O:\_Theophysics_v4`, `T:\...` and `C:\Users\lowes\...`.
- `fruits_scorer_v2` is imported from `\\192.168.1.177\Desktop` (another subnet, so it probably fails).
- `pyproject.toml` entry points point to a package that doesn't exist.
- The runner exits 0 even when layers fail.

## Every output field, by module
**Identity:** _layer_status, analyzed_at, file, paper_id, run_id, schema_version, series_id, source_path. Run summary: analyst_report, analytics_04, deepseek_enabled, excel, heartbeat, html_reports, layer_health, output_dir, paper_count, papers, series_name, series_path.

**L1:** automated_readability, avg_paragraph_words, coleman_liau, dale_chall, flesch_kincaid_grade, flesch_reading_ease, gunning_fog, header_count, keybert_keywords, lexicon_count, paragraph_count, reading_time_min, sentence_count, smog_index, syllable_count, text_standard, top_bigrams, top_trigrams, unique_word_count, vocab_richness, word_count, yake_keywords.

**L1 paper_analyzer (not wired in):**
- `a_`: argument_grade, claim_count, claim_density_per1k, evidence_count, evidence_density_per1k, evidence_to_claim_ratio, falsifiability_markers
- `d_`: compression_ratio, density_label, signal_noise_ratio, stopword_ratio, trigram_redundancy
- `f_`: flow_label, transition_count, transition_density_pct
- `g_`: adj_pct, adv_pct, assertive_verb_count, fluff_flag, modal_verb_count, modal_vs_assertive_ratio, noun_pct, passive_pct, passive_voice_count, prep_pct, verb_pct, weight_signal
- `lk_`: avg_degree, centralization, clustering_coeff, concept_edges, concept_nodes, cross_domain_bridges, external_links, internal_external_ratio, internal_links, isolated_nodes, link_citation, link_concept, link_density_per1k, link_dependency, link_evidence, link_navigation, link_quality_score, most_central_paragraph, overlink_flag, total_links, underlink_flag
- `r_`: avg_dependency_depth, cognitive_load, flesch_kincaid_grade, gunning_fog, max_dependency_depth, reading_time_min, smog_index, text_standard
- `s_`: avg_sentences_per_paragraph, avg_words_per_sentence, header_count, paragraph_count, sentence_count, ttr, unique_word_count, word_count
- `sm_`: coherence_flag, topic_drift_avg, topic_drift_max, topic_drift_scores

**L2:**
- academic_grade, academic_signal_count, academic_signal_density
- citation_count, citation_density_per1k, doi_references, external_theories, external_theory_count, footnote_count
- has_abstract, has_conclusion, has_introduction, has_methodology, has_references_section, has_results
- ss_citation_count, ss_error, ss_found, ss_influential_citations, ss_reference_count, ss_title, ss_venue, ss_year
- structure_score, title_detected, url_references

**L3:**
- canon_discipline_factor, chi_keyword_score, chi_score, chi_status, ckg_raw, ckg_tier
- cross_domain_bridges, dominant_fruit, falsifiability_markers, fruits_composite, fruits_detail, knowledge_score
- me_avg_score, me_dominant_variable
- me_C_christ_coherence, me_E_entropy_engagement, me_F_faith_coupling, me_G_gravity_belonging, me_K_knowledge_logos, me_M_mass_meaning, me_Q_quantum_observer, me_R_relationship, me_S_spacetime_structure, me_T_time_eternity
- proof_pressure_terms, scripture_refs, unsupported_numeric_claims, wisdom_score, wk_ratio, wk_status

**L4:**
- 7q_confidence, 7q_file, 7q_verdict
- Forward: q0-q7, summary, top_3_strengthening_actions
- Reverse: r1-r7, verdict, confidence_score
- Promotion: p1_posture_frameworks … p7_integration_map, plus infobox_fields (analogical_count, bundled_claims, confidence_label, decisive_test_short, domain_count, effective_n, iso_hint, iso_status, paper_type, strongest_q, structural_count, weakest_q)
- Template: bridge_count, controversy_score, deaths, t_score, tier

**L5:** entity_concepts, entity_count, entity_orgs, entity_people, entity_types_found, key_sentence_1..3, topic_1..3, topic_count.

**L6:**
- Scores: absolute_pressure, anti_fruit_pressure, balance_score, coherence_score, combined_score, discipline_score, evidence_density, falsifiability_density, fruit_integrity_score, hedge_density, protection_score, rhetorical_force, threat_score, truth_score, warmth_score
- Claim counts: anchored_claims, claim_count, contradiction_flags, contradictory_claims, falsifiable_claims, overstated_claims, speculative_claims, under_supported_claims
- Structure counts: paragraph_count, section_count, sentence_count
- Fruits: anti_{9 fruits}, fruit_{9 fruits}
- Attributes: attr_{authority_usurpation, charismatic_manipulation, deception_mastery, global_solution_complex, humility_index, moral_courage, spiritual_coherence, spiritual_discernment}_{counter_pressure, kind, neg_hits, net_score, pos_hits, strength}
- Profile: character_posture, integrity_profiles, primary_protections, primary_threats, top_risky_1/2, top_supported_1/2
- claim_records[]:
  - identity: source, claim_index, sentence_index, claim_text, claim_kind
  - presence flags: support_status, evidence_present, falsifiability_present, dependency_present, hedge_present, absolute_overreach, local_contradiction, precision_present
  - verdict: claim_status, claim_score, evidence_basis, evidence_candidates, review_note, sentence_truth_status
- Per-sentence (standalone scanner): claim_strength, evidence_anchor, falsifiability_signal, dependency_signal, precision_signal, hedge_pressure, absolute_pressure, contradiction_pressure, truth_score, truth_status

**L7:** betweenness, centrality, centrality_within_series, cluster, cluster_count, degree, edge_count, most_central, node_count.

**L8:**
- NRC: anger, anticipation, disgust, fear, joy, negative, positive, sadness, surprise, trust, top_emotions, error
- GoEmotions: emo_{28 labels}, emo_dominant, emo_sentence_count, emo_top_5
- Fruit mapping: fruit_emo_{9 fruits} (each with _pos and _neg), fruit_emo_composite, fruit_emo_net, fruit_emo_strongest, fruit_emo_weakest
- Anti-fruit mapping: anti_emo_{betrayal, conflict, corruption, cruelty, despair, harshness, hatred, impatience, indulgence}, anti_emo_composite
- Status: goemotions_status, goemotions_error

**L9:**
- lr_: cttr, error, hdd, mattr, mtld, rttr, terms, ttr, words
- td_ readability: automated_readability_index, lix, rix
- td_ coherence and dependency: first_order_coherence, second_order_coherence, dependency_distance_mean/std, prop_adjacent_dependency_relation_mean/std
- td_ size: n_sentences, n_tokens, sentence_length_mean/median/std, syllables_per_token_mean/median/std, token_length_mean/median/std
- td_ POS: pos_prop_{ADJ, ADP, ADV, AUX, CCONJ, DET, INTJ, NOUN, NUM, PART, PRON, PROPN, PUNCT, SCONJ, SYM, VERB, X}
- textdescriptives_error

**L10:** idea_density_error, idea_density_level, idea_density_max, idea_density_mean, idea_density_min, idea_density_std, idea_paragraphs_analyzed, idea_total_propositions.

**L12 (series):**
- Totals: article_count, avg_concepts_per_article, total_breakthroughs, total_words, unique_concepts, top_concepts
- Per article: path, word_count, concepts, concept_count, domains, domain_count, sections, section_count, breakthroughs, breakthrough_details (trigger, position, domains, concepts, integration_order)
- Graph: coherence_matrix, graph_stats (nodes, edges, density), generated_notes (atoms, molecules, hubs)
- Run: generated, output_dir, series_folder

**L13 (series):**
- Content: executive_summary, dominant_theme, story_arc, factual_check, historical_context_check, theological_boundary_notes, strongest_papers, weakest_links, missing_bridge_sections, top_editorial_actions, report_body_markdown
- Run: series_name, series_path, run_id, model, generated_at, error

**L14 heartbeat:**
- Row: heartbeat_combined_mean, heartbeat_peak_score, heartbeat_valley_score, heartbeat_html
- Summary: fruit_mean/std/min/max, chi_mean/std/min/max, combined_mean/std, peak_sentence/text/score, valley_sentence/text/score
- Per sentence: idx, text, section, section_idx, fruits{9}, fruit_composite, fruit_dominant, chi{G,M,E,S,T,K,R,Q,F,C}, chi_composite, chi_dominant, combined, combined_smooth, and structural{definition, derivation, scope_bound, prediction, evidence, equation, edge_case, modularity, steelman, overclaim, cross_domain, pos, neg, net}
- v2_structural: grade, normalized_score, fruits, zones

**Referenced but never produced (always blank):** L1_avg_sentence_length, L1_reading_level, L2_academic_signal_score, L5_key_sentence.
