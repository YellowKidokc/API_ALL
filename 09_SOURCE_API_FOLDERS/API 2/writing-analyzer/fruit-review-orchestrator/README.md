# Fruit/Anti-Fruit Review Orchestrator

One-pass workflow for:
1. extracting χ/7Q claims into structured feature packets,
2. sending those packets to OpenAI + DeepSeek for **independent ratings**, and
3. comparing model ratings against the Python baseline.

This folder is intentionally standalone so it can be discarded after this experiment.

## Folder Layout

- `config.example.txt` — copy to `config.txt` and add API keys.
- `features/feature_packets.jsonl` — one JSON line per claim packet.
- `features/feature_summary.json` — run-level summary stats.
- `features/feature_bundle.xlsx` — Excel export of packet + packet summaries.
- `reviews/run_<id>/model_reviews.jsonl` — merged model outputs.
- `reviews/run_<id>/model_reviews.xlsx` — Excel export with one row per packet/model pair.
- `compare/comparison.jsonl` — packet-level comparison JSON.
- `compare/comparison_summary.json` — run-level comparison stats.
- `compare/comparison_disagreements.csv` — triage CSV.
- `compare/comparison.xlsx` — Excel export (comparison + summary tabs).
- `feature_extractor.py` — create feature packets from text files using 7Q/χ evaluator.
- `run_review_models.py` — send packets to DeepSeek and OpenAI.
- `compare_reviews.py` — score agreements/disagreement.
- `prompts/claim_review_prompt.txt` — model prompt template.

## Workflow

1. Put source files (txt/md/html/pdf->txt preferred) in `INBOX\`.
2. Copy `config.example.txt` to `config.txt` and add keys.
3. Build packets:
   ```powershell
   python feature_extractor.py --source-dir INBOX --workbook "\\dlowenas\h_hp\Desktop\7Q\7Q Full Method.xlsx" --out-dir features
   ```
4. Run model review:
   ```powershell
   python run_review_models.py --packets features/feature_packets.jsonl --reviews-dir reviews
   ```
   - This writes `reviews\\run_<id>\\model_reviews.xlsx`.
5. Compare:
   ```powershell
   python compare_reviews.py --packets features/feature_packets.jsonl --reviews reviews\\run_<run_id>\\model_reviews.jsonl --out compare
   ```
   - This writes `compare\\comparison.xlsx`.

## Notes

- Models are given only **ranking-style features** (claims + ordered fruit/anti-fruit variances), not scoring formulas.
- They can return any rubric they choose inside the requested output format.
- If no model key is present, that provider is skipped automatically.
- `ANTI_FRUIT_PENALTY` can be set in `config.txt` or overridden with `--anti-penalty` to increase/decrease anti-fruit drag.
