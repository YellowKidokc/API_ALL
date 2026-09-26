from __future__ import annotations

import os
from pathlib import Path


def main() -> int:
    input_dir = Path(os.environ.get("PAPER_GRADER_INPUT", "/data/input"))
    output_dir = Path(os.environ.get("PAPER_GRADER_OUTPUT", "/data/output"))
    archive_dir = Path(os.environ.get("PAPER_GRADER_ARCHIVE", "/data/archive"))

    for path in (input_dir, output_dir, archive_dir):
        path.mkdir(parents=True, exist_ok=True)

    files = [p for p in input_dir.iterdir() if p.is_file()]
    print("Paper Grader scaffold is ready.")
    print(f"Input:   {input_dir} ({len(files)} file(s) waiting)")
    print(f"Output:  {output_dir}")
    print(f"Archive: {archive_dir}")
    print("Next build step: implement intake, metrics, Excel, HTML, vectors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
