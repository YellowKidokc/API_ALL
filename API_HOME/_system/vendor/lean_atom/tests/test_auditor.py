"""Tests for trust auditor (sorry, admit, custom axioms)."""

from lean_atom.config import TrustConfig
from lean_atom.runner.auditor import TrustAuditor


def test_auditor_detects_sorry():
    auditor = TrustAuditor(TrustConfig())
    decl = {
        "declaration_kind": "theorem",
        "fully_qualified_name": "Test.unproven",
        "formal_statement": "theorem unproven : 1 = 1",
        "proof_script": "by sorry"
    }
    res = auditor.audit_declaration(decl)
    assert res["sorry_count"] == 1
    assert "CONTAINS_SORRY" in res["trust_statuses"]
    assert res["trust_status"] == "PROOF_ESCAPE"


def test_auditor_detects_custom_axiom():
    auditor = TrustAuditor(TrustConfig())
    decl = {
        "declaration_kind": "axiom",
        "fully_qualified_name": "Test.my_axiom",
        "formal_statement": "axiom my_axiom : ∃ x, x = 0",
        "proof_script": ""
    }
    res = auditor.audit_declaration(decl)
    assert "CUSTOM_AXIOMS" in res["trust_statuses"]
    assert "Test.my_axiom" in res["custom_axioms"]


def test_auditor_clean_proof():
    auditor = TrustAuditor(TrustConfig())
    decl = {
        "declaration_kind": "theorem",
        "fully_qualified_name": "Test.clean",
        "formal_statement": "theorem clean : True",
        "proof_script": "by trivial"
    }
    res = auditor.audit_declaration(decl)
    assert res["sorry_count"] == 0
    assert res["trust_status"] == "CLEAN"
    assert "CLEAN" in res["trust_statuses"]
