"""ONE_MENU tests. Run: python -m unittest discover -s API_HOME/tests   (or: python API_HOME/tests/test_engine.py)

Everything runs offline with --mock (fake, clearly labelled replies); no API key is needed or used.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME))
from engine import focus, llm, paths, text  # noqa: E402
from engine.gateway import Gateway  # noqa: E402


def data_config(root: Path) -> Path:
    example = json.loads((HOME / "config" / "paths.example.json").read_text(encoding="utf-8"))
    cfg = {k: (str(root / "data" / v[len("../_data/"):]) if v.startswith("../_data/") else v) for k, v in example.items()}
    path = root / "paths.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def menu(args: list[str], cfg: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "ONE_MENU_PATHS_FILE": str(cfg), "PYTHONIOENCODING": "utf-8"}
    env.pop("DEEPSEEK_API_KEY", None)
    return subprocess.run([sys.executable, str(HOME / "engine" / "menu.py"), *args, "--yes"], cwd=HOME, env=env,
                          capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=300)


class Portability(unittest.TestCase):
    def test_no_absolute_paths_in_our_code(self):
        pattern = re.compile(r"""["'](?:[A-Za-z]:[\\/]|\\\\\\\\|//192\.|/home/|/Users/)""")
        offenders = []
        for folder in ("engine", "stations", "tools"):
            for py in (HOME / folder).rglob("*.py"):
                for n, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                    if pattern.search(line) and "PATH_KEYS" not in line and "noqa-path" not in line and "migrate_legacy" not in py.name:
                        offenders.append(f"{py.relative_to(HOME)}:{n}")
        self.assertEqual([], offenders)

    def test_relative_values_move_with_the_folder(self):
        self.assertEqual(paths.expand("../_data/papers"), (HOME.parent / "_data" / "papers").resolve())

    def test_internal_path_rejects_escape(self):
        with self.assertRaises(paths.PathConfigurationError):
            paths.inside("..", "outside")

    def test_every_station_follows_the_naming_rule(self):
        registry = json.loads((HOME / "config" / "stations.json").read_text(encoding="utf-8"))
        numbers = [r["number"] for r in registry]
        self.assertEqual(len(numbers), len(set(numbers)))
        for row in registry:
            folder = HOME / row["folder"]
            self.assertEqual(folder.name, f"{row['number']}_{row['name']}")
            self.assertEqual(row["script"], f"{row['number']}_{row['name'].lower()}.py")
            for required in (row["script"], "FOCUS.md", "PROMPT.md", "station.json", "README.md"):
                self.assertTrue((folder / required).exists(), f"{folder.name} lacks {required}")

    def test_one_batch_file(self):
        self.assertEqual(["ONE_MENU.bat", "SETUP.bat"], sorted(p.name for p in HOME.parent.glob("*.bat")))
        self.assertEqual([], list(HOME.glob("*.bat")))
        self.assertEqual([], [p for p in (HOME / "stations").rglob("*.bat")])

    def test_no_keys_in_config(self):
        for f in (HOME / "config").glob("*.json"):
            self.assertIsNone(re.search(r"sk-[A-Za-z0-9]{20,}", f.read_text(encoding="utf-8")), f.name)


class FocusAndText(unittest.TestCase):
    def test_three_levels_and_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            station, paper = root / "station", root / "paper"
            station.mkdir()
            (paper / "01_NOTES").mkdir(parents=True)
            (station / "FOCUS.md").write_text("# comment\n- standing\n")
            (paper / "01_NOTES" / "FOCUS.md").write_text("- paper point\n")
            block, digest = focus.compose(station, paper, ["run point"])
            for word in ("standing", "paper point", "run point", "## EXTRA FOCUS FROM DAVID:"):
                self.assertIn(word, block)
            self.assertNotIn("comment", block)
            self.assertEqual(64, len(digest))
            self.assertEqual(("", focus.compose(root / "none")[1]), focus.compose(root / "none"))

    def test_segment_numbers_sentences(self):
        paragraphs, sentences = text.segment("Dr. Smith spoke. The tomb was empty!\n\nWho moved it? Nobody knows.")
        self.assertEqual(["P01", "P02"], [p.id for p in paragraphs])
        self.assertEqual(4, len(sentences))
        self.assertEqual("S004", sentences[-1].id)


class Limiter(unittest.TestCase):
    def test_never_more_than_the_ceiling(self):
        lim = llm.AdaptiveLimiter(5)
        peak, active, lock = [0], [0], threading.Lock()

        def work():
            with lim:
                with lock:
                    active[0] += 1
                    peak[0] = max(peak[0], active[0])
                time.sleep(0.02)
                with lock:
                    active[0] -= 1
        threads = [threading.Thread(target=work) for _ in range(40)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertLessEqual(peak[0], 5)

    def test_halves_on_errors(self):
        lim = llm.AdaptiveLimiter(30)
        with patch.object(llm, "log"):
            for _ in range(10):
                lim.record(True)
        self.assertEqual(15, lim.current)

    def test_deepseek_only_no_fallback(self):
        self.assertEqual([("deepseek", "deepseek-chat")], llm.fallback_chain("deepseek", "deepseek-chat"))


class GatewayTests(unittest.TestCase):
    def test_relay_counts_calls_goal_ids_and_adds_focus(self):
        gw = Gateway(3, "unittest", mock=True).start()
        try:
            gw.focus["30_EVIDENCE_INTAKE"] = "## EXTRA FOCUS FROM DAVID:\n- entropy"
            body = json.dumps({"model": "x", "messages": [{"role": "user", "content": "hi"}]}).encode()
            req = urllib.request.Request(gw.env_for("30_EVIDENCE_INTAKE")["DEEPSEEK_BASE_URL"] + "/chat/completions", data=body,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as r:
                self.assertEqual(200, r.status)
            rows = [json.loads(x) for x in gw.receipts.read_text().splitlines()]
            self.assertEqual("API-30.0", rows[-1]["goal_id"])
            self.assertTrue(rows[-1]["focus_added"])
            self.assertEqual(1, gw.stats.snapshot()["calls"])
        finally:
            gw.stop()
            gw.receipts.unlink(missing_ok=True)


class EndToEnd(unittest.TestCase):
    """The acceptance commands, offline (--mock)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.cfg = data_config(root)
        cls.root = root
        subs = root / "data" / "youtube" / "subtitles" / "Chan"
        subs.mkdir(parents=True)
        (subs / "Tomb.md").write_text("# Tomb\n\n**Video ID:** `abcdefghijk`\n\n## Transcript\n\n[00:01] The resurrection.\n[00:05] The empty tomb.\n")
        (root / "paper.md").write_text("# The Case\n\nThe resurrection of Jesus is attested early. Love is patient.\n\nGrace comes from outside.\n")
        (root / "mine.md").write_text("# Mine\n\nThe resurrection preserves information through death.\n")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_full_chain(self):
        for step in (["47", "--item", str(self.root / "paper.md")], ):
            r = menu(step, self.cfg)
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
        subprocess.run([sys.executable, str(HOME / "stations/47_NEW_PAPER/47_new_paper.py"), str(self.root / "mine.md"), "--own"],
                       env={**os.environ, "ONE_MENU_PATHS_FILE": str(self.cfg)}, capture_output=True, check=True)
        r = menu(["Y", "--mock", "--channel", "Chan"], self.cfg)
        self.assertEqual(0, r.returncode, r.stdout[-3000:] + r.stderr[-3000:])
        r = menu(["P", "--mock"], self.cfg)
        self.assertEqual(0, r.returncode, r.stdout[-3000:] + r.stderr[-3000:])
        self.assertIn("API-40.1", r.stdout)
        r = menu(["48", "49", "--mock", "--topic", "resurrection", "--limit", "5"], self.cfg)
        self.assertEqual(0, r.returncode, r.stdout[-3000:] + r.stderr[-3000:])
        r = menu(["find", "resurrection", "--min", "1"], self.cfg)
        self.assertIn("scoring 1+", r.stdout)
        papers = list((self.root / "data" / "papers").glob("*/paper.json"))
        report = papers[0].parent / "03_REPORT"
        for name in ("report.html", "report.xlsx", "statistics.json", "aggregate.json", "aggregate.md"):
            self.assertTrue((report / name).exists(), name)
        html = (report / "report.html").read_text(encoding="utf-8")
        self.assertNotIn("The Resurrection as Information Preserved", html)
        self.assertNotIn("rng(20260925)", html)
        run = next((papers[0].parent / "02_RUNS" / "40_ANALYTICAL_ARMS").glob("2*"))
        for suffix in (".json", ".xlsx", ".html", ".run.json", ".md"):
            self.assertTrue((run / f"40_ANALYTICAL_ARMS{suffix}").exists(), suffix)
        self.assertTrue(list((run / "calls").glob("API-40.*.json")))
        self.assertTrue((run / "steps.log").read_text())
        gap = self.root / "data" / "syntheses" / "resurrection" / "03_REPORT" / "gap_map.md"
        self.assertIn("## EXPAND", gap.read_text(encoding="utf-8"))

    def test_failures_are_reported_as_failures(self):
        r = menu(["47", "--item", str(self.root / "paper.md")], self.cfg)
        env = {**os.environ, "ONE_MENU_PATHS_FILE": str(self.cfg), "ONE_MENU_NO_FALLBACK": "1"}
        for key in ("DEEPSEEK_API_KEY", "OPENROUTER_API_KEY"):
            env.pop(key, None)
        r = subprocess.run([sys.executable, str(HOME / "stations/40_ANALYTICAL_ARMS/40_analytical_arms.py"), "--limit", "1", "--redo"],
                           cwd=HOME, env=env, capture_output=True, text=True, timeout=120)
        self.assertNotEqual(0, r.returncode, "a run whose calls all failed must not exit 0")

    def test_dry_run_on_every_station(self):
        registry = json.loads((HOME / "config" / "stations.json").read_text(encoding="utf-8"))
        for row in registry:
            if row["number"] in ("90", "91", "01", "06"):
                continue
            args = [row["number"], "--dry-run"] + (["--topic", "x"] if row["number"] in ("48", "49") else [])
            r = menu(args, self.cfg)
            self.assertNotIn("unrecognized arguments", r.stdout + r.stderr, row["label"])


class DomainRules(unittest.TestCase):
    def rubric(self):
        from engine import triage
        return triage.load_rubric((HOME / "stations/10_CKG_THEOLOGY/RUBRIC.md").read_text(encoding="utf-8"))

    def test_triage_cap_priority_and_exemptions(self):
        from engine import triage, mock
        reply = json.loads(mock.respond("theology_triage", [{"role": "user", "content": ""}]))
        out = triage.enforce(reply, self.rubric(), comments_available=False)
        verdict = {r["row"]: r["verdict"] for r in out["rows"]}
        self.assertEqual([2, 3, 9], out["flags"])              # priority rows beat higher-severity Fruit/Enemy
        self.assertEqual("NOTE", verdict[8])
        self.assertEqual("NOTE", verdict[12])                  # no timestamp
        self.assertEqual("CLAIM", verdict[17])                 # always CLAIM, never capped
        self.assertNotEqual("CLAIM", verdict[5])               # history is a lead, not a claim
        self.assertEqual("??", verdict[15])                    # no comments acquired
        self.assertEqual(17, len(out["rows"]))
        layer = triage.claims_into_graph(reply["argument_layer"], out["rows"])
        self.assertTrue(any(c["id"] == "RC17" for c in layer["claims"]))

    def test_mirror_needs_order_stages_and_prediction(self):
        from engine import mirror
        base = {"stages": [{"n": i, "match": "direct", "timestamp": "01:00"} for i in range(3)], "directional": "yes",
                "level": "STRUCTURAL", "prediction": "p"}
        self.assertEqual("STRUCTURAL", mirror.enforce(base)["level"])
        self.assertEqual("ANALOGY", mirror.enforce({**base, "prediction": ""})["level"])
        self.assertEqual("ANALOGY", mirror.enforce({**base, "out_of_order": [2]})["level"])
        self.assertEqual("ANALOGY", mirror.enforce({**base, "stages": base["stages"][:2]})["level"])
        self.assertEqual("IDENTITY", mirror.enforce({**base, "level": "IDENTITY"})["level"])
        self.assertEqual("NONE", mirror.enforce({"stages": [], "level": "STRUCTURAL"})["level"])

    def test_youtube_naming_rule(self):
        from engine import ytnames
        n = ytnames.parse("Gary Habermas - Chapter 159 - The Historical Jesus - Gary Habermas", "Gary Habermas")
        self.assertEqual(("Ch 159 - The Historical Jesus", "Ch 159 · The Historical Jesus"), (n.file_stem, n.h1))
        self.assertEqual("Ep 012 - Why the Tomb Was Empty", ytnames.parse("Ep. 12: Why the Tomb Was Empty | DDW", "DDW").file_stem)
        self.assertEqual("2021-03-04 - Minimal Facts", ytnames.parse("Minimal Facts", "X", "20210304").file_stem)
        self.assertEqual("The #1 Argument for God", ytnames.parse("The #1 Argument for God", "X").file_stem)
        self.assertEqual("What Is Truth", ytnames.parse("What Is Truth?", "X").file_stem)

    def test_only_allowed_providers(self):
        self.assertTrue(llm.allowed("deepseek"))
        self.assertFalse(llm.allowed("openrouter"))
        self.assertFalse(llm.allowed("openai"))
        r = llm.call([{"role": "user", "content": "x"}], provider="openai", model="gpt-4o")
        self.assertIn("not allowed", r.error)

    def test_domain_puts_ckg_then_its_station_after_cleaning(self):
        from engine.menu import order_chain, domain_additions
        self.assertEqual(["03", "10"], domain_additions("theology", ["07", "02", "08"], False))
        self.assertEqual(["03", "11"], domain_additions("physics", ["08"], False))
        self.assertEqual(["07", "02", "03", "10", "08", "09"], order_chain(["07", "02", "08", "09", "03", "10"]))


if __name__ == "__main__":
    unittest.main()
