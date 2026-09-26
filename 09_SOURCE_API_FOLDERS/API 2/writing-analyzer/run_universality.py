#!/usr/bin/env python3
"""
run_universality.py
===================
Runs prompt 11 (universality class test) against MDA and GTQ corpora
separately, through both DeepSeek and OpenAI O3.

Saves to:  universality-class-runner/run_TIMESTAMP/
  mda_deepseek.md
  mda_o3.md
  gtq_deepseek.md
  gtq_o3.md
  summary.md     (header + first 400 chars of each output)
"""

import sys
import time
import pathlib
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
CONFIG_PATH  = SCRIPT_DIR / "config.txt"
PROMPT_FILE  = SCRIPT_DIR / "prompts" / "11_universality_class_test.txt"
OUT_DIR      = SCRIPT_DIR / "universality-class-runner"

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

PRICING = {
    "deepseek-chat":     (0.00027, 0.00110),
    "deepseek-reasoner": (0.00055, 0.00219),
    "o3":                (0.01000, 0.04000),
    "o3-mini":           (0.00110, 0.00440),
    "gpt-4o":            (0.00250, 0.01000),
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


def load_foundation(path_str):
    if not path_str:
        return ""
    p = pathlib.Path(path_str)
    if not p.exists():
        print(f"  [WARNING] Foundation doc not found: {p}")
        return ""
    text = p.read_text(encoding="utf-8", errors="replace")
    print(f"  Foundation doc: {p.name}  ({len(text):,} chars)")
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
        print(f"  [SKIP] {label} not found: {p}")
        return []

    client = chromadb.PersistentClient(path=str(p))
    ef     = embedding_functions.DefaultEmbeddingFunction()
    col    = client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    if col.count() == 0:
        print(f"  [SKIP] {label} is empty.")
        return []

    n       = min(top_k, col.count())
    results = col.query(query_texts=[prompt_text], n_results=n)
    docs    = results.get("documents", [[]])[0]
    metas   = results.get("metadatas", [[]])[0]

    chunks = []
    for doc, meta in zip(docs, metas):
        source = meta.get("source", "unknown")
        chunks.append(f"[{label} | {source}]\n{doc}")

    print(f"  [{label}] {len(chunks)} chunk(s) retrieved from {col.count():,}-chunk corpus.")
    return chunks


def build_prompt_for_corpus(foundation, corpus_chunks, prompt_text, corpus_label):
    parts = []
    if foundation:
        parts.append(foundation)
    if corpus_chunks:
        parts.append(
            f"[CONTEXT FROM {corpus_label} CORPUS — retrieved by semantic similarity]\n\n"
            + "\n\n".join(corpus_chunks)
            + "\n\n[END CONTEXT]"
        )
    parts.append(prompt_text)
    return "\n\n".join(parts)


def is_o3_model(model_name):
    return model_name.startswith("o3") or model_name.startswith("o1")


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

    t0       = time.time()
    response = client.chat.completions.create(**kwargs)
    elapsed  = time.time() - t0
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
    if not is_o3_model(model):
        kwargs["temperature"] = float(cfg.get("TEMPERATURE", "1.0"))

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
    return f"in={in_tok:,}  out={out_tok:,}  total=${ic+oc:.4f}"


def run_pair(label, corpus_chunks, foundation, prompt_text, cfg, run_dir, results):
    """Run one corpus through both DeepSeek and O3. Append results dict."""
    ds_model = cfg.get("MODEL", "deepseek-chat")
    oa_model = cfg.get("OPENAI_MODEL", "o3")
    oa_key   = cfg.get("OPENAI_API_KEY", "")
    oa_ready = oa_key and not oa_key.startswith("sk-PASTE")

    full_prompt = build_prompt_for_corpus(foundation, corpus_chunks, prompt_text, label)
    slug = label.lower().replace(" ", "_")

    # DeepSeek
    print(f"\n  ── {label} × DeepSeek ({ds_model}) ──")
    print(f"  Prompt length: {len(full_prompt):,} chars")
    try:
        reply, usage, elapsed, _ = call_deepseek(cfg, full_prompt)
        in_tok  = usage.prompt_tokens     if usage else len(full_prompt) // 4
        out_tok = usage.completion_tokens if usage else 0
        print(f"  Done {elapsed:.1f}s  |  {format_cost(ds_model, in_tok, out_tok)}")
        out_path = run_dir / f"{slug}_deepseek.md"
        header = f"# {label} × DeepSeek ({ds_model})\n\nDate: {datetime.datetime.now().isoformat()[:16]}\n\n---\n\n"
        out_path.write_text(header + reply, encoding="utf-8")
        results.append((f"{label} / DeepSeek", str(out_path), reply[:600]))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append((f"{label} / DeepSeek", "ERROR", str(e)))

    # OpenAI
    if oa_ready:
        print(f"\n  ── {label} × OpenAI ({oa_model}) ──")
        print(f"  Prompt length: {len(full_prompt):,} chars")
        reply, usage, elapsed, _ = call_openai(cfg, full_prompt)
        if reply:
            in_tok  = usage.prompt_tokens     if usage else len(full_prompt) // 4
            out_tok = usage.completion_tokens if usage else 0
            print(f"  Done {elapsed:.1f}s  |  {format_cost(oa_model, in_tok, out_tok)}")
            out_path = run_dir / f"{slug}_o3.md"
            header = f"# {label} × OpenAI ({oa_model})\n\nDate: {datetime.datetime.now().isoformat()[:16]}\n\n---\n\n"
            out_path.write_text(header + reply, encoding="utf-8")
            results.append((f"{label} / O3", str(out_path), reply[:600]))
        else:
            print(f"  [SKIP] OpenAI key not configured or error.")
    else:
        print(f"\n  [SKIP] OpenAI key not set — DeepSeek only.")


def write_summary(run_dir, results, ts):
    lines = [
        "# Universality Class Test — Run Summary",
        f"\nDate: {ts}",
        "\nThis run tested prompt 11 (universality class classification) against",
        "MDA and GTQ corpora using DeepSeek and OpenAI O3.",
        "\n---\n",
    ]
    for label, path, preview in results:
        lines.append(f"## {label}")
        lines.append(f"File: `{path}`\n")
        lines.append("**Opening passage:**\n")
        lines.append(f"```\n{preview}\n```\n")
    (run_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Summary: {run_dir / 'summary.md'}")


def main():
    cfg = parse_config(CONFIG_PATH)

    if not PROMPT_FILE.exists():
        sys.exit(f"ERROR: Prompt not found: {PROMPT_FILE}")

    ds_key = cfg.get("DEEPSEEK_API_KEY", "")
    if not ds_key or ds_key.startswith("sk-PASTE"):
        sys.exit("ERROR: Set DEEPSEEK_API_KEY in config.txt")

    prompt_text = PROMPT_FILE.read_text(encoding="utf-8", errors="replace").strip()
    foundation  = load_foundation(cfg.get("FOUNDATION_DOC", ""))

    collection_name = cfg.get("COLLECTION_NAME", "my_docs")
    top_k           = int(cfg.get("TOP_K", "8") or "8")

    # Retrieve from each corpus separately
    mda_dir = cfg.get("CHROMA_DIR", "")
    gtq_dir = cfg.get("GTQ_CHROMA_DIR", "")

    print()
    print("=" * 60)
    print("  UNIVERSALITY CLASS TEST")
    print("  Prompt 11 × MDA + GTQ × DeepSeek + O3")
    print("=" * 60)
    print(f"  DeepSeek model : {cfg.get('MODEL','deepseek-chat')}")
    print(f"  OpenAI model   : {cfg.get('OPENAI_MODEL','o3')}")

    mda_chunks = []
    gtq_chunks = []

    if mda_dir:
        print("\n  Querying MDA corpus...")
        mda_chunks = query_corpus(mda_dir, collection_name, prompt_text, top_k, "MDA")
    else:
        print("  [SKIP] CHROMA_DIR not configured.")

    if gtq_dir:
        print("\n  Querying GTQ corpus...")
        gtq_chunks = query_corpus(gtq_dir, collection_name, prompt_text, top_k, "GTQ")
    else:
        print("  [SKIP] GTQ_CHROMA_DIR not configured.")

    OUT_DIR.mkdir(exist_ok=True)
    ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUT_DIR / f"run_{ts}"
    run_dir.mkdir(exist_ok=True)
    print(f"\n  Output folder: {run_dir}")

    results = []

    if mda_chunks:
        run_pair("MDA", mda_chunks, foundation, prompt_text, cfg, run_dir, results)

    if gtq_chunks:
        run_pair("GTQ", gtq_chunks, foundation, prompt_text, cfg, run_dir, results)

    if not mda_chunks and not gtq_chunks:
        sys.exit("ERROR: No corpus chunks retrieved. Check CHROMA_DIR and GTQ_CHROMA_DIR in config.txt.")

    write_summary(run_dir, results, ts)

    print()
    print("=" * 60)
    print(f"  Done. Results in: {run_dir}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
