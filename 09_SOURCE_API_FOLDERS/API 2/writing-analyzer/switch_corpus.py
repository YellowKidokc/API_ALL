#!/usr/bin/env python3
"""
switch_corpus.py
================
Discovers all ChromaDB corpora in 09_DATABASES, shows a numbered menu,
and updates CHROMA_DIR in config.txt to the chosen one.
"""

import sys
import pathlib
import re

SCRIPT_DIR  = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.txt"

# Root folder to scan for ChromaDB collections
DB_ROOT = pathlib.Path(r"X:\09_DATABASES")


def find_corpora(root: pathlib.Path) -> list:
    """Return list of (friendly_name, path) for every ChromaDB folder found."""
    found = []
    if not root.exists():
        return found
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        # ChromaDB always creates chroma.sqlite3 in the root of the db folder
        if (folder / "chroma.sqlite3").exists():
            name = friendly_name(folder.name)
            found.append((name, folder))
    return found


def friendly_name(folder_name: str) -> str:
    """Turn 'MDA_Vectorization_2026-06-17' into 'MDA  (2026-06-17)'."""
    # Extract date pattern
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", folder_name)
    date_str = f"  ({date_match.group(1)})" if date_match else ""
    # Strip date and common suffixes
    name = re.sub(r"_?\d{4}-\d{2}-\d{2}", "", folder_name)
    name = re.sub(r"[_-]?[Vv]ectorization[_-]?", " ", name).strip(" _-")
    return f"{name}{date_str}"


def parse_config(path: pathlib.Path) -> list:
    """Return lines of config.txt."""
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def update_chroma_dir(config_path: pathlib.Path, new_path: pathlib.Path):
    """Update or add CHROMA_DIR= in config.txt."""
    lines = parse_config(config_path)
    new_line = f"CHROMA_DIR={new_path}"
    updated = False
    result = []
    for line in lines:
        if line.strip().startswith("CHROMA_DIR="):
            result.append(new_line)
            updated = True
        else:
            result.append(line)
    if not updated:
        result.append(new_line)
    config_path.write_text("\n".join(result) + "\n", encoding="utf-8")


def main():
    corpora = find_corpora(DB_ROOT)

    if not corpora:
        print(f"\nNo ChromaDB corpora found in {DB_ROOT}")
        print("Run VECTORIZE_SERIES.bat to create one.")
        input("\nPress Enter to close...")
        return

    # Show current setting
    lines = parse_config(CONFIG_PATH)
    current = next((l.split("=", 1)[1].strip() for l in lines
                    if l.strip().startswith("CHROMA_DIR=")), None)

    print("=" * 60)
    print("  Switch Corpus  —  Select a knowledge base")
    print("=" * 60)

    for i, (name, path) in enumerate(corpora, 1):
        marker = " <-- active" if current and pathlib.Path(current) == path else ""
        print(f"  {i}. {name}{marker}")
        print(f"     {path}")
        print()

    print("=" * 60)
    choice = input("  Enter number (or Enter to cancel): ").strip()

    if not choice:
        print("  Cancelled.")
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(corpora):
            raise ValueError
    except ValueError:
        print("  Invalid choice.")
        input("\nPress Enter to close...")
        return

    name, path = corpora[idx]
    update_chroma_dir(CONFIG_PATH, path)

    print()
    print(f"  Switched to: {name}")
    print(f"  Path       : {path}")
    print(f"  config.txt updated.")
    print("=" * 60)
    input("\nPress Enter to close...")


if __name__ == "__main__":
    main()
