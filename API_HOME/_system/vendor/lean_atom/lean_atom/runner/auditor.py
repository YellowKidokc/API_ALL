"""Trust and proof-escape auditor for Lean declarations."""

import re
from typing import Dict, List, Any
from ..config import TrustConfig


SORRY_REGEX = re.compile(r"\bsorry\b")
ADMIT_REGEX = re.compile(r"\badmit\b")
UNSAFE_REGEX = re.compile(r"\bunsafe\b")
BLOCK_COMMENT = re.compile(r"/-.*?-/", re.S)
LINE_COMMENT = re.compile(r"--[^\n]*")
STRING_LIT = re.compile(r'"(?:[^"\\]|\\.)*"')


def strip_comments(text: str) -> str:
    """Drop comments, docstrings and string literals so prose such as
    'constructors admit no recursion' is not counted as a tactic."""
    return LINE_COMMENT.sub("", STRING_LIT.sub('""', BLOCK_COMMENT.sub("", text)))


class TrustAuditor:
    def __init__(self, config: TrustConfig):
        self.config = config

    def audit_declaration(self, decl: Dict[str, Any]) -> Dict[str, Any]:
        """Audit a declaration for trust issues, sorries, admits, and custom axioms."""
        proof_text = decl.get("proof_script", "") or ""
        stmt_text = decl.get("formal_statement", "") or ""
        kind = (decl.get("declaration_kind", "") or "").lower()

        combined_text = strip_comments(f"{stmt_text}\n{proof_text}")

        sorry_matches = list(SORRY_REGEX.finditer(combined_text))
        sorry_count = len(sorry_matches)

        admit_matches = list(ADMIT_REGEX.finditer(combined_text))
        admit_count = len(admit_matches)

        has_unsafe = bool(UNSAFE_REGEX.search(strip_comments(stmt_text)))

        trust_statuses: List[str] = []
        custom_axioms: List[str] = []
        proof_escapes: List[str] = []
        details_list: List[str] = []

        if kind == "axiom":
            custom_axioms.append(decl.get("fully_qualified_name", ""))
            if self.config.flag_custom_axioms:
                trust_statuses.append("CUSTOM_AXIOMS")
                details_list.append("Declared as primitive axiom in Lean environment.")

        if sorry_count > 0 and self.config.flag_sorry:
            trust_statuses.append("CONTAINS_SORRY")
            details_list.append(f"Contains {sorry_count} 'sorry' placeholder(s).")

        if admit_count > 0 and self.config.flag_admit:
            trust_statuses.append("CONTAINS_ADMIT")
            details_list.append(f"Contains {admit_count} 'admit' tactic(s).")

        if has_unsafe and self.config.flag_unsafe:
            trust_statuses.append("UNSAFE_FEATURE")
            proof_escapes.append("unsafe")
            details_list.append("Uses 'unsafe' declaration keyword.")

        # Determine primary trust status
        if not trust_statuses:
            trust_statuses.append("CLEAN")
            primary_status = "CLEAN"
        elif "CONTAINS_SORRY" in trust_statuses or "CONTAINS_ADMIT" in trust_statuses:
            primary_status = "PROOF_ESCAPE"
        elif "CUSTOM_AXIOMS" in trust_statuses:
            primary_status = "CUSTOM_AXIOMS"
        else:
            primary_status = trust_statuses[0]

        return {
            "trust_status": primary_status,
            "trust_statuses": trust_statuses,
            "sorry_count": sorry_count,
            "admit_count": admit_count,
            "custom_axioms": custom_axioms,
            "proof_escapes": proof_escapes,
            "details": "; ".join(details_list) if details_list else "Zero trust escapes detected."
        }
