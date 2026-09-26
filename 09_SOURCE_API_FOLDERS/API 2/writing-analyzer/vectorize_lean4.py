#!/usr/bin/env python3
"""
vectorize_lean4.py
==================
Reads all .lean files from the Theophysics Lean 4 project and upserts
them into the Cannon ChromaDB corpus as structured chunks.

Chunking strategy:
  - Each top-level definition, theorem, or namespace block = one chunk
  - Preserve lean syntax as-is for retrieval
  - Metadata tags: source, file, kind (theorem/def/structure/inductive)
"""

import re
import sys
import pathlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Config ──────────────────────────────────────────────────────────────────
LEAN_DIR = pathlib.Path(r"H:\Desktop 2\LEAN 4\Lean 4")
CANNON_CHROMA = pathlib.Path(r"X:\09_DATABASES\Cannon_Vectorization_2026-06-17")
COLLECTION    = "my_docs"

LEAN_FILES = [
    "Final_Lean4_From_Excel.lean",
    "Theophysics_Core.lean",
    "Theophysics_Adversarial.lean",
    "Theophysics_Coherence.lean",
    "Theophysics_Fracture.lean",
    "Theophysics_Fall.lean",
    "Theophysics_ChiEvaluator.lean",
]

# Patterns that start a new top-level item
ITEM_START = re.compile(
    r"^(theorem|def|structure|inductive|abbrev|instance|class|noncomputable def"
    r"|private def|protected theorem|/-!|\/-)",
    re.MULTILINE,
)

DOCBLOCK_RE = re.compile(r"^/-!(.*?)-/", re.DOTALL | re.MULTILINE)


# ── Chunking ────────────────────────────────────────────────────────────────

def kind_of(line: str) -> str:
    for kw in ("theorem", "def", "structure", "inductive", "instance", "class", "/-!"):
        if line.strip().startswith(kw):
            return kw
    return "other"


def chunk_file(text: str, filename: str) -> list[dict]:
    """Split a Lean file into logical chunks at top-level declarations."""
    lines = text.splitlines(keepends=True)
    chunks = []

    # Extract module doc block as first chunk
    doc_match = DOCBLOCK_RE.search(text)
    if doc_match:
        doc_text = doc_match.group(0).strip()
        chunks.append({
            "text":     doc_text,
            "filename": filename,
            "kind":     "docblock",
        })

    # Split remaining text at top-level declarations
    # Find line numbers where a new top-level item starts (column 0, keyword)
    boundaries: list[int] = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        # Only at column 0 (no indentation)
        if line == stripped and ITEM_START.match(line):
            boundaries.append(i)

    if not boundaries:
        # Fallback: whole file as one chunk
        chunks.append({"text": text.strip(), "filename": filename, "kind": "file"})
        return chunks

    for idx, start in enumerate(boundaries):
        end = boundaries[idx + 1] if idx + 1 < len(boundaries) else len(lines)
        block = "".join(lines[start:end]).strip()
        if len(block) < 20:
            continue
        chunks.append({
            "text":     block,
            "filename": filename,
            "kind":     kind_of(lines[start]),
        })

    return chunks


def split_to_max(chunk: dict, max_chars: int = 2000) -> list[dict]:
    """If a chunk is very large, split it into smaller pieces."""
    text = chunk["text"]
    if len(text) <= max_chars:
        return [chunk]
    result = []
    while text:
        piece = text[:max_chars]
        # Try to break at newline
        nl = piece.rfind("\n", max_chars // 2)
        if nl > 0:
            piece = text[:nl]
        result.append({**chunk, "text": piece.strip()})
        text = text[len(piece):].strip()
    return result


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    try:
        import chromadb
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    except ImportError:
        print("Installing chromadb...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "chromadb", "-q"], check=True)
        import chromadb
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    print(f"\n  Connecting to Cannon corpus: {CANNON_CHROMA}")
    client = chromadb.PersistentClient(path=str(CANNON_CHROMA))
    col = client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=DefaultEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )

    print(f"  Collection '{COLLECTION}' — existing chunks: {col.count()}")
    print()

    all_chunks = []
    for fname in LEAN_FILES:
        fpath = LEAN_DIR / fname
        if not fpath.exists():
            print(f"  [SKIP] {fname} — not found")
            continue
        text = fpath.read_text(encoding="utf-8", errors="replace")
        raw_chunks = chunk_file(text, fname)
        # Split oversized chunks
        flat = []
        for c in raw_chunks:
            flat.extend(split_to_max(c))
        all_chunks.extend(flat)
        print(f"  {fname:45s}  →  {len(flat):3d} chunks")

    print(f"\n  Total chunks to upsert: {len(all_chunks)}")

    # Build ids, texts, metadatas
    ids, texts, metas = [], [], []
    for i, c in enumerate(all_chunks):
        chunk_id = f"lean4-theophysics-{c['filename'].replace('.lean','').lower()}-{i:04d}"
        ids.append(chunk_id)
        texts.append(c["text"])
        metas.append({
            "source":   f"Lean4 | {c['filename']}",
            "file":     c["filename"],
            "kind":     c["kind"],
            "corpus":   "Lean4-Theophysics",
        })

    # Upsert in batches of 100
    batch = 100
    for start in range(0, len(ids), batch):
        col.upsert(
            ids=ids[start:start+batch],
            documents=texts[start:start+batch],
            metadatas=metas[start:start+batch],
        )
        print(f"  Upserted {min(start+batch, len(ids))} / {len(ids)}", end="\r")

    print(f"\n\n  Done.  Cannon corpus now has {col.count()} total chunks.")
    print(f"         Lean 4 chunks added: {len(ids)}")
    print()

    # Quick sanity query
    result = col.query(
        query_texts=["chi product collapses when any channel is zero"],
        n_results=3,
    )
    print("  Sanity query: 'chi product collapses when any channel is zero'")
    for i, (doc, meta) in enumerate(
        zip(result["documents"][0], result["metadatas"][0])
    ):
        print(f"    [{i+1}] [{meta.get('source','')}]  {doc[:100].replace(chr(10),' ')}...")
    print()


if __name__ == "__main__":
    main()
