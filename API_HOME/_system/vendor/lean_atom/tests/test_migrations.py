"""Tests for SQLite database migrations and schema."""

import tempfile
from pathlib import Path
from lean_atom.db.migrations import apply_migrations, get_connection


def test_migrations_create_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        ver = apply_migrations(db_path)
        assert ver == 1

        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row["name"] for row in cursor.fetchall()}

        expected_tables = {
            "schema_migrations",
            "projects",
            "source_files",
            "declarations",
            "dependencies",
            "builds",
            "trust_findings",
            "classifications",
            "ai_runs",
            "exports",
            "receipts"
        }
        assert expected_tables.issubset(tables)
        conn.close()
