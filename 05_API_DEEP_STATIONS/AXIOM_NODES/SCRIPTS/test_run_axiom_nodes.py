#!/usr/bin/env python3
"""Smoke test for the AXIOM_NODES runner without hitting live APIs."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from axiom_io import paper_uuid, safe_filename
from axiom_prompt import build_axiom_prompt


class TestAxiomIO(unittest.TestCase):
    def test_safe_filename(self):
        self.assertEqual(safe_filename("Hello World!"), "Hello_World")

    def test_paper_uuid_stable(self):
        p = Path("/outbox/priority/sample.md")
        self.assertEqual(paper_uuid(p), paper_uuid(p))


class TestAxiomPrompt(unittest.TestCase):
    def test_prompt_contains_nodes_and_schema(self):
        prompt = build_axiom_prompt("This paper discusses existence and distinction.")
        self.assertIn("SCHEMA:", prompt)
        self.assertIn("SOURCE:", prompt)
        self.assertIn("A1.1", prompt)


class TestRunnerFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="axiom_nodes_test_")
        self.workspace = Path(self.tmp)
        (self.workspace / "01_PRIORITY").mkdir(parents=True)
        (self.workspace / "06_JSON_RECORDS").mkdir(parents=True)
        (self.workspace / "00_ORIGINAL_UNTOUCHED").mkdir(parents=True)
        self.sample = self.workspace / "01_PRIORITY" / "sample.md"
        self.sample.write_text("# Test Paper\n\nThis paper asserts existence and distinction.", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_full_flow_with_mocked_complete(self):
        import run_axiom_nodes

        fake_response = {
            "title": "Test Paper",
            "summary": "The paper maps to core axioms.",
            "primary_mode": "AX_CORE",
            "axiom_nodes": [
                {
                    "node_id": "A1.1",
                    "name": "A1.1 — Existence",
                    "mode": "AX_CORE",
                    "alignment": "directly_asserted",
                    "evidence_quote": "This paper asserts existence",
                    "confidence": "high",
                    "notes": "Explicitly stated"
                }
            ]
        }

        original_complete = run_axiom_nodes.complete
        run_axiom_nodes.complete = lambda *a, **k: json.dumps(fake_response)
        try:
            rc = run_axiom_nodes.main(["--workspace", str(self.workspace), "--provider", "deepseek"])
            self.assertEqual(rc, 0)
        finally:
            run_axiom_nodes.complete = original_complete

        puuid = paper_uuid(self.sample)
        self.assertTrue((self.workspace / "06_JSON_RECORDS" / "Test_Paper_axiom_nodes_api.json").exists())
        self.assertTrue((self.workspace / "00_ORIGINAL_UNTOUCHED" / "Test_Paper_original.md").exists())

        companion = self.sample.read_text(encoding="utf-8")
        self.assertIn("# Test Paper", companion)
        self.assertIn("## Axiom Node Mapping (Axiom Nodes API)", companion)
        self.assertIn("A1.1", companion)
        self.assertIn(f"`{puuid}`", companion)


if __name__ == "__main__":
    unittest.main()
