#!/usr/bin/env python3
"""
process_compare.py
==================
Runs every prompt in prompts/ through BOTH DeepSeek and OpenAI (O3),
side by side in the same output folder.

Saves:
  OUTBOX/compare_TIMESTAMP/
    01_find_variables_deepseek.md
    01_find_variables_o3.md
    02_isomorphic_deepseek.md
    02_isomorphic_o3.md
    ...

Config keys used:
  DEEPSEEK_API_KEY, MODEL, MAX_TOKENS, TEMPERATURE   — DeepSeek settings
  OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS    — OpenAI/O3 settings
  CHROMA_DIR, GTQ_CHROMA_DIR, CANNON_CHROMA_DIR      — corpora
  FOUNDATION_DOC                                     — canonical axioms

O3 note: temperature is not supported — omitted automatically.
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
    "deepseek-chat":     (0.00027,  0.00110),
    "deepseek-reasoner": (0.00055,  0.00219),
    "o3":                (0.01000,  0.04000),   # approximate — check platform.openai.com
    "o3-mini":           (0.00110,  0.00440),
    "gpt-4o":            (0.00250,  0.01000),
}


# ---------------------------------------------------------------------------
#  Helpers  (duplicated from process_multi.py for standalone running)
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
    print(f"  Foundation doc loaded: {p.name}  ({len(text):,} chars)")
    return (
        "[FOUNDATION DOCUMENT — CANONICAL AXIOMS — TREAT AS FIXED FRAMEWORK]\n"
        + text
        + "\n[END FOUNDATION DOCUMENT]"
    )


def query_corpus(chroma_dir_str, collection_name, prompt_text, top_k, label):
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
        print(f"  [SKIP] {label} corpus is empty.")
        return []

    n = min(top_k, col.count())
    results = col.query(query_texts=[prompt_text], n_results=n)
    docs  = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    chunks = []
    for doc, meta in zip(docs, metas):
        source = meta.get("source", "unknown")
        chunks.append(f"[{label} | {source}]\n{doc}")

    print(f"  [{label}] {len(chunks)} chunk(s) from {col.count():,}-chunk corpus.")
    return chunks


def build_context(cfg, prompt_text):
    collection_name = cfg.get("COLLECTION_NAME", "my_docs")
    top_k = int(cfg.get("TOP_K", "8") or "8")
    all_chunks = []
    for cfg_key, label in [("CHROMA_DIR","MDA"),("GTQ_CHROMA_DIR","GTQ"),("CANNON_CHROMA_DIR","Cannon")]:
        path = cfg.get(cfg_key, "")
        if path:
            all_chunks.extend(query_corpus(path, collection_name, prompt_text, top_k, label))
    if not all_chunks:
        return ""
    lines = (
        ["[CONTEXT FROM KNOWLEDGE BASE — retrieved by semantic similarity]"]
        + all_chunks
        + ["[END CONTEXT]"]
    )
    return "\n\n".join(lines)


def is_o3_model(model_name):
    """O3 models do not accept temperature or top_p."""
    return model_name.startswith("o3") or model_name.startswith("o1")


def call_deepseek(cfg, full_prompt):
    import openai
    api_key    = cfg.get("DEEPSEEK_API_KEY", "")
    model      = cfg.get("MODEL", "deepseek-chat")
    max_tokens = int(cfg.get("MAX_TOKENS", "4096") or "0")
    temperature = float(cfg.get("TEMPERATURE", "0.3"))

    client = openai.OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": [{"type": "text", "text": full_prompt}]}],
        "temperature": temperature,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    t0 = time.time()
    response = client.chat.completions.create(**kwargs)
    elapsed = time.time() - t0
    return response.choices[0].message.content, response.usage, elapsed, model


def call_openai(cfg, full_prompt):
    import openai
    api_key    = cfg.get("OPENAI_API_KEY", "")
    model      = cfg.get("OPENAI_MODEL", "o3")
    max_tokens = int(cfg.get("OPENAI_MAX_TOKENS", "16000") or "16000")

    if not api_key or api_key.startswith("sk-PASTE"):
        return None, None, 0, model

    client = openai.OpenAI(api_key=api_key)
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": full_prompt}],
        "max_completion_tokens": max_tokens,
    }
    # O3 / O1 models do not accept temperature
    if not is_o3_model(model):
        temperature = float(cfg.get("TEMPERATURE", "1.0"))
        kwargs["temperature"] = temperature

    t0 = time.time()
    try:
        response = client.chat.completions.create(**kwargs)
    except openai.AuthenticationError:
        print(f"  [OpenAI] ERROR: Invalid API key.")
        return None, None, 0, model
    except openai.APIError as e:
        print(f"  [OpenAI] ERROR: {e}")
        return None, None, 0, model

    elapsed = time.time() - t0
    return response.choices[0].message.content, response.usage, elapsed, model


def format_cost(model, in_tok, out_tok):
    if model not in PRICING:
        return f"no pricing for '{model}'"
    ir, or_ = PRICING[model]
    ic = (in_tok / 1000) * ir
    oc = (out_tok / 1000) * or_
    return f"in={in_tok:,}tok ${ic:.4f}  out={out_tok:,}tok ${oc:.4f}  total=${ic+oc:.4f}"


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    cfg = parse_config(CONFIG_PATH)

    ds_key = cfg.get("DEEPSEEK_API_KEY", "")
    oa_key = cfg.get("OPENAI_API_KEY", "")

    if not ds_key or ds_key.startswith("sk-PASTE"):
        sys.exit("ERROR: Set DEEPSEEK_API_KEY in config.txt")

    print()
    print("=" * 60)
    print("  COMPARE  —  DeepSeek vs OpenAI / O3")
    print("=" * 60)

    ds_model = cfg.get("MODEL", "deepseek-chat")
    oa_model = cfg.get("OPENAI_MODEL", "o3")
    oa_ready = oa_key and not oa_key.startswith("sk-PASTE")

    print(f"  DeepSeek : {ds_model}")
    print(f"  OpenAI   : {oa_model}  {'✓' if oa_ready else '✗ key not set — DeepSeek only'}")

    foundation = load_foundation(cfg.get("FOUNDATION_DOC", ""))

    if not PROMPTS_DIR.exists():
        sys.exit(f"ERROR: prompts/ not found at {PROMPTS_DIR}")
    prompt_files = sorted(PROMPTS_DIR.glob("*.txt"))
    if not prompt_files:
        sys.exit("ERROR: No prompts found.")
    print(f"  Prompts  : {len(prompt_files)}")

    OUTBOX_DIR.mkdir(exist_ok=True)
    ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTBOX_DIR / f"compare_{ts}"
    run_dir.mkdir(exist_ok=True)
    print(f"  Output   : {run_dir}")

    total_cost = 0.0

    for i, pf in enumerate(prompt_files, 1):
        prompt_name = pf.stem
        prompt_text = pf.read_text(encoding="utf-8", errors="replace").strip()
        if not prompt_text:
            continue

        print()
        print(f"  ── [{i}/{len(prompt_files)}] {prompt_name} ──")

        context = build_context(cfg, prompt_text)
        parts = []
        if foundation:
            parts.append(foundation)
        if context:
            parts.append(context)
        parts.append(prompt_text)
        full_prompt = "\n\n".join(parts)

        # --- DeepSeek ---
        print(f"  DeepSeek ({ds_model})  [{len(full_prompt):,} chars]...")
        try:
            ds_reply, ds_usage, ds_elapsed, _ = call_deepseek(cfg, full_prompt)
            in_tok  = ds_usage.prompt_tokens     if ds_usage else len(full_prompt)//4
            out_tok = ds_usage.completion_tokens if ds_usage else 0
            print(f"  Done {ds_elapsed:.1f}s  |  {format_cost(ds_model, in_tok, out_tok)}")
            out_path = run_dir / f"{i:02d}_{prompt_name}_deepseek.md"
            out_path.write_text(ds_reply, encoding="utf-8")
            if ds_model in PRICING:
                ir, or_ = PRICING[ds_model]
                total_cost += (in_tok/1000)*ir + (out_tok/1000)*or_
        except Exception as e:
            print(f"  DeepSeek ERROR: {e}")

        # --- OpenAI / O3 ---
        if oa_ready:
            print(f"  OpenAI   ({oa_model})  [{len(full_prompt):,} chars]...")
            oa_reply, oa_usage, oa_elapsed, _ = call_openai(cfg, full_prompt)
            if oa_reply:
                in_tok  = oa_usage.prompt_tokens     if oa_usage else len(full_prompt)//4
                out_tok = oa_usage.completion_tokens if oa_usage else 0
                print(f"  Done {oa_elapsed:.1f}s  |  {format_cost(oa_model, in_tok, out_tok)}")
                out_path = run_dir / f"{i:02d}_{prompt_name}_o3.md"
                out_path.write_text(oa_reply, encoding="utf-8")
                if oa_model in PRICING:
                    ir, or_ = PRICING[oa_model]
                    total_cost += (in_tok/1000)*ir + (out_tok/1000)*or_

    print()
    print("=" * 60)
    print(f"  Done. Output: {run_dir}")
    print(f"  Total cost:  ${total_cost:.4f}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
