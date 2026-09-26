"""Tests for Lean extractor and namespace parser."""

from pathlib import Path
from lean_atom.scanner.extractor import LeanExtractor


def test_extractor_sample_file():
    sample_path = Path(__file__).parent / "fixtures" / "sample_lean_project" / "Sample.lean"
    text = sample_path.read_text(encoding="utf-8")

    decls = LeanExtractor.extract_declarations(text, "Sample.lean")
    assert len(decls) >= 6

    # Test names and namespaces
    names = [d["fully_qualified_name"] for d in decls]
    assert "SampleFixture.Math.existence_floor" in names
    assert "SampleFixture.Math.StateProfile" in names
    assert "SampleFixture.Math.Measureable" in names
    assert "SampleFixture.Math.SubModule.sum_positive" in names
    assert "SampleFixture.Math.SubModule.unresolved_boundary" in names

    # Test multiline statement capture
    sum_thm = next(d for d in decls if d["declaration_name"] == "sum_positive")
    assert "a + b > 0" in sum_thm["formal_statement"]
    assert "omega" in sum_thm["proof_script"]

    # Test axiom kind
    axiom_decl = next(d for d in decls if d["declaration_name"] == "existence_floor")
    assert axiom_decl["declaration_kind"] == "axiom"

    # Test structure kind
    struct_decl = next(d for d in decls if d["declaration_name"] == "StateProfile")
    assert struct_decl["declaration_kind"] == "structure"
