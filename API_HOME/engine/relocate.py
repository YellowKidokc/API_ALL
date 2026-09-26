"""RELOCATE: run after moving API_HOME (or the drives around it). One pass fixes every external path.

For each key in config/paths.json:
  FOUND     the path exists: kept.
  MOVED     it doesn't, but RELOCATE found it again. It tries, in order:
              1. the same position relative to API_HOME as before the move (folder moved together)
              2. the same path on every other drive letter (D: -> E:)
              3. a search under search_roots and the folders around API_HOME, matching the folder
                 name and its fingerprint file (e.g. INBOX, lakefile.lean, .obsidian)
            You confirm each (Enter = accept). With --auto every find is accepted.
  MISSING   nothing found: type the new location, or Enter to keep the old value.

Relative values (../ONE_MENU_DATA/...) move with the folder and never need fixing.
Nothing else changes, because no script holds a path. Ends with the station 90 health check.

  RELOCATE.bat            interactive
  RELOCATE.bat --auto     accept every find, ask nothing (missing stay as they are)
"""
from __future__ import annotations

import json
import os
import string
import sys
from pathlib import Path, PureWindowsPath

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.paths import API_HOME, CONFIG_DIR, config_file, expand, key_specs  # noqa: E402

MAX_DEPTH = 4


def _drives() -> list[str]:
    if os.name != "nt":
        return []
    return [f"{d}:\\" for d in string.ascii_uppercase if Path(f"{d}:\\").exists()]


def _fits(candidate: Path, spec: dict, name: str, parent: str = "") -> bool:
    if not candidate.exists() or candidate.name.lower() != name.lower():
        return False
    try:  # never "find" something inside API_HOME itself (vendor/, stations/ ...)
        candidate.resolve().relative_to(API_HOME)
        return False
    except ValueError:
        pass
    if parent and candidate.parent.name.lower() != parent.lower():
        return False
    fingerprint = spec.get("fingerprint")
    return not fingerprint or (candidate / fingerprint).exists()


def _search(name: str, spec: dict, roots: list[Path], parent: str = "") -> Path | None:
    for root in roots:
        if not root.is_dir():
            continue
        frontier = [(root, 0)]
        while frontier:
            folder, depth = frontier.pop(0)
            candidate = folder / name
            if _fits(candidate, spec, name, parent):
                return candidate
            if depth >= MAX_DEPTH:
                continue
            try:
                children = [c for c in folder.iterdir() if c.is_dir() and not c.name.startswith((".", "$"))]
            except OSError:
                continue
            frontier.extend((c, depth + 1) for c in children[:400])
    return None


def find_again(raw: str, spec: dict, old_home: str | None, roots: list[Path]) -> Path | None:
    old = PureWindowsPath(raw) if (":" in raw[:3] or raw.startswith("\\\\")) else Path(raw)  # noqa-path
    name = old.name
    parent = old.parent.name
    if old_home:  # 1. same position relative to API_HOME
        try:
            rel = os.path.relpath(str(old), old_home)
            candidate = (API_HOME / rel).resolve()
            if _fits(candidate, spec, name):
                return candidate
            # a folder created on first use may not exist yet: keep its relative position if its parent moved along
            if spec.get("create") and candidate.parent.exists():
                return candidate
        except ValueError:
            pass
    if isinstance(old, PureWindowsPath) and old.drive:  # 2. other drive letters
        tail = str(old)[len(old.drive):].lstrip("\\/")
        for drive in _drives():
            candidate = Path(drive) / tail
            if _fits(candidate, spec, name):
                return candidate
    return _search(name, spec, roots, parent) if name else None  # 3. search (name and parent folder must match)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="RELOCATE", description="Find every external path again after a move.")
    parser.add_argument("items", nargs="*", help=argparse.SUPPRESS)
    parser.add_argument("--auto", action="store_true", help="accept every find, ask nothing")
    parser.add_argument("--dry-run", action="store_true", help="show what would change, save nothing")
    opts = parser.parse_known_args()[0]
    auto = opts.auto
    interactive = sys.stdin.isatty() and not auto
    specs = key_specs()
    example = json.loads((CONFIG_DIR / "paths.example.json").read_text(encoding="utf-8"))
    target = config_file()
    current = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    old_home = current.get("_api_home")
    if old_home and Path(old_home) != API_HOME:
        print(f"API_HOME moved: {old_home}  ->  {API_HOME}\n")
    roots_raw = str(current.get("search_roots") or "")
    roots = [expand(r) for r in roots_raw.split(";") if r.strip()] + [API_HOME.parent, API_HOME.parent.parent]
    roots += [Path(d) for d in _drives()]
    changed = 0
    for key in [k for k in example if k != "search_roots"]:
        spec = specs.get(key, {})
        raw = str(current.get(key, example.get(key, ""))).strip()
        if not raw:
            print(f"  -        {key:<24} not set ({spec.get('what', '')})")
            current.setdefault(key, "")
            continue
        path = expand(raw)
        if path.exists() or (spec.get("create") and not Path(raw).is_absolute() and ":" not in raw[:3]):
            print(f"  FOUND    {key:<24} {raw}")
            current[key] = raw
            continue
        guess = find_again(raw, spec, old_home, roots)
        if guess:
            accept = True
            if interactive:
                accept = input(f"  MOVED?   {key:<24} {raw}\n           found at {guess}  use it? [Y/n] ").strip().lower() not in ("n", "no")
            if accept:
                print(f"  MOVED    {key:<24} {raw}  ->  {guess}")
                current[key] = str(guess)
                changed += 1
                continue
        print(f"  MISSING  {key:<24} {raw}   ({spec.get('what', '')})")
        if interactive:
            value = input("           new location (Enter keeps it): ").strip().strip('"')
            if value:
                if expand(value).exists() or spec.get("create"):
                    current[key] = value
                    changed += 1
                else:
                    print("           not found; kept the old value")
    current["_api_home"] = str(API_HOME)
    current.setdefault("search_roots", roots_raw)
    if opts.dry_run:
        print(f"\nDry run: {changed} change(s) found, nothing saved.")
        return 0
    target.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved {target} ({changed} change(s)).\n")
    from engine.health import main as health
    return health(quick=True)


if __name__ == "__main__":
    raise SystemExit(main())
