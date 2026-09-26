#!/usr/bin/env python3
"""
vectorize_series.py
====================
Asks for a series name and source folder, vectorizes it into
X:\09_DATABASES\<NAME>_Vectorization_<DATE>, then offers to switch to it.
"""

import sys
import subprocess
import pathlib
import datetime

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
DB_ROOT    = pathlib.Path(r"X:\09_DATABASES")


def main():
    today = datetime.date.today().strftime("%Y-%m-%d")

    print("=" * 60)
    print("  Vectorize New Series")
    print("=" * 60)
    print()

    series_name = input("  Series name (e.g. GTQ, MDA, GENESIS): ").strip()
    if not series_name:
        print("  Cancelled.")
        return

    series_name = series_name.upper().replace(" ", "_")

    source = input("  Source folder path\n  (paste full path, e.g. \\\\nas\\brain\\gtq): ").strip().strip('"')
    if not source:
        print("  Cancelled.")
        return

    source_path = pathlib.Path(source)
    if not source_path.exists():
        print(f"\n  ERROR: Folder not found: {source_path}")
        input("\nPress Enter to close...")
        return

    db_path = DB_ROOT / f"{series_name}_Vectorization_{today}"

    print()
    print(f"  Series   : {series_name}")
    print(f"  Source   : {source_path}")
    print(f"  Output   : {db_path}")
    print()
    confirm = input("  Proceed? (y / n): ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return

    print()
    print("  Running vectorizer...")
    print("-" * 60)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "vectorize.py"),
         "--source", str(source_path),
         "--db",     str(db_path),
         "--clear"],
        cwd=str(SCRIPT_DIR),
    )

    if result.returncode != 0:
        print("\n  ERROR: Vectorization failed. See output above.")
        input("\nPress Enter to close...")
        return

    print("-" * 60)
    print(f"\n  Done!  '{series_name}' is ready.")
    print()

    switch = input("  Switch to this corpus now? (y / n): ").strip().lower()
    if switch == "y":
        import switch_corpus
        switch_corpus.update_chroma_dir(SCRIPT_DIR / "config.txt", db_path)
        print(f"  Switched to {series_name}.")

    print()
    input("Press Enter to close...")


if __name__ == "__main__":
    main()
