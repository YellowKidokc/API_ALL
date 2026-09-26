# X:\04_STATIONS research report (read-only)

Nothing on the NAS was modified. I copied the code files to my scratchpad to grep them, and I ran only listings, reads and md5 checks.

**Sources.** I read paper-intelligence-suite (§1) myself. Before your "no sub-agents" message arrived, I had already started four sub-agents:
- **Three finished and handed back.** I merged their findings for paper-proof-grader plus the July comparison, A_AI-RESEARCH-AGENTS/A_BIL/OBS/A_GUI, and _DORMANT. I spot-checked their key claims with md5 comparisons.
- **The fourth, a second pass on paper-intelligence-suite, was still running when I finished.** It duplicates §1, so its result can be ignored.

---

## 1. paper-intelligence-suite.station (ST_038)

**Purpose:** a multi-layer paper scorer. Layers are named PA and L1–L13; most are local NLP, and L4, L13 and L12's extra scripts call OpenAI. It turns .md/.txt/.html papers into a wide per-paper row, an Excel workbook, a JSON snapshot and an HTML scorecard.

**Status**
- Newest code: every sub-module `pipeline.py` and the root `fruit_dynamics.py` are dated 2026-06-18. Everything else is dated 2026-06-16, which is a bulk copy date.
- The last station artifacts are `_outbox/ART_20260618_*__ST_038__mda-long-decline.json`.
- The analyzers are production code, and the station wrapper is a template.

### Two ways the suite runs

**A) Station wrapper (root `pipeline.py`)**
- It uses the SSS_v1 template, "STATION_SCRIPT_STANDARD v1", POF 2828, 2026-06-14.
- The only step specific to this station (section 07_PROCESS) is `compute_fruit_dynamics(text)` plus `vectorization`, as described in `wiring_spec.json`.
- It reads `_inbox`, writes `_outbox/ART_{ts}__ST_038__{stem}.json` and moves inputs to `_processed`.
- `config.json` sets station_id ST_038, worker `M12_paper_review`, final_export true, and templates `15_TEMPLATES/paper_intelligence.xlsx` and `PI_MDA-001-story-introduction.html`.
- The `nlp_id` routing supports NONE, OPENAI, OLLAMA, or a folder under `05_MODELS`.
- There is no argparse.

**B) Full orchestrator `00_ORCHESTRATOR/run_pipeline.py`**
- It carries `SCHEMA_VERSION = "2026.04.07-B"` and is the real scorer.
- It adds a hard-coded backend path `O:\999_IGNORE\Obsidian Programs\Python_Backend` to sys.path.
- Each sub-folder 01–14 also has its own SSS_v1 `pipeline.py`. These are identical except for station name, id `PI_01`…`PI_14`, and the entrypoint named in its `config.json`. They all run with worker NONE, i.e. local.

### Launchers and CLI

**`run_pipeline.py`**
- Flags: `--paper`, `--series`, `--output`, `--openai` (the help text says "~$0.02/paper").
- **Bug:** `RUN_LOCAL_PAPER_INTELLIGENCE.bat` passes `--pattern "*.md"`, which `run_pipeline.py` does not accept, so argparse will exit. `RUN.bat` calls that bat, so `RUN.bat` fails too.
- `RUN_LOCAL_PAPER_INTELLIGENCE.bat` runs `.venv` python against `X:\WORKFLOWS\MDA-PUBLICATION\01_LOSSLESS\articles` and writes to `...EXPORTS\paper_intelligence`.

**`LAUNCH.bat` menu**
1. Single paper
2. Series
3. GTQ preset, on `O:\_Theophysics_v4\...GENESIS TO QUANTUM...`
4. `06_TRUTH_ENGINE\truth_runner.py --folder` (truth_runner has no argparse, so this is likely a no-op)
5. `07_KNOWLEDGE_GRAPHS\graph_builder.py --folder`
6. `04_OPENAI_7Q\seven_q_runner.py --folder`

**Other launchers**
- `INSTALL.bat` pip-installs textstat, keybert, yake, sumy, semanticscholar, python-louvain, nltk, openai, openpyxl, pandas, scipy, scikit-learn, pyvis, sentence-transformers, spacy + `en_core_web_sm`, and gensim. It also downloads the NLTK data punkt, stopwords and averaged_perceptron_tagger.
- `RUN_7Q_GTQ.bat` reads the User env var `OPENAI_API_KEY` and runs `C:\Users\lowes\AppData\Local\Temp\run_7q.py`. That is a temp file, so the launcher is stale.
- `SET_OPENAI_KEY.ps1` prompts for a key and saves it as the User env var `OPENAI_API_KEY`. No key is stored in the script.
- `RUN_NOW_NO_PAUSE.bat` is mislabeled "Paper Proof Grader" and runs root `pipeline.py`.
- `THEOPHYSICS_7Q_HOTKEYS.ahk` is dated 2026-04-12.

**Other orchestrator scripts**
- `run_drop_zone.py`: `--zone`, `--mode paper|brain|both`, `--openai`. Launched by `20_DROP_PAPER_ONLY\RUN_PAPER_ONLY.bat`, `21_DROP_BRAIN_ONLY\RUN_BRAIN_ONLY.bat` and `22_DROP_BOTH_ALIGNMENT\RUN_BOTH_ALIGNMENT.bat`. Each zone has an `INBOX`, a `FETCH_SOURCE.txt` and `RUNS/*/run_manifest.json`; the last runs were 2026-05-04.
- `run_brain_alignment.py`: `--folder`, `--output`, `--openai`. It writes `alignment_summary.json` and `alignment_join.csv` with `paper_word_count`, `paper_text_standard`, `paper_fk_grade`, `paper_chi_score`, `paper_ckg_tier`, `paper_claim_markers`, `paper_claims_truth_engine`, `paper_truth_score` and `paper_combined_score`.
- `run_baseline.py`: no CLI. Compares 5 corpora (Convergence TX 6.6, evolution, consciousness, worldviews, inaugurals).
- `run_convergence_batch.py`: no CLI. Hard-coded `O:\..\THE CONVERGENCE TX 6.6` input and `T:\THEOPHYSICS_PAPER_INTELLIGENCE\OUTPUT` output. Writes vault markdown.
- `deep_workbook.py <results.json> [out.xlsx]`: builds about 20 tabs keyed by prefix (L1_Readability, L2_Academic, L3_CHI_WK_Cross, L3_Fruits, L3_MasterEquation, L4_OpenAI_7Q, L5_NLP_Deep, L6_Truth_Coherence, L7_Knowledge_Graph, L8_NRC_Emotion, L8_GoEmotions, L8_Fruits_Emotion, L8_AntiFruits_Emotion, L9_TextDescriptives, L9_Lexical_Richness, L10_Idea_Density, L13_PeerReview), plus Overview, Layer_Health and ALL_METRICS.

**Orchestrator outputs**
- Files: `*_PAPER_INTELLIGENCE_*.xlsx`, `*_pipeline_results_*.json`, `*_run_summary_*.json`, `snapshots/<paper_id>_snapshot.json`, and `knowledge_graph_*.json/html/graphml`.
- Identity columns: `paper_id` (a hash), `file`, `series_id`, `run_id`, `schema_version`, `source_path`, `analyzed_at`, `snapshot_path`, and `_layer_status{PA..L13: ok/error/skipped/partial}`.
- Workbook column order: PA, L1–L10, L13.

### Layer by layer (key prefix → fields)

**PA: `01_TEXT_ANALYTICS/paper_analyzer.py`** (local: spaCy `en_core_web_sm`, sentence-transformers `all-MiniLM-L6-v2`, textstat, networkx)
- **Structure (`PA_s_`):** word_count, unique_word_count, ttr, sentence_count, paragraph_count, header_count, avg_words_per_sentence, avg_sentences_per_paragraph
- **Grammar (`PA_g_`, spaCy):** noun_pct, verb_pct, adj_pct, adv_pct, prep_pct, passive_voice_count, passive_pct, modal_verb_count, assertive_verb_count, modal_vs_assertive_ratio, weight_signal (CONCEPTUAL if noun>20%, VERBAL if verb>15%, else MIXED), fluff_flag (adj+adv>15%)
- **Semantic (`PA_sm_`, MiniLM):** topic_drift_avg, topic_drift_max, topic_drift_scores, coherence_flag (COHERENT/MODERATE/SCATTERED), semantic_error
- **Density (`PA_d_`):** compression_ratio, density_label, stopword_ratio, trigram_redundancy, signal_noise_ratio
- **Readability (`PA_r_`):** flesch_kincaid_grade, gunning_fog, smog_index, text_standard, reading_time_min, avg_dependency_depth, max_dependency_depth, cognitive_load (HIGH if avg depth >4), readability_note
- **Argument (`PA_a_`):** claim_count, claim_density_per1k, evidence_count, evidence_density_per1k, evidence_to_claim_ratio, falsifiability_markers, argument_grade (ratio ≥2 A, ≥1 B, ≥0.5 C, else D)
- **Flow (`PA_f_`):** transition_density_pct, transition_count, flow_label
- **Links (`PA_lk_`):** total_links, link_density_per1k, link_citation, link_concept, link_dependency, link_evidence, link_navigation, internal_links, external_links, internal_external_ratio, cross_domain_bridges, link_quality_score, underlink_flag, overlink_flag, concept_nodes, concept_edges, avg_degree, clustering_coeff, most_central_paragraph, centralization, isolated_nodes, graph_error

**L1: `text_analyzer.py`** (local: textstat, KeyBERT on MiniLM, YAKE with n=2 and top_n)
- word_count, unique_word_count, vocab_richness, paragraph_count, header_count, avg_paragraph_words
- flesch_reading_ease, flesch_kincaid_grade, gunning_fog, smog_index, automated_readability, coleman_liau, dale_chall, text_standard
- reading_time_min, syllable_count, lexicon_count, sentence_count
- keybert_keywords, yake_keywords, top_bigrams, top_trigrams
- Known issue: HTML input is not stripped, so CSS tokens leak into the n-grams (documented in VARIABLE_INVENTORY).

**L2: `02_ACADEMIC_STANDARD/academic_scorer.py`** (v1 is the one wired in; regex, plus the optional Semantic Scholar API via the `semanticscholar` package, with no key)
- **Title:** title_detected
- **Citations:** citation_count, author_year_citation_count, numeric_citation_count, citation_density_per1k
- **Theory:** external_theory_count, external_theories, academic_signal_count, academic_signal_density
- **Structure:** structure_score (x/7), heading_count, reference_entry_count, has_abstract, has_introduction, has_methodology, has_results, has_discussion, has_conclusion, has_references(_section), footnote_count, url_references, doi_references
- **Claims:** claim_marker_count, claim_density_per1k, evidence_marker_count, evidence_density_per1k, evidence_to_claim_ratio, falsifiability_marker_count, falsifiability_density_per1k
- **Hedging:** hedge_count, hedge_density_per1k, absolute_claim_count, absolute_density_per1k, hedge_to_absolute_ratio
- **Other markers:** counterargument_count, limitation_count, novelty_marker_count, definition_marker_count, quantitative_marker_count, equation_count, equation_density_per1k
- **Candidates:** claim_candidate_1..3, evidence_candidate_1..2
- **Rubric (each /5, total /25):** rubric_structure_points, rubric_grounding_points, rubric_claim_points, rubric_quantitative_points, rubric_falsifiability_points, academic_rubric_total, academic_rubric_grade (e.g. "A (Rigorous)")
- **academic_grade:** total ≥40 A (Publication Grade), ≥25 B, ≥15 C, ≥5 D, else F
- **Semantic Scholar:** ss_found, ss_title, ss_year, ss_venue, ss_citation_count, ss_influential_citations, ss_reference_count
- **`academic_scorer_v2.py`** (not wired in) adds: word_count, sentence_count, body_doi_citation_count, body_url_citation_count, bracket_year_citation_count, citation_style_count, has_limitations, has_literature_review, has_research_question, recent_reference_count, older_reference_count, reference_year_count, strong_claim_count, strong_claim_density_per1k, unsupported_strong_claim_count, unsupported_strong_claim_1..3, evidence_candidate_3, falsifiability_candidate_1..3, recommendation_1..3 / recommendations.

**L3: `03_THEOPHYSICS_METRICS/theophysics_scorer.py`** (local term counts, norm = 1000/words)
- chi_score = min(10, Σ(count × weight × norm)/10); chi_status HIGH ≥8, STRONG ≥6, MODERATE ≥4, WEAK
- wisdom_score, knowledge_score; wk_ratio = wisdom count / knowledge count; wk_status WISDOM-LED ≥1.5, BALANCED ≥1, else KNOWLEDGE-DOMINANT
- fruits_composite (12 fruits: love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, self_control, grace, hope, humility), anti_fruits_composite (9), fruits_net_score = max(0, fruits − 0.65 × anti), dominant_fruit, dominant_anti_fruit, fruits_detail, anti_fruits_detail
- me_avg_score, me_dominant_variable, and `me_{G_gravity_belonging, M_mass_meaning, E_entropy_engagement, S_spacetime_structure, T_time_eternity, K_knowledge_logos, R_relationship, Q_quantum_observer, F_faith_coupling, C_christ_coherence}` (each min(10, count × norm / 3))
- cross_domain_bridges, scripture_refs
- ckg_raw = min(100, 5·axioms + 3·citations + 2·evidence + 4·bridges + 5·chi); ckg_tier A ≥80, B ≥60, C ≥40, D ≥20, else F

**L4: `04_OPENAI_7Q/seven_q_runner.py`** (only with `--openai`)
- CLI: `--paper`, `--folder`, `--vault-output`
- Row fields: `L4_7q_verdict`, `L4_7q_confidence`, `L4_7q_file`
- Paper text is truncated to 6000 characters.
- JSON keys: forward `q0..q7`, `summary`, `top_3_strengthening_actions`; reverse `r1..r7`, `verdict`, `confidence_score`.

**L5: `05_NLP_DEEP/nlp_analyzer.py`** (local: spaCy `en_core_web_sm` NER, gensim LDA corpus model with 5 topics, sumy TextRank)
- entity_count, entity_people, entity_orgs, entity_concepts (NORP + LAW), entity_types_found
- key_sentence_1..3, topic_1..3, topic_count

**L6: `06_TRUTH_ENGINE/truth_runner.py` → `truth_coherence_scanner.py`** (local lexicons; spaCy `en_core_web_sm` for NER)
- **Scanner CLI:** `target`, `--url` (repeatable, fetches web pages), `--output-dir`.
- **Per sentence:** truth = clamp(0.28 claim + 0.26 evidence + 0.18 falsifiability + 0.14 dependency + 0.14 precision − (0.45 hedge + 0.30 absolute + 0.25 contradiction) + 0.35). Status: supported ≥0.7, mixed ≥0.5, speculative, unsupported.
- **Per section:** coherence = 0.45 lexical_cohesion + 0.30 heading_alignment + 0.15 bridge + 0.10 (1 − jump).
- **Document fields:**
  - truth_score, coherence_score, combined_score (= 0.58 truth + 0.42 coherence)
  - evidence_density, falsifiability_density, hedge_density, absolute_pressure, rhetorical_force
  - warmth_score (mean of love, peace, kindness, gentleness), discipline_score (mean of faithfulness, self_control, patience), balance_score
  - fruit_integrity_score = clamp(mean fruit − 0.65 × mean anti + 0.25); anti_fruit_pressure
  - character_posture (labels such as "falsifiable and mature", "polished but manipulative", "coherent but cold", "confident but spiritually rotten"), integrity_profiles
  - threat_score, protection_score, primary_threats, primary_protections
  - claim_count, anchored_claims, under_supported_claims, overstated_claims, falsifiable_claims, speculative_claims, contradictory_claims, contradiction_flags
  - sentence_count, paragraph_count, section_count
  - top_supported_1..2, top_risky_1..2
- **Per fruit:** `fruit_{9}`, `anti_{9}`, `anti_fruit_{9}`.
- **Per character attribute:** `attr_{name}_{kind, pos_hits, neg_hits, strength, counter_pressure, net_score}` for 8 attributes: spiritual_coherence, humility_index, spiritual_discernment, moral_courage, deception_mastery, charismatic_manipulation, authority_usurpation, global_solution_complex. That is 48 columns.

**L7: `07_KNOWLEDGE_GRAPHS/graph_builder.py`** (series only; networkx + python-louvain)
- Edge weight: +3 same domain, +1 if |Δchi| <1.5, +2 same CKG tier, + keyword overlap.
- Node fields: centrality (degree), betweenness, cluster (Louvain), label, chi_score, combined_score, truth_score, truth_tier, wk_ratio, dominant_variable, word_count, topic_1.
- Stats: node_count, edges, cluster_count, most_central.
- Row fields: `L7_centrality_within_series`, `L7_cluster`.
- `graph_generators.py` (`input_json`, `--out`) emits tag_graph, axiom_dependency, master_equation and paper_to_paper graphs with `{nodes, edges, summary{paper_count, edge_count}}` plus HTML.

**L8: `08_EMOTION_PROFILE/emotion_analyzer.py`** (local: NRCLex; HF `monologg/bert-base-cased-goemotions-original`)
- nrc_status, `nrc_{fear, anger, anticipation, trust, surprise, positive, negative, sadness, disgust, joy}`, nrc_top_emotions
- goemotions_status, `emo_{27 GoEmotions labels}`, emo_dominant, emo_top_5, emo_sentence_count
- `fruit_emo_{love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, self_control}` with `_pos` and `_neg` variants
- `anti_emo_{hatred, despair, conflict, impatience, cruelty, corruption, betrayal, harshness, indulgence}`
- fruit_emo_composite, anti_emo_composite, fruit_emo_net (= fruit − anti), fruit_emo_strongest, fruit_emo_weakest

**L9: `09_LINGUISTIC_DEPTH/linguistic_analyzer.py`** (local: spaCy + textdescriptives + lexicalrichness)
- `td_{every column}` from the textdescriptives components coherence, readability, dependency_distance, pos_proportions and descriptive_stats; textdescriptives_status
- lr_words, lr_terms, lr_ttr, lr_rttr, lr_cttr, lr_mtld (threshold 0.72), lr_mattr (window 25), lr_hdd (sample 42), lr_error

**L10: `10_IDEA_DENSITY/idea_density_analyzer.py`** (local: `ideadensity` CPIDR)
- idea_density_mean, idea_density_min, idea_density_max, idea_density_std, idea_density_level (VERY HIGH, HIGH, MODERATE, LOW), idea_paragraphs_analyzed, idea_total_propositions, idea_density_status, idea_density_error

**L11: `11_HTML_REPORT/generate_report.py`**
- CLI: `--json`, `--output`, `--single`, `--snapshot`.
- Renders a dark/gold Chart.js scorecard. Snapshot mode adds tabs Claims, Equations, Assumptions, Evidence, Kill conditions, Comparison, Weak points, Revision.
- Local; uses YAKE.

**L12: `12_HEARTBEAT`** (not wired into `run_pipeline`; standalone plus a station wrapper)
- **`heartbeat_analyzer.py`** (SBERT `all-MiniLM-L6-v2`):
  - Per sentence: fruit_composite (mean cosine to fruit anchors minus anti anchors), chi_composite, combined, combined_smooth (window 5), section.
  - Structural pattern hits: definition, derivation, equation, evidence, prediction, scope_bound, edge_case, modularity, steelman, cross_domain, overclaim. structural_net = pos − 2 × overclaim.
  - Summary: fruit_mean/std/min/max, chi_mean/std/min/max, combined_mean/std, peak_score/sentence/text, valley_score/sentence/text, sentence_count, section_boundaries.
  - `v2_structural`: total_score, normalized_score, grade, interpretation, per-fruit score/positive_hits/negative_hits/tier, zones (theory/critique/defense word counts). This comes from the external `fruits_scorer_v2` at `\\192.168.1.177\Desktop`.
- **`canonical_anchors.py`:** SBERT anchor groups: 24 Properties, 10 Laws (±), 9 Fruits, 9 Anti-Fruits, 6 Armor of God, 8 Beatitudes, 9 Gifts, 8 Couplings.
- **`word_level_mapper.py paper [-o] [--openai]`:** word-by-channel Excel with channels A–N: GoEmotions 27, fruit blend, anti-fruit, SBERT fruit, SBERT chi 10, structural 11, 24 properties, laws constructive/destructive, fruits-as-physics, armor, beatitudes, gifts, couplings. With `--openai` it adds channels O–V from the sentence scorer.

**L13: `04_OPENAI_7Q/prompts/` + `lib/snapshot_*`** (only with `--openai` and `OPENAI_API_KEY`)
- Row fields: `L13_sections_ok`, `L13_sections_err`.
- Section outputs merge into the `ProofExplorerSnapshot` schema v1.0.0:
  - identity, thesis, claim_inventory, equations, assumptions, kill_conditions, evidence_map, physics_comparison, novelty, coherence, overstatement, revision, spine_analysis, citations
  - `pipeline_metrics` (the whole flat row)
  - theophysics overlay: seven_q_grid, decision_tree_status, swap_test, ckg_score, fruits_score, spine_mappings, declared_axioms, lean_file_path

**L13 section fields**
- **coherence_score** (0–10 each): definition_clarity, equation_coherence, claim_discipline, scope_control, falsifiability, citation_adequacy, domain_separation, reader_burden; review_readiness (0–100); justifications
- **overstatement_detector:** overstated_passages, rhetorical_strength_index, evidence_strength_index, delta, severity
- **claim_inventory:** claim, claim_type, importance, evidence_present, testability, risk_level, needs_citation
- **equation_audit:** equation, purpose, variables_defined, variable_definitions, dimensional_status, operational_status, role, issues
- **assumption_stack:** explicit, implicit, imported, theological, scientific, philosophical, measurement, causal
- **kill_conditions:** claim, kill_condition, test_method, severity, current_status
- **evidence_map:** claim, supporting_evidence, evidence_type, evidence_quality, counterevidence_needed, gap
- **physics_comparison:** nearest_theory, similarity, difference, does_paper_outperform, category_confusion_risk, honest_label
- **novelty_classification:** novelty_levels, primary_novelty, overstated_novelty_flags, honest_label
- **revision_plan:** strongest_part, weakest_part, must_fix_before_publication, best_next_test, needs_expert_review
- **spine_analysis:** article_title, proposed_reader_title, movement_chain[number, question_asked, answer_given, terms_introduced, clarity_flag], page_question, page_answer
- Every section also returns ai_confidence.

**`04_OPENAI_7Q` extras**
- **`ollama_7q_runner.py`** (the entrypoint the station config names):
  - CLI: `--paper`, `--output`, `--model` (default `qwen2.5:3b`), `--head` 3000, `--tail` 700, `--timeout` 360, `--classic-tokens`, `--section-tokens`, `--sections`.
  - Env: `OLLAMA_URL` (default `127.0.0.1:11434/api/generate`).
  - `RUN_LOCAL_OLLAMA_7Q.bat` runs it with head 1800, tail 400 and `--sections classic,snapshot`.
- **`engine_v2/`** (the imported "7Q Engine v2"; `main.py` modes test/forward/backward/llm-full/llm-judge/compact, OpenAI `gpt-4o`, env `OPENAI_API_KEY`):
  - 211 classification labels.
  - Truth score T = (S + E + L + D + P + C)/6 × XDM. S = structure, E = evidence = PS × CF with CF = (0.5 + 0.5·ED)(0.5 + 0.5·EC) and E capped at 0.5 if ED <0.3, L = logic/terminus, D = discrimination, P = posture, C = combat.
  - XDM: ×1.5 / 1.3 / 1.15 / 0.9.
  - Classes: ESTABLISHED ≥0.85, WELLSUP ≥0.65, TENTATIVE ≥0.40, SPECULATIVE ≥0.15, UNSUPPORTED.
  - Outputs Obsidian notes plus HTML.
- **`prompts_smoketest.py`**; `_archive/20260522_legacy_7q/promotion_pass.py` calls `api.openai.com` with `gpt-4o-mini`.

**`12_HEARTBEAT` OpenAI scripts** (env `OPENAI_API_KEY`)
- **`openai_8_prompts.py`:** `paper`, `-o`, `--publish`, `--all`, `--only`; model **o3**; cached. Prompts: 1 upgrade_path, 2 overclaim_audit, 3 missing_equations, 4 analogy_vs_isomorphism (always run), 5 hostile_reviewer, 6 prior_art, 7 one_question, 8 audience_gateway (with `--publish`).
- **`openai_paper_intel.py`:** o3 for paper-level work and gpt-4o-mini for sentences.
  - Output fields: competing_theories, citation_gaps, similar_papers, isomorphic_bridges (rigorous/broken/novel with strength 0–1), physics_audit (physics_grade), argument_structure (weakest_link, missing_steps, hidden_assumptions, formal_validity), novel_contribution (novelty_score), falsifiable_predictions, killer_objection (paper_survives, best_defense), publication_readiness (target_journals, blocking_issues), readability (structure_score).
  - overall_grade{rigor, originality, physics_accuracy, theological_depth, clarity, citation_completeness, publication_readiness, one_line_verdict}.
- **`openai_sentence_scorer.py`** (gpt-4o-mini, batches of about 10 sentences): type, axiom_deps (1–193), axiom_notes, theories, bridge_score, bridge_note, logic_score, falsifiable, missing_citations, strongest_objection.
- **`openai_mda_two_lane.py`:** `paper`, `--lane math|attention|both`, `--model` (default gpt-4o-mini), `-o`. Math-only audit or reader-attention audit.
- **`_run_boundary_question.py`:** a one-off o3 call on the "analogy → isomorphism → Maxwell" question.

**`13_WEB_INTAKE/app.py`** (FastAPI/uvicorn on :8088 via `run.bat`)
- Routes: `/`, `/submit`, `/status/{id}`, `/report/{id}`, `/raw/{id}`, `/healthz`.
- Runs `analyze_paper` in a thread with OpenAI off, then L11 HTML.

**`14_OBSIDIAN_BRAIN_ARM`**
- `run_obsidian_brain.py --vault ...` (plus 2 more flags) calls `obsidian_pipeline.run_obsidian_sync`. It uses yaml and regex; no model.
- Per doc: doc_id, title, relative_path, word_count, heading_count, wikilinks, tags (explicit/inferred), knowledge_type, source_type, status, domain, confidence.
- Summary: total_docs, by_domain, by_knowledge_type, by_source_type, by_status, top_tags, node_count, edge_count.
- Writes a digest HTML/CSV and classified JSON/JSONL.

**`15_PAPER_GRADER`**
- md5 shows these are **identical copies** of the paper-proof-grader root files: expanded_report, formal_verification, fruits_of_spirit_bridge, run_axiom_7q_stations, GRADING_WORKFLOW and PROCESS_INDEX.
- Its `fruit_dynamics.py` (11 KB) is the older version without `compute_fruit_dynamics`.

**Root `fruit_dynamics.py`** (numpy/scipy `solve_ivp`, 2026-06-18)
- Model: fruit ODE dF_i/dt = β_i φ (1 − F_i); faith ODE dφ/dt = αW̄ + βĒ − cφ; salvation ζ = sigmoid(k(‖F‖₂ − θ)); Φ_faith = γ(1 + ΣF_i e^−d_i)^p.
- Output fields:
  - `text_metrics`: total_words, fruit_token_hits, fruit_density, word_signal, experience_signal, dominant_fruit
  - `trajectory`: t, phi, fruit_norm, zeta, phase_transition_t
  - `final_state`: phi, fruit_vector{9}, fruit_norm, salvation_state, utility
- **Bug:** `_word_counts` uses `rf"\\b{fruit}\\b"`, which matches a literal backslash-b. So only self_control and faithfulness (which use an alias list) are ever counted; love, joy and the rest are always 0.
- **Design flaw:** dominant_fruit comes from the ODE end state, which shares φ across all fruits. It therefore reflects the highest β_i, not the text.

**`04_ANALYTICS`**
- A vault analytics toolkit ("BreakthroughVaultToolkit_v2", about 40 helper scripts).
- `run_series_analytics.py` / `run_full_series_suite.py`: GTQ series overview, knowledge graph, atoms/molecules, co-term density, coherence matrix. networkx, no CLI.
- `chi_computation.py`: a societal Chi time series (Pi/Lambda/A triads, 1960–2024), writing to `O:/Theophysics_Backend/...`.
- `theophysics_analytics/engine.py`: symbolic models of 8 "unsolved problems".
- `sync_to_postgres.py`.
- `ARCHIVE/Gemini_delete`: docs only.
- A README contains `export ANTHROPIC_API_KEY=sk-ant-...`. It is a **placeholder** (7 characters), not a real key.

**`paper-grader-nlp.station` (nested)**
- An SSS wrapper plus `python -m paper_grader` (env PAPER_GRADER_INPUT/OUTPUT/ARCHIVE). It imports a paper-proof-grader `pipeline`.
- `consolidate_metrics.py` builds one workbook row per `*.paper-grade.json`: paper_id, source_file, generated_at, grade, grade_confidence, rigor_verdict, word_count, section_count, equation_count, claim_count, avg_claim_maturity, max_claim_maturity, mature_claims_ge4, `Q1..Q7 coverage %`, `Q1..Q7 weak#`, top_terms.
- `EXPORTS/runbooks/build_paper_grade_metrics_dashboard.py` + `.ps1`. EXPORTS dated 2026-06-03.

**Docker**
- `Dockerfile`, `docker-compose.yml`, `docker_entrypoint.py` (grade | 7q | all | schema | report; Ollama via `OLLAMA_URL`/`OLLAMA_MODEL`, default qwen2.5:3b) and `requirements-docker.txt`.
- md5 shows `docker_entrypoint.py` is **identical** to the one in paper-proof-grader's DOCKER_PACKAGE.

**Specification docs, not code:** `OUTPUT_ARTIFACT_MAP.json` / `OUTPUT_CONTRACT.md` / `MASTER_VARIABLE_SCHEMA.md` (identical to paper-proof-grader) describe a target of 14 required workbook sheets and readiness-gate fields (claim_uuid, source_span, claim_type, evidence_required, support_status, kill_condition, overclaim_risk, category_error_risk, formal_route_or_boundary). **These are not implemented.**

---

## 2. paper-proof-grader.station (ST_039)

**Status:** newest code 2026-06-18 (`pipeline.py`, `config.json`); last artifact 2026-07-01. `_MIGRATION_NOTES` calls it a remote stub whose real location is `\\dlowenas\brain\Backside\apps\paper-proof-grader-main (1)`. No hard-coded keys.

**`pipeline.py` (SSS_v1)**
- Does **not** grade proofs. It runs the Fruits `SemanticAnchorScorer` with `all-MiniLM-L6-v2` (hashed n-gram fallback), plus an embed request to `localhost:8700/nlp/embed`. In the 07-01 artifact that request got connection refused.
- `RUN.bat`, `FRONT_DOOR.bat` (xcopies `FETCH_SOURCE` into `_inbox`) and `RUN_NOW_NO_PAUSE.bat` all run it.
- Fields: semantic_backend, semantic_ontology, semantic_fruit_alignment, semantic_anti_alignment, semantic_net_alignment, semantic_dominant_anchor, semantic_dominant_anti_anchor, semantic_fruit_anchor_scores{9}, semantic_anti_anchor_scores{coercion, domination, deception, fear_shame, fragmentation, exploitation, certainty_inflation, tribal_binding}, vectorization{dimension, vector, model, ...}, series_context (EMA α 0.3, always disabled).

**`pipeline_legacy.py`** (1105 lines; the real regex grader, run through `workflow.py`)
- **Metrics:** word_count, section_count, equation_count (cap 200), claim_candidate_count (cap 250), top_terms.
- **Per claim:**
  - claim_maturity_level/label, a 1–7 ladder: Metaphor, Analogy, Structural Correspondence, Formal Model, Machine-Checked Theorem, Empirical Support, Public Proof Claim
  - Q1_identity, Q2_scope, Q3_mechanism, Q4_evidence, Q5_falsifiability, Q6_boundary, Q7_listener_risk
  - evidence_bar, facts_snapshot, forward_test, reverse_test, kill_conditions, not_claimed, proof_boundary, nearby_equation, formal_verification{}
- **Grade:** score = % of (Q4 + Q5 + Q6 + maturity≥4) over 4·claims. A ≥85 GREEN_READY, B ≥65 YELLOW_REVIEW, C ≥40 ORANGE_REPAIR, else D RED_REPAIR. Fields grade, grade_confidence, rigor_verdict.
- **Dashboard:** Q_COVERAGE_PCT, Q_WEAK_COUNT, Q_FILL_CLASS, Q_OBSERVED_VALUES, MATURITY_COUNT/PCT, EVIDENCE_MARKED, KILL_COUNT, law hits 1–10. VECTOR_HASH is a hard-coded constant.
- **Manifest:** source_sha256, source_size_bytes, detected_format, grader_version "v0.2-station", rubric_version.
- **XLSX sheets:** Review_Control, Summary, Claim Audit (25 columns), Equations, Sections.
- Standalone `main()` breaks: `config.json` lacks the input_dir/output_dir/archive_dir keys.

**`formal_verification.py`**
- Maps claims to theorem families (closure, sign_invariance, targeted_openness, external_grace, necessary_conditions, justice_mercy_transform), each pointing at an intended `lean/*.lean` file.
- Per claim: lean (formalizable, counterexample_found or not_attempted; "proven" is never assigned), alloy, state_model, bridge_status, theorem_dependencies, lean_files, formalization_note.
- Totals: lean.{proven, formalizable, counterexample_found, not_attempted, speculative}, formal_candidate_dependencies.

**`workflow.py`**
- CLI: `[paper]`, `--out`.
- score = min(100, 4·claims + 8·equations); A ≥80, B ≥60, C ≥40, else NEEDS_WORK.
- **Bug:** it reads `claim_count`, but the legacy grader writes `claim_candidate_count`.

**`expanded_report.py`**
- claim_count, evidence_count/pct, falsifiable_count/pct, boundary_count/pct, high_risk_count, formalizable_count, lean_proven_count, avg_maturity.
- Score = 50 + min(15, eq//4) + min(15, ev%//5) + min(10, fals%//8) + min(10, bound%//10) − min(20, 4·highrisk).
- **Broken in the station:** `output_dir` is missing from config.

**`fruits_of_spirit_bridge.py`**
- CLI: `--input`, `--output`, `--pattern`, `--no-recursive`, `--limit`, `--no-excel`.
- Env: FRUITS_BRIDGE_CONFIG, TRUTH_ENGINE_ROOT, FRUITS_OUTPUT, PAPER_GRADER_LEXICON_XLSX, FRUITS_EMBEDDING_MODEL.
- Launcher `RUN_FRUITS_OF_SPIRIT.bat`; its default input `DROP_PAPERS_HERE` does not exist.
- **Metrics:**
  - tokens, sentences, fruit, anti_fruit, grounding, contradiction
  - coherence = 0.6 × Jaccard continuity + 0.4 × length balance
  - integration = (fruit + ground + coh)/3
  - truth = .34 coh + .23 ground + .23 fruit + .20 integ − .14 anti − .12 contra
  - propaganda = .5 anti + .3(1 − ground) + .2 contra
  - snr, assertion_ratio, contradiction_pressure, coherence_density
  - top_fruit/anti/ground/contra
- **From the Truth Engine** at `\\dlowenas\github\Truth Engine (1)`: christ_vector, cronkite_delta, sigma_state, archetype, role, kill_conditions, christ_vector_alignment/label, dominant_fruit, weakest_fruit. The agent got permission denied on that share, so these internals are unverified.
- It also emits all the semantic_* fields.

**`run_axiom_7q_stations.py`** (1074 lines)
- CLI: `--openai`, `--openai-model` (env `AXIOM_7Q_OPENAI_MODEL`, default **o3**), `--openai-limit`, `--file-limit`. `RUN_AXIOM_7Q_OPENAI_SAMPLE.bat` runs it with o3 on 1 file and 1 claim.
- Input: `EXPORTS/reports/0*.claim-audit.csv`, plus `REFERENCE/canonical_chain_nodes.psv` (46 nodes) and axiom cards from 6 HTML files.
- **Per claim:**
  - forward.score 0–7
  - reverse.status FAIL_REVIEW, WEAKENED, SURVIVES_WITH_REPAIRS or SURVIVES
  - reverse.weaknesses: missing_evidence, missing_kill_condition, missing_mechanism, overbroad_scope, missing_boundary, high_listener_risk
  - axiom_hits[sequence, chain_position, display_id, node_type, family, kill_condition, source, matched_terms]
- **Per paper:** hit_counts, average_score, score_counts, status_counts, weakness_counts.
- **OpenAI prompt:** "Theophysics Axiom + 7Q verifier… do not rubber-stamp… strict JSON". Output fields: candidate (accept/repair/reject/unsure), confidence, axiom_ids, suggested_registry_terms, required_evidence, failure_conditions, rationale.
- Outputs HTML plus a 5-sheet XLSX.

**`DOCKER_PACKAGE_20260507_191530`**
- `docker_entrypoint.py` is identical to the PIS one. The orchestrator it loads is missing here but present in paper-intelligence-suite (§1).
- `paper_defensibility_snapshot.py` (1162 lines, `input`, `--output`):
  - Nabla address: domain, entity, state, audience, use, risk R0–R4, vector (G..C levels 0–3), pair hash.
  - Score events: CLAIM_ARCH_SURFACE, CLAIM_ARCH_OPERATIONAL, DOMAIN_BOUNDARY_UNBRIDGED, EVIDENCE_QUOTE_PRESENT, EVIDENCE_BRIDGE_GAP, KILL_ARCH_PRESENT/MISSING, EQ_SEM_STATUS, EQ_SEM_UNDEFINED_VARS, OVERSTATEMENT.
  - Four-score dashboard: academic_readiness, framework_coherence, public_communication, risk.
  - An `llm_extractor` hook exists but no provider is wired to it.
- `RUN_DOCKER_GTQ_ALL25.bat` targets image `theophysics/paper-intelligence:gtq-all25-20260507-191530`.

**Other sub-folders**
- `ONLINE_CODEX_PACKAGE`: specs and a Codex prompt for a 9-box snapshot UI; no code.
- `REFERENCE`: the axiom registry.
- `INPUT`: 25 GTQ papers.
- `_PURGE_CANDIDATE`: duplicates.
- **chi_qi_v5_metric_engine.py and nlp_deep_runner.py are not anywhere in this station**, including the Docker and Codex packages and _PURGE_CANDIDATE.

### Comparison with the July copy (`\\192.168.2.50\h_hp\...\Academic Paper Grading\paper-proof-grader`, newest file 2026-07-15)

**Verdict:** the July copy is **newer** (07-10/07-15) and is a portable, git-ready repo. The station copy is **fuller**. Neither is a subset of the other.

**Only in the July copy**
- **`chi_qi_v5_metric_engine.py`** (07-10, 920 lines, local):
  - CLI: `--input`, `--out`, `--lexicon` (repeatable), `--recursive`, `--max-files`, `--deep-axiom-spans`.
  - Per-metric fields: raw_hits, weighted_hits, unique_terms, density_per_1000_words, distribution_score, cooccurrence_score, counter_signal_score, evidence_support, boundary_support, score, confidence, qualifier, symptom, symptom_severity, repair_action, route_trigger, evidence_spans.
  - Formula: score = clamp(.35 marker + .20 density + .20 support + .15 distribution − .20 counter).
  - Metric ids: axiom, law, evidence, boundary, falsification, coherence, fruit, anti_fruit (`.general.score`).
  - Vectors (each normalized to 100): domain_vector (10), chi_vector (G..C), axiom, definition, lemma, theorem, property, equation, boundary_condition, assumption, fruit, anti_fruit, law, structured_law.
  - Routing fields: pass_2_deep_audit_recommended, pass_3_llm_review_recommended (always False).
  - Some declared fields are never computed: structural_completeness, formal_support, rival_score, margin.
- **`nlp_deep_runner.py`** (07-10, spaCy `en_core_web_sm`):
  - CLI: `--input`, `--out`, `--recursive`, `--max-files`, `--key-sentences`.
  - Fields: word_count, content_word_count, top_terms, topics (5 domains), entities (engine, entity_count, entity_labels), key_sentences (score, index, offsets, reasons), spacy_available.
- A relative-path `config.json`.

**Newer or larger in the station copy**
- `pipeline_legacy.py` (1105 lines) versus July `pipeline.py` (678 lines, a de-networked grader without the formal layer, sha256 manifest, dashboard grade, Q coverage or law hits).
- `run_axiom_7q_stations.py`: 1074 lines with canonical registry, OpenAI o3, HTML and XLSX, versus July's 219-line rules-only version from May 14.
- `expanded_report.py`: the station copy adds the Lean counts.
- Station only: formal_verification, fruits_of_spirit_bridge, workflow, Docker snapshot/entrypoint.

**To merge:** the station's legacy grader + formal layer + 7Q-v2 + Fruits, plus July's chi_qi_v5 + nlp_deep + portable config.

---

## 3. A_AI-RESEARCH-AGENTS

**Status:** stock upstream clones plus six PowerShell launchers dated 2026-05-18 to 05-23; the .venvs were built 2026-06-11. All scripts hard-code `D:\AI-RESEARCH-AGENTS\...`, which is stale.

- **gpt-researcher:** `assafelovic/gpt-researcher` v0.14.7, HEAD `92bfc038`, unmodified.
  - Defaults: retriever tavily; FAST `openai:gpt-4o-mini`, SMART `openai:gpt-4.1`, STRATEGIC `openai:o4-mini`; embeddings `openai:text-embedding-3-small`.
  - Env: OPENAI_API_KEY, TAVILY_API_KEY, GOOGLE_API_KEY, DOC_PATH.
  - Launchers: `start-gpt-researcher.ps1` (uvicorn on 127.0.0.1:8000) and `run-gpt-researcher-service.ps1` (restart loop on 0.0.0.0:8000).
  - `register-task.ps1/.bat` creates the scheduled task "GPTResearcher" (at logon, restart ×999).
  - **`write-env.ps1` writes real keys in plaintext to `gpt-researcher\.env` on the NAS.**
- **local-deep-researcher:** `langchain-ai/local-deep-researcher`, HEAD `e1721099`. The launcher sets SEARCH_API=duckduckgo, LLM_PROVIDER=ollama, `LOCAL_LLM=llama3.1:8b`, and runs `langgraph dev`. The code default is llama3.2; `.env.example` mentions qwen_qwq-32b on LM Studio.
- `check-env.ps1` checks whether TAVILY, GOOGLE, OPENAI and OPENROUTER keys are set, without printing them.

## 4. A_BIL (Behavioral Intelligence Layer / Preference Engine)

**Purpose:** local-first capture-and-learn. It takes in screenshots, clipboard, browser dwell, GitHub repos and Exa searches, and trains River online logistic-regression preference models that score and re-rank.

**Status**
- Prototype, partially wired. Newest code is 2026-06-01; the newest model pkl is 2026-06-13.
- Paths are stale: the code hard-codes `X:\BIL` and `D:\BIL`/`D:\FAP`.
- Data is thin, e.g. `ratings.jsonl` has 1 line and the clipboard log 101.
- **`docker-compose.yml` has a hard-coded MySQL password and WEBUI_SECRET_KEY.**

**Launchers**
- `START_BIL.bat` starts three things: the nested plugin `bil.bil_server` on :8420, `clipboard_watcher.py` and `bil_service.py` (tray).
- `RUN_FAP_HEALTHCHECK.bat`, `RUN_FAP_POSTGRES_SYNC.bat`, and `INSTALL_FAP_POSTGRES_SYNC_TASKS.bat` (scheduled tasks at 07:45 and 19:45).

**Top-level scripts**
- `bil_service.py`: screenshots via mss, described by Ollama **moondream**; PREFER/REJECT ratings with a dataset tag; posts to `brain.dlowehomelab.com/capture`.
- `vectorize_mda.py` and `map_framework_coverage.py`: local SBERT MiniLM at `\\dlowenas\brain\Backside\_models\_Models\sbert_minilm`. They compute neighbor similarity and 22 concept-coverage scores (STRONG >0.45, MODERATE >0.35).
- `build_master_workbook.py`: merges 8 station manifests into `MASTER_STATION_WORKBOOK.xlsx`.
- `_build_consciousness_dict.py`, `_cross_ref.py` and others are one-off helpers.

**engines/** (Ollama)
- threshold_engine (**mistral**; confidence gate 0.3–0.85)
- truth_engine (mistral; tiers T1 VERIFIED … T5 DARK)
- vision_engine (moondream; llava mentioned)
- emotion_engine (mistral: valence, intensity, emotion, engagement)
- github/repo_analyzer (GitHub REST plus a mistral README fact-check)
- embeddings/text_embedder (Infinity server at 192.168.1.177:7997, all-MiniLM-L6-v2)

**pipeline/ (FAP "Paper Mill")**
- `fap_boot.py --init-db --dry-run`; watchdog hot folders under `D:\FAP`; Postgres `192.168.1.97`, schema `fap.*`.
- `llm_hub.py`: Tier 1 is Ollama mistral. Tier 2 is **Anthropic `claude-sonnet-4-20250514`** via `api.anthropic.com/v1/messages`, env **ANTHROPIC_API_KEY**, used for grade_paper, cross_domain_analysis, axiom_mapping, gap_detection and voice_audit.
- The last Postgres sync on 2026-06-01 failed with a connection timeout.

**adapters/**
- `exa_tracker.py`: env EXA_API_KEY.
- Video FastAPI on :8421: Piped and ProxiTok clients, YouTube Data API v3 (env YOUTUBE_API_KEY), River VideoModel.

**Other**
- `nas-deploy/pil_api.py`: FastAPI on :8420 using moondream. The notes say the NAS container returned 502.
- `browser/`: MV3 extension "Bill".
- The compose stack runs ragflow, open-webui, qdrant, a gpt-researcher container, infinity and a dashboard.

## 5. A_behavioral-intelligence-layer-OBS-Plugin-Final-Claude vs the copy nested in A_BIL

The two have **diverged**.
- md5-identical files: `.gitignore`, `__init__`, `bil_features.py`, `bil_models.py`.
- **Nested copy (the live one run by START_BIL):** 23.9 KB `bil_server.py` dated 06-01 on :8420.
  - Routes: status, clipboard/predict, context, summary, decide, web, clipboard, rank, github.
  - Decision bands: prioritize ≥0.72, consider ≥0.55, neutral ≥0.40, else deprioritize.
  - Four River models: web, clipboard, files, content.
  - Has exports: `bil_events.jsonl` and a pkl dated 06-13.
- **Standalone copy (all files dated 06-10):** a minimal server plus two CLIs.
  - `bil.ingest --path --host --dry-run`
  - `bil.llm_query --model --ollama --bil --exports --feed-back`, using Ollama with default `llama3` (env OLLAMA_HOST, OLLAMA_MODEL, BIL_HOST).
  - Adds a browser extension.

## 6. A_GUI
- `brain/`: a stub. It holds one `session_summary.md` reading "Pending LLM completion" (06-12).
- `brain-dashboard/` v0.1.0 (05-20): a PySide6 read-only MVP.
  - CLI: `--version`, `--headless-smoke-test`.
  - Reads `intake_engine/state.json` and the `_LOGS` folder, and lists `Theophysics_`/`FAP_` scheduled tasks.
  - Bug: last_run_time is mapped from RunLevel.
  - Only the Overview tab exists. No LLM.

## 7. _DORMANT (62 stations; overview only)

- All share the SSS_v1 scaffold. `pipeline.py` was rewritten 2026-06-18; everything else is dated about 06-16. The `.fisnote` files (08-08) are markers only.
- No hard-coded keys were found in the top-level files.
- Per-station purpose and models:
  - 7q-classifier: OpenAI gpt-4o-mini
  - 7q-engine: 7Q v2, OpenAI gpt-4o, Ollama option
  - ai-portal-generator
  - ai-research-agents: a runtime copy, 14.6k files
  - apologetic-pipeline: YouTube → Whisper
  - axioms: paper decomposition, rigor gates, grade HTML; 3.2k files
  - brain-map, open-brain-map: wrapped repos
  - claim-extractor: claims + 7Q
  - classify-documents: MiniLM/DeBERTa
  - coherence-discoherence: content only
  - contradiction-deep, contradiction-detector, contradiction-scan: local NLI
  - deberta-runner: MoritzLaurer DeBERTa-v3-large-mnli-fever-anli-ling-wanli and deberta-v3-base-zeroshot-v1.1
  - evidence-map
  - fact-verifier
  - falsification
  - file-intelligence, fis: FIS on Postgres
  - graph-linker
  - harvest-links
  - hdbscan-cluster
  - html-article: an 18-lane HTML assembly
  - image-processor: CLIP `openai/clip-vit-base-patch32`
  - lightfm-recommender, recbole-recommender, preference-implicit
  - link-pull, link-research: crawl4ai
  - llm-runner: raw Mistral
  - load-bearing-claims
  - master-equation-canon, operators-canon, trinity-canon
  - math-layer, math-translation-layer: TypeScript; 4.3k files; one spec addressed to Kimi
  - math-verify
  - mda-citation-spine: OpenAI runner
  - mda-publication
  - metadata-extractor
  - obsidian-export
  - paper-grader-nlp
  - paper-recommender: Semantic Scholar
  - paper-review: M12
  - paperqa2: vendored, LiteLLM with OpenAI as default
  - postgres-sync
  - preference-engine
  - readability-rewriter
  - sbert-embedder: all-MiniLM-L6-v2 via Infinity + Qdrant
  - section-splitter
  - series-flow-auditor: deterministic
  - session-handoff-combined, session-handoff-drop
  - theophysics-engine: a Replit Vite/TS app
  - timeline-verifier
  - transcribe-and-classify, whisper-transcribe: Whisper
  - vault-rater-tsr100: "Lowe Standard", OpenAI gpt-4o via Cloudflare AI Gateway
  - youtube-fetch, youtube-qa, youtube-scrape

---

## FLAT METRIC LIST: paper-intelligence-suite

- **Identity:** paper_id, file, series_id, run_id, schema_version, source_path, analyzed_at, snapshot_path, _layer_status
- **PA_s:** word_count, unique_word_count, ttr, sentence_count, paragraph_count, header_count, avg_words_per_sentence, avg_sentences_per_paragraph
- **PA_g:** noun_pct, verb_pct, adj_pct, adv_pct, prep_pct, passive_voice_count, passive_pct, modal_verb_count, assertive_verb_count, modal_vs_assertive_ratio, weight_signal, fluff_flag
- **PA_sm:** topic_drift_avg, topic_drift_max, topic_drift_scores, coherence_flag
- **PA_d:** compression_ratio, density_label, stopword_ratio, trigram_redundancy, signal_noise_ratio
- **PA_r:** flesch_kincaid_grade, gunning_fog, smog_index, text_standard, reading_time_min, avg_dependency_depth, max_dependency_depth, cognitive_load
- **PA_a:** claim_count, claim_density_per1k, evidence_count, evidence_density_per1k, evidence_to_claim_ratio, falsifiability_markers, argument_grade
- **PA_f:** transition_density_pct, transition_count, flow_label
- **PA_lk:** total_links, link_density_per1k, link_citation, link_concept, link_dependency, link_evidence, link_navigation, internal_links, external_links, internal_external_ratio, cross_domain_bridges, link_quality_score, underlink_flag, overlink_flag, concept_nodes, concept_edges, avg_degree, clustering_coeff, most_central_paragraph, centralization, isolated_nodes
- **L1:** word_count, unique_word_count, vocab_richness, paragraph_count, header_count, avg_paragraph_words, flesch_reading_ease, flesch_kincaid_grade, gunning_fog, smog_index, automated_readability, coleman_liau, dale_chall, text_standard, reading_time_min, syllable_count, lexicon_count, sentence_count, keybert_keywords, yake_keywords, top_bigrams, top_trigrams
- **L2:** title_detected, citation_count, author_year_citation_count, numeric_citation_count, citation_density_per1k, external_theory_count, external_theories, academic_signal_count, academic_signal_density, structure_score, heading_count, reference_entry_count, has_abstract, has_introduction, has_methodology, has_results, has_discussion, has_conclusion, has_references_section, footnote_count, url_references, doi_references, claim_marker_count, claim_density_per1k, evidence_marker_count, evidence_density_per1k, evidence_to_claim_ratio, falsifiability_marker_count, falsifiability_density_per1k, hedge_count, hedge_density_per1k, absolute_claim_count, absolute_density_per1k, hedge_to_absolute_ratio, counterargument_count, limitation_count, novelty_marker_count, definition_marker_count, quantitative_marker_count, equation_count, equation_density_per1k, claim_candidate_1-3, evidence_candidate_1-2, rubric_structure_points, rubric_grounding_points, rubric_claim_points, rubric_quantitative_points, rubric_falsifiability_points, academic_rubric_total, academic_rubric_grade, academic_grade, ss_found, ss_title, ss_year, ss_venue, ss_citation_count, ss_influential_citations, ss_reference_count
- **L2 v2 extras (not wired in):** body_doi_citation_count, body_url_citation_count, bracket_year_citation_count, citation_style_count, has_limitations, has_literature_review, has_research_question, recent_reference_count, older_reference_count, reference_year_count, strong_claim_count, strong_claim_density_per1k, unsupported_strong_claim_count/_1-3, falsifiability_candidate_1-3, recommendation_1-3
- **L3:** chi_score, chi_status, wisdom_score, knowledge_score, wk_ratio, wk_status, fruits_composite, anti_fruits_composite, fruits_net_score, dominant_fruit, dominant_anti_fruit, fruits_detail, anti_fruits_detail, me_avg_score, me_dominant_variable, cross_domain_bridges, scripture_refs, ckg_raw, ckg_tier, me_G/M/E/S/T/K/R/Q/F/C (10)
- **L4:** 7q_verdict, 7q_confidence, 7q_file; plus forward q0-q7, summary, top_3_strengthening_actions and reverse r1-r7, verdict, confidence_score
- **L5:** entity_count, entity_people, entity_orgs, entity_concepts, entity_types_found, key_sentence_1-3, topic_1-3, topic_count
- **L6:** truth_score, coherence_score, combined_score, evidence_density, falsifiability_density, hedge_density, absolute_pressure, rhetorical_force, warmth_score, discipline_score, balance_score, fruit_integrity_score, anti_fruit_pressure, character_posture, integrity_profiles, threat_score, protection_score, primary_threats, primary_protections, claim_count, anchored_claims, under_supported_claims, overstated_claims, falsifiable_claims, speculative_claims, contradictory_claims, contradiction_flags, sentence_count, paragraph_count, section_count, top_supported_1-2, top_risky_1-2, fruit_{9}, anti_{9}, anti_fruit_{9}, attr_{8}_{kind, pos_hits, neg_hits, strength, counter_pressure, net_score}
- **L7:** centrality_within_series, cluster; plus node degree, betweenness, cluster_count, most_central, node_count
- **L8:** nrc_status, nrc_{10}, nrc_top_emotions, goemotions_status, emo_{27}, emo_dominant, emo_top_5, emo_sentence_count, fruit_emo_{9} (+_pos/_neg), anti_emo_{9}, fruit_emo_composite, anti_emo_composite, fruit_emo_net, fruit_emo_strongest, fruit_emo_weakest
- **L9:** td_{all textdescriptives columns}, textdescriptives_status, lr_words, lr_terms, lr_ttr, lr_rttr, lr_cttr, lr_mtld, lr_mattr, lr_hdd
- **L10:** idea_density_mean, idea_density_min, idea_density_max, idea_density_std, idea_density_level, idea_paragraphs_analyzed, idea_total_propositions, idea_density_status
- **L12 heartbeat:** per sentence fruit_composite, chi_composite, combined, combined_smooth, plus 11 structural categories and structural_pos/neg/net; summary fruit_mean/std/min/max, chi_mean/std/min/max, combined_mean/std, peak_*, valley_*; v2_structural total_score, normalized_score, grade, per-fruit score/tier, zones
- **L12 word mapper:** channels A–V
- **L12 OpenAI sentence scorer:** type, axiom_deps, axiom_notes, theories, bridge_score, bridge_note, logic_score, falsifiable, missing_citations, strongest_objection
- **L12 paper intel:** competing_theories, citation_gaps, similar_papers, isomorphic_bridges, physics_audit, argument_structure, novel_contribution, falsifiable_predictions, killer_objection, publication_readiness, readability, overall_grade{rigor, originality, physics_accuracy, theological_depth, clarity, citation_completeness, publication_readiness}
- **L13:** sections_ok, sections_err, plus all snapshot sections: definition_clarity, equation_coherence, claim_discipline, scope_control, falsifiability, citation_adequacy, domain_separation, reader_burden, review_readiness, rhetorical_strength_index, evidence_strength_index, delta, severity, and the claim, equation, assumption, kill, evidence, comparison, novelty, revision and spine fields
- **engine_v2:** S, E (PS, CF, ED, EC), L, D, P, C, XDM, T, confidence class
- **fruit_dynamics:** total_words, fruit_token_hits, fruit_density, word_signal, experience_signal, dominant_fruit, trajectory t/phi/fruit_norm/zeta, phase_transition_t, final phi, fruit_vector, fruit_norm, salvation_state, utility
- **Brain arm:** knowledge_type, source_type, status, domain, confidence, by_* counts, top_tags, node_count, edge_count
- **Alignment:** paper_word_count, paper_text_standard, paper_fk_grade, paper_chi_score, paper_ckg_tier, paper_claim_markers, paper_claims_truth_engine, paper_truth_score, paper_combined_score

## FLAT METRIC LIST: paper-proof-grader

- **Station `pipeline.py`:** semantic_fruit_alignment, semantic_anti_alignment, semantic_net_alignment, semantic_dominant_anchor, semantic_dominant_anti_anchor, semantic_fruit_anchor_scores{9}, semantic_anti_anchor_scores{8}, vectorization dimension/vector, series_context
- **`pipeline_legacy`:** word_count, section_count, equation_count, claim_candidate_count, top_terms, claim_maturity_level/label, Q1-Q7, evidence_bar, facts_snapshot, forward_test, reverse_test, kill_conditions, not_claimed, proof_boundary, nearby_equation, grade, grade_confidence, rigor_verdict, Q_COVERAGE_PCT, Q_WEAK_COUNT, Q_FILL_CLASS, Q_OBSERVED_VALUES, MATURITY_COUNT/PCT, EVIDENCE_MARKED, KILL_COUNT, law hits 1-10, source_sha256, source_size_bytes, character_count
- **`formal_verification`:** lean, alloy, state_model, bridge_status, theorem_dependencies, lean_files, formalization_note, lean.proven/formalizable/counterexample_found/not_attempted/speculative, formal_candidate_dependencies
- **`workflow`:** score, grade
- **`expanded_report`:** claim_count, evidence_count/pct, falsifiable_count/pct, boundary_count/pct, high_risk_count, formalizable_count, lean_proven_count, avg_maturity, overall score and label
- **`fruits_bridge`:** tokens, sentences, truth, coherence, fruit, anti_fruit, grounding, contradiction, integration, propaganda, snr, assertion_ratio, contradiction_pressure, coherence_density, top_*, christ_vector, cronkite_delta, sigma_state, archetype, role, kill_conditions, christ_vector_alignment/label, dominant_fruit, weakest_fruit, semantic_*
- **`axiom_7q`:** forward.score, reverse.status, reverse.weaknesses, axiom_hits, hit_counts, average_score, score_counts, status_counts, weakness_counts, OpenAI candidate/confidence/axiom_ids/suggested_registry_terms/required_evidence/failure_conditions/rationale
- **Docker defensibility snapshot:** address domain/entity/state/audience/use/risk/vector/hash, 10 ScoreEvent ids, academic_readiness, framework_coherence, public_communication, risk
- **`consolidate_metrics` (via paper-grader-nlp):** avg_claim_maturity, max_claim_maturity, mature_claims_ge4, Q coverage %, Q weak#
- **July `chi_qi_v5`:** raw_hits, weighted_hits, unique_terms, density_per_1000_words, distribution_score, cooccurrence_score, counter_signal_score, evidence_support, boundary_support, score, confidence, qualifier, symptom, symptom_severity, repair_action, route_trigger, 8 metric ids, 14 vectors, hash_sha256, pass_2_deep_audit_recommended, top_domain/chi/axiom/fruit/law
- **July `nlp_deep`:** word_count, content_word_count, top_terms, topics, entity_count, entity_labels, key_sentences, spacy_available

## Every LLM provider and model referenced

- **OpenAI**, env `OPENAI_API_KEY`:
  - gpt-4o-mini: PIS L4 seven_q_runner, the 10 L13 prompts, openai_sentence_scorer, openai_mda_two_lane, the archived promotion_pass, dormant 7q-classifier, gpt-researcher FAST
  - gpt-4o: PIS spine_analysis, engine_v2, dormant 7q-engine, vault-rater-tsr100 via Cloudflare AI Gateway
  - o3: PIS openai_8_prompts, openai_paper_intel, _run_boundary_question; proof-grader run_axiom_7q (env `AXIOM_7Q_OPENAI_MODEL`)
  - gpt-4.1, o4-mini, text-embedding-3-small: gpt-researcher defaults
  - PaperQA2 (dormant) defaults to OpenAI through LiteLLM
- **Anthropic**, env `ANTHROPIC_API_KEY`: claude-sonnet-4-20250514 in A_BIL `pipeline/llm_hub.py`. The PIS README key is a placeholder.
- **Ollama, local:**
  - qwen2.5:3b: PIS ollama_7q_runner and docker (env `OLLAMA_URL`, `OLLAMA_MODEL`)
  - mistral, moondream, llava: A_BIL
  - llama3: standalone BIL llm_query
  - llama3.1:8b and llama3.2: local-deep-researcher
  - Ollama route in the SSS_v1 template
- **LM Studio:** qwen_qwq-32b, in local-deep-researcher `.env.example`
- **Raw weights:** Mistral in dormant llm-runner
- **Local NLP models:**
  - sentence-transformers all-MiniLM-L6-v2: PA, L1 KeyBERT, L12, fruits bridge, Infinity, sbert-embedder
  - spaCy en_core_web_sm
  - HF monologg/bert-base-cased-goemotions-original
  - NRCLex, textstat, YAKE, gensim LDA, sumy, textdescriptives, lexicalrichness, ideadensity CPIDR, networkx, python-louvain
  - DeBERTa-v3 MoritzLaurer NLI/zero-shot, CLIP openai/clip-vit-base-patch32, Whisper, River, LightFM, RecBole, HDBSCAN
- **Non-LLM APIs:** Semantic Scholar (L2, paper-recommender), Tavily, DuckDuckGo, SearXNG, Perplexity, Exa (EXA_API_KEY), YouTube Data v3 (YOUTUBE_API_KEY), GitHub REST. GOOGLE_API_KEY and OPENROUTER_API_KEY are checked by the research-agent scripts but not used by any code here.
- **Hard-coded or plaintext secrets:**
  - `A_AI-RESEARCH-AGENTS\gpt-researcher\.env` holds real keys, written by write-env.ps1.
  - `A_BIL\docker-compose.yml` holds a MySQL password and WEBUI_SECRET_KEY.
  - None were found in PIS, paper-proof-grader or _DORMANT source.

## Bugs found
1. `RUN_LOCAL_PAPER_INTELLIGENCE.bat` and `RUN.bat` pass `--pattern`, which `run_pipeline.py` rejects.
2. The regex in `fruit_dynamics._word_counts` is double-escaped, so 7 of 9 fruits are always 0.
3. `LAUNCH.bat` option 4 passes `--folder` to `truth_runner.py`, which has no CLI.
4. In paper-proof-grader, `expanded_report.py` and `pipeline_legacy.main()` fail because config keys are missing.
5. `workflow.py` reads the wrong key (`claim_count` instead of `claim_candidate_count`).
6. The station `pipeline.py` cannot reach the embed endpoint on :8700.
7. A_BIL and A_AI-RESEARCH-AGENTS hard-code the old `X:\BIL`, `D:\` paths.