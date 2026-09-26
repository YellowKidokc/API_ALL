#!/usr/bin/env python3
"""ATOMS station runner — classify sources into claim atoms.

Reads WORKSPACE/OUTBOX/01_PRIORITY, WORKSPACE/OUTBOX/02_SERIES,
WORKSPACE/OUTBOX/03_GENERAL (.md/.txt), calls the LLM, appends atom
classification to the bottom of each paper, and writes JSON records to
WORKSPACE/OUTBOX/06_JSON_RECORDS.

Default workspace is ../../OUTBOX relative to this script.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure imports work when the script is invoked from any cwd.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from llm_client import complete
from atom_prompt import build_atom_prompt
from atom_io import paper_uuid, write_json_record, enrich_markdown_companion, preserve_original

SUPPORTED_EXTS = {".md", ".txt"}
MAX_SOURCE_CHARS = 100_000


def _root(cli_root: Path | None = None) -> Path:
    if cli_root is not None:
        return cli_root
    return _SCRIPT_DIR.parent


def _workspace(root: Path, cli_workspace: Path | None = None) -> Path:
    if cli_workspace is not None:
        return cli_workspace
    # Default: ../../OUTBOX from API_DEEP/ATOMS -> APIs/APIs/OUTBOX
    return root.parents[1] / "OUTBOX"


OUTBOX_INPUT_DIRS = ["01_PRIORITY", "02_SERIES", "03_GENERAL"]


def _scan_outbox(workspace: Path) -> list[Path]:
    """Scan the WORKSPACE priority/series/general folders for papers to enrich."""
    items: list[Path] = []
    for sub in OUTBOX_INPUT_DIRS:
        folder = workspace / sub
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTS:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if len(text) > MAX_SOURCE_CHARS:
                print(f"  WARNING: skipping oversized file {path}")
                continue
            items.append(path)
    return items


def _parse_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


def _process_item(workspace: Path, item: Path, provider: str) -> dict:
    puuid = paper_uuid(item)
    short_uuid = puuid[:8]
    print(f"[{short_uuid}] {item.name} — reading", flush=True)
    source_text = item.read_text(encoding="utf-8")

    print(f"[{short_uuid}] {item.name} — classifying atoms", flush=True)
    prompt = build_atom_prompt(source_text)
    result = complete(provider, prompt, json_mode=True)

    try:
        data = _parse_json(result)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Provider returned invalid JSON: {exc}") from exc

    # Enforce the source identity fields. The model may hallucinate these;
    # the station's generated IDs are authoritative.
    data["paper_uuid"] = puuid
    data["source_path"] = str(item)
    data.setdefault("title", item.stem)
    data.setdefault("atoms", [])

    preserve_original(workspace, data, item)
    json_path = write_json_record(workspace, puuid, data)
    md_path = enrich_markdown_companion(workspace, puuid, data, item, target_path=item)

    print(f"[{short_uuid}] {item.name} — wrote {md_path.name} + {json_path.name}", flush=True)
    return {"item": item, "paper_uuid": puuid, "status": "OK"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ATOMS station runner")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="ATOMS station root directory (default: parent of script)",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Workspace directory containing OUTBOX (default: ../../OUTBOX relative to root)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="deepseek",
        help="LLM provider to use (default: deepseek)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Process at most N items",
    )
    args = parser.parse_args(argv)

    root = _root(args.root)
    workspace = _workspace(root, args.workspace)
    items = _scan_outbox(workspace)
    print(f"ATOMS station: {len(items)} eligible item(s) in {workspace}")

    if not items:
        print("No eligible items found in WORKSPACE/01_PRIORITY, WORKSPACE/02_SERIES, or WORKSPACE/03_GENERAL.")
        return 0

    if args.max_items is not None:
        items = items[: args.max_items]
        print(f"--max-items set: processing {len(items)} item(s).")

    results = []
    for item in items:
        try:
            result = _process_item(workspace, item, args.provider)
            results.append(result)
        except Exception as exc:
            print(f"  ERROR processing {item}: {exc}")
            results.append({"item": item, "status": "FAILED", "error": str(exc)})

    ok = sum(1 for r in results if r.get("status") == "OK")
    failed = len(results) - ok
    print(f"\nResults: {ok} ok, {failed} failed, {len(results)} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
