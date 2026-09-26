# MASTER INDEX FORMAT — v0.3 (TAB-DELIMITED RUNNING LIST)
**POF 2828 | 2026-09-14 | canonical copy: 999_TEMPLATES/API_LAYER_v0.3**
*The running index. Tab-delimited. One row per paper. Python-proof:
every column has a source map saying exactly which file, which heading,
and which @marker it reads from. Joined to paper + claims layer on
source_sha256 end to end.*

<!-- @template layer=index version=0.3 -->

---

## Column contract

<!-- TAB-DELIMITED. One header row, then one row per paper.
     Every value is read from a specific location — no inference, no
     aggregation across files unless the source map says so.
     Parsers: split on \t, not comma. Quote fields containing tabs. -->

### Column definitions

| # | Column name | Type | Source file | Source location | Notes |
|---|---|---|---|---|---|
| 1 | `paper_id` | string | paper YAML | `paper_id:` | slug + short hash, primary key |
| 2 | `source_sha256` | string | paper YAML | `source_sha256:` | joins paper → claims layer → index |
| 3 | `clean_title` | string | paper YAML | `clean_title:` | |
| 4 | `chapter` | string | paper YAML | `chapter:` | ONE_STORY key or null |
| 5 | `content_type` | enum | paper YAML | `content_type:` | closed vocabulary |
| 6 | `domain` | enum | paper YAML | `domain:` | closed ~16 |
| 7 | `reader_category` | enum | paper YAML | `reader_category:` | closed ~10 |
| 8 | `governing_question` | string | paper YAML | `governing_question:` | |
| 9 | `one_sentence_finding` | string | paper YAML | `one_sentence_finding:` | |
| 10 | `paper_rating` | int | paper YAML | `paper_rating:` | -10..+10, cap rule |
| 11 | `rating_awarded_by` | enum | paper YAML | `rating_awarded_by:` | API / HUMAN:<name> / LEAN:<id> |
| 12 | `evidence_status` | enum | paper YAML | `evidence_status:` | CANDIDATE / AUDITED / APPROVED |
| 13 | `formal_status` | enum | paper YAML | `formal_status:` | NOT_ESTABLISHED / TARGETS_QUEUED / RECEIPTED |
| 14 | `evd_state` | enum | paper YAML | `evd_state:` | UNSCORED / SCORED / GATED |
| 15 | `evd_support` | int | paper YAML | `evd_support:` | |
| 16 | `evd_counter` | int | paper YAML | `evd_counter:` | |
| 17 | `evd_balance` | float/null | paper YAML | `evd_balance:` | null while UNSCORED/GATED |
| 18 | `evd_families` | int | paper YAML | `evd_families:` | |
| 19 | `evd_coverage` | float | paper YAML | `evd_coverage:` | 0.00–1.00, from deferral section |
| 20 | `evd_gated` | bool | paper YAML | `evd_gated:` | |
| 21 | `evd_stable` | bool/null | paper YAML | `evd_stable:` | |
| 22 | `evd_weakest_claim` | string | paper YAML | `evd_weakest_claim:` | |
| 23 | `coherence` | int/null | paper YAML | `coherence:` | 0-5, separate axis |
| 24 | `physical_event` | string | paper YAML | `physical_event:` | |
| 25 | `total_claims` | int | claims layer | `Layer integrity > Total claims` | |
| 26 | `claims_with_falsifiers` | int | claims layer | `Layer integrity > Claims with falsifiers` | |
| 27 | `hidden_premises` | int | claims layer | `Layer integrity > Hidden premises found` | |
| 28 | `lean_targets_queued` | int | claims layer | `Layer integrity > Lean targets queued` | |
| 29 | `predictions_logged` | int | claims layer | `Layer integrity > Predictions logged` | |
| 30 | `bridges_registered` | int | claims layer | `Layer integrity > Bridges registered` | |
| 31 | `bridges_blank_lost` | int | claims layer | `Layer integrity > Bridges with blank LOST column` | must be 0 |
| 32 | `truth_predicates` | int | paper body | `Extraction completeness check > {{count}} predicates` | |
| 33 | `source_paragraphs` | int | paper body | `Extraction completeness check > {{count}} source paragraphs` | |
| 34 | `original_argument_steps` | int | paper body | `Argument score > Originality > count ORIGINAL` | |
| 35 | `total_argument_steps` | int | paper body | `Argument score > Originality > count total` | |
| 36 | `supplementary_arguments` | int | paper body | count of `**Supplementary argument N**` blocks | |
| 37 | `weak_links_identified` | int | paper body | row count in `Argument strengthening` table | |
| 38 | `semantic_provider` | string | paper YAML | `semantic_provider:` | |
| 39 | `semantic_model` | string | paper YAML | `semantic_model:` | |
| 40 | `processed_date` | date | paper YAML | `processed_date:` | |
| 41 | `tags` | string[] | paper YAML | `tags:` | comma-joined inside quotes |
| 42 | `claim_ids` | string[] | paper YAML | `claim_ids:` | comma-joined inside quotes |
| 43 | `lean_receipts` | string[] | paper YAML | `lean_receipts:` | comma-joined inside quotes |

---

## Source map

<!-- THE PYTHON-PROOF PART. For every column, exactly which file to open
     and which regex/marker to read. A parser that follows this map will
     produce the index without any human judgment calls. -->

```
SOURCE MAP — v0.3
=================

For paper P with source_sha256 = S:

  PAPER FILE:  the .md file whose YAML contains `source_sha256: S`
  CLAIMS FILE: the .md file whose YAML contains `type: claims_layer` AND `source_sha256: S`

  Columns 1–24, 38–43:
    Open PAPER FILE → parse YAML frontmatter → read field by column name.
    Field names match exactly (paper_id, source_sha256, clean_title, etc.)

  Columns 25–31:
    Open CLAIMS FILE → find heading "## Layer integrity"
    → parse the markdown table beneath it
    → read "Value" column by row label matching column name
    (total_claims, claims_with_falsifiers, hidden_premises,
     lean_targets_queued, predictions_logged, bridges_registered,
     bridges_blank_lost)

  Columns 32–33:
    Open PAPER FILE → find blockquote starting with
    "**Extraction completeness check**"
    → regex: /(\d+) predicates extracted from (\d+) source paragraphs/
    → group 1 = truth_predicates, group 2 = source_paragraphs

  Columns 34–35:
    Open PAPER FILE → find heading "### Argument score assessment"
    → find row where Metric = "Originality"
    → read "Current" cell → regex: /(\d+)\s*\/\s*(\d+)/
    → group 1 = original_argument_steps, group 2 = total_argument_steps

  Column 36:
    Open PAPER FILE → count occurrences of /^\*\*Supplementary argument \d+\*\*/
    → supplementary_arguments = count

  Column 37:
    Open PAPER FILE → find heading "### Argument strengthening"
    → count data rows in the table beneath it (exclude header + separator)
    → weak_links_identified = count
```

---

## Example row (tab-delimited)

```tsv
paper_id	source_sha256	clean_title	chapter	content_type	domain	reader_category	governing_question	one_sentence_finding	paper_rating	rating_awarded_by	evidence_status	formal_status	evd_state	evd_support	evd_counter	evd_balance	evd_families	evd_coverage	evd_gated	evd_stable	evd_weakest_claim	coherence	physical_event	total_claims	claims_with_falsifiers	hidden_premises	lean_targets_queued	predictions_logged	bridges_registered	bridges_blank_lost	truth_predicates	source_paragraphs	original_argument_steps	total_argument_steps	supplementary_arguments	weak_links_identified	semantic_provider	semantic_model	processed_date	tags	claim_ids	lean_receipts
```

---

## Validation rules

<!-- Parser runs these after building each row. Failures are logged, not silently fixed. -->

| Rule | Check | On fail |
|---|---|---|
| V1 | `source_sha256` in index matches paper YAML matches claims layer YAML | HARD FAIL — files are mismatched |
| V2 | `bridges_blank_lost` == 0 | WARNING — claims layer has incomplete bridges |
| V3 | `evd_balance` is null when `evd_state` is UNSCORED or GATED | HARD FAIL — balance faked |
| V4 | `paper_rating` ≤ 8 when `rating_awarded_by` starts with "API" | HARD FAIL — cap rule violated |
| V5 | `paper_rating` ≤ 9 when `rating_awarded_by` starts with "HUMAN" | HARD FAIL — cap rule violated |
| V6 | `paper_rating` == 10 only when `rating_awarded_by` starts with "LEAN" | HARD FAIL — cap rule violated |
| V7 | `total_claims` > 0 | WARNING — paper has no claims extracted |
| V8 | `truth_predicates` > 0 | WARNING — exhaustive extraction found nothing |
| V9 | `lean_targets_queued` ≤ `total_claims` | HARD FAIL — more targets than claims |
| V10 | `claims_with_falsifiers` ≤ `total_claims` | HARD FAIL — arithmetic |
| V11 | every `claim_id` in `claim_ids` array exists as a row in claims layer Claims table | HARD FAIL — dangling reference |
| V12 | `evd_coverage` == 1.0 - (deferred_count / total_questions) | WARNING — coverage doesn't match deferral section |

---

## Join diagram

```
┌─────────────────────┐     source_sha256     ┌──────────────────────┐
│   PAPER FILE        │◄────────────────────►│   CLAIMS LAYER FILE  │
│   (YAML + body)     │                       │   (claims, bridges,  │
│                     │                       │    predictions, etc.) │
│   Cols 1–24, 32–43  │                       │   Cols 25–31         │
└─────────┬───────────┘                       └──────────┬───────────┘
          │                                              │
          │              source_sha256                   │
          └──────────────────┬───────────────────────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │  MASTER INDEX   │
                   │  (this file)    │
                   │  Cols 1–43      │
                   │  one row/paper  │
                   └─────────────────┘
```

---

## Parser contract

1. Walk all `.md` files in the output directory.
2. For each file with YAML `type: axiom_companion` (or `type: evidence-sheet`), treat as a PAPER FILE.
3. For each PAPER FILE, read `source_sha256` from YAML.
4. Find the CLAIMS FILE: the `.md` with `type: claims_layer` and matching `source_sha256`.
5. If no CLAIMS FILE found: columns 25–31 = null, log WARNING.
6. Read all columns per the source map above.
7. Run validation rules V1–V12.
8. Emit one TSV row.
9. After all papers: emit header row + all data rows, sorted by `chapter` then `paper_id`.

---

_POF 2828 · not a probability of truth · human ruling required_

<!-- @template layer=index version=0.3 end -->
