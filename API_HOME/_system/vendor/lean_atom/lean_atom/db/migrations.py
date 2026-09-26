"""SQLite database migrations engine."""

import sqlite3
from pathlib import Path
from typing import Optional


CURRENT_SCHEMA_VERSION = 1


def get_connection(db_path: str) -> sqlite3.Connection:
    """Open SQLite connection with row factory and foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_migrations(db_path: str, schema_sql_path: Optional[str] = None) -> int:
    """Apply schema migrations to ensure database is at current version."""
    if not schema_sql_path:
        schema_sql_path = str(Path(__file__).parent / "schema.sql")

    conn = get_connection(db_path)
    try:
        with conn:
            # Check schema_migrations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_migrations")
            row = cursor.fetchone()
            latest = row[0] if row and row[0] is not None else 0

            if latest < CURRENT_SCHEMA_VERSION:
                with open(schema_sql_path, "r", encoding="utf-8") as f:
                    sql = f.read()
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)",
                    (CURRENT_SCHEMA_VERSION,)
                )
                return CURRENT_SCHEMA_VERSION
            return latest
    finally:
        conn.close()
