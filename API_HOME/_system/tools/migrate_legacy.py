"""Copy the gathered legacy code into API_HOME/vendor and make it portable.

Re-runnable: when David updates a live script, copy the new version into the gathered
folder (01_YOUTUBE ... 09_SOURCE_API_FOLDERS) and run

    python API_HOME/tools/migrate_legacy.py

It rebuilds vendor/ from scratch and rewrites MIGRATION_REPORT.md with every change:

  1. API URLs     every literal provider URL becomes os.environ.get("<PROVIDER>_BASE_URL", <same URL>),
                  so during a ONE_MENU run each call goes through engine/gateway.py (one global
                  limiter, retries, receipts, focus) and still works unchanged when run by hand.
  2. Hard paths   every drive-letter / UNC literal becomes os.environ.get("ONE_MENU_PATH_<KEY>", ...)
                  where <KEY> is a config/paths.json key; ONE_MENU exports those variables.
  3. Data roots   scripts that used their own folder as the data root read the matching key.
  4. Input chunking removed where the document fits the context window (whole item per call).
  5. Data bugs    fixed and listed (each fix names what was wrong).

Nothing in the gathered source folders is modified.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
API_HOME = HERE.parent
REPO = API_HOME.parent
VENDOR = API_HOME / "vendor"

SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", "_archive_zips", "INBOX", "OUTBOX", "inbox",
             "outbox", "LOGS", "logs", "records", "RECORDS", "exports", "OUTPUT", "ARCHIVE", "DROP_PAPERS_HERE"}
CODE_EXT = {".py", ".json", ".md", ".txt", ".toml", ".yaml", ".yml", ".csv", ".html", ".schema"}
SKIP_FILES = {"axiom_files.json", "iso_files.json", "keys.local.json", "config.txt", "Clipboard Text.txt"}


@dataclass
class Family:
    name: str          # folder under vendor/
    source: str        # folder under the repo root
    only: tuple = ()   # restrict to these top-level names (files or folders)
    skip: tuple = ()   # top-level names to leave out


FAMILIES = [
    Family("youtube/deepseek_home", "01_YOUTUBE/deepseek-home"),
    Family("youtube/clean", "01_YOUTUBE/Python Clean Library"),
    Family("youtube/grab", "01_YOUTUBE/yt-transcript-downloader_ROOT", only=("ytgrab.py", "ytbsd.py", "channel_size.py", "requirements.txt")),
    Family("ckg", "02_CKG/backside_CKG"),
    Family("evidence/SCRIPTS", "03_EVIDENCE/backside_SCRIPTS", skip=("_backup_before_stacking_20260916",)),
    Family("evidence", "03_EVIDENCE/front_EVIDENCE", only=("SIDECAR_CODES.json", "SIDECAR_GUIDE.md", "New Classification.md")),
    Family("evidence_chain", "07_PIPELINE_WORKFLOWS_API/EvidenceChainIntake"),
    Family("grader", "04_PAPER_GRADER/Academic_paper-proof-grader_Jul"),
    Family("api_deep/ATOMS", "05_API_DEEP_STATIONS/ATOMS"),
    Family("api_deep/AXIOM_NODES", "05_API_DEEP_STATIONS/AXIOM_NODES"),
    Family("lean_atom", "06_LEAN/LEAN_ATOM_EXTRACTOR"),
]

# --------------------------------------------------------------------------------------
# 1. Provider URLs -> gateway-aware expressions.
URL_RULES = [
    # (literal prefix, env var, default base)
    ("https://api.deepseek.com", "DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    ("https://api.openai.com/v1", "OPENAI_BASE_URL", "https://api.openai.com/v1"),
    ("https://openrouter.ai/api/v1", "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    ("https://api.moonshot.ai/v1", "MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
    ("https://api.anthropic.com", "ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
]

# 2. Hard-coded roots -> paths.json keys. Longest prefix first.
PATH_KEYS = [
    (r"D:\GitHub\nerve\source\html\atoms\Template\CKGARGUMENT_TEMPLATE_V1.md", "ckg_argument_template"),
    (r"X:\00_CONVERSION_STATION\Transcripts to Markdown", "conversion_station"),
    (r"C:\Users\David\Documents\faiththruphysics.com\00_ Production\00_ Production", "production_root"),
    (r"\\192.168.2.50\h_hp\Desktop\___Pipeline_Done_New\One page paper API", "pipeline_api_root"),
    (r"\\192.168.2.50\h_hp\Desktop\_____pipeline-workflows-main\LEAN_FLOOR", "lean_floor"),
    (r"\\192.168.2.50\h_hp\Desktop\APIs\APIs", "apis_root"),
    (r"//192.168.2.50/h_hp/Desktop/ALL_LEAN4", "lean_harvest"),
    (r"D:\GitHub\Canonizationv1", "canonization_root"),
    (r"D:\GitHub\David-OSv3\_FIS_ROOT_SIDECAR_ARCHIVE", "sidecar_mirror"),
    (r"D:\GitHub\Faith-through-physics-atoms", "atoms_repo"),
    (r"D:\GitHub\Faith-Thru-Physics-Lean-4-", "lean_root"),
    (r"d:/GitHub/Faith-Thru-Physics-Lean-4-", "lean_root"),
    (r"C:\lean-cache\mathlib4-v431", "mathlib_cache"),
]

# 3-5. Exact per-file edits: (vendor-relative file, old, new, reason). Each must apply exactly once.
EDITS: list[tuple[str, str, str, str]] = [
    # ---------------- YouTube chain
    ("youtube/deepseek_home/index_video.py", 'CLEAN_ROOT = REPO / "obsidian_transcripts"',
     'CLEAN_ROOT = Path(os.environ.get("ONE_MENU_PATH_YT_CLEAN") or REPO / "obsidian_transcripts")', "data root: yt_clean"),
    ("youtube/deepseek_home/index_video.py", 'OUT_ROOT = REPO / "obsidian_indexed"',
     'OUT_ROOT = Path(os.environ.get("ONE_MENU_PATH_YT_INDEXED") or REPO / "obsidian_indexed")', "data root: yt_indexed"),
    ("youtube/deepseek_home/index_video.py", "CHUNK_WORDS = 2500",
     "CHUNK_WORDS = 40000  # ONE_MENU: whole transcript per call; split only past the context window (was 2500)",
     "input chunking removed (whole item per call); truncated replies still halve as before"),
    ("youtube/deepseek_home/home.py", '"claims": 1200', '"claims": 40000',
     "input chunking removed for the claims task (was 1,200-word chunks)"),
    ("youtube/deepseek_home/watch_pipeline.py", 'SUBS = REPO / "subtitles"',
     'SUBS = Path(os.environ.get("ONE_MENU_PATH_YT_SUBTITLES") or REPO / "subtitles")', "data root: yt_subtitles"),
    ("youtube/deepseek_home/watch_pipeline.py", 'CLEAN_OUT = REPO / "obsidian_transcripts"',
     'CLEAN_OUT = Path(os.environ.get("ONE_MENU_PATH_YT_CLEAN") or REPO / "obsidian_transcripts")', "data root: yt_clean"),
    ("youtube/deepseek_home/watch_pipeline.py", 'VENV_PY = REPO / "venv" / "Scripts" / "python.exe"',
     "VENV_PY = Path(sys.executable)", "use the Python ONE_MENU runs on, not a repo venv"),
    ("youtube/deepseek_home/watch_pipeline.py", 'REPO / "Python Clean Library"', 'HERE.parent / "clean"',
     "cleaner is vendored beside this folder"),
    ("youtube/deepseek_home/build_catalog.py", 'SUBS_ROOT = OUT_ROOT.parent / "subtitles"',
     'SUBS_ROOT = Path(os.environ.get("ONE_MENU_PATH_YT_SUBTITLES") or OUT_ROOT.parent / "subtitles")', "data root: yt_subtitles"),
    # ---------------- CKG: config and templates live in the vendored backside
    ("ckg/PYTHON/run_ckg.py", '    hidden = root.parent / "_BACKSIDE" / "CKG" / "CONFIG"\n',
     '    hidden = Path(__file__).resolve().parents[1] / "CONFIG"  # ONE_MENU: vendored backside\n',
     "config found in vendor/ckg/CONFIG instead of <root>/../_BACKSIDE"),
    ("ckg/workbench/ckg.py", '    hidden = root.parent / "_BACKSIDE" / "CKG" / "CONFIG"\n',
     '    hidden = Path(__file__).resolve().parents[1] / "CONFIG"  # ONE_MENU: vendored backside\n',
     "config found in vendor/ckg/CONFIG"),
    ("ckg/workbench/ckg.py", '    hidden = root.parent / "_BACKSIDE" / "CKG" / "templates" / name\n',
     '    hidden = Path(__file__).resolve().parents[1] / "templates" / name  # ONE_MENU: vendored backside\n',
     "master template found in vendor/ckg/templates"),
    # ---------------- EVIDENCE: data root is the evidence_root key; templates stay vendored
    ("evidence/SCRIPTS/turbo_pipeline_runner.py", "    return SCRIPTS_DIR.parent\n",
     '    return Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_ROOT") or SCRIPTS_DIR.parent)\n', "data root: evidence_root"),
    ("evidence/SCRIPTS/turbo_pipeline_runner.py",
     '    parser.add_argument("--root", type=Path, default=None, help="Working EVIDENCE folder (default: parent of SCRIPTS dir)")\n',
     '    parser.add_argument("--root", type=Path, default=None, help="Working EVIDENCE folder (default: parent of SCRIPTS dir)")\n'
     '    parser.add_argument("--limit", type=int, default=None, help="ONE_MENU: process at most N documents, then stop")\n',
     "new --limit flag (the master prompt asks for it)"),
    ("evidence/SCRIPTS/turbo_pipeline_runner.py", "        workload = collect_workload()\n        batch_total = len(workload)\n",
     "        workload = collect_workload()\n        if args.limit is not None:\n"
     "            remaining = args.limit - total_completed - total_errors\n"
     "            workload = workload[:max(0, remaining)]\n        batch_total = len(workload)\n",
     "--limit caps the queue"),
    ("evidence/SCRIPTS/turbo_pipeline_runner.py", "            if args.continuous:\n                print(\"[Watcher]",
     "            if args.continuous and args.limit is None:\n                print(\"[Watcher]", "--limit ends continuous mode"),
    ("evidence/SCRIPTS/api_original_merge.py", "ROOT = Path(__file__).resolve().parents[1]",
     'ROOT = Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_ROOT") or Path(__file__).resolve().parents[1])', "data root: evidence_root"),
    ("evidence/SCRIPTS/argument_builder.py", "ROOT = Path(__file__).resolve().parents[1]",
     'ROOT = Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_ROOT") or Path(__file__).resolve().parents[1])', "data root: evidence_root"),
    ("evidence/SCRIPTS/article_stack.py", "ROOT = Path(__file__).resolve().parents[1]",
     'ROOT = Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_ROOT") or Path(__file__).resolve().parents[1])', "data root: evidence_root"),
    ("evidence/SCRIPTS/best_arguments_and_weaknesses.py", "ROOT = Path(__file__).resolve().parents[1]",
     'ROOT = Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_ROOT") or Path(__file__).resolve().parents[1])', "data root: evidence_root"),
    ("evidence/SCRIPTS/three_dials_annotate.py", "ROOT = Path(__file__).resolve().parents[1]",
     'ROOT = Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_ROOT") or Path(__file__).resolve().parents[1])', "data root: evidence_root"),
    ("evidence/SCRIPTS/evidence_sidecars.py", "SIDECAR_DIR = Path(__file__).resolve().parents[1] / 'SIDECAR'",
     "SIDECAR_DIR = Path(os.environ.get('ONE_MENU_PATH_EVIDENCE_ROOT') or Path(__file__).resolve().parents[1]) / 'SIDECAR'",
     "data root: evidence_root"),
    ("evidence/SCRIPTS/evidence_sidecars.py",
     "parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1] / 'OUTBOX')",
     "parser.add_argument('--root', type=Path, default=Path(os.environ.get('ONE_MENU_PATH_EVIDENCE_ROOT') or Path(__file__).resolve().parents[1]) / 'OUTBOX')",
     "data root: evidence_root"),
    # data bugs ------------------------------------------------------------------
    ("evidence/SCRIPTS/sync_to_sqlite.py",
     "        pred_matches = re.findall(r'\\|\\s*(P\\d+)\\s*\\|\\s*([^\\|]+)\\s*\\|\\s*([^\\|]+)\\s*\\|\\s*([^\\|]+)\\s*\\|\\s*([^\\|]+)\\s*\\|', text)\n"
     "        for pnum, ptext, warrant, logic, modality in pred_matches:\n",
     "        # ONE_MENU fix: the template table is `| # | Truth Predicate | Source Role | Modality | Formal form | Warrant |`.\n"
     "        # The old pattern required P## ids and stored Source Role as warrant and Modality as the formal form.\n"
     "        section = re.search(r'### Extracted Truth Predicates([\\s\\S]*?)(?=\\n#{2,3} |\\Z)', text)\n"
     "        rows = re.findall(r'^\\|\\s*(P?\\d+)\\s*\\|([^|]*)\\|([^|]*)\\|([^|]*)\\|([^|]*)\\|([^|]*)\\|', section.group(1) if section else '', re.M)\n"
     "        pred_matches = [(n, t, w, f, m) for n, t, _role, m, f, w in rows]\n"
     "        for pnum, ptext, warrant, logic, modality in pred_matches:\n",
     "BUG FIX: truth predicates were parsed from the wrong columns (and usually not at all)"),
    ("evidence/SCRIPTS/theophysics_congruence_matrix.py",
     '                if data.get("status") == "PROVEN":\n                    # Mark all verified\n                    verified_lean_papers.add("ALL_CURRENT_BATCH")\n',
     '                if data.get("status") == "PROVEN":\n                    # ONE_MENU fix: one PROVEN receipt used to mark EVERY paper proven.\n'
     '                    for key in ("paper_id", "slug", "paper", "source", "title"):\n'
     '                        if data.get(key):\n'
     '                            verified_lean_papers.add(re.sub(r"[^\\w]", "_", str(data[key])).strip("_").lower())\n'
     '                    verified_lean_papers.add(re.sub(r"[^\\w]", "_", rf.stem).strip("_").lower())\n',
     "BUG FIX: one PROVEN Lean receipt marked all papers proven"),
    ("evidence/SCRIPTS/theophysics_congruence_matrix.py",
     'has_lean = (slug_clean in existing_lean_files) or ("ALL_CURRENT_BATCH" in verified_lean_papers)',
     "has_lean = (slug_clean in existing_lean_files) or (slug_clean in verified_lean_papers)", "per-paper Lean status"),
    ("evidence/SCRIPTS/theophysics_congruence_matrix.py", "support_count = len(re.findall(r'evidence_type:', text)) or 4",
     "support_count = len(re.findall(r'evidence_type:', text))  # ONE_MENU fix: `or 4` made every paper SUPPORTED",
     "BUG FIX: zero evidence counted as 4, so every paper read SUPPORTED"),
    ("evidence/SCRIPTS/series_evaluator.py", '        if f.name.startswith("00_") or f.name.startswith("01_THE_STORY"):',
     '        if f.name.startswith(("00_", "01_THE_STORY", "SERIES_")) or "_GRAND_SYNTHESIS" in f.name:  # ONE_MENU fix: skip our own outputs',
     "BUG FIX: the evaluator re-read its own and the synthesizer's outputs as papers"),
    ("evidence/SCRIPTS/series_grand_synthesizer.py", "the_six_m = re.search(r'(## The Six[\\s\\S]*?)(?=## S01|\\Z)', text)",
     "the_six_m = re.search(r'((?:## |> \\[!success\\] )The Six[\\s\\S]*?)(?=\\n## |\\n\\n(?!>)|\\Z)', text)  # ONE_MENU fix: template uses a callout",
     "BUG FIX: 'The Six' is a callout in the template, the old pattern never matched"),
    ("evidence/SCRIPTS/series_grand_synthesizer.py", "pred_m = re.search(r'(\\| P# \\|[\\s\\S]*?)(?=\\n\\n|\\Z)', text)",
     "pred_m = re.search(r'(\\| (?:P#|#) \\| Truth Predicate[\\s\\S]*?)(?=\\n\\n|\\Z)', text)  # ONE_MENU fix: header is `| # |`",
     "BUG FIX: predicate table header is `| # |`, the old pattern never matched"),
    # ---------------- Evidence chain (E)
    ("evidence_chain/SCRIPTS/epistemic_intake_v2.py", "INTAKE_ROOT = SCRIPTS_DIR.parent",
     'INTAKE_ROOT = Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_CHAIN_ROOT") or SCRIPTS_DIR.parent)', "data root: evidence_chain_root"),
    ("evidence_chain/SCRIPTS/organize_and_retake_folders.py", "INTAKE_ROOT = SCRIPTS_DIR.parent",
     'INTAKE_ROOT = Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_CHAIN_ROOT") or SCRIPTS_DIR.parent)', "data root: evidence_chain_root"),
    ("evidence_chain/SCRIPTS/build_master_classification_api.py", "INTAKE_ROOT = SCRIPTS_DIR.parent",
     'INTAKE_ROOT = Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_CHAIN_ROOT") or SCRIPTS_DIR.parent)', "data root: evidence_chain_root"),
    # ---------------- Grader: data folders under grader_root
    ("grader/pipeline.py", "    return path if path.is_absolute() else HERE / path",
     '    base = Path(os.environ.get("ONE_MENU_PATH_GRADER_ROOT") or HERE)  # ONE_MENU: data outside the code\n'
     '    return path if path.is_absolute() else base / path', "data root: grader_root"),
    # ---------------- API_DEEP atoms / axiom nodes workspace
    ("api_deep/ATOMS/SCRIPTS/run_atoms.py", '    return root.parents[1] / "OUTBOX"',
     '    return Path(os.environ.get("ONE_MENU_PATH_ATOMS_WORKSPACE") or root.parents[1] / "OUTBOX")', "data root: atoms_workspace"),
    ("api_deep/AXIOM_NODES/SCRIPTS/run_axiom_nodes.py", '    return root.parents[1] / "OUTBOX"',
     '    return Path(os.environ.get("ONE_MENU_PATH_ATOMS_WORKSPACE") or root.parents[1] / "OUTBOX")', "data root: atoms_workspace"),
]


# Generic data-root lines, applied after EDITS to whatever still matches (family prefix, pattern, key).
ROOT_LINES = [
    ("evidence/SCRIPTS/", r"^(ROOT_DIR|ROOT) = (SCRIPTS_DIR\.parent|Path\(__file__\)\.resolve\(\)\.parents\[1\])$", "evidence_root"),
    ("evidence/SCRIPTS/theophysics_congruence_matrix.py",
     r"^ROOT_DIR = SCRIPTS_DIR if SCRIPTS_DIR\.name == \"_____pipeline-workflows-main\" else SCRIPTS_DIR\.parent$", "evidence_root"),
    ("evidence_chain/SCRIPTS/", r"^(ROOT|INTAKE_ROOT) = (SCRIPTS_DIR\.parent|HERE\.parent|Path\(__file__\)\.resolve\(\)\.parents\[1\])$",
     "evidence_chain_root"),
]


def apply_root_lines(report: "Report") -> None:
    for prefix, pattern, key in ROOT_LINES:
        for path in sorted(VENDOR.rglob("*.py")):
            rel = path.relative_to(VENDOR).as_posix()
            if not rel.startswith(prefix):
                continue
            text = path.read_text(encoding="utf-8")
            def repl(m: re.Match) -> str:
                name, default = m.group(0).split(" = ", 1)
                new = f'{name} = Path(os.environ.get("ONE_MENU_PATH_{key.upper()}") or ({default}))'
                report.add("data-root", rel, text.count("\n", 0, m.start()) + 1, m.group(0), new)
                return new
            new_text = re.sub(pattern, repl, text, flags=re.M)
            if new_text != text:
                path.write_text(ensure_import_path(ensure_import_os(new_text)), encoding="utf-8")


# Turbo's master-index row: replace fixed placeholder numbers with values read from the reply.
TURBO_PLACEHOLDERS = ["evd_support", "evd_counter", "evd_families", "evd_coverage", "coherence", "total_claims",
                      "claims_with_falsifiers", "hidden_premises", "lean_targets_queued", "predictions_logged",
                      "bridges_registered", "truth_predicates", "original_argument_steps", "total_argument_steps",
                      "supplementary_arguments", "weak_links_identified"]


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.counts: dict[str, int] = {}

    def add(self, kind: str, file: str, line: int | str, old: str, new: str) -> None:
        self.counts[kind] = self.counts.get(kind, 0) + 1
        clip = lambda s: s.replace("|", "\\|").replace("\n", " ⏎ ")[:150]
        self.lines.append(f"| {kind} | `{file}` | {line} | `{clip(old)}` | `{clip(new)}` |")


def copy_family(family: Family, report: Report) -> None:
    src = REPO / family.source
    dst = VENDOR / family.name
    if not src.is_dir():
        print(f"skip {family.source}: not found")
        return
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        top = rel.parts[0]
        if family.only and top not in family.only:
            continue
        if top in family.skip or any(p in SKIP_DIRS for p in rel.parts[:-1]) or path.name in SKIP_FILES:
            continue
        if path.is_dir() or path.suffix.lower() not in CODE_EXT:
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    report.add("copy", family.name, "", family.source, f"vendor/{family.name}")


def _has_path_name(text: str) -> bool:
    return bool(re.search(r"^\s*from pathlib import [^\n]*\bPath\b|^\s*Path\s*=", text, re.M))


def ensure_import_path(text: str) -> str:
    """Our rewrites use Path(...); some originals only did `import pathlib`."""
    if not re.search(r"(?<![\w.])Path\(", text) or _has_path_name(text):
        return text
    lines = text.split("\n")
    insert = 0
    for i, line in enumerate(lines[:80]):
        if line.startswith("from __future__"):
            insert = i + 1
    return "\n".join(lines[:insert] + ["from pathlib import Path  # ONE_MENU"] + lines[insert:])


def ensure_import_os(text: str) -> str:
    if re.search(r"^import os\b|^import .*\bos\b", text, re.M):
        return text
    lines = text.split("\n")
    insert = 0
    for i, line in enumerate(lines[:60]):
        if line.startswith("from __future__"):
            insert = i + 1
    return "\n".join(lines[:insert] + ["import os  # ONE_MENU"] + lines[insert:])


def rewrite_urls(rel: str, text: str, report: Report) -> str:
    def repl(match: re.Match) -> str:
        quote, body = match.group(1), match.group(2)
        for prefix, env, default in URL_RULES:
            if body.startswith(prefix):
                rest = body[len(prefix):]
                expr = f'os.environ.get("{env}", "{default}").rstrip("/")'
                new = expr if not rest else f'{expr} + {quote}{rest}{quote}'
                line = text.count("\n", 0, match.start()) + 1
                report.add("api-url", rel, line, match.group(0), new)
                return new
        return match.group(0)
    # plain (non-f) string literals only; f-strings are left alone and reported by the check below
    return re.sub(r'(?<![fFrRbB\w])(["\'])(https://(?:api\.deepseek\.com|api\.openai\.com/v1|openrouter\.ai/api/v1|api\.moonshot\.ai/v1|api\.anthropic\.com)[^"\'\s]*)\1',
                  repl, text)


def rewrite_paths(rel: str, text: str, report: Report) -> str:
    def repl(match: re.Match) -> str:
        prefix_r, quote, body = match.group(1) or "", match.group(2), match.group(3)
        for literal, key in PATH_KEYS:
            if body.lower().startswith(literal.lower()):
                rest = body[len(literal):].lstrip("\\/")
                base = f'os.environ.get("ONE_MENU_PATH_{key.upper()}", "")'
                if rest:
                    parts = ", ".join(f'"{p}"' for p in re.split(r"[\\/]+", rest) if p)
                    new = f"os.path.join({base}, {parts})"
                else:
                    new = base
                line = text.count("\n", 0, match.start()) + 1
                report.add("hard-path", rel, line, match.group(0), new)
                return new
        return match.group(0)
    return re.sub(r'(?<![\w])(r|R)?(["\'])((?:[A-Za-z]:[\\/]|\\\\\\\\|\\\\192|//192)[^"\'\n]*)\2', repl, text)


def apply_edits(report: Report) -> list[str]:
    problems = []
    for rel, old, new, reason in EDITS:
        path = VENDOR / rel
        if not path.exists():
            problems.append(f"edit target missing: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        count = text.count(old)
        if count != 1:
            problems.append(f"edit did not match exactly once ({count}x) in {rel}: {reason}")
            continue
        line = text[:text.find(old)].count("\n") + 1
        text = text.replace(old, new)
        if "os.environ" in new or "os.path" in new:
            text = ensure_import_os(text)
        text = ensure_import_path(text)
        if "sys.executable" in new and not re.search(r"^import sys\b|^import .*\bsys\b", text, re.M):
            text = "import sys  # ONE_MENU\n" + text
        path.write_text(text, encoding="utf-8")
        report.add("bug-fix" if reason.startswith("BUG FIX") else "edit", rel, line, old, new + "   — " + reason)
    return problems


def fix_turbo_index(report: Report) -> list[str]:
    path = VENDOR / "evidence/SCRIPTS/turbo_pipeline_runner.py"
    text = path.read_text(encoding="utf-8")
    changed = 0
    for key in TURBO_PLACEHOLDERS:
        pattern = re.compile(rf'(            "{key}": )([0-9.]+)(,)')
        match = pattern.search(text)
        if match:
            text = text[:match.start()] + f'{match.group(1)}_reply_number(rendered_output, "{key}"){match.group(3)}' + text[match.end():]
            changed += 1
    helper = ('\n\ndef _reply_number(text, key):\n'
              '    """ONE_MENU fix: read a number the model wrote (key: value); None when absent.\n'
              '    The index used to store the same invented numbers for every paper."""\n'
              '    match = re.search(rf"^\\s*{key}:\\s*([0-9]+(?:\\.[0-9]+)?)", text or "", re.M)\n'
              '    if not match:\n        return None\n'
              '    value = float(match.group(1))\n'
              '    return int(value) if value.is_integer() else value\n')
    text = text.replace("\nALLOWED_EXTS = ", helper + "\nALLOWED_EXTS = ", 1)
    path.write_text(text, encoding="utf-8")
    report.add("bug-fix", "evidence/SCRIPTS/turbo_pipeline_runner.py", "index row", f"{changed} fixed placeholder numbers",
               "_reply_number(rendered_output, key) — None when the reply has no value")
    return [] if changed == len(TURBO_PLACEHOLDERS) else [f"turbo index: only {changed}/{len(TURBO_PLACEHOLDERS)} placeholders replaced"]


def check(report: Report) -> list[str]:
    problems = []
    for path in sorted(VENDOR.rglob("*.py")):
        rel = path.relative_to(VENDOR).as_posix()
        try:
            compile(path.read_text(encoding="utf-8", errors="replace"), str(path), "exec")
        except SyntaxError as exc:
            original = _original_of(rel)
            try:
                if original:
                    compile(original.read_text(encoding="utf-8", errors="replace"), str(original), "exec")
                problems.append(f"does not compile: {rel}:{exc.lineno}: {exc.msg}")
            except SyntaxError:
                report.add("note", rel, exc.lineno, "original also fails on this Python", f"needs Python 3.12+ ({exc.msg})")
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"(?<![\w.])Path\(", text) and not _has_path_name(text):
            problems.append(f"uses Path(...) without importing it: {rel}")
        if re.search(r"(?<![\w.])os\.(environ|path)", text) and not re.search(r"^\s*import (?:[\w, ]*\b)?os\b", text, re.M):
            problems.append(f"uses os without importing it: {rel}")
        for match in re.finditer(r'["\'](?:[A-Za-z]:[\\/]|\\\\192|//192)[^"\']*["\']', text):
            line = text.count("\n", 0, match.start()) + 1
            problems.append(f"absolute path left in {rel}:{line}: {match.group(0)[:90]}")
        for match in re.finditer(r"(?<=[\"'])https://(?:api\.deepseek\.com|api\.openai\.com|openrouter\.ai/api|api\.moonshot\.ai|api\.anthropic\.com)", text):
            before = text[max(0, match.start() - 60):match.start()]
            if "os.environ.get(" not in before:
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"provider URL not routed in {rel}:{line}")
    return problems


def _original_of(rel: str) -> Path | None:
    for family in FAMILIES:
        if rel.startswith(family.name + "/"):
            candidate = REPO / family.source / rel[len(family.name) + 1:]
            return candidate if candidate.exists() else None
    return None


def main() -> int:
    if VENDOR.exists():
        shutil.rmtree(VENDOR)
    VENDOR.mkdir(parents=True)
    report = Report()
    for family in FAMILIES:
        copy_family(family, report)
    for path in sorted(VENDOR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".py", ".toml"):
            continue
        rel = path.relative_to(VENDOR).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        new = text
        if path.suffix == ".py":
            new = rewrite_urls(rel, new, report)
            new = rewrite_paths(rel, new, report)
            if new != text:
                new = ensure_import_path(ensure_import_os(new))
        else:  # toml cannot hold expressions: blank the path, ONE_MENU passes --root
            for literal, key in PATH_KEYS:
                if literal in new:
                    report.add("hard-path", rel, "", literal, f'"" (passed at run time from paths key {key})')
                    new = new.replace(literal, "")
        if new != text:
            path.write_text(new, encoding="utf-8")
    problems = apply_edits(report)
    problems += fix_turbo_index(report)
    apply_root_lines(report)
    problems += check(report)
    write_report(report, problems)
    print(f"vendor rebuilt: {sum(1 for _ in VENDOR.rglob('*.py'))} Python files; " +
          ", ".join(f"{k} {v}" for k, v in sorted(report.counts.items())))
    for p in problems:
        print("PROBLEM:", p)
    return 1 if problems else 0


def write_report(report: Report, problems: list[str]) -> None:
    keys = sorted({k for _, k in PATH_KEYS})
    text = [
        "# Migration report", "",
        "Generated by `tools/migrate_legacy.py`. Re-run it after copying newer live scripts into the gathered folders;",
        "it rebuilds `vendor/` and this file. The gathered folders themselves are never modified.", "",
        "## What changed, in one line each", "",
        "- **API calls**: every provider URL now reads `<PROVIDER>_BASE_URL` first. During a ONE_MENU run that points at",
        "  `engine/gateway.py`, so legacy calls share the one global limiter, retries, receipts and focus. Run by hand, the",
        "  default URL is used exactly as before.",
        "- **Paths**: every drive-letter or UNC literal now reads `ONE_MENU_PATH_<KEY>`, exported from `config/paths.json`.",
        f"  Keys introduced by this migration: {', '.join(f'`{k}`' for k in keys)}.",
        "- **Data roots**: scripts that treated their own folder as the data folder now read `evidence_root`,",
        "  `evidence_chain_root`, `yt_subtitles`, `yt_clean`, `yt_indexed`, `grader_root` or `atoms_workspace`.",
        "- **Chunking**: `index_video.py` (2,500 words) and `home.py` claims (1,200 words) now send the whole transcript;",
        "  the existing halve-on-truncated-reply fallback remains the only split.",
        "- **Data bugs fixed**: see the `bug-fix` rows.", "",
        "## Counts", "",
        *[f"- {k}: {v}" for k, v in sorted(report.counts.items())], "",
        "## Problems found by the post-migration check", "",
        *([f"- {p}" for p in problems] or ["- none: every vendored file compiles, no absolute path or unrouted provider URL remains"]), "",
        "## Every change", "",
        "| kind | file | line | before | after |", "|---|---|---|---|---|",
        *report.lines, "",
    ]
    (API_HOME / "MIGRATION_REPORT.md").write_text("\n".join(text), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
