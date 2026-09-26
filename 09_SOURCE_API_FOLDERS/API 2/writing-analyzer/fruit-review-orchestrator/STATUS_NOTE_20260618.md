# Writing Analyzer — Orchestrator Handoff Note (2026-06-18)

## Current status (as of tonight)
- Extraction pipeline is healthy and complete:
  - `features\feature_packets.jsonl` generated (56 packets)
  - `features\feature_summary.json`
  - `features\feature_bundle.xlsx`
- Path setup used:
  - Input work-in:
    - `X:\06_ENGINES\writing-analyzer\fruit-review-orchestrator\work_input`
  - Local 7Q files:
    - `X:\06_ENGINES\writing-analyzer\fruit-review-orchestrator\q7q_local\`
  - Wrapper:
    - `q7q_local_wrapper.py`
    - `features` extraction command now works via package-safe entrypoint (`python -m q7q_local.chi_evaluator_7q`)

## Known issues still open
- `run_review_models.py` has a syntax/indentation error near around line 321 and currently won’t execute.
- `config.txt` currently has placeholder API keys (`sk-PASTE-YOUR-KEY-HERE`), so live model calls won’t run until real keys are provided.
- Earlier runs had stale duplicates because output/inputs mixed `.json` noise; now cleaned into `work_input` with 56 `.md` files only.

## Last successful commands
```bash
python feature_extractor.py --source-dir "X:\06_ENGINES\writing-analyzer\fruit-review-orchestrator\work_input" --workbook "X:\06_ENGINES\writing-analyzer\fruit-review-orchestrator\q7q_local\7Q_Full_Method.xlsx" --evaluator "X:\06_ENGINES\writing-analyzer\fruit-review-orchestrator\q7q_local_wrapper.py" --out-dir features
```

## Next-step plan (resume tomorrow)
1. Fix `run_review_models.py` indentation/syntax around `main()` near line ~321.
2. Run model review:
   ```bash
   python run_review_models.py --packets "features\\feature_packets.jsonl" --reviews-dir reviews --top-models openai,deepseek --run-id manual_run
   ```
3. Run comparison:
   ```bash
   python compare_reviews.py --packets "features\\feature_packets.jsonl" --reviews "reviews\\run_manual_run\\model_reviews.jsonl" --out compare
   ```
4. Produce final outputs:
   - `reviews\\run_manual_run\\model_reviews.xlsx`
   - `compare\\comparison.xlsx`
   - `compare\\comparison_disagreements.csv`

## Quick rule for the day
Only 2 files in final review pass:
- Python engine output (JSON/Excel bundles)
- Excel as single source, HTML later
