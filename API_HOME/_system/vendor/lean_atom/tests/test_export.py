"""Tests for deterministic Atom JSON export against Schema 1.0."""

import json
import tempfile
from pathlib import Path
from lean_atom.models import AtomRecord
from lean_atom.exporter.atom_exporter import AtomExporter


def test_export_record_matches_schema():
    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = AtomExporter(tmpdir)

        fake_row = {
            "id": "Theophysics:Sample.lean:SampleFixture.Math.existence_floor",
            "project_name": "Theophysics",
            "relative_path": "Sample.lean",
            "source_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "start_line": 5,
            "end_line": 6,
            "declaration_kind": "axiom",
            "declaration_name": "existence_floor",
            "namespace": "SampleFixture.Math",
            "fully_qualified_name": "SampleFixture.Math.existence_floor",
            "formal_statement": "axiom existence_floor : ∃ (x : Nat), x = 0",
            "proof_script": "",
            "variables_json": "[]",
            "types_json": "[\"∃ (x : Nat), x = 0\"]",
            "imports_json": "[\"Init.Core\"]",
            "applicability": "FORMALIZABLE",
            "formalization_status": "CHECKED",
            "logical_roles_json": "[\"PRIMITIVE\"]",
            "reasoning_regimes_json": "[\"CONSTRUCTIVE\"]",
            "formal_result": "PROVED_IN_SYSTEM",
            "trust_statuses_json": "[\"CUSTOM_AXIOMS\"]",
            "lean_version": "Lean 4.30.0",
            "receipt_hash": "SHA256:abc123"
        }

        record = exporter.assemble_record(fake_row)
        assert isinstance(record, AtomRecord)
        assert record.schema_version == "1.0"
        assert record.id == "Theophysics:Sample.lean:SampleFixture.Math.existence_floor"
        assert record.lean.declaration_kind == "axiom"
        assert record.classification.trust_statuses == ["CUSTOM_AXIOMS"]

        out_path = exporter.export_record(record)
        assert out_path.exists()

        # Parse JSON and verify required top-level keys
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_keys = {
            "id", "schema_version", "source", "lean", "classification",
            "proof", "verification", "semantics", "provenance"
        }
        assert required_keys.issubset(set(data.keys()))
