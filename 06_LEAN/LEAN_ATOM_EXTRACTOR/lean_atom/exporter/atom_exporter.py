"""Deterministic Atom JSON Record Exporter."""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any
from ..models import AtomRecord, SourceInfo, LeanInfo, ClassificationInfo, ProofInfo, VerificationInfo, SemanticsInfo, ProvenanceInfo


class AtomExporter:
    def __init__(self, export_dir: str):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def assemble_record(self, row: Dict[str, Any], ai_data: Dict[str, Any] = None) -> AtomRecord:
        """Assemble standardized AtomRecord from database row and optional AI run."""
        # Source
        source = SourceInfo(
            file=Path(row.get("relative_path", "")).name,
            relative_path=row.get("relative_path", "").replace("\\", "/"),
            source_hash=row.get("source_hash", ""),
            start_line=row.get("start_line"),
            end_line=row.get("end_line")
        )

        # Parse JSON columns safely
        def safe_json_list(val):
            if isinstance(val, list):
                return val
            if not val:
                return []
            try:
                return json.loads(val)
            except Exception:
                return []

        # Lean
        lean = LeanInfo(
            project=row.get("project_name", "Theophysics"),
            module=Path(row.get("relative_path", "")).stem,
            namespace=row.get("namespace", "") or "",
            declaration_kind=row.get("declaration_kind", ""),
            declaration_name=row.get("declaration_name", ""),
            fully_qualified_name=row.get("fully_qualified_name", ""),
            formal_statement=row.get("formal_statement", ""),
            variables=safe_json_list(row.get("variables_json")),
            types=safe_json_list(row.get("types_json")),
            imports=safe_json_list(row.get("imports_json")),
            definitions_used=[],
            premises_used=[],
            custom_axioms=[row.get("fully_qualified_name")] if row.get("declaration_kind") == "axiom" else [],
            dependencies=[],
            theorem_lineage=[]
        )

        # Classification
        classification = ClassificationInfo(
            applicability=row.get("applicability", "UNKNOWN") or "UNKNOWN",
            formalization_status=row.get("formalization_status", "NONE") or "NONE",
            logical_roles=safe_json_list(row.get("logical_roles_json")),
            reasoning_regimes=safe_json_list(row.get("reasoning_regimes_json")),
            formal_result=row.get("formal_result", "NO_RESULT") or "NO_RESULT",
            trust_statuses=safe_json_list(row.get("trust_statuses_json")) or ["AUDIT_REQUIRED"]
        )

        # Proof
        proof = ProofInfo(
            method="TACTIC" if "by" in (row.get("proof_script") or "") else ("TERM" if row.get("proof_script") else ""),
            proof_term_or_tactics=row.get("proof_script", "") or "",
            failed_attempts=[],
            countermodels=[]
        )

        # Verification
        verification = VerificationInfo(
            lean_version=row.get("lean_version", "") or "",
            toolchain_version=row.get("toolchain_version", "") or "",
            build_command="lake build",
            build_result=row.get("build_result", "NOT_RUN") or "NOT_RUN",
            checked_at=row.get("checked_at", "") or "",
            stdout="",
            stderr="",
            receipt_hash=row.get("receipt_hash", "") or "",
            sorry_count=row.get("sorry_count", 0) or 0,
            admit_count=row.get("admit_count", 0) or 0,
            proof_escapes=[]
        )

        # Semantics
        ai_data = ai_data or {}
        semantics = SemanticsInfo(
            natural_language_statement=ai_data.get("natural_language_statement", ""),
            domains=ai_data.get("domains", ["MATHEMATICS"]),
            object_type=ai_data.get("object_type", "CLAIM"),
            role=ai_data.get("role", "AX_DERIVED"),
            correspondence_status=row.get("correspondence_status", "UNASSESSED") or "UNASSESSED",
            interpretation_boundary=ai_data.get("interpretation_boundary", ""),
            proves=ai_data.get("proves", []),
            does_not_prove=ai_data.get("does_not_prove", []),
            bridge_candidates=ai_data.get("bridge_candidates", [])
        )

        # Provenance
        mechanical_fields = [
            "id", "schema_version", "source", "lean", "proof.proof_term_or_tactics", "verification"
        ]
        ai_fields = list(ai_data.keys()) if ai_data else []

        provenance = ProvenanceInfo(
            mechanical_fields=mechanical_fields,
            ai_generated_fields=ai_fields,
            human_reviewed_fields=[],
            ai_provider=ai_data.get("provider", ""),
            model=ai_data.get("model", ""),
            prompt_version=ai_data.get("prompt_version", ""),
            classified_at=ai_data.get("classified_at", "")
        )

        record = AtomRecord(
            id=row["id"],
            schema_version="1.0",
            source=source,
            lean=lean,
            classification=classification,
            proof=proof,
            verification=verification,
            semantics=semantics,
            provenance=provenance
        )
        return record

    def export_record(self, record: AtomRecord) -> Path:
        """Write deterministic JSON file for single AtomRecord."""
        # Sanitize filename: replace colons, slashes
        clean_name = record.id.replace(":", "__").replace("/", "_").replace("\\", "_")
        out_path = self.export_dir / f"{clean_name}.atom.json"

        # Deterministic JSON with 2-space indentation
        json_str = record.model_dump_json(indent=2)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json_str)

        return out_path
