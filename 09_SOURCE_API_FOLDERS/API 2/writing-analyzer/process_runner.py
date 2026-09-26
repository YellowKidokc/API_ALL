#!/usr/bin/env python3
"""
process_runner.py
=================
Reads config, queries ChromaDB from vectorization\ folder,
calls DeepSeek with prompt.txt, saves result to OUTBOX\.
Called by PROCESS.bat.
"""

import sys
import json
import time
import pathlib
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR  = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.txt"
PROMPT_PATH = SCRIPT_DIR / "prompt.txt"
OUTBOX_DIR  = SCRIPT_DIR / "OUTBOX"
CHROMA_DIR  = SCRIPT_DIR / "vectorization"

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

PRICING = {
    "deepseek-chat":     (0.00027, 0.00110),
    "deepseek-reasoner": (0.00055, 0.00219),
}


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


def read_prompt(path):
    if not path.exists():
        sys.exit(f"ERROR: prompt.txt not found at {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    text = "\n".join(l for l in lines if not l.strip().startswith("#")).strip()
    if not text:
        sys.exit("ERROR: prompt.txt is empty.")
    return text


def query_chromadb(chroma_dir, collection_name, prompt_text, top_k):
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        sys.exit("ERROR: chromadb not installed. Run PROCESS.bat which installs it automatically.")

    if not chroma_dir.exists():
        sys.exit(f"ERROR: vectorization folder not found at {chroma_dir}\nRun PROCESS.bat to vectorize first.")

    client = chromadb.PersistentClient(path=str(chroma_dir))
    ef = embedding_functions.DefaultEmbeddingFunction()
    col = client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    if col.count() == 0:
        sys.exit("ERROR: vectorization\ is empty. Drop files in INBOX\\ and run PROCESS.bat.")

    results = col.query(query_texts=[prompt_text], n_results=min(top_k, col.count()))
    docs  = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    lines = ["[CONTEXT FROM KNOWLEDGE BASE]"]
    for doc, meta in zip(docs, metas):
        lines.append(f"--- Source: {meta.get('source', 'unknown')} ---")
        lines.append(doc)
    lines.append("[END CONTEXT]")
    print(f"  Retrieved {len(docs)} chunk(s) from '{collection_name}'.")
    return "\n".join(lines)


def format_cost(model, in_tok, out_tok):
    if model not in PRICING:
        return f"  (no pricing data for '{model}')"
    ir, or_ = PRICING[model]
    ic = (in_tok / 1000) * ir
    oc = (out_tok / 1000) * or_
    return (f"  Input  : ~{in_tok:,} tokens  ${ic:.6f}\n"
            f"  Output : ~{out_tok:,} tokens  ${oc:.6f}\n"
            f"  TOTAL  : ${ic+oc:.6f}")


def main():
    cfg = parse_config(CONFIG_PATH)
    api_key         = cfg.get("DEEPSEEK_API_KEY", "")
    model           = cfg.get("MODEL", "deepseek-chat")
    max_tokens      = int(cfg.get("MAX_TOKENS", "4096") or "0")
    temperature     = float(cfg.get("TEMPERATURE", "0.3"))
    collection_name = cfg.get("COLLECTION_NAME", "my_docs")
    top_k           = int(cfg.get("TOP_K", "8") or "8")
    # CHROMA_DIR is always the local vectorization\ folder when called from PROCESS.bat
    chroma_dir      = pathlib.Path(cfg.get("CHROMA_DIR", str(CHROMA_DIR)))

    if not api_key or api_key.startswith("sk-PASTE"):
        sys.exit("ERROR: Paste your DeepSeek API key into config.txt")

    prompt_text = read_prompt(PROMPT_PATH)
    context     = query_chromadb(chroma_dir, collection_name, prompt_text, top_k)
    full_prompt = context + "\n\n" + prompt_text

    try:
        import openai
    except ImportError:
        sys.exit("ERROR: openai not installed.\nRun:  pip install openai")

    client = openai.OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    print(f"  Sending to DeepSeek ({model})...")
    t0 = time.time()

    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": [{"type": "text", "text": full_prompt}]}],
        "temperature": temperature,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    try:
        response = client.chat.completions.create(**kwargs)
    except openai.AuthenticationError:
        sys.exit("ERROR: Invalid API key.")
    except openai.RateLimitError:
        sys.exit("ERROR: Rate limited — wait a moment and try again.")
    except openai.APIError as e:
        sys.exit(f"ERROR: DeepSeek API error: {e}")

    elapsed = time.time() - t0
    reply   = response.choices[0].message.content
    usage   = response.usage

    print(f"  Response received in {elapsed:.1f}s")
    print()
    print("=" * 60)
    print(reply)
    print("=" * 60)

    # Save to OUTBOX
    OUTBOX_DIR.mkdir(exist_ok=True)
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTBOX_DIR / f"analysis_{model}_{ts}.md"
    out_path.write_text(reply, encoding="utf-8")
    print(f"\n  Saved  : {out_path.name}")

    in_tok  = usage.prompt_tokens     if usage else len(full_prompt) // 4
    out_tok = usage.completion_tokens if usage else 0
    print("\n--- Cost ---")
    print(format_cost(model, in_tok, out_tok))


if __name__ == "__main__":
    main()
