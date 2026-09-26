"""article_stack.py — the one rule every pipeline script follows.

Created 2026-09-16 (Claude, with David). Status: TESTED.

  1. PRESERVE the original article byte-for-byte (OUTBOX/00_ORIGINALS_PRESERVED, SHA-256 checked).
  2. STACK: generated material on top, a marker line, then the ORIGINAL ARTICLE unchanged below.
  3. VERIFY the bytes below the marker equal the original.

If a file that is already stacked comes back in, `original_of()` peels off the old top so
the original is never nested or double-wrapped.
"""
from __future__ import annotations
import os  # ONE_MENU

import hashlib
import re
import shutil
from pathlib import Path

ROOT = Path(os.environ.get("ONE_MENU_PATH_EVIDENCE_ROOT") or Path(__file__).resolve().parents[1])
PRESERVED_DIR = ROOT / "OUTBOX" / "00_ORIGINALS_PRESERVED"
MARKER_PREFIX = b"<!-- ===== ORIGINAL ARTICLE BELOW - UNCHANGED"
_MARKER_RE = re.compile(rb"<!-- ===== ORIGINAL ARTICLE BELOW - UNCHANGED sha256=([0-9a-f]{64}) ===== -->\r?\n")
BOM = b"\xef\xbb\xbf"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def original_of(raw: bytes) -> bytes:
    """Return the original article inside `raw` (peels a previous stack if present)."""
    m = None
    for m in _MARKER_RE.finditer(raw):
        pass
    if m:
        body = raw[m.end():]
        if sha256_bytes(body) == m.group(1).decode():
            return body
    return raw[len(BOM):] if raw.startswith(BOM) else raw


def preserve(src: Path) -> tuple[bytes, str, Path]:
    """Copy the original article (never the stacked wrapper) to 00_ORIGINALS_PRESERVED."""
    original = original_of(Path(src).read_bytes())
    sha = sha256_bytes(original)
    PRESERVED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PRESERVED_DIR / f"{Path(src).stem}__{sha[:8]}{Path(src).suffix}"
    if not dest.exists():
        dest.write_bytes(original)
        try:
            shutil.copystat(src, dest)
        except OSError:
            pass
    if sha256_bytes(dest.read_bytes()) != sha:
        raise RuntimeError(f"preserved copy does not match original: {dest}")
    return original, sha, dest


def stack(top_text: str, original: bytes) -> bytes:
    """Generated material on top, original article below, unchanged."""
    original = original_of(original)
    sha = sha256_bytes(original)
    marker = MARKER_PREFIX + f" sha256={sha} ===== -->\n".encode()
    out = top_text.rstrip().encode("utf-8") + b"\n\n" + marker + original
    if original_of(out) != original:
        raise RuntimeError("stacking altered the original article")
    return out


def write_stacked(path: Path, top_text: str, original: bytes) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = stack(top_text, original)
    path.write_bytes(data)
    if original_of(path.read_bytes()) != original_of(original):
        raise RuntimeError(f"written file lost its original article: {path}")
    from evidence_sidecars import record_output
    record_output(path, top_text, status="stack_verified")
    return path
