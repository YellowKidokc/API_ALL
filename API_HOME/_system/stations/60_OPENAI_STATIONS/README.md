# 60_OPENAI_STATIONS

The 23 api_call_NN prompts, grouped into bundles so one whole-document call answers several.

- Script: `60_openai_stations.py` (run it through `ONE_MENU.bat 60`)
- Works on: papers
- Menu options it accepts: limit, workers, provider, model, focus, redo
- Standing focus: `FOCUS.md` (2-4 lines; appended to every prompt this station sends)

## API goals

| id | title | asks for |
|---|---|---|
| `API-60.01` | LINGUISTICS_WORD_GAME | api_call_01 prompt (prompts/01_LINGUISTICS_WORD_GAME/prompt.txt) |
| `API-60.02` | FRAMEWORK_ALIGNMENT_CHI | api_call_02 prompt (prompts/02_FRAMEWORK_ALIGNMENT_CHI/prompt.txt) |
| `API-60.03` | READER_STRUCTURE | api_call_03 prompt (prompts/03_READER_STRUCTURE/prompt.txt) |
| `API-60.04` | CLAIMS_AND_ARGUMENT | api_call_04 prompt (prompts/04_CLAIMS_AND_ARGUMENT/prompt.txt) |
| `API-60.05` | PEER_REVIEW_44 | api_call_05 prompt (prompts/05_PEER_REVIEW_44/prompt.txt) |
| `API-60.06` | FRUITS_YUKAWA | api_call_06 prompt (prompts/06_FRUITS_YUKAWA/prompt.txt) |
| `API-60.07` | JUSTICE_MERCY_OPERATOR | api_call_07 prompt (prompts/07_JUSTICE_MERCY_OPERATOR/prompt.txt) |
| `API-60.08` | KNOWLEDGE_GRAPH | api_call_08 prompt (prompts/08_KNOWLEDGE_GRAPH/prompt.txt) |
| `API-60.09` | GLOSSARY | api_call_09 prompt (prompts/09_GLOSSARY/prompt.txt) |
| `API-60.10` | FINAL_REPORT | api_call_10 prompt (prompts/10_FINAL_REPORT/prompt.txt) |
| `API-60.11` | DOMAIN_PERCENTAGES | api_call_11 prompt (prompts/11_DOMAIN_PERCENTAGES/prompt.txt) |
| `API-60.12` | METADATA | api_call_12 prompt (prompts/12_METADATA/prompt.txt) |
| `API-60.13` | ISOMORPHISM_REGISTRY_HTML | api_call_13 prompt (prompts/13_ISOMORPHISM_REGISTRY_HTML/prompt.txt) |
| `API-60.14` | CANON_CLAIMS_JSON | api_call_14 prompt (prompts/14_CANON_CLAIMS_JSON/prompt.txt) |
| `API-60.15` | ISOMORPHISM_TEST_4_LEVEL | api_call_15 prompt (prompts/15_ISOMORPHISM_TEST_4_LEVEL/prompt.txt) |
| `API-60.16` | PROOF_MAP_JSON | api_call_16 prompt (prompts/16_PROOF_MAP_JSON/prompt.txt) |
| `API-60.17` | ADVERSARIAL_AUDIT | api_call_17 prompt (prompts/17_ADVERSARIAL_AUDIT/prompt.txt) |
| `API-60.18` | SEO | api_call_18 prompt (prompts/18_SEO/prompt.txt) |
| `API-60.19` | PAGE_SHELL_AUDIT | api_call_19 prompt (prompts/19_PAGE_SHELL_AUDIT/prompt.txt) |
| `API-60.20` | TRILEMMA_RESOLVER | api_call_20 prompt (prompts/20_TRILEMMA_RESOLVER/prompt.txt) |
| `API-60.21` | GREAT_GRADER | api_call_21 prompt (prompts/21_GREAT_GRADER/prompt.txt) |
| `API-60.22` | CLASSIFY_AXIOMIZE_ORGANIZE | api_call_22 prompt (prompts/22_CLASSIFY_AXIOMIZE_ORGANIZE/prompt.txt) |
| `API-60.23` | MATH_TRANSLATION_LAYER | api_call_23 prompt (prompts/23_MATH_TRANSLATION_LAYER/prompt.txt) |
| `API-60.B1` | BUNDLE_READER | one call answering: API-60.01, API-60.03, API-60.09, API-60.11, API-60.12 |
| `API-60.B2` | BUNDLE_GRADING | one call answering: API-60.05, API-60.17 |
| `API-60.B3` | BUNDLE_GREAT_GRADER | one call answering: API-60.21 |
| `API-60.B4` | BUNDLE_CLAIMS | one call answering: API-60.04, API-60.14, API-60.16, API-60.22 |
| `API-60.B5` | BUNDLE_FRAMEWORK | one call answering: API-60.02, API-60.06, API-60.07, API-60.15 |
| `API-60.B6` | BUNDLE_GRAPH | one call answering: API-60.08 |
| `API-60.B7` | BUNDLE_MATH | one call answering: API-60.23 |
| `API-60.B8` | BUNDLE_PUBLISHING | one call answering: API-60.18, API-60.19 |
| `API-60.B9` | BUNDLE_REGISTRY_HTML | one call answering: API-60.13 |
| `API-60.B10` | BUNDLE_FINAL | one call answering: API-60.10 |

## Outputs

Per item, in a dated folder that is never overwritten: `02_RUNS/60_OPENAI_STATIONS/<date>/` with `.json`, `.xlsx`, `.html`, `.run.json` (receipt: source hash, model, prompt version, focus text + hash, tokens, time, errors), `.md` where the station writes prose, `calls/<goal id>-<n>.json` (every reply), and `steps.log` (every step it took).
