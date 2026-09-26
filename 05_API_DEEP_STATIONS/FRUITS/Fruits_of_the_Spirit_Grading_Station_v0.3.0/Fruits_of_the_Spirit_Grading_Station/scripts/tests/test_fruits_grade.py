import importlib.util
import pathlib
import sys
import tempfile
import unittest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "fruits_grade.py"
SPEC = importlib.util.spec_from_file_location("fruits_grade", MODULE_PATH)
fg = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = fg
SPEC.loader.exec_module(fg)


def valid_report():
    fruits = []
    for fruit_id in fg.FRUIT_IDS:
        fruits.append({
            "fruit_id": fruit_id, "score": 2, "confidence": 0.5,
            "mechanism": "bounded test mechanism", "positive_evidence": [],
            "counterevidence": [], "evidence_coverage": 0.2,
            "stress_tests": {name: "UNKNOWN" for name in fg.STRESS_IDS},
            "counterfeit": {"flag": False, "claimed_label": None, "missing_companion": None, "anti_fruit_output": None, "severity": "NONE"},
            "rationale": "Mixed or insufficient test evidence."
        })
    gates = []
    for gate_id in fg.GATE_IDS:
        gates.append({"gate_id": gate_id, "status": "UNKNOWN", "hard": gate_id in fg.HARD_GATES, "rationale": "Not evidenced.", "evidence_refs": [], "resolution": None})
    return {
        "spec_version": "0.3.0",
        "target": {"type": "paper", "title": "Fixture", "domain": "test", "unit": "document", "comparison_class": "test", "population_boundary": "source only"},
        "gate_results": gates, "fruit_profile": fruits, "contradictions": [],
        "counterfeit_flags": [], "anti_fruit_pressure": [], "stakeholder_divergence": [],
        "aggregation": {"mode": "gated_profile"}, "epistemic_status": "UNRESOLVED",
        "system_status": "REPAIRABLE", "confidence": 0.5, "missing_evidence": ["longitudinal evidence"],
        "repair_path": ["add evidence"], "falsifier": "contrary evidence", "limitations": ["fixture"]
    }


class FruitsStationTests(unittest.TestCase):
    def test_valid_fixture(self):
        self.assertEqual(fg.validate_report(valid_report()), [])

    def test_requires_exact_nine(self):
        report = valid_report()
        report["fruit_profile"].pop()
        self.assertTrue(any("exactly nine" in x for x in fg.validate_report(report)))

    def test_hard_gate_veto_blocks_positive_status(self):
        report = valid_report()
        report["system_status"] = "ROBUST"
        report["gate_results"][0]["status"] = "FAIL"
        with tempfile.TemporaryDirectory() as folder:
            source = pathlib.Path(folder) / "source.md"
            source.write_text("fixture", encoding="utf-8")
            result = fg.normalize_and_recompute(report, source, "rubric", "prompt", {"provider": "fixture", "model": "fixture"})
        self.assertEqual(result["system_status"], "BLOCKED")
        self.assertTrue(result["aggregation"]["vetoes"])

    def test_unknown_contradiction_does_not_create_veto(self):
        report = valid_report()
        contradiction_gate = next(x for x in report["gate_results"] if x["gate_id"] == "gate.contradiction")
        contradiction_gate["status"] = "UNKNOWN"
        with tempfile.TemporaryDirectory() as folder:
            source = pathlib.Path(folder) / "source.md"
            source.write_text("fixture", encoding="utf-8")
            result = fg.normalize_and_recompute(report, source, "rubric", "prompt", {"provider": "fixture", "model": "fixture"})
        self.assertEqual(result["aggregation"]["vetoes"], [])


if __name__ == "__main__":
    unittest.main()
