"""Data models for Lean 4 Atom Record Schema 1.0."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# --- Controlled Classification Enums ---

class Applicability(str, Enum):
    FORMALIZABLE = "FORMALIZABLE"
    PARTIAL = "PARTIAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class FormalizationStatus(str, Enum):
    NONE = "NONE"
    TARGET = "TARGET"
    DRAFT = "DRAFT"
    PARSES = "PARSES"
    CHECKED = "CHECKED"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


class LogicalRole(str, Enum):
    PRIMITIVE = "PRIMITIVE"
    ASSUMPTION = "ASSUMPTION"
    DEFINITIONAL = "DEFINITIONAL"
    DERIVED = "DERIVED"
    EQUIVALENCE = "EQUIVALENCE"
    EXISTENCE = "EXISTENCE"
    UNIQUENESS = "UNIQUENESS"
    IMPOSSIBILITY = "IMPOSSIBILITY"
    CONSISTENCY = "CONSISTENCY"
    INDEPENDENCE = "INDEPENDENCE"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    MODEL_WITNESS = "MODEL_WITNESS"


class ReasoningRegime(str, Enum):
    CONSTRUCTIVE = "CONSTRUCTIVE"
    CLASSICAL = "CLASSICAL"
    NONCOMPUTABLE = "NONCOMPUTABLE"
    DECIDABLE = "DECIDABLE"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class BuildResult(str, Enum):
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    TOOLCHAIN_MISMATCH = "TOOLCHAIN_MISMATCH"


class TrustStatus(str, Enum):
    CLEAN = "CLEAN"
    CONTAINS_SORRY = "CONTAINS_SORRY"
    CONTAINS_ADMIT = "CONTAINS_ADMIT"
    CUSTOM_AXIOMS = "CUSTOM_AXIOMS"
    UNSAFE_FEATURE = "UNSAFE_FEATURE"
    PROOF_ESCAPE = "PROOF_ESCAPE"
    AUDIT_REQUIRED = "AUDIT_REQUIRED"


class CorrespondenceStatus(str, Enum):
    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    MODEL_ONLY = "MODEL_ONLY"
    PROPOSED = "PROPOSED"
    DISPUTED = "DISPUTED"
    MISMATCH = "MISMATCH"
    UNASSESSED = "UNASSESSED"


class FormalResult(str, Enum):
    PROVED_IN_SYSTEM = "PROVED_IN_SYSTEM"
    REFUTED = "REFUTED"
    COUNTERMODEL_FOUND = "COUNTERMODEL_FOUND"
    CONSISTENCY_RELATIVE = "CONSISTENCY_RELATIVE"
    SATISFIABLE_WITNESS = "SATISFIABLE_WITNESS"
    INCONCLUSIVE = "INCONCLUSIVE"
    NO_RESULT = "NO_RESULT"


class DeclarationKind(str, Enum):
    AXIOM = "axiom"
    DEF = "def"
    THEOREM = "theorem"
    LEMMA = "lemma"
    STRUCTURE = "structure"
    CLASS = "class"
    INSTANCE = "instance"
    INDUCTIVE = "inductive"
    ABBREV = "abbrev"
    EXAMPLE = "example"


# --- Atom Record Sub-Schemas ---

class SourceInfo(BaseModel):
    file: str = ""
    relative_path: str = ""
    source_hash: str = ""
    start_line: Optional[int] = None
    end_line: Optional[int] = None


class LeanInfo(BaseModel):
    project: str = ""
    module: str = ""
    namespace: str = ""
    declaration_kind: str = ""
    declaration_name: str = ""
    fully_qualified_name: str = ""
    formal_statement: str = ""
    variables: List[str] = Field(default_factory=list)
    types: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    definitions_used: List[str] = Field(default_factory=list)
    premises_used: List[str] = Field(default_factory=list)
    custom_axioms: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    theorem_lineage: List[str] = Field(default_factory=list)


class ClassificationInfo(BaseModel):
    applicability: Applicability = Applicability.UNKNOWN
    formalization_status: FormalizationStatus = FormalizationStatus.NONE
    logical_roles: List[LogicalRole] = Field(default_factory=list)
    reasoning_regimes: List[ReasoningRegime] = Field(default_factory=list)
    formal_result: FormalResult = FormalResult.NO_RESULT
    trust_statuses: List[TrustStatus] = Field(default_factory=lambda: [TrustStatus.AUDIT_REQUIRED])


class ProofInfo(BaseModel):
    method: str = ""
    proof_term_or_tactics: str = ""
    failed_attempts: List[str] = Field(default_factory=list)
    countermodels: List[str] = Field(default_factory=list)


class VerificationInfo(BaseModel):
    lean_version: str = ""
    toolchain_version: str = ""
    build_command: str = ""
    build_result: BuildResult = BuildResult.NOT_RUN
    checked_at: str = ""
    stdout: str = ""
    stderr: str = ""
    receipt_hash: str = ""
    sorry_count: int = 0
    admit_count: int = 0
    proof_escapes: List[str] = Field(default_factory=list)


class SemanticsInfo(BaseModel):
    natural_language_statement: str = ""
    domains: List[str] = Field(default_factory=list)
    object_type: str = ""
    role: str = ""
    correspondence_status: CorrespondenceStatus = CorrespondenceStatus.UNASSESSED
    interpretation_boundary: str = ""
    proves: List[str] = Field(default_factory=list)
    does_not_prove: List[str] = Field(default_factory=list)
    bridge_candidates: List[str] = Field(default_factory=list)


class ProvenanceInfo(BaseModel):
    mechanical_fields: List[str] = Field(default_factory=list)
    ai_generated_fields: List[str] = Field(default_factory=list)
    human_reviewed_fields: List[str] = Field(default_factory=list)
    ai_provider: str = ""
    model: str = ""
    prompt_version: str = ""
    classified_at: str = ""


# --- Master Atom Record (Schema 1.0) ---

class AtomRecord(BaseModel):
    id: str = ""
    schema_version: str = "1.0"
    source: SourceInfo = Field(default_factory=SourceInfo)
    lean: LeanInfo = Field(default_factory=LeanInfo)
    classification: ClassificationInfo = Field(default_factory=ClassificationInfo)
    proof: ProofInfo = Field(default_factory=ProofInfo)
    verification: VerificationInfo = Field(default_factory=VerificationInfo)
    semantics: SemanticsInfo = Field(default_factory=SemanticsInfo)
    provenance: ProvenanceInfo = Field(default_factory=ProvenanceInfo)
