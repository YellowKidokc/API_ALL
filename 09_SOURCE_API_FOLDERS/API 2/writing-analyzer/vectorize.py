#!/usr/bin/env python3
"""
Vectorize — ingest files from any folder into ChromaDB
=======================================================
Chunks and embeds text/HTML files into a persistent ChromaDB collection.

Usage:
    python vectorize.py                          (input/ -> chroma_db/)
    python vectorize.py --source PATH            (custom source folder)
    python vectorize.py --db PATH                (custom ChromaDB output folder)
    python vectorize.py --source PATH --db PATH  (fully custom)
    python vectorize.py --clear                  (wipe collection first)
"""

import sys
import pathlib
import argparse

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.txt"

TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm",
    ".py", ".js", ".ts", ".c", ".cpp", ".h", ".java", ".rb",
    ".rs", ".go", ".sh", ".bat", ".ps1", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".conf", ".log", ".sql", ".r",
    ".tex", ".bib", ".rst", ".org", ".slack", ".eml",
}

HTML_EXTENSIONS = {".html", ".htm"}

CHUNK_SIZE    = 500
CHUNK_OVERLAP = 50

# Directories to never descend into
SKIP_DIRS = {
    ".git", ".lake", ".svn", ".hg",
    "node_modules", "__pycache__", ".pytest_cache",
    ".venv", "venv", ".tox",
    "build", "dist", ".cache",
}


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def parse_config(path: pathlib.Path) -> dict:
    cfg = {}
    if not path.exists():
        return cfg
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            cfg[key.strip()] = value.strip()
    return cfg


def is_likely_text(path: pathlib.Path) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            f.read(8192)
        return True
    except (UnicodeDecodeError, PermissionError):
        return False


def extract_html_text(path: pathlib.Path) -> str:
    """Strip HTML tags and return clean readable text."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except ImportError:
        # Fallback: crude tag strip without bs4
        import re
        return re.sub(r"<[^>]+>", " ", raw)


def read_file(path: pathlib.Path) -> str:
    if path.suffix.lower() in HTML_EXTENSIONS:
        return extract_html_text(path)
    return path.read_text(encoding="utf-8", errors="replace")


def chunk_text(text: str) -> list:
    """Split text into overlapping chunks of ~CHUNK_SIZE chars."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 > CHUNK_SIZE and current:
            chunks.append(current.strip())
            current = current[-CHUNK_OVERLAP:] + "\n\n" + para
        else:
            current = (current + "\n\n" + para).strip() if current else para
    if current.strip():
        chunks.append(current.strip())
    result = []
    for chunk in chunks:
        if len(chunk) <= CHUNK_SIZE * 2:
            result.append(chunk)
        else:
            for i in range(0, len(chunk), CHUNK_SIZE - CHUNK_OVERLAP):
                result.append(chunk[i:i + CHUNK_SIZE])
    return [c for c in result if c.strip()]


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Ingest files into ChromaDB.")
    parser.add_argument("--source", type=str, default=None,
                        help="Source folder to ingest (default: input/ next to this script).")
    parser.add_argument("--db", type=str, default=None,
                        help="ChromaDB output folder (default: chroma_db/ next to this script).")
    parser.add_argument("--clear", action="store_true",
                        help="Delete all existing chunks in the collection before ingesting.")
    args = parser.parse_args()

    cfg = parse_config(CONFIG_PATH)
    collection_name = cfg.get("COLLECTION_NAME", "my_docs")

    input_dir  = pathlib.Path(args.source) if args.source else SCRIPT_DIR / "input"
    chroma_dir = pathlib.Path(args.db)     if args.db     else pathlib.Path(cfg.get("CHROMA_DIR", str(SCRIPT_DIR / "chroma_db")))

    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        sys.exit("ERROR: chromadb is not installed.\nRun:  pip install chromadb sentence-transformers")

    print("=" * 60)
    print("  Vectorize  —  ChromaDB Ingestion")
    print("=" * 60)
    print(f"  Source     : {input_dir}")
    print(f"  Collection : {collection_name}")
    print(f"  Storage    : {chroma_dir}")
    print("=" * 60)

    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    ef = embedding_functions.DefaultEmbeddingFunction()

    if args.clear:
        try:
            client.delete_collection(collection_name)
            print(f"\n  [Cleared existing collection '{collection_name}']\n")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    existing_count = collection.count()

    if not input_dir.exists():
        sys.exit(f"ERROR: Source folder not found: {input_dir}")

    input_files = []
    for p in sorted(input_dir.rglob("*")):
        # Skip blacklisted directories anywhere in the path
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file() and p.name not in (".gitkeep", "desktop.ini"):
            ext = p.suffix.lower()
            if ext in TEXT_EXTENSIONS or is_likely_text(p):
                input_files.append(p)

    if not input_files:
        print("\nNo text files found — nothing to ingest.")
        return

    print(f"\n  Found {len(input_files)} file(s):\n")

    total_chunks = 0
    skipped = 0
    for file_path in input_files:
        try:
            rel = file_path.relative_to(input_dir)
        except ValueError:
            rel = pathlib.Path(file_path.name)

        try:
            text = read_file(file_path)
        except Exception as e:
            print(f"    [SKIP] {rel}  ({e})")
            skipped += 1
            continue

        if not text.strip():
            print(f"    [SKIP] {rel}  (empty after parsing)")
            skipped += 1
            continue

        chunks = chunk_text(text)
        if not chunks:
            skipped += 1
            continue

        safe_rel = str(rel).replace("\\", "/")
        ids       = [f"{safe_rel}__{i}" for i in range(len(chunks))]
        metadatas = [{"source": safe_rel, "chunk_index": i} for i in range(len(chunks))]

        collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
        total_chunks += len(chunks)
        print(f"    [OK] {rel}  ({len(chunks)} chunks)")

    print()
    print("=" * 60)
    print(f"  Done!  {total_chunks} chunks ingested into '{collection_name}'.")
    if skipped:
        print(f"  Skipped: {skipped} file(s)")
    print(f"  Total chunks in collection: {existing_count + total_chunks}")
    print(f"  ChromaDB path: {chroma_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
