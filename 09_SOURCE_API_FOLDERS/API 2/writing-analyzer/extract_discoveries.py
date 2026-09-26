#!/usr/bin/env python3
"""
extract_discoveries.py
======================
Scans the most recent OUTBOX run for structured findings.
Handles TWO output formats:
  DeepSeek: ```CANDIDATE: ... ``` code blocks, ## N. section headers
  O3:       plain-text CANDIDATE: blocks, QUESTION N — section headers

Saves to discoveries/pass_N_TIMESTAMP.md and vectorizes into Cannon corpus.
"""

import re
import sys
import pathlib
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR      = pathlib.Path(__file__).resolve().parent
OUTBOX_DIR      = SCRIPT_DIR / "OUTBOX"
DISCOVERIES_DIR = SCRIPT_DIR / "discoveries"
CONFIG_PATH     = SCRIPT_DIR / "config.txt"

# Separator lines O3 uses between sections
SEP_RE = re.compile(r'^[─━═\-]{8,}')


def parse_config():
    cfg = {}
    if not CONFIG_PATH.exists():
        return cfg
    for line in CONFIG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            cfg[k.strip()] = v.strip()
    return cfg


def find_latest_run():
    if not OUTBOX_DIR.exists():
        return None
    folders = sorted(
        [f for f in OUTBOX_DIR.iterdir() if f.is_dir()],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return folders[0] if folders else None


def extract_from_file(md_path):
    """Return list of (kind, content) tuples from one output .md file."""
    text  = md_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    findings = []
    seen_blocks = set()

    # ----------------------------------------------------------------
    # 1. CANDIDATE / REJECTED — backtick blocks (DeepSeek format)
    # ----------------------------------------------------------------
    in_block   = False
    block_buf  = []
    for line in lines:
        s = line.strip()
        if s.startswith("```"):
            if not in_block:
                in_block  = True
                block_buf = []
            else:
                in_block = False
                block    = "\n".join(block_buf).strip()
                sig      = block[:60]
                if sig not in seen_blocks:
                    seen_blocks.add(sig)
                    if block.startswith("CANDIDATE:"):
                        findings.append(("CANDIDATE", block))
                    elif block.startswith("REJECTED:"):
                        findings.append(("REJECTED", block))
                block_buf = []
        elif in_block:
            block_buf.append(line)

    # ----------------------------------------------------------------
    # 2. CANDIDATE / REJECTED — plain-text blocks (O3 format)
    #    Start: line beginning with CANDIDATE: or REJECTED:
    #    End:   separator line (─────) OR next CANDIDATE/REJECTED OR EOF
    # ----------------------------------------------------------------
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        kind = None
        if s.startswith("CANDIDATE:"):
            kind = "CANDIDATE"
        elif s.startswith("REJECTED:"):
            kind = "REJECTED"

        if kind:
            buf = [lines[i]]
            i  += 1
            while i < len(lines):
                ns = lines[i].strip()
                if (SEP_RE.match(ns)
                        or ns.startswith("CANDIDATE:")
                        or ns.startswith("REJECTED:")):
                    break
                buf.append(lines[i])
                i += 1
            block = "\n".join(buf).strip()
            sig   = block[:60]
            if sig not in seen_blocks:
                seen_blocks.add(sig)
                findings.append((kind, block))
        else:
            i += 1

    # ----------------------------------------------------------------
    # 3. Question sections — two header styles:
    #    DeepSeek: ## 6. ...
    #    O3:       QUESTION 6 — ...
    #
    #    Section ends at next header, separator, or EOF.
    # ----------------------------------------------------------------
    section_end = r'(?=\n(?:##\s*\d+\.|QUESTION\s+\d+\s*[——\-])|\n[─━═\-]{8,}|\Z)'

    targets = [
        # (label,                   pattern for header)
        ("Q6_REVERSE_DISCOVERIES",  r'(?:##\s*6\.|QUESTION\s+6\s*[——\-])'),
        ("Q10_REVERSE_INSIGHTS",    r'(?:##\s*10\.|QUESTION\s+10\s*[——\-])'),
        ("Q3_STRUCTURAL_IMPROVEMENTS", r'(?:##\s*3\.|QUESTION\s+3\s*[——\-])'),
    ]

    for label, hdr in targets:
        pat = re.compile(
            r'(?:^|\n)' + hdr + r'[^\n]*\n(.*?)' + section_end,
            re.DOTALL | re.IGNORECASE
        )
        m = pat.search(text)
        if m:
            content = m.group(1).strip()
            if len(content) > 80:          # skip empty or near-empty sections
                findings.append((label, content[:3000]))

    return findings


def vectorize_file(disc_path, cannon_dir):
    import chromadb
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(path=cannon_dir)
    ef     = embedding_functions.DefaultEmbeddingFunction()
    col    = client.get_or_create_collection(
        "my_docs",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    text   = disc_path.read_text(encoding="utf-8", errors="replace")
    chunks, buf = [], []
    for line in text.splitlines():
        buf.append(line)
        if len("\n".join(buf)) >= 500:
            chunks.append("\n".join(buf))
            buf = []
    if buf:
        chunks.append("\n".join(buf))

    for i, chunk in enumerate(chunks):
        col.upsert(
            ids=[f"{disc_path.stem}_chunk_{i:04d}"],
            documents=[chunk],
            metadatas=[{"source": disc_path.name, "chunk_index": i}],
        )

    print(f"  Vectorized {len(chunks)} chunks  →  Cannon corpus now {col.count():,} total.")


def main():
    cfg = parse_config()

    run_folder = find_latest_run()
    if not run_folder:
        sys.exit("ERROR: No OUTBOX run folder found. Run the prompts first.")

    print()
    print("=" * 60)
    print("  EXTRACT DISCOVERIES")
    print("=" * 60)
    print(f"  Source run : {run_folder.name}")

    md_files = sorted(run_folder.glob("*.md"))
    if not md_files:
        sys.exit(f"ERROR: No .md files in {run_folder}")

    all_findings = []
    for md in md_files:
        findings = extract_from_file(md)
        for kind, content in findings:
            all_findings.append((md.stem, kind, content))
        model_tag = "o3" if md.stem.endswith("_o3") else "deepseek"
        print(f"  [{model_tag}] {md.name}: {len(findings)} finding(s)")

    if not all_findings:
        print("\n  WARNING: No structured findings extracted.")
        print("  Outputs may use unexpected formatting — check one .md file manually.")
        return

    # --- Write discovery file ---
    DISCOVERIES_DIR.mkdir(exist_ok=True)
    existing  = sorted(DISCOVERIES_DIR.glob("pass_*.md"))
    pass_num  = len(existing) + 1
    ts        = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    disc_path = DISCOVERIES_DIR / f"pass_{pass_num:02d}_{ts}.md"

    lines = [
        f"# Pass {pass_num} Discoveries",
        f"Source : {run_folder.name}",
        f"Date   : {ts}",
        "",
        "---",
        "",
        "## PRIOR DISCOVERIES — CONFIRMED STRUCTURAL PREDICTIONS UNDER INVESTIGATION",
        "",
        "The following structural correspondences were identified in prior analysis.",
        "Treat these as confirmed hypotheses under investigation.",
        "Your task is to find NEW mappings that these prior discoveries make visible —",
        "structures that were invisible before but become detectable now that these",
        "anchors exist.",
        "",
    ]

    for source, kind, content in all_findings:
        lines.append(f"### [{kind}] — {source}")
        lines.append("")
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")

    disc_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Discovery file : {disc_path.name}")
    print(f"  Total findings : {len(all_findings)}")

    # --- Vectorize ---
    cannon_dir = cfg.get("CANNON_CHROMA_DIR", "")
    if cannon_dir:
        print(f"\n  Vectorizing into Cannon corpus...")
        try:
            vectorize_file(disc_path, cannon_dir)
        except Exception as e:
            print(f"  [WARNING] Vectorization failed: {e}")
            print(f"  Discovery file saved — run_pass2.py will use it as direct context.")
    else:
        print("  [SKIP] CANNON_CHROMA_DIR not set.")

    print()
    print("  Done. Run PASS2.bat to re-run with enriched context.")
    print()


if __name__ == "__main__":
    main()
