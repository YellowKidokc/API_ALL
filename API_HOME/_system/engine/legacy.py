"""Runner for wrapped (legacy) stations whose code lives in API_HOME/vendor/.

Everything about a wrapped station is declared once in its station.json:

  "vendor":  "evidence/SCRIPTS/turbo_pipeline_runner.py"   script inside API_HOME/vendor
  "module":  "workbench.ckg"                                (optional) run with -m, cwd = vendor dir
  "args":    ["--root", "{evidence_root}"]                  fixed args; {key} = a paths.json key
  "flags":   {"limit": "--limit", "workers": "--workers", "redo": "--force"}
             menu option -> the script's REAL flag. Only these options are offered.
  "provider_values": {"deepseek": "deepseek", "openrouter": "openrouter"}
             provider names the script accepts (others are not forwarded)
  "items":   "positional" | "--input" | null               how selected items are passed
  "focus":   "gateway"                                     focus reaches the prompts via the relay

Every configured path key is exported to the script as ONE_MENU_PATH_<KEY>; the vendored
code reads those instead of the drive letters it used to contain (see MIGRATION_REPORT.md).
API calls reach engine/gateway.py through DEEPSEEK_BASE_URL / OPENAI_BASE_URL / ... which the
menu sets, so the global limiter, retries and receipts cover legacy code too.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from .paths import API_HOME, PathConfigurationError, expand, external, inside, load_paths


def options(meta: dict) -> list[str]:
    """The menu options this station really accepts, derived from its flag map."""
    opts = list(meta.get("flags", {}))
    if meta.get("focus") in ("gateway", "flag"):
        opts.append("focus")
    opts += list(meta.get("extra_flags", {}))
    if meta.get("channel_item"):
        opts.append("channel")
    return [o for o in dict.fromkeys(opts) if o != "dry_run"]


def path_env() -> dict[str, str]:
    env = {}
    for key, raw in load_paths().items():
        value = os.environ.get(f"ONE_MENU_{key.upper()}", "").strip() or raw.strip()
        if value:
            env[f"ONE_MENU_PATH_{key.upper()}"] = str(expand(value))
    env["ONE_MENU_HOME"] = str(API_HOME)
    return env


def _fill(template: str) -> str:
    def repl(match: re.Match) -> str:
        key = match.group(1)
        if key == "API_HOME":
            return str(API_HOME)
        if key == "python":
            return sys.executable
        if key == "channel":
            return "{channel}"
        return str(external(key, create=key.endswith("_root") or key.startswith("yt_")))
    return re.sub(r"\{([a-zA-Z0-9_]+)\}", repl, template)


def build_command(meta: dict, args: argparse.Namespace, passthrough: list[str]) -> tuple[list[str], Path]:
    vendor_dir = inside("vendor")
    if meta.get("module"):
        cwd = inside("vendor", meta["module_root"])
        cmd = [sys.executable, "-m", meta["module"]]
    else:
        script = inside("vendor", meta["vendor"])
        if not script.is_file():
            raise FileNotFoundError(f"vendored script missing: {script} (run tools/migrate_legacy.py)")
        cwd = inside("vendor", meta.get("cwd", str(Path(meta["vendor"]).parent)))
        cmd = [sys.executable, str(script)]
    cmd += [_fill(a) for a in meta.get("args", [])]
    flags = meta.get("flags", {})
    values = {"limit": args.limit, "workers": args.workers}
    if args.model and (not meta.get("model_values") or args.model in meta["model_values"]):
        values["model"] = args.model
    for option, value in values.items():
        if value is not None and option in flags:
            cmd += [flags[option], str(value)]
    if args.provider and "provider" in flags:
        mapped = meta.get("provider_values", {}).get(args.provider)
        if mapped:
            cmd += [flags["provider"], mapped]
        else:
            print(f"note: this script cannot use provider '{args.provider}'; it keeps its own default", file=sys.stderr)
    if args.redo and "redo" in flags:
        cmd.append(flags["redo"])
    if args.dry_run and "dry_run" in flags:
        cmd.append(flags["dry_run"])
    for extra, flag in meta.get("extra_flags", {}).items():
        value = getattr(args, extra, None)
        if value not in (None, False, ""):
            cmd += [flag] if value is True else [flag, str(value)]
    if args.focus and meta.get("focus") == "flag":
        cmd += [meta["focus_flag"], "; ".join(args.focus)]
    items = list(args.items)
    if not items and getattr(args, "channel", None) and meta.get("channel_item"):
        items = [_fill(meta["channel_item"]).replace("{channel}", args.channel)]
    if not items and meta.get("default_items"):
        items = [_fill(x) for x in meta["default_items"]]
    how = meta.get("items")
    for item in items:
        if how == "positional":
            cmd.append(item)
        elif how:
            cmd += [how, item]
    if meta.get("subcommand"):
        cmd.append(getattr(args, "command", None) or meta["subcommand"])
    cmd += passthrough
    return cmd, cwd if cwd.exists() else vendor_dir


def main(label: str) -> int:
    meta = json.loads((API_HOME / "stations" / label / "station.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(prog=label, description=meta.get("description", ""))
    parser.add_argument("items", nargs="*")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--focus", action="append", default=[])
    parser.add_argument("--redo", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    if meta.get("channel_item"):
        parser.add_argument("--channel")
    if meta.get("subcommand"):
        parser.add_argument("--command", help=f"subcommand (default {meta['subcommand']})")
    for extra, flag in meta.get("extra_flags", {}).items():
        kind = meta.get("extra_types", {}).get(extra, "str")
        if kind == "bool":
            parser.add_argument(f"--{extra.replace('_', '-')}", dest=extra, action="store_true")
        else:
            parser.add_argument(f"--{extra.replace('_', '-')}", dest=extra)
    args, passthrough = parser.parse_known_args()
    unsupported = [name for name, value in (("limit", args.limit), ("workers", args.workers), ("model", args.model),
                                            ("redo", args.redo)) if value not in (None, False) and name not in meta.get("flags", {})]
    if unsupported:
        print(f"{label}: ignoring options this script does not have: {', '.join(unsupported)}", file=sys.stderr)
    if args.focus and meta.get("focus") not in ("gateway", "flag"):
        print(f"{label}: this script cannot take extra focus; it was not sent", file=sys.stderr)
    elif args.focus and not os.environ.get("ONE_MENU_GATEWAY"):
        print(f"{label}: focus reaches this script only when run through ONE_MENU (the relay adds it)", file=sys.stderr)
    try:
        cmd, cwd = build_command(meta, args, passthrough)
    except (PathConfigurationError, FileNotFoundError) as exc:
        print(f"{label}: {exc}", file=sys.stderr)
        return 2
    env = {**os.environ, **path_env(), "PYTHONIOENCODING": "utf-8"}
    for key, value in meta.get("env", {}).items():
        env[key] = _fill(value)
    print(f"{label}: $ {' '.join(cmd)}\n   (in {cwd})", flush=True)
    if args.dry_run and "dry_run" not in meta.get("flags", {}):
        print(f"{label}: dry run: the command above was not started")
        return 0
    stdin = None
    if meta.get("answers"):
        stdin = "\n".join(_fill(a) for a in meta["answers"]) + "\n"
    completed = subprocess.run(cmd, cwd=cwd, env=env, input=stdin, text=stdin is not None)
    return completed.returncode
