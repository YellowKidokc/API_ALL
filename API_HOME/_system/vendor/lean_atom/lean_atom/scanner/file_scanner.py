"""File discovery and SHA-256 hash tracker."""

import fnmatch
import hashlib
from pathlib import Path
from typing import List, Tuple
from ..config import ScannerConfig


def compute_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class FileScanner:
    def __init__(self, root_dir: str, config: ScannerConfig):
        self.root_dir = Path(root_dir)
        self.config = config

    def should_exclude(self, rel_path: Path) -> bool:
        # Check directories
        for part in rel_path.parts[:-1]:
            if part in self.config.exclude_dirs:
                return True

        # Check filename patterns
        filename = rel_path.name
        for pat in self.config.exclude_patterns:
            if fnmatch.fnmatch(filename, pat):
                return True

        return False

    def scan(self) -> List[Tuple[Path, str]]:
        """
        Scan root_dir for .lean files.
        Returns list of (relative_path, sha256_hash).
        """
        results = []
        if not self.root_dir.exists():
            return results

        for p in self.root_dir.rglob("*.lean"):
            try:
                rel = p.relative_to(self.root_dir)
            except ValueError:
                continue

            if self.should_exclude(rel):
                continue

            try:
                fhash = compute_file_hash(p)
                results.append((rel, fhash))
            except (IOError, PermissionError):
                continue

        # Deterministic sorting
        results.sort(key=lambda x: str(x[0]))
        return results
