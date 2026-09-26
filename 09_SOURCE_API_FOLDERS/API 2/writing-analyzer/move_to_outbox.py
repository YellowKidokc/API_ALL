#!/usr/bin/env python3
"""
move_to_outbox.py
=================
Moves files from INBOX\ into OUTBOX\processed_<timestamp>\ after a run.
Called by PROCESS.bat after analysis completes.
"""

import pathlib
import datetime
import shutil

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
INBOX_DIR  = SCRIPT_DIR / "INBOX"
OUTBOX_DIR = SCRIPT_DIR / "OUTBOX"

def main():
    files = [f for f in INBOX_DIR.iterdir()
             if f.is_file() and f.name not in (".gitkeep", "desktop.ini")]

    if not files:
        print("  No files to move.")
        return

    ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest    = OUTBOX_DIR / f"processed_{ts}"
    dest.mkdir(parents=True, exist_ok=True)

    for f in files:
        shutil.move(str(f), str(dest / f.name))
        print(f"  Moved  : {f.name}  →  OUTBOX\\processed_{ts}\\")

    print(f"\n  {len(files)} file(s) moved to OUTBOX\\processed_{ts}\\")

if __name__ == "__main__":
    main()
