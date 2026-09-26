"""Repository layer for SQLite operations."""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from .migrations import get_connection


from contextlib import contextmanager


def make_stable_id(project_name: str, rel_path: str, fq_name: str) -> str:
    """Generate canonical stable declaration ID: project:rel_path:fq_name."""
    # Normalize slashes
    clean_path = rel_path.replace("\\", "/")
    return f"{project_name}:{clean_path}:{fq_name}"


class Repository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def get_conn(self):
        conn = get_connection(self.db_path)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    # --- Projects & Files ---

    def upsert_project(self, project_id: str, name: str, root_path: str, config_hash: str = "") -> None:
        with self.get_conn() as conn:
            conn.execute("""
                INSERT INTO projects (id, name, root_path, config_hash)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    root_path=excluded.root_path,
                    config_hash=excluded.config_hash
            """, (project_id, name, root_path, config_hash))

    def get_source_file_hash(self, project_id: str, rel_path: str) -> Optional[str]:
        clean_path = rel_path.replace("\\", "/")
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT source_hash FROM source_files WHERE project_id = ? AND relative_path = ?",
                (project_id, clean_path)
            )
            row = cursor.fetchone()
            return row["source_hash"] if row else None

    def upsert_source_file(self, file_id: str, project_id: str, rel_path: str, source_hash: str) -> None:
        clean_path = rel_path.replace("\\", "/")
        with self.get_conn() as conn:
            conn.execute("""
                INSERT INTO source_files (id, project_id, relative_path, source_hash, is_active)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(project_id, relative_path) DO UPDATE SET
                    source_hash=excluded.source_hash,
                    last_scanned_at=CURRENT_TIMESTAMP,
                    is_active=1
            """, (file_id, project_id, clean_path, source_hash))

    # --- Declarations ---

    def upsert_declaration(self, data: Dict[str, Any]) -> str:
        decl_id = data["id"]
        with self.get_conn() as conn:
            conn.execute("""
                INSERT INTO declarations (
                    id, file_id, project_id, declaration_kind, declaration_name,
                    namespace, fully_qualified_name, formal_statement, proof_script,
                    variables_json, types_json, imports_json, start_line, end_line
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    file_id=excluded.file_id,
                    declaration_kind=excluded.declaration_kind,
                    declaration_name=excluded.declaration_name,
                    namespace=excluded.namespace,
                    formal_statement=excluded.formal_statement,
                    proof_script=excluded.proof_script,
                    variables_json=excluded.variables_json,
                    types_json=excluded.types_json,
                    imports_json=excluded.imports_json,
                    start_line=excluded.start_line,
                    end_line=excluded.end_line,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                decl_id,
                data["file_id"],
                data["project_id"],
                data["declaration_kind"],
                data["declaration_name"],
                data.get("namespace", ""),
                data["fully_qualified_name"],
                data["formal_statement"],
                data.get("proof_script", ""),
                json.dumps(data.get("variables", [])),
                json.dumps(data.get("types", [])),
                json.dumps(data.get("imports", [])),
                data.get("start_line"),
                data.get("end_line")
            ))

            # Ensure default classification row exists
            conn.execute("""
                INSERT OR IGNORE INTO classifications (declaration_id)
                VALUES (?)
            """, (decl_id,))

        return decl_id

    # --- Classifications ---

    def upsert_classification(self, decl_id: str, data: Dict[str, Any]) -> None:
        with self.get_conn() as conn:
            conn.execute("""
                INSERT INTO classifications (
                    declaration_id, applicability, formalization_status, logical_roles_json,
                    reasoning_regimes_json, statement_form, formal_result, trust_statuses_json,
                    correspondence_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(declaration_id) DO UPDATE SET
                    applicability=excluded.applicability,
                    formalization_status=excluded.formalization_status,
                    logical_roles_json=excluded.logical_roles_json,
                    reasoning_regimes_json=excluded.reasoning_regimes_json,
                    statement_form=excluded.statement_form,
                    formal_result=excluded.formal_result,
                    trust_statuses_json=excluded.trust_statuses_json,
                    correspondence_status=excluded.correspondence_status,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                decl_id,
                data.get("applicability", "UNKNOWN"),
                data.get("formalization_status", "NONE"),
                json.dumps(data.get("logical_roles", [])),
                json.dumps(data.get("reasoning_regimes", [])),
                data.get("statement_form", "UNCONDITIONAL"),
                data.get("formal_result", "NO_RESULT"),
                json.dumps(data.get("trust_statuses", ["AUDIT_REQUIRED"])),
                data.get("correspondence_status", "UNASSESSED")
            ))

    # --- Builds & Trust ---

    def record_build(self, decl_id: str, data: Dict[str, Any]) -> None:
        with self.get_conn() as conn:
            conn.execute("""
                INSERT INTO builds (
                    declaration_id, lean_version, toolchain_version, build_command,
                    build_result, stdout, stderr, exit_code, receipt_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decl_id,
                data.get("lean_version", ""),
                data.get("toolchain_version", ""),
                data.get("build_command", ""),
                data.get("build_result", "NOT_RUN"),
                data.get("stdout", ""),
                data.get("stderr", ""),
                data.get("exit_code", 0),
                data.get("receipt_hash", "")
            ))

    def record_trust_finding(self, decl_id: str, data: Dict[str, Any]) -> None:
        with self.get_conn() as conn:
            conn.execute("""
                INSERT INTO trust_findings (
                    declaration_id, trust_status, sorry_count, admit_count,
                    custom_axioms_json, proof_escapes_json, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                decl_id,
                data.get("trust_status", "AUDIT_REQUIRED"),
                data.get("sorry_count", 0),
                data.get("admit_count", 0),
                json.dumps(data.get("custom_axioms", [])),
                json.dumps(data.get("proof_escapes", [])),
                data.get("details", "")
            ))

    # --- Queries ---

    def list_declarations(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_conn() as conn:
            query = """
                SELECT d.*, f.relative_path, f.source_hash,
                       c.applicability, c.formalization_status, c.logical_roles_json,
                       c.reasoning_regimes_json, c.statement_form, c.formal_result,
                       c.trust_statuses_json, c.correspondence_status,
                       b.build_result, b.lean_version, b.receipt_hash,
                       t.trust_status as primary_trust_status, t.sorry_count, t.admit_count
                FROM declarations d
                JOIN source_files f ON d.file_id = f.id
                LEFT JOIN classifications c ON d.id = c.declaration_id
                LEFT JOIN (
                    SELECT declaration_id, build_result, lean_version, receipt_hash,
                           MAX(id) as max_id
                    FROM builds GROUP BY declaration_id
                ) b ON d.id = b.declaration_id
                LEFT JOIN (
                    SELECT declaration_id, trust_status, sorry_count, admit_count,
                           MAX(id) as max_id
                    FROM trust_findings GROUP BY declaration_id
                ) t ON d.id = t.declaration_id
            """
            params = []
            if project_id:
                query += " WHERE d.project_id = ?"
                params.append(project_id)
            query += " ORDER BY d.fully_qualified_name ASC"

            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_declaration(self, decl_id: str) -> Optional[Dict[str, Any]]:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.*, f.relative_path, f.source_hash, p.name as project_name,
                       c.applicability, c.formalization_status, c.logical_roles_json,
                       c.reasoning_regimes_json, c.statement_form, c.formal_result,
                       c.trust_statuses_json, c.correspondence_status
                FROM declarations d
                JOIN source_files f ON d.file_id = f.id
                JOIN projects p ON d.project_id = p.id
                LEFT JOIN classifications c ON d.id = c.declaration_id
                WHERE d.id = ?
            """, (decl_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
