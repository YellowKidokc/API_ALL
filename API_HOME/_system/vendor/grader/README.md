# Paper Proof Grader

Deterministic first-pass tooling for reviewing papers and long-form technical/theological drafts.

This folder currently provides local scripts for:

- text extraction from plain text, Markdown, HTML, CSV, TSV, JSON, and XLSX inputs
- section, sentence, equation, and claim-candidate detection
- lightweight 7Q-style claim checks
- lexicon-based chi/Qi metric sidecars
- optional spaCy-backed entity extraction, with a deterministic fallback
- JSON, Markdown, HTML, CSV, and XLSX report exports

It is a structural audit helper. It does not prove truth, validate theology, establish experimental support, or replace expert review.

## Scripts

```text
pipeline.py
```

Batch workflow for files dropped into the configured input folder. It writes paper-grade reports, claim-audit CSV files, and archives processed source files.

```text
chi_qi_v5_metric_engine.py
```

Lexicon-based metric engine. Produces `.chi`, JSON, and CSV summaries with evidence spans and score metadata.

```text
nlp_deep_runner.py
```

Comparison lane for topics, top terms, entities, and key sentences. Uses spaCy when available and falls back to deterministic regex extraction.

```text
run_axiom_7q_stations.py
```

Post-processes generated `*.claim-audit.csv` files into forward/reverse 7Q station reports.

```text
expanded_report.py
```

Builds expanded Markdown/HTML reports from existing JSON outputs.

## Quick Start

Create the configured folders, place `.txt`, `.md`, `.html`, or `.htm` files in the input folder, then run:

```powershell
python pipeline.py
```

You can also run the metric engines directly:

```powershell
python chi_qi_v5_metric_engine.py --input .\README.md --out .\OUTPUT
python nlp_deep_runner.py --input .\README.md --out .\OUTPUT
```

## Configuration

The default paths live in `config.json`. They are intentionally simple local paths so the repo can run without private network shares.

## Current Boundaries

- Claim detection is heuristic and marker-based.
- Equation detection is notation-based and may overcount.
- 7Q labels are rule-based signals, not final judgments.
- Lexicon quality controls metric quality.
- Optional NLP libraries improve extraction, but the scripts still run without them.
