# SERIES AGGREGATION TEMPLATE — v0.3
**POF 2828 | 2026-09-14 | canonical copy: 999_TEMPLATES/API_LAYER_v0.3**
*Aggregates a series of papers into a single overview. DeepSeek runs on
ALL papers in the series at once. Produces: series identity, kernel map,
claim consolidation, cross-paper evidence, structural spine, destination
map, and gap analysis. One of these per series.*

<!-- @template layer=series version=0.3 -->

---

```yaml
---
type: series_aggregation
series_id: "{{series_slug}}"
series_title: "{{series_title}}"
template_version: SERIES_AGG_V0.3
paper_count: {{count}}
paper_ids: [{{comma_separated_paper_ids}}]
source_sha256s: [{{comma_separated_sha256s}}]
generated_at: {{ISO_8601_timestamp}}
series_status: {{DRAFT | REVIEWED | CANONICAL}}

# audit trail
semantic_provider: "{{provider}}"
semantic_model: "{{exact_model_string}}"
usage_tokens: {{prompt_completion_total_cost_object}}
---
```

---

<!-- ═══════════════════════════════════════════════ -->
<!-- SERIES IDENTITY (the first thing you see)      -->
<!-- ═══════════════════════════════════════════════ -->

# {{series_title}}

## Series at a glance

**Papers in series:** {{count}}
**Governing question:** {{the_one_question_the_whole_series_answers}}
**One-sentence finding:** {{what_the_series_establishes_taken_together}}
**Domains touched:** {{list_of_domains}}
**Strongest claim:** {{the_single_strongest_claim_across_all_papers, with paper_id}}
**Weakest load-bearing claim:** {{the_single_weakest_claim_that_something_depends_on, with paper_id}}
**Series rating:** {{aggregate — min of paper_ratings, not average}}

## Series verdict

> {{UNSCORED / SCORED — with aggregate balance and coverage}}
> {{count}} papers scored, {{count}} unscored, {{count}} gated.

---

## Paper inventory

| # | Paper ID | Title | Domain | Rating | State | Role in series |
|---|---|---|---|---|---|---|
| 1 | {{paper_id}} | {{title}} | {{domain}} | {{rating}} | {{SCORED/UNSCORED/GATED}} | {{what this paper does for the series}} |
| 2 | {{paper_id}} | {{title}} | {{domain}} | {{rating}} | {{state}} | {{role}} |
<!-- One row per paper in series order -->

---

<!-- ═══════════════════════════════════════════════ -->
<!-- KERNEL MAP                                      -->
<!-- ═══════════════════════════════════════════════ -->

## Kernel map

<!-- Every novel kernel across all papers in the series. Duplicates identified
     and collapsed. This is the intellectual inventory — what did the series
     actually produce? -->

### Novel kernels (unique to this series)

| Kernel ID | Kernel | Source paper | Novel? | Status | Destination |
|---|---|---|---|---|---|
| K-001 | {{kernel_description}} | {{paper_id}} | {{NOVEL / ADAPTED / STANDARD}} | {{ACTIVE / EXTRACTED / RETIRED}} | {{where_it_lands}} |
| K-002 | {{kernel}} | {{paper_id}} | {{novelty}} | {{status}} | {{destination}} |
<!-- Every kernel. No cap. -->

### Duplicate / overlapping kernels

<!-- Kernels that appear in more than one paper. Which version wins? -->

| Kernel | Appears in | Best version | Why it wins | Others retire? |
|---|---|---|---|---|
| {{kernel}} | {{paper_id_1, paper_id_2}} | {{paper_id}} | {{reason}} | {{yes/no — if no, explain}} |

### Retired kernels

<!-- Kernels superseded by better versions elsewhere. Kept for the record. -->

| Kernel | Original paper | Superseded by | Reason |
|---|---|---|---|
| {{kernel}} | {{paper_id}} | {{superseding_paper_or_kernel}} | {{reason}} |

---

## Claim consolidation

<!-- All claims across all papers, deduplicated. Claims that appear in
     multiple papers get ONE row with all sources listed. Contradictions
     between papers are flagged explicitly. -->

| Consolidated claim | Source papers | Register | Load-bearing | Best support | Best objection | Balance | Contradicted by |
|---|---|---|---|---|---|---|---|
| {{claim_text}} | {{paper_id_1, paper_id_2}} | {{NATIVE/BRIDGE/DERIVED}} | {{yes/no}} | {{best_evidence_across_all_papers}} | {{best_objection_across_all_papers}} | {{aggregate_balance}} | {{paper_id if any paper contradicts this, else "none"}} |

### Internal contradictions

<!-- Claims within the series that contradict each other. This is the
     disagreement layer — where the series fights itself. -->

| Claim A (paper) | Claim B (paper) | Nature of contradiction | Which survives | Ruling basis |
|---|---|---|---|---|
| {{claim_A}} ({{paper_id}}) | {{claim_B}} ({{paper_id}}) | {{what_conflicts}} | {{A / B / UNRESOLVED}} | {{evidence / logic / governance_rule}} |

---

## Cross-paper evidence

<!-- Evidence that spans papers — support in one paper for a claim in another.
     This is where the series becomes more than the sum of its parts. -->

| Evidence (source paper) | Supports claim in (target paper) | Strength | Family |
|---|---|---|---|
| {{evidence}} ({{paper_id}}) | {{claim}} in {{paper_id}} | {{STRONG / MODERATE / WEAK}} | {{family_id_or_new}} |

---

## Structural spine

<!-- The argument of the series as a whole. Not a summary — the actual
     logical structure. What does paper 1 establish that paper 2 needs?
     What's the dependency chain across papers? -->

### Series argument (numbered steps with paper sources)

1. {{step}} — established in {{paper_id}} `{{ORIGINAL | CLASSICAL:<source> | STANDARD}}`
2. {{step}} — established in {{paper_id}} `{{provenance}}`
3. {{step}} — established in {{paper_id}} `{{provenance}}`
4. {{therefore}} `{{provenance}}`

### Paper dependency chain

<!-- Which papers depend on which? If paper 5 falls, which others are exposed? -->

```
{{paper_1}} ──► {{paper_3}} ──► {{paper_7}}
{{paper_2}} ──► {{paper_3}}
{{paper_4}} (independent)
{{paper_5}} ──► {{paper_6}} ──► {{paper_7}}
```

| Paper | Depends on | If this falls, exposed papers |
|---|---|---|
| {{paper_id}} | {{dependency_paper_ids}} | {{downstream_paper_ids}} |

---

## Truth predicate consolidation

<!-- All truth predicates from all papers, deduplicated. The series-level
     predicate inventory. -->

| # | Truth predicate | Source paper(s) | Warrant | Appears in N papers |
|---|---|---|---|---|
| SP-001 | {{predicate}} | {{paper_ids}} | {{warrant}} | {{count}} |
<!-- Every unique predicate across the series. Duplicates collapsed. -->

**Series totals:** {{count}} unique predicates from {{count}} total ({{count}} duplicates removed).

---

## Bridge inventory (series-wide)

<!-- All bridges across all papers. Are there bridges that span papers? -->

| Bridge | Source domain → Target domain | Paper | Word-gate | Grade | Shared with other papers? |
|---|---|---|---|---|---|
| {{bridge}} | {{domain_A}} → {{domain_B}} | {{paper_id}} | {{word_gate}} | {{grade}} | {{yes: paper_ids / no}} |

---

## Destination map

<!-- Where does everything land? This is the extraction map —
     what goes into the main work, what stands alone, what retires. -->

| Paper | Verdict | Destination | Key content moving | What gets cut |
|---|---|---|---|---|
| {{paper_id}} | {{INTO_MAIN / STANDALONE / RETIRE}} | {{where_it_goes}} | {{kernels_and_claims_that_move}} | {{what_doesnt_survive}} |

### By destination

| Destination | Source papers | Key content |
|---|---|---|
| {{destination_1}} | {{paper_ids}} | {{what_lands_there}} |
| {{destination_2}} | {{paper_ids}} | {{content}} |

---

## Gap analysis

<!-- What's MISSING from the series? What should be there but isn't? -->

### Logical gaps
| Gap | Between papers | What's needed | Priority |
|---|---|---|---|
| {{gap_description}} | {{paper_id}} → {{paper_id}} | {{what_would_fill_it}} | {{HIGH / MEDIUM / LOW}} |

### Domain gaps
| Domain | Coverage in series | What's missing |
|---|---|---|
| {{domain}} | {{STRONG / PARTIAL / ABSENT}} | {{what_the_series_doesn't_address}} |

### Unanswered questions (series-level)
| Question | Raised in | Not answered in | Priority |
|---|---|---|---|
| {{question}} | {{paper_id}} | {{any paper}} | {{priority}} |

---

## Series audit

| What held (across the series) | What broke | What's overstated | Defensible version | Blast radius |
|---|---|---|---|---|
| {{held}} | {{broke}} | {{overstated}} | {{defensible}} | INERT / LOCAL / STRUCTURAL |

---

## Series dashboard

```dataview
TABLE WITHOUT ID
  file.link AS Paper,
  clean_title AS Title,
  paper_rating AS Rating,
  evd_balance AS Balance,
  evd_state AS State,
  evd_coverage AS Coverage
FROM ""
WHERE type = "evidence-sheet" AND contains(this.paper_ids, paper_id)
SORT paper_rating DESC
```

---

_POF 2828 · not a probability of truth · human ruling required_

<!-- @template layer=series version=0.3 end -->
