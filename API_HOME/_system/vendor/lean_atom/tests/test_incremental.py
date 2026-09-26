"""Tests for incremental scanning and hash detection."""

import tempfile
from pathlib import Path
from lean_atom.db.migrations import apply_migrations
from lean_atom.db.repository import Repository
from lean_atom.scanner.file_scanner import compute_file_hash


def test_incremental_hash_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        apply_migrations(db_path)
        repo = Repository(db_path)

        test_file = Path(tmpdir) / "Test.lean"
        test_file.write_text("theorem t1 : True := by trivial", encoding="utf-8")
        h1 = compute_file_hash(test_file)

        proj_id = "TestProj"
        repo.upsert_project(proj_id, "Test Project", str(tmpdir))
        repo.upsert_source_file("f1", proj_id, "Test.lean", h1)

        # Same hash check
        stored = repo.get_source_file_hash(proj_id, "Test.lean")
        assert stored == h1

        # Modify file and verify hash change
        test_file.write_text("theorem t1_modified : True := by trivial", encoding="utf-8")
        h2 = compute_file_hash(test_file)
        assert h1 != h2
