#!/usr/bin/env python3
"""CLI entry point for the CKG source-review station."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# Windows consoles default to cp1252; the CKG pipeline emits Unicode arrows,
# math symbols, and source text. Force UTF-8 for stdout/stderr before any print.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

# Ensure the CKG station root is importable even when the runner is invoked
# from a batch file or a UNC path where the current directory is not in sys.path.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from workbench.ckg import initialize, lock, scan, scan_verbose, Runner, master_template_path
from workbench.extract_cpe import extract_all
from workbench.paper_type import tagged_name
from workbench.providers import load_local_keys, provider_from_config


def _root(cli_root: Path | None = None) -> Path:
    if cli_root is not None:
        return cli_root
    return Path(__file__).resolve().parents[1]


def _config_dir(root: Path) -> Path:
    """Return CONFIG dir, preferring the hidden _BACKSIDE location."""
    hidden = root.parent / "_BACKSIDE" / "CKG" / "CONFIG"
    if hidden.exists():
        return hidden
    legacy = root / "CONFIG"
    if legacy.exists():
        return legacy
    return hidden


def _load_config(root: Path) -> dict:
    path = _config_dir(root) / "ckg.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Malformed CONFIG/ckg.json: {exc}")
    return {}


def _master_index_path(root: Path) -> Path:
    return root / "OUTBOX" / "00_MASTER_INDEX.csv"


def _write_master_index(root: Path, results: list[dict]) -> None:
    index_path = _master_index_path(root)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "paper_uuid",
                "source_path",
                "status",
                "stage",
                "error",
            ],
        )
        writer.writeheader()
        for res in results:
            writer.writerow(
                {
                    "paper_uuid": res.get("paper_uuid", ""),
                    "source_path": str(res.get("item", "")),
                    "status": res.get("status", ""),
                    "stage": res.get("stage", ""),
                    "error": res.get("error", ""),
                }
            )


def _print_scan_summary(
    root: Path,
    items: list[Path],
    total: int,
    counts: dict[str, int],
    excluded: list[str],
) -> None:
    """Print the same scan summary used before both inventory and run."""
    print("=" * 60)
    print("SCAN SUMMARY")
    print("=" * 60)
    print(f"  Total files found:   {total}")
    print(f"  Eligible for run:    {counts.get('eligible', 0)}")
    print(f"  Waiting/excluded:    {counts.get('waiting', 0)}")
    print(f"  Unsupported format:  {counts.get('unsupported', 0)}")
    print(f"  Oversized (>100k):   {counts.get('oversized', 0)}")
    print(f"  Content duplicates:  {counts.get('duplicate', 0)}")
    print("=" * 60)

    if not items:
        print("No eligible inbox items found.")
        return

    duplicates = [line for line in excluded if line.startswith("DUPLICATE:")]
    if duplicates:
        print("\nDuplicates detected (first occurrence kept):")
        for line in duplicates[:20]:
            print(f"  {line}")
        if len(duplicates) > 20:
            print(f"  ... and {len(duplicates) - 20} more")

    print("\nEligible items:")
    for i, item in enumerate(items, start=1):
        print(f"  {i:3d}. {item.relative_to(root / 'INBOX')}")


def cmd_inventory(root: Path, _config: dict) -> int:
    """List eligible inbox items without making any API calls."""
    items, total, counts, excluded = scan_verbose(root)
    _print_scan_summary(root, items, total, counts, excluded)
    return 0


def _safe_filename(text: str) -> str:
    """Make a filesystem-safe, readable stem from free text."""
    import re
    safe = re.sub(r"[^\w\s-]", "", text.strip()).strip()
    safe = re.sub(r"[-\s]+", "_", safe)
    return safe[:80].strip("_")


def _read_map(root: Path, paper_uuid: str) -> dict:
    """Load the map checkpoint for a paper, if present."""
    path = root / "SYSTEM" / "RECORDS" / paper_uuid / "map.json"
    if not path.exists():
        return {}
    try:
        wrapped = json.loads(path.read_text(encoding="utf-8"))
        return wrapped.get("data", {})
    except (json.JSONDecodeError, KeyError):
        return {}


def _companion_name(map_data: dict, paper_uuid: str) -> str:
    """Readable companion filename with a leading type tag."""
    return tagged_name(map_data, paper_uuid, ".md")


def _original_name(map_data: dict, paper_uuid: str) -> str:
    """Readable original filename with a leading type tag."""
    return f"{Path(_companion_name(map_data, paper_uuid)).stem}_original.md"


def _publish_to_root(
    root: Path, paper_uuid: str, map_data: dict, original_path: Path
) -> None:
    """Publish the companion and processed original into the OUTBOX root with readable names."""
    from workbench.ckg import atomic

    companion = root / "OUTBOX" / f"{paper_uuid}.md"
    if companion.exists():
        atomic(root / "OUTBOX" / _companion_name(map_data, paper_uuid), companion.read_bytes())

    if original_path.exists():
        suffix = original_path.suffix
        if suffix == ".md":
            name = _original_name(map_data, paper_uuid)
        else:
            name = f"{Path(_companion_name(map_data, paper_uuid)).stem}{suffix}"
        atomic(root / "OUTBOX" / name, original_path.read_bytes())


def _classify_companion(root: Path, paper_uuid: str, map_data: dict) -> None:
    """Copy a completed companion into domain, series, and tag classification folders."""
    companion = root / "OUTBOX" / f"{paper_uuid}.md"
    if not companion.exists():
        return
    name = _companion_name(map_data, paper_uuid)
    domain = _safe_filename(map_data.get("domain") or "UNKNOWN") or "UNKNOWN"
    project = _safe_filename(map_data.get("project") or "UNKNOWN") or "UNKNOWN"
    keywords = map_data.get("keywords") or []
    labels = [("02_BY_DOMAIN", domain), ("04_BY_SERIES", project)]
    for kw in keywords:
        tag = _safe_filename(str(kw)) or "UNKNOWN"
        labels.append(("03_BY_TAG", tag))
    for folder, label in labels:
        dest = root / "OUTBOX" / folder / label / name
        if dest == companion:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        from workbench.ckg import atomic
        atomic(dest, companion.read_bytes())


def _move_processed_to_outbox(root: Path, results: list[dict]) -> None:
    """Move successfully processed inbox items to OUTBOX/00_ORIGINAL, preserving structure."""
    original_dir = root / "OUTBOX" / "00_ORIGINAL"
    moved = 0
    for res in results:
        if res.get("status") != "SOURCE_REVIEW_COMPLETE":
            continue
        item = res.get("item")
        paper_uuid = res.get("paper_uuid") or ""
        if not isinstance(item, Path):
            continue
        try:
            rel = item.relative_to(root / "INBOX")
        except ValueError:
            rel = Path(item.name)
        map_data = _read_map(root, paper_uuid) if paper_uuid else {}
        new_name = tagged_name(map_data, paper_uuid, item.suffix)
        dest = original_dir / rel.parent / new_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            item.rename(dest)
            moved += 1
        except OSError as exc:
            print(f"  WARNING: could not move {item} to {dest}: {exc}")
            continue
        _classify_companion(root, paper_uuid, map_data)
        _publish_to_root(root, paper_uuid, map_data, dest)
    if moved:
        print(f"Moved {moved} processed item(s) to OUTBOX/00_ORIGINAL")


def _prompt_item_count(eligible: int) -> int:
    """Ask the user how many eligible items to process."""
    prompt = f"How many items do you want to process? (1-{eligible}, Enter=all): "
    while True:
        answer = input(prompt).strip()
        if answer == "":
            return eligible
        try:
            n = int(answer)
        except ValueError:
            print("Please enter a number, or press Enter for all.")
            continue
        if n < 1:
            print("Minimum is 1.")
            continue
        if n > eligible:
            print(f"Maximum is {eligible}.")
            continue
        return n


def cmd_run(
    root: Path,
    config: dict,
    workers: int | None,
    yes: bool = False,
    max_items: int | None = None,
) -> int:
    """Run the CKG pipeline against eligible inbox items."""
    workers = workers if workers is not None else config.get("workers", 1)
    template_path = master_template_path(root)
    if not template_path.exists():
        raise SystemExit(f"Master template not found: {template_path}")

    keys = load_local_keys(root)
    provider = provider_from_config(config, root)

    with lock(root):
        initialize(root)
        items, total, counts, excluded = scan_verbose(root)
        _print_scan_summary(root, items, total, counts, excluded)

        if not items:
            return 0

        if max_items is not None:
            n = min(max_items, len(items))
            print(f"\n--max-items set: processing {n} item(s).")
        elif yes:
            n = len(items)
            print(f"\n--yes set: processing all {n} item(s).")
        else:
            n = _prompt_item_count(len(items))

        items = items[:n]
        print(f"\nProcessing {len(items)} item(s) with {workers} worker(s)...")
        runner = Runner(root, provider)
        results = runner.batch(items, workers)

        _write_master_index(root, results)
        _move_processed_to_outbox(root, results)

        # Extract claims / proofs / evidence atoms from all companions.
        counts = extract_all(root)
        print(f"Extracted {sum(counts.values())} CPE atom(s): {counts}")

        complete = sum(1 for r in results if r["status"] == "SOURCE_REVIEW_COMPLETE")
        failed = len(results) - complete
        print(f"Results: {complete} complete, {failed} failed, {len(results)} total")
        if failed:
            for r in results:
                if r["status"] != "SOURCE_REVIEW_COMPLETE":
                    print(f"  FAILED: {r['item']} — {r.get('error', 'unknown')}")
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CKG source-review runner")
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="List eligible inbox items without API calls",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Concurrent workers (default: CONFIG/ckg.json -> 1)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="CKG station root directory (default: inferred from script location)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Process all eligible items without prompting (non-interactive mode)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Process at most N items (overrides the interactive prompt)",
    )
    args = parser.parse_args(argv)

    root = _root(args.root)
    config = _load_config(root)

    if args.inventory:
        return cmd_inventory(root, config)
    return cmd_run(root, config, args.workers, yes=args.yes, max_items=args.max_items)


if __name__ == "__main__":
    raise SystemExit(main())
