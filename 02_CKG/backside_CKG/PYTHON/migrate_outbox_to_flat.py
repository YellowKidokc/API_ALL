#!/usr/bin/env python3
"""One-time migration: flatten CKG OUTBOX so companions live at the root.

- Moves companions from OUTBOX/01_ALL_PAPERS to OUTBOX/ with readable names.
- Renames any UUID-only root files (companions and originals) to readable names.
- Removes duplicate originals such as ``foo_original_001.md`` when
  ``foo_original.md`` already exists.
- Copies processed originals from OUTBOX/00_ORIGINAL to OUTBOX/ with readable
  names (adds '_original' suffix).
- Leaves classification folders (02_BY_DOMAIN, 03_BY_TAG, 04_BY_SERIES)
  and CLAIMS_PROOFS_EVIDENCE untouched.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

_SCRIPT = Path(__file__).absolute()
_BACKSIDE_CKG = _SCRIPT.parents[1]          # .../_BACKSIDE/CKG
_VISIBLE_CKG = _BACKSIDE_CKG.parents[1] / "CKG"  # .../CKG (visible station root)
for p in (_BACKSIDE_CKG, _VISIBLE_CKG):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from workbench.ckg import atomic
from workbench.paper_type import tagged_name


_UUID_RE = re.compile(r"[0-9a-f]{64}")
_ORIGINAL_SUFFIX_RE = re.compile(r"_original(_\d{3})?$")


def _read_map(root: Path, paper_uuid: str) -> dict:
    candidates = [
        root / "SYSTEM" / "RECORDS" / paper_uuid / "map.json",
        root.parent / "_BACKSIDE" / "CKG" / "SYSTEM" / "RECORDS" / paper_uuid / "map.json",
    ]
    for cand in candidates:
        if cand.exists():
            try:
                wrapped = json.loads(cand.read_text(encoding="utf-8"))
                return wrapped.get("data", {})
            except (json.JSONDecodeError, OSError):
                pass
    return {}


def _extract_uuid(path: Path) -> str | None:
    """Best-effort paper UUID from filename or frontmatter."""
    stem = path.stem
    m = _ORIGINAL_SUFFIX_RE.search(stem)
    if m:
        stem = stem[: m.start()]
    tokens = _UUID_RE.findall(stem)
    if tokens:
        return tokens[-1]
    if path.exists():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        m2 = re.search(r"^paper_uuid:\s*([0-9a-f]+)", text, re.MULTILINE)
        if m2 and len(m2.group(1)) >= 64:
            return m2.group(1)
    return None


def _is_original(path: Path) -> bool:
    return bool(_ORIGINAL_SUFFIX_RE.search(path.stem))


def _desired_root_name(map_data: dict, paper_uuid: str, is_original: bool) -> str:
    base = tagged_name(map_data, paper_uuid, ".md")
    if is_original:
        return f"{Path(base).stem}_original.md"
    return base


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unique_dest(folder: Path, name: str) -> Path:
    dest = folder / name
    if not dest.exists():
        return dest
    stem = Path(name).stem
    suffix = Path(name).suffix
    for i in range(1, 1000):
        cand = folder / f"{stem}_{i:03d}{suffix}"
        if not cand.exists():
            return cand
    raise RuntimeError(f"Could not find unique name for {name}")


def _root_uuids(outbox: Path) -> set[str]:
    """Collect UUIDs already represented at the OUTBOX root."""
    found: set[str] = set()
    for path in outbox.glob("*.md"):
        uuid = _extract_uuid(path)
        if uuid:
            found.add(uuid)
    return found


def migrate(root: Path) -> dict[str, int]:
    print(f"[migrate] root={root} exists={root.exists()}")
    counts = {
        "companions_moved": 0,
        "root_renamed": 0,
        "duplicates_removed": 0,
        "originals_copied": 0,
    }
    all_papers = root / "OUTBOX" / "01_ALL_PAPERS"
    print(f"[migrate] all_papers={all_papers} exists={all_papers.exists()}")
    original_dir = root / "OUTBOX" / "00_ORIGINAL"
    outbox = root / "OUTBOX"

    # 1. Move any remaining companions from the legacy flat folder.
    if all_papers.exists():
        for path in sorted(all_papers.glob("*.md")):
            paper_uuid = path.stem
            map_data = _read_map(root, paper_uuid)
            name = _derived_name(map_data, paper_uuid, ".md")
            dest = _unique_dest(outbox, name)
            shutil.move(str(path), str(dest))
            counts["companions_moved"] += 1

    # 2. Rename UUID-only / duplicate files already at the root.
    for path in sorted(outbox.glob("*.md")):
        paper_uuid = _extract_uuid(path)
        if not paper_uuid:
            continue
        map_data = _read_map(root, paper_uuid)
        desired = _desired_root_name(map_data, paper_uuid, _is_original(path))
        if desired == path.name:
            continue
        dest = outbox / desired
        if dest.exists():
            # Same paper already has the target name -> this file is a duplicate.
            if (
                _extract_uuid(dest) == paper_uuid
                and _is_original(dest) == _is_original(path)
            ):
                # Keep the shorter / non-numbered name; remove the duplicate if identical.
                if _sha256(dest) == _sha256(path):
                    path.unlink()
                    counts["duplicates_removed"] += 1
                    continue
                # Same content not verified -> fall back to a numbered suffix.
                dest = _unique_dest(outbox, desired)
            else:
                # Different paper occupies the name -> use a numbered suffix.
                dest = _unique_dest(outbox, desired)
        shutil.move(str(path), str(dest))
        counts["root_renamed"] += 1

    # 3. Copy processed originals if their UUID is not already at the root.
    present_uuids = _root_uuids(outbox)
    if original_dir.exists():
        for path in sorted(original_dir.rglob("*")):
            if not path.is_file():
                continue
            paper_uuid = _extract_uuid(path)
            if paper_uuid and paper_uuid in present_uuids:
                continue
            suffix = path.suffix
            if paper_uuid:
                map_data = _read_map(root, paper_uuid)
                name = tagged_name(map_data, paper_uuid, suffix)
            else:
                name = path.name
            if suffix == ".md":
                name = f"{Path(name).stem}_original.md"
            dest = _unique_dest(outbox, name)
            shutil.copy2(str(path), str(dest))
            counts["originals_copied"] += 1
            if paper_uuid:
                present_uuids.add(paper_uuid)

    # 4. Final pass: remove obvious duplicate originals (foo_original_001.md, etc.)
    originals: dict[str, list[Path]] = {}
    for path in outbox.glob("*.md"):
        if not _is_original(path):
            continue
        stem = path.stem
        m = _ORIGINAL_SUFFIX_RE.search(stem)
        base_stem = stem[: m.start()] if m else stem
        originals.setdefault(base_stem, []).append(path)
    for base_stem, paths in originals.items():
        if len(paths) <= 1:
            continue
        base_path = outbox / f"{base_stem}_original.md"
        if base_path not in paths:
            # No canonical base; keep the alphabetically first and remove identical others.
            paths.sort(key=lambda p: p.name)
            base_path = paths[0]
        for dup in paths:
            if dup == base_path:
                continue
            if _sha256(dup) == _sha256(base_path):
                dup.unlink()
                counts["duplicates_removed"] += 1

    # 5. Tag orphan originals that have a matching tagged companion.
    companion_bases: dict[str, str] = {}
    for path in outbox.glob("*.md"):
        if _is_original(path):
            continue
        stem = path.stem
        if "_" not in stem:
            continue
        tag, base = stem.split("_", 1)
        companion_bases.setdefault(base, tag)

    for path in sorted(outbox.glob("*.md")):
        if not _is_original(path):
            continue
        stem = path.stem
        m = _ORIGINAL_SUFFIX_RE.search(stem)
        base_stem = stem[: m.start()] if m else stem
        if "_" in base_stem:
            maybe_tag = base_stem.split("_", 1)[0]
            # Already tagged (the base itself begins with a known tag).
            if maybe_tag in {
                "YT", "MEQ", "APOLO", "THEO", "BIBLE", "HIST", "PHIL", "PHYS", "SCI", "METH", "OTHER"
            }:
                continue
        matches = [
            (tag, base)
            for base, tag in companion_bases.items()
            if base_stem == base or base_stem.startswith(base) or base.startswith(base_stem)
        ]
        if len(matches) != 1:
            continue
        tag, base = matches[0]
        desired = f"{tag}_{base}_original.md"
        if desired == path.name:
            continue
        dest = _unique_dest(outbox, desired)
        shutil.move(str(path), str(dest))
        counts["root_renamed"] += 1

    # 6. Remove empty legacy folder.
    if all_papers.exists() and not any(all_papers.iterdir()):
        all_papers.rmdir()

    return counts


def main() -> int:
    root = _VISIBLE_CKG
    counts = migrate(root)
    print(f"Migration complete: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
