#!/usr/bin/env python3
"""
process_multi.py
================
Runs every prompt in prompts/ against one or more ChromaDB corpora.
Prepends the foundation document (NO_DRIFT_CANONICAL_LAWS.md) to every call.
Saves numbered output files to OUTBOX/run_TIMESTAMP/.

Config keys used:
  DEEPSEEK_API_KEY    — required
  MODEL               — deepseek-chat | deepseek-reasoner
  MAX_TOKENS          — int, 0 = no limit
  TEMPERATURE         — float 0-1
  COLLECTION_NAME     — collection name inside each ChromaDB (default my_docs)
  TOP_K               — chunks per corpus per query (default 8)
  CHROMA_DIR          — path to primary corpus (e.g. MDA)
  GTQ_CHROMA_DIR      — path to GTQ corpus (optional second corpus)
  CANNON_CHROMA_DIR   — path to Cannon corpus (optional third corpus)
  FOUNDATION_DOC      — path to NO_DRIFT_CANONICAL_LAWS.md (optional but recommended)
"""

import sys
import time
import pathlib
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR  = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.txt"
PROMPTS_DIR = SCRIPT_DIR / "prompts"
OUTBOX_DIR  = SCRIPT_DIR / "OUTBOX"

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

PRICING = {
    "deepseek-chat":     (0.00027, 0.00110),
    "deepseek-reasoner": (0.00055, 0.00219),
}


# ---------------------------------------------------------------------------
#  Config / helpers
# ---------------------------------------------------------------------------

def parse_config(path):
    cfg = {}
    if not path.exists():
        return cfg
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            cfg[k.strip()] = v.strip()
    return cfg


def load_foundation(path_str):
    if not path_str:
        return ""
    p = pathlib.Path(path_str)
    if not p.exists():
        print(f"  [WARNING] Foundation doc not found: {p}")
        return ""
    text = p.read_text(encoding="utf-8", errors="replace")
    header = "[FOUNDATION DOCUMENT — CANONICAL AXIOMS — TREAT AS FIXED LAWS NOT HYPOTHESES]"
    footer = "[END FOUNDATION DOCUMENT]"
    print(f"  Foundation doc loaded: {p.name}  ({len(text):,} chars)")
    return f"{header}\n{text}\n{footer}"


def query_corpus(chroma_dir_str, collection_name, prompt_text, top_k, label):
    """Query one ChromaDB corpus; return list of labeled text strings."""
    import chromadb
    from chromadb.utils import embedding_functions

    p = pathlib.Path(chroma_dir_str)
    if not p.exists():
        print(f"  [SKIP] {label} corpus not found: {p}")
        return []

    client = chromadb.PersistentClient(path=str(p))
    ef = embedding_functions.DefaultEmbeddingFunction()
    col = client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    if col.count() == 0:
        print(f"  [SKIP] {label} corpus is empty — run vectorize.py first.")
        return []

    n = min(top_k, col.count())
    results = col.query(query_texts=[prompt_text], n_results=n)
    docs  = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    chunks = []
    for doc, meta in zip(docs, metas):
        source = meta.get("source", "unknown")
        chunks.append(f"[{label} | {source}]\n{doc}")

    print(f"  [{label}] Retrieved {len(chunks)} chunk(s) from {col.count():,}-chunk corpus.")
    return chunks


def build_context(cfg, prompt_text):
    collection_name = cfg.get("COLLECTION_NAME", "my_docs")
    top_k = int(cfg.get("TOP_K", "8") or "8")

    all_chunks = []

    # Query each corpus that is configured and non-empty
    corpora = [
        ("CHROMA_DIR",        "MDA"),
        ("GTQ_CHROMA_DIR",    "GTQ"),
        ("CANNON_CHROMA_DIR", "Cannon"),
    ]
    for cfg_key, label in corpora:
        path = cfg.get(cfg_key, "")
        if path:
            all_chunks.extend(query_corpus(path, collection_name, prompt_text, top_k, label))

    if not all_chunks:
        return ""

    lines = (
        ["[CONTEXT FROM KNOWLEDGE BASE — retrieved by semantic similarity to this prompt]"]
        + all_chunks
        + ["[END CONTEXT]"]
    )
    return "\n\n".join(lines)


def call_deepseek(client, model, max_tokens, temperature, full_prompt):
    import openai

    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": [{"type": "text", "text": full_prompt}]}],
        "temperature": temperature,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    t0 = time.time()
    try:
        response = client.chat.completions.create(**kwargs)
    except openai.AuthenticationError:
        sys.exit("ERROR: Invalid DeepSeek API key.")
    except openai.RateLimitError:
        sys.exit("ERROR: Rate limited — wait a moment and retry.")
    except openai.APIError as e:
        sys.exit(f"ERROR: DeepSeek API error: {e}")

    elapsed = time.time() - t0
    return response.choices[0].message.content, response.usage, elapsed


def format_cost(model, in_tok, out_tok):
    if model not in PRICING:
        return f"no pricing for '{model}'"
    ir, or_ = PRICING[model]
    ic = (in_tok / 1000) * ir
    oc = (out_tok / 1000) * or_
    return (f"in={in_tok:,}tok ${ic:.5f}  out={out_tok:,}tok ${oc:.5f}  "
            f"total=${ic + oc:.5f}")


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    cfg         = parse_config(CONFIG_PATH)
    api_key     = cfg.get("DEEPSEEK_API_KEY", "")
    model       = cfg.get("MODEL", "deepseek-chat")
    max_tokens  = int(cfg.get("MAX_TOKENS", "4096") or "0")
    temperature = float(cfg.get("TEMPERATURE", "0.3"))

    if not api_key or api_key.startswith("sk-PASTE"):
        sys.exit("ERROR: Set DEEPSEEK_API_KEY in config.txt")

    print()
    print("=" * 60)
    print("  PROCESS MULTI — Multi-Prompt × Multi-Corpus")
    print("=" * 60)

    # Foundation document
    foundation = load_foundation(cfg.get("FOUNDATION_DOC", ""))

    # Collect prompt files
    if not PROMPTS_DIR.exists():
        sys.exit(f"ERROR: prompts/ folder not found at {PROMPTS_DIR}")
    prompt_files = sorted(PROMPTS_DIR.glob("*.txt"))
    if not prompt_files:
        sys.exit("ERROR: No .txt files found in prompts/")
    print(f"  Prompts found: {len(prompt_files)}")
    for pf in prompt_files:
        print(f"    {pf.name}")

    # Set up DeepSeek client
    try:
        import openai
    except ImportError:
        sys.exit("ERROR: Run:  pip install openai")
    ds_client = openai.OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    # Create output run folder
    OUTBOX_DIR.mkdir(exist_ok=True)
    ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTBOX_DIR / f"run_{ts}"
    run_dir.mkdir(exist_ok=True)
    print(f"  Output folder: {run_dir}")

    total_in_tok  = 0
    total_out_tok = 0
    total_cost    = 0.0

    for i, pf in enumerate(prompt_files, 1):
        prompt_name = pf.stem
        prompt_text = pf.read_text(encoding="utf-8", errors="replace").strip()
        if not prompt_text:
            print(f"\n  [SKIP] {pf.name} is empty.")
            continue

        print()
        print(f"  ── [{i}/{len(prompt_files)}] {prompt_name} ──")

        # Build context from all corpora
        context = build_context(cfg, prompt_text)

        # Assemble full prompt
        parts = []
        if foundation:
            parts.append(foundation)
        if context:
            parts.append(context)
        parts.append(prompt_text)
        full_prompt = "\n\n".join(parts)

        print(f"  Sending to DeepSeek ({model})  [{len(full_prompt):,} chars]...")

        reply, usage, elapsed = call_deepseek(ds_client, model, max_tokens, temperature, full_prompt)

        in_tok  = usage.prompt_tokens     if usage else len(full_prompt) // 4
        out_tok = usage.completion_tokens if usage else 0
        total_in_tok  += in_tok
        total_out_tok += out_tok

        cost_str = format_cost(model, in_tok, out_tok)
        print(f"  Done in {elapsed:.1f}s  |  {cost_str}")

        if model in PRICING:
            ir, or_ = PRICING[model]
            total_cost += (in_tok / 1000) * ir + (out_tok / 1000) * or_

        # Save result
        out_name = f"{i:02d}_{prompt_name}.md"
        out_path = run_dir / out_name
        out_path.write_text(reply, encoding="utf-8")
        print(f"  Saved: {out_name}")

    print()
    print("=" * 60)
    print(f"  All {len(prompt_files)} prompt(s) complete.")
    print(f"  Run folder: {run_dir}")
    print(f"  Total tokens — in: {total_in_tok:,}  out: {total_out_tok:,}")
    print(f"  Total cost:  ${total_cost:.5f}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
