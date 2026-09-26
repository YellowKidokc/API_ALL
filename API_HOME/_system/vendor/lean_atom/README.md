# Lean 4 Corpus Scanner & Atom Record Extractor (`lean-atom-extractor`)

A production-grade Python application that scans a Lean 4 repository, extracts every declaration into a normalized SQLite registry, executes compiler builds and trust audits (`sorry`, `admit`, custom axioms), optionally enriches semantic interpretation via AI with strict provenance quarantines, exports standardized **Atom JSON Records (Schema 1.0)**, and provides a quiet, high-density web dashboard.

---

## Core Principles

1. **Separation of Verified Facts from AI Interpretations**:
   - Python and the Lean compiler produce mechanical facts (AST signatures, exit codes, receipts, `sorry` counts).
   - AI may classify meaning, domain, correspondence, and interpretation boundaries.
   - AI classifications are never reported as Lean-verified facts and carry strict provenance.
2. **Read-Only Source Guarantee**:
   - Source `.lean` files are never modified.
3. **Incremental Processing**:
   - Uses SHA-256 file hashing to skip unchanged files unless `--force` is provided.

---

## Installation & Setup

```bash
cd d:\GitHub\lean-atom-extractor
pip install -r requirements.txt
pip install -e .
```

---

## CLI Commands

```bash
# 1. Discover files, modules, namespaces, and declarations
lean-atom scan

# 2. Force re-scan of all files even if unchanged
lean-atom scan --force

# 3. Populate deterministic classifications (logical roles, reasoning regimes)
lean-atom classify

# 4. Run compiler verification and record SHA-256 receipts
lean-atom verify

# 5. Audit declarations for trust escapes (sorry, admit, custom axioms)
lean-atom audit

# 6. Request optional AI semantic enrichment (Ollama / Cloudflare / OpenRouter)
lean-atom enrich --limit 20

# 7. Export standardized Atom JSON records (Schema 1.0)
lean-atom export --out ./exports

# 8. Launch the local high-density web interface
lean-atom serve --port 8989
```

---

## Architecture

- `lean_atom/models.py`: Pydantic models strictly matching Schema 1.0.
- `lean_atom/scanner/`: File scanner and Lean 4 declaration parser for all 10 declaration kinds (`axiom`, `def`, `theorem`, `lemma`, `structure`, `class`, `instance`, `inductive`, `abbrev`, `example`).
- `lean_atom/runner/`: Safe compiler subprocess runner (`lake build`, `lean`) and trust auditor.
- `lean_atom/db/`: 10 normalized SQLite tables with versioned migrations and stable declaration IDs (`project:rel_path:fq_name`).
- `lean_atom/ai/`: Provider interface with schema validation and strict quarantine for malformed outputs.
- `lean_atom/exporter/`: Deterministic JSON record generator.
- `lean_atom/web/`: Quiet spreadsheet UI with filters, verified/AI visual separation, and export modal.

---

## Running Tests

```bash
pytest
```
