"""Station 90 HEALTHCHECK: every station, every path key, every API key.

Beyond "does the file exist", it proves the menu never offers a fake option:
  * each native station's --help must list every option in its station.json;
  * each wrapped station's real script --help must list every flag its station.json maps to
    (e.g. --limit for 30 EVIDENCE_INTAKE), so a flag the script doesn't have is caught here.
Scripts whose --help cannot run on this machine (missing optional packages) are reported, not failed.

  python engine/health.py          full check
  python engine/health.py --quick  skip the --help runs
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.paths import API_HOME, expand, key_specs, load_paths  # noqa: E402

NATIVE_FLAGS = {"limit": "--limit", "workers": "--workers", "provider": "--provider", "model": "--model",
                "focus": "--focus", "redo": "--redo", "channel": "--channel", "topic": "--topic"}
KEYS = ["DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "MOONSHOT_API_KEY", "ANTHROPIC_API_KEY"]


def _help(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        done = subprocess.run(cmd + ["--help"], cwd=cwd, capture_output=True, text=True, timeout=60,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    return done.returncode == 0, done.stdout + done.stderr


def check_station(row: dict, quick: bool) -> list[tuple[str, bool, str]]:
    out = []
    folder = API_HOME / row["folder"]
    meta_path = folder / "station.json"
    script = folder / row["script"]
    missing = [n for n, p in (("folder", folder), ("script", script), ("FOCUS.md", folder / "FOCUS.md"),
                             ("station.json", meta_path), ("PROMPT.md", folder / "PROMPT.md")) if not p.exists()]
    if missing:
        return [(row["label"], False, "missing " + ", ".join(missing))]
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if quick:
        return [(row["label"], True, "files present")]
    if meta.get("kind") == "legacy":
        wanted_any = meta.get("flags") or meta.get("extra_flags") or meta.get("focus") == "flag"
        if not wanted_any:
            return [(row["label"], True, "no options to verify (the script takes none)")]
        if meta.get("module"):
            cmd, cwd = [sys.executable, "-m", meta["module"]], API_HOME / "vendor" / meta["module_root"]
        else:
            real = API_HOME / "vendor" / meta["vendor"]
            if not real.exists():
                return [(row["label"], False, f"vendored script missing: vendor/{meta['vendor']}")]
            cmd, cwd = [sys.executable, str(real)], real.parent
        ok, text = _help(cmd, cwd)
        wanted = list(meta.get("flags", {}).values()) + list(meta.get("extra_flags", {}).values())
        if meta.get("focus") == "flag":
            wanted.append(meta["focus_flag"])
        if not ok:
            reason = (text.strip().splitlines() or ["no output"])[-1][:120]
            out.append((row["label"], None, f"could not run --help here ({reason}); flags not verified"))
        else:
            absent = [f for f in wanted if f not in text]
            out.append((row["label"], not absent, "all mapped flags exist in the real script" if not absent
                        else f"station.json maps flags the script does not have: {', '.join(absent)}"))
    else:
        ok, text = _help([sys.executable, str(script)], folder)
        if not ok and "usage" not in text:
            out.append((row["label"], False, f"--help failed: {(text.strip().splitlines() or [''])[-1][:120]}"))
        else:
            absent = [NATIVE_FLAGS[o] for o in meta.get("options", []) if o in NATIVE_FLAGS and NATIVE_FLAGS[o] not in text]
            out.append((row["label"], not absent, "options match --help" if not absent
                        else f"declares options its script lacks: {', '.join(absent)}"))
    return out


def check(quick: bool = False) -> tuple[int, list[tuple[str, str, bool | None, str]]]:
    results: list[tuple[str, str, bool | None, str]] = []
    specs = key_specs()
    for key, raw in load_paths().items():
        if key == "search_roots":
            continue
        value = os.environ.get(f"ONE_MENU_{key.upper()}", "").strip() or raw.strip()
        if not value:
            results.append(("path", key, None, f"not set · {specs.get(key, {}).get('what', '')}"))
            continue
        path = expand(value)
        ok = path.exists() or bool(specs.get(key, {}).get("create"))
        results.append(("path", key, ok, str(path) + ("" if path.exists() else " (created on first use)" if ok else " MISSING")))
    rows = [r for r in json.loads((API_HOME / "config" / "stations.json").read_text(encoding="utf-8")) if not r.get("retired")]
    numbers = [r["number"] for r in rows]
    if len(numbers) != len(set(numbers)):
        results.append(("station", "numbers", False, "duplicate station numbers in stations.json"))
    for row in rows:
        for name, ok, detail in check_station(row, quick):
            results.append(("station", name, ok, detail))
    for env in KEYS:
        present = bool(os.environ.get(env))
        results.append(("key", env, present if env == "DEEPSEEK_API_KEY" else (True if present else None),
                        "present" if present else "missing"))
    failed = [r for r in results if r[2] is False and r[0] == "station"]
    return (1 if failed else 0), results


def main(quick: bool = False) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="90_HEALTHCHECK", description="Check every station, path key and API key.")
    parser.add_argument("items", nargs="*", help=argparse.SUPPRESS)
    parser.add_argument("--quick", action="store_true", help="skip running each script's --help")
    parser.add_argument("--dry-run", action="store_true", help=argparse.SUPPRESS)
    quick = quick or parser.parse_known_args()[0].quick
    code, results = check(quick)
    mark = {True: "OK     ", False: "PROBLEM", None: "note   "}
    for kind, name, ok, detail in results:
        print(f"  {mark[ok]} {kind:<7} {name:<30} {detail}")
    problems = sum(1 for r in results if r[2] is False)
    print(f"\n{problems} problem(s)." + ("" if not quick else "  (quick: option checks skipped)"))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
