"""Series manifest builder and helpers for the CKG series pipeline."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from workbench.ckg import atomic, lock, save


def _extract_paper_uuid(filename: str) -> str:
    """Best-effort extraction of a stable paper UUID from a companion filename.

    The runner names companions ``<paper_uuid>.md``. Legacy files may prefix a
    title, so the last 64-character hex token is preferred; otherwise the
    frontmatter ``paper_uuid`` is read.
    """
    path = Path(filename)
    stem = path.stem
    hex_tokens = re.findall(r"[0-9a-f]{64}", stem)
    if hex_tokens:
        return hex_tokens[-1]
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^paper_uuid:\s*([0-9a-f]+)", text, re.MULTILINE)
        if m:
            return m.group(1)
    return stem


def scan_series(series_dir: Path) -> list[dict[str, Any]]:
    """List companion files in ``series_dir`` and build member records."""
    members: list[dict[str, Any]] = []
    for path in sorted(series_dir.glob("*.md")):
        if path.name.startswith("00_"):
            continue
        if "GRAND_SYNTHESIS" in path.name.upper():
            continue
        paper_uuid = _extract_paper_uuid(path.name)
        text = path.read_text(encoding="utf-8", errors="replace")
        members.append(
            {
                "paper_uuid": paper_uuid,
                "filename": path.name,
                "path": str(path),
                "sha256": _sha256(path),
                "status": "INCLUDED",
            }
        )
    return members


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(series_dir: Path) -> dict[str, Any]:
    """Create the 00_SERIES_MANIFEST.json payload for a single series."""
    members = scan_series(series_dir)
    return {
        "series": series_dir.name,
        "series_dir": str(series_dir),
        "members": members,
        "member_count": len(members),
    }


def build_all_manifests(root: Path) -> list[dict[str, Any]]:
    """Build manifests for every series folder under OUTBOX/04_BY_SERIES."""
    series_root = root / "OUTBOX" / "04_BY_SERIES"
    manifests: list[dict[str, Any]] = []
    if not series_root.exists():
        return manifests
    for series_dir in sorted(series_root.iterdir()):
        if not series_dir.is_dir() or series_dir.name in {"SCRIPTS", "LEGACY_REFERENCE"}:
            continue
        manifest = build_manifest(series_dir)
        save(series_dir / "00_SERIES_MANIFEST.json", manifest)
        manifests.append(manifest)
    return manifests


def main() -> int:
    parser = argparse.ArgumentParser(description="CKG series manifest builder")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--series", type=str, default=None, help="Single series folder name")
    args = parser.parse_args()

    with lock(args.root):
        if args.series:
            series_dir = args.root / "OUTBOX" / "04_BY_SERIES" / args.series
            if not series_dir.is_dir():
                raise FileNotFoundError(f"Series folder not found: {series_dir}")
            manifest = build_manifest(series_dir)
            save(series_dir / "00_SERIES_MANIFEST.json", manifest)
            print(
                f"[series_tools] Wrote manifest for {args.series}: "
                f"{manifest['member_count']} member(s)"
            )
        else:
            manifests = build_all_manifests(args.root)
            print(
                f"[series_tools] Wrote {len(manifests)} series manifest(s) under "
                f"{(args.root / 'OUTBOX' / '04_BY_SERIES')}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
