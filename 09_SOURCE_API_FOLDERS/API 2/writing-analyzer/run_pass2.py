#!/usr/bin/env python3
"""
run_pass2.py
============
Same as run_three.py but prepends the most recent discoveries file as
PRIOR DISCOVERIES context before each prompt call.

Reads discoveries/pass_N_*.md (most recent).
Saves to OUTBOX/pass2_TIMESTAMP/.
"""

import sys
import time
import pathlib
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR      = pathlib.Path(__file__).resolve().parent
CONFIG_PATH     = SCRIPT_DIR / "config.txt"
PROMPTS_DIR     = SCRIPT_DIR / "prompts"
OUTBOX_DIR      = SCRIPT_DIR / "OUTBOX"
DISCOVERIES_DIR = SCRIPT_DIR / "discoveries"

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
FEATURED = {"ONE", "TWO", "THREE", "FOUR"}

PRICING = {
    "deepseek-chat":     (0.00027, 0.00110),
    "deepseek-reasoner": (0.00055, 0.00219),
    "o3":                (0.01000, 0.04000),
    "o3-mini":           (0.00110, 0.00440),
    "gpt-4o":            (0.00250, 0.01000),
}


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


def load_prior_discoveries():
    if not DISCOVERIES_DIR.exists():
        return ""
    files = sorted(DISCOVERIES_DIR.glob("pass_*.md"), reverse=True)
    if not files:
        return ""
    text = files[0].read_text(encoding="utf-8", errors="replace")
    print(f"  Prior discoveries : {files[0].name}  ({len(text):,} chars)")
    return text


def load_foundation(path_str):
    if not path_str:
        return ""
    p = pathlib.Path(path_str)
    if not p.exists():
        print(f"  [WARNING] Foundation doc not found: {p}")
        return ""
    text = p.read_text(encoding="utf-8", errors="replace")
    print(f"  Foundation doc    : {p.name}  ({len(text):,} chars)")
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
        print(f"  [SKIP] {label} corpus not found.")
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

    print(f"  [{label}] {len(chunks)} chunks ({col.count():,} total in corpus).")
    return chunks


def build_context(cfg, prompt_text):
    collection_name = cfg.get("COLLECTION_NAME", "my_docs")
    top_k = int(cfg.get("TOP_K", "8") or "8")
    all_chunks = []
    for cfg_key, label in [("CHROMA_DIR", "MDA"), ("GTQ_CHROMA_DIR", "GTQ"), ("CANNON_CHROMA_DIR", "Cannon")]:
        path = cfg.get(cfg_key, "")
        if path:
            all_chunks.extend(query_corpus(path, collection_name, prompt_text, top_k, label))
    if not all_chunks:
        return ""
    return "\n\n".join(
        ["[CONTEXT FROM KNOWLEDGE BASE — retrieved by semantic similarity]"]
        + all_chunks
        + ["[END CONTEXT]"]
    )


def is_o3_model(m):
    return m.startswith("o3") or m.startswith("o1")


def call_openai(cfg, full_prompt):
    import openai
    api_key    = cfg.get("OPENAI_API_KEY", "")
    model      = cfg.get("OPENAI_MODEL", "o3")
    max_tokens = int(cfg.get("OPENAI_MAX_TOKENS", "16000") or "16000")

    if not api_key or api_key.startswith("sk-PASTE"):
        print("  [O3] No API key — skipping.")
        return None, None, 0, model

    client = openai.OpenAI(api_key=api_key)
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": full_prompt}],
        "max_completion_tokens": max_tokens,
    }
    if not is_o3_model(model):
        kwargs["temperature"] = float(cfg.get("TEMPERATURE", "1.0"))

    t0 = time.time()
    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        print(f"  [O3] ERROR: {e}")
        return None, None, 0, model

    return response.choices[0].message.content, response.usage, time.time() - t0, model


def call_deepseek(cfg, full_prompt):
    import openai
    api_key     = cfg.get("DEEPSEEK_API_KEY", "")
    model       = cfg.get("MODEL", "deepseek-chat")
    max_tokens  = int(cfg.get("MAX_TOKENS", "4096") or "0")
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
    return response.choices[0].message.content, response.usage, time.time() - t0, model


def format_cost(model, in_tok, out_tok):
    if model not in PRICING:
        return f"~{in_tok + out_tok:,} tokens"
    ir, or_ = PRICING[model]
    ic = (in_tok / 1000) * ir
    oc = (out_tok / 1000) * or_
    return f"in={in_tok:,} ${ic:.4f}  out={out_tok:,} ${oc:.4f}  total=${ic+oc:.4f}"


def run_prompt(cfg, pf, run_dir, idx, foundation, prior_discoveries):
    prompt_name = pf.stem
    prompt_text = pf.read_text(encoding="utf-8", errors="replace").strip()
    if not prompt_text:
        return 0.0

    print()
    print(f"  ── [{idx}] {prompt_name} ──")

    context = build_context(cfg, prompt_text)

    # Order: foundation → prior discoveries → retrieved context → prompt
    parts = []
    if foundation:
        parts.append(foundation)
    if prior_discoveries:
        parts.append(prior_discoveries)
    if context:
        parts.append(context)
    parts.append(prompt_text)
    full_prompt = "\n\n".join(parts)

    print(f"  Total prompt: {len(full_prompt):,} chars")

    total_cost = 0.0
    ds_model   = cfg.get("MODEL", "deepseek-chat")
    oa_model   = cfg.get("OPENAI_MODEL", "o3")

    # O3 first
    print(f"  [O3 / {oa_model}] calling...")
    oa_reply, oa_usage, oa_elapsed, _ = call_openai(cfg, full_prompt)
    if oa_reply:
        in_tok  = oa_usage.prompt_tokens     if oa_usage else len(full_prompt) // 4
        out_tok = oa_usage.completion_tokens if oa_usage else 0
        print(f"  Done {oa_elapsed:.1f}s  |  {format_cost(oa_model, in_tok, out_tok)}")
        (run_dir / f"{idx:02d}_{prompt_name}_o3.md").write_text(oa_reply, encoding="utf-8")
        if oa_model in PRICING:
            ir, or_ = PRICING[oa_model]
            total_cost += (in_tok / 1000) * ir + (out_tok / 1000) * or_

    # DeepSeek second
    print(f"  [DeepSeek / {ds_model}] calling...")
    try:
        ds_reply, ds_usage, ds_elapsed, _ = call_deepseek(cfg, full_prompt)
        in_tok  = ds_usage.prompt_tokens     if ds_usage else len(full_prompt) // 4
        out_tok = ds_usage.completion_tokens if ds_usage else 0
        print(f"  Done {ds_elapsed:.1f}s  |  {format_cost(ds_model, in_tok, out_tok)}")
        (run_dir / f"{idx:02d}_{prompt_name}_deepseek.md").write_text(ds_reply, encoding="utf-8")
        if ds_model in PRICING:
            ir, or_ = PRICING[ds_model]
            total_cost += (in_tok / 1000) * ir + (out_tok / 1000) * or_
    except Exception as e:
        print(f"  [DeepSeek] ERROR: {e}")

    return total_cost


def main():
    cfg = parse_config()

    print()
    print("=" * 60)
    print("  PASS 2  —  Enriched Context Run")
    print("=" * 60)

    if not cfg.get("DEEPSEEK_API_KEY", "").startswith("sk-"):
        sys.exit("ERROR: Set DEEPSEEK_API_KEY in config.txt")

    foundation       = load_foundation(cfg.get("FOUNDATION_DOC", ""))
    prior_discoveries = load_prior_discoveries()

    if not prior_discoveries:
        print("  WARNING: No discovery file found in discoveries/.")
        print("  Run extract_discoveries.py first, or run PASS2.bat which does it automatically.")

    all_prompts = sorted(PROMPTS_DIR.glob("*.txt"))
    featured    = [p for p in all_prompts if any(f in p.stem.upper() for f in FEATURED)]

    if not featured:
        sys.exit("ERROR: No ONE/TWO/THREE prompts found.")

    print(f"  Prompts : {len(featured)}")
    for p in featured:
        print(f"    {p.name}")

    OUTBOX_DIR.mkdir(exist_ok=True)
    ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTBOX_DIR / f"pass2_{ts}"
    run_dir.mkdir(exist_ok=True)
    print(f"  Output  : {run_dir}")

    total_cost = 0.0
    for i, pf in enumerate(featured, 1):
        total_cost += run_prompt(cfg, pf, run_dir, i, foundation, prior_discoveries)

    print()
    print("=" * 60)
    print(f"  Done. Output: {run_dir}")
    print(f"  Total cost : ${total_cost:.4f}")
    print("  Run PASS2.bat again to do another iteration.")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
