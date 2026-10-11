#!/usr/bin/env python3
"""Smoke test for the ATOMS runner without hitting live APIs."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure local modules are importable.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from atom_io import paper_uuid, safe_filename
from atom_prompt import build_atom_prompt


class TestAtomIO(unittest.TestCase):
    def test_safe_filename(self):
        self.assertEqual(safe_filename("Hello World!"), "Hello_World")
        self.assertEqual(safe_filename("  Multiple   spaces  "), "Multiple_spaces")

    def test_paper_uuid_stable(self):
        p = Path("/inbox/sample.md")
        self.assertEqual(paper_uuid(p), paper_uuid(p))


class TestAtomPrompt(unittest.TestCase):
    def test_prompt_contains_schema_and_source(self):
        prompt = build_atom_prompt("This is a test source.")
        self.assertIn("SCHEMA:", prompt)
        self.assertIn("SOURCE:", prompt)
        self.assertIn("claim", prompt)


class TestRunnerFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="atoms_test_")
        self.workspace = Path(self.tmp)
        (self.workspace / "01_PRIORITY").mkdir(parents=True)
        (self.workspace / "06_JSON_RECORDS").mkdir(parents=True)
        (self.workspace / "00_ORIGINAL_UNTOUCHED").mkdir(parents=True)
        self.sample = self.workspace / "01_PRIORITY" / "sample.md"
        self.sample.write_text("# Test\n\nThis is a sample source text.", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_full_flow_with_mocked_complete(self):
        import run_atoms

        fake_response = {
            "title": "Test Document",
            "domainType": "theology",
            "summary": "A test summary.",
            "atoms": [
                {
                    "nodeType": "claim",
                    "stage": "01_canonical",
                    "name": "Sample Claim",
                    "statementTechnical": "Technical statement.",
                    "statementPlain": "Plain statement.",
                    "claimClass": "theorem",
                    "falsificationCondition": "A counterexample exists.",
                    "verificationStatus": "informal",
                    "challengeStatus": "unchallenged",
                    "edges": []
                }
            ]
        }

        original_complete = run_atoms.complete
        run_atoms.complete = lambda *a, **k: json.dumps(fake_response)
        try:
            rc = run_atoms.main(["--workspace", str(self.workspace), "--provider", "deepseek"])
            self.assertEqual(rc, 0)
        finally:
            run_atoms.complete = original_complete

        puuid = paper_uuid(self.sample)
        self.assertTrue((self.workspace / "06_JSON_RECORDS" / "Test_Document_axiom_api.json").exists())
        self.assertTrue((self.workspace / "00_ORIGINAL_UNTOUCHED" / "Test_Document_original.md").exists())

        # The source file was enriched in place in OUTBOX/01_PRIORITY.
        self.assertTrue(self.sample.exists())
        companion = self.sample.read_text(encoding="utf-8")
        self.assertIn("# Test", companion)
        self.assertIn("## Atom Classification (Axiom API)", companion)
        self.assertIn("Sample Claim", companion)
        self.assertIn(f"`{puuid}`", companion)


if __name__ == "__main__":
    unittest.main()
