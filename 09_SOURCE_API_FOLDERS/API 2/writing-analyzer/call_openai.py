#!/usr/bin/env python3
"""
DeepSeek Direct-Call Script
============================
Reads your prompt from  prompt.txt,
attaches every file from  input/,
sends it all to the DeepSeek API,
prints the response AND saves it to  output/,
and shows an estimated cost breakdown.

Usage:
    python call_openai.py            (uses defaults from config.txt)
    python call_openai.py --dry-run  (show what WOULD be sent, no API call)
"""

import os
import sys
import json
import glob
import time

# Force UTF-8 output on Windows so Unicode in responses prints cleanly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pathlib
import argparse
import datetime
import mimetypes

# ---------------------------------------------------------------------------
#  Pricing table  (USD per 1 000 tokens — update when needed)
#  Source: https://api-docs.deepseek.com/quick_start/pricing
# ---------------------------------------------------------------------------
PRICING = {
    # model name              : (input $/1K, output $/1K)
    "deepseek-chat":           (0.00027,  0.00110),   # DeepSeek-V3
    "deepseek-reasoner":       (0.00055,  0.00219),   # DeepSeek-R1
}

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.txt"
PROMPT_PATH = SCRIPT_DIR / "prompt.txt"
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"

# File extensions we know how to read as text
TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm",
    ".py", ".js", ".ts", ".c", ".cpp", ".h", ".java", ".rb",
    ".rs", ".go", ".sh", ".bat", ".ps1", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".conf", ".log", ".sql", ".r",
    ".tex", ".bib", ".rst", ".org", ".slack", ".eml",
}

# Image extensions the vision models accept
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def parse_config(path: pathlib.Path) -> dict:
    """Read KEY=VALUE pairs from config.txt, ignoring comments and blanks."""
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


def read_prompt(path: pathlib.Path) -> str:
    """Read prompt.txt, stripping comment lines."""
    if not path.exists():
        sys.exit(f"ERROR: prompt file not found: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    content_lines = [l for l in lines if not l.strip().startswith("#")]
    text = "\n".join(content_lines).strip()
    if not text:
        sys.exit("ERROR: prompt.txt is empty (only comments). Write your prompt there first.")
    return text


def gather_input_files(input_dir: pathlib.Path):
    """Return list of (relative_name, abs_path, kind) for every file in input/."""
    files = []
    if not input_dir.exists():
        return files
    for p in sorted(input_dir.rglob("*")):
        if p.is_file() and p.name != ".gitkeep":
            ext = p.suffix.lower()
            if ext in IMAGE_EXTENSIONS:
                kind = "image"
            elif ext in TEXT_EXTENSIONS or is_likely_text(p):
                kind = "text"
            else:
                kind = "binary_skip"
            files.append((p.relative_to(input_dir), p, kind))
    return files


def is_likely_text(path: pathlib.Path) -> bool:
    """Best-effort check: try reading first 8 KB as UTF-8."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            f.read(8192)
        return True
    except (UnicodeDecodeError, PermissionError):
        return False


def estimate_tokens(text: str) -> int:
    """Rough token count: ~4 chars per token for English."""
    return max(1, len(text) // 4)


def format_cost(model: str, input_tokens: int, output_tokens: int) -> str:
    """Return a human-readable cost estimate."""
    if model not in PRICING:
        return f"(pricing data not available for model '{model}')"
    in_rate, out_rate = PRICING[model]
    in_cost = (input_tokens / 1000) * in_rate
    out_cost = (output_tokens / 1000) * out_rate
    total = in_cost + out_cost
    lines = [
        f"  Model          : {model}",
        f"  Input tokens   : ~{input_tokens:,}",
        f"  Output tokens  : ~{output_tokens:,}",
        f"  Input cost     : ${in_cost:.6f}",
        f"  Output cost    : ${out_cost:.6f}",
        f"  ESTIMATED TOTAL: ${total:.6f}",
    ]
    return "\n".join(lines)


import base64


def build_messages(prompt_text: str, files: list) -> list:
    """Build the messages array for the Chat Completions API."""
    content_parts = []

    # 1. The user's prompt
    content_parts.append({"type": "text", "text": prompt_text})

    # 2. Attached files
    for rel_name, abs_path, kind in files:
        if kind == "text":
            file_text = abs_path.read_text(encoding="utf-8", errors="replace")
            header = f"\n--- FILE: {rel_name} ---\n"
            content_parts.append({"type": "text", "text": header + file_text})
        elif kind == "image":
            mime = mimetypes.guess_type(str(abs_path))[0] or "image/png"
            b64 = base64.b64encode(abs_path.read_bytes()).decode("ascii")
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            })
        else:
            content_parts.append({
                "type": "text",
                "text": f"\n[Skipped binary file: {rel_name}]\n",
            })

    return [{"role": "user", "content": content_parts}]


def save_output(text: str, model: str) -> pathlib.Path:
    """Write the response to output/ with a timestamped filename."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"response_{model}_{ts}.txt"
    out_path.write_text(text, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Call the DeepSeek API with your prompt + files.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be sent without making the API call.")
    args = parser.parse_args()

    # --- Config ---
    cfg = parse_config(CONFIG_PATH)
    api_key = cfg.get("DEEPSEEK_API_KEY", "")
    model = cfg.get("MODEL", "deepseek-chat")
    max_tokens = int(cfg.get("MAX_TOKENS", "4096") or "0")
    temperature = float(cfg.get("TEMPERATURE", "0.7"))
    use_vectordb = cfg.get("USE_VECTORDB", "false").lower() == "true"
    collection_name = cfg.get("COLLECTION_NAME", "my_docs")
    top_k = int(cfg.get("TOP_K", "5") or "5")
    chroma_dir = pathlib.Path(cfg.get("CHROMA_DIR", str(SCRIPT_DIR / "chroma_db")))

    if not api_key or api_key.startswith("sk-PASTE"):
        if not args.dry_run:
            sys.exit(
                "ERROR: No valid API key found.\n"
                "Open config.txt and paste your DeepSeek key on the DEEPSEEK_API_KEY= line.\n"
                "Get one at: https://platform.deepseek.com/api_keys"
            )

    # --- Prompt ---
    prompt_text = read_prompt(PROMPT_PATH)

    # --- Input files ---
    files = gather_input_files(INPUT_DIR)

    print("=" * 60)
    print("  DeepSeek Direct-Call")
    print("=" * 60)
    print(f"  Model       : {model}")
    print(f"  Temperature : {temperature}")
    print(f"  Max tokens  : {max_tokens or 'model default'}")
    print(f"  Vector DB   : {'ON — ' + collection_name if use_vectordb else 'off'}")
    print(f"  Prompt size : {len(prompt_text):,} chars")
    print(f"  Input files : {len(files)}")
    for rel, _, kind in files:
        tag = "IMG" if kind == "image" else ("TXT" if kind == "text" else "SKIP")
        print(f"    [{tag}] {rel}")
    print("=" * 60)

    # --- Optional: retrieve context from ChromaDB ---
    vector_context = ""
    if use_vectordb:
        if not chroma_dir.exists():
            print("\nWARNING: USE_VECTORDB=true but chroma_db/ folder not found.")
            print("Run VECTORIZE.bat first to ingest your files.\n")
        else:
            try:
                import chromadb
                from chromadb.utils import embedding_functions
                client_chroma = chromadb.PersistentClient(path=str(chroma_dir))
                ef = embedding_functions.DefaultEmbeddingFunction()
                col = client_chroma.get_or_create_collection(
                    name=collection_name, embedding_function=ef,
                    metadata={"hnsw:space": "cosine"},
                )
                if col.count() == 0:
                    print(f"\nWARNING: Collection '{collection_name}' is empty.")
                    print("Run VECTORIZE.bat first to ingest your files.\n")
                else:
                    results = col.query(
                        query_texts=[prompt_text],
                        n_results=min(top_k, col.count()),
                    )
                    docs = results.get("documents", [[]])[0]
                    metas = results.get("metadatas", [[]])[0]
                    if docs:
                        lines = ["[CONTEXT FROM KNOWLEDGE BASE]"]
                        for doc, meta in zip(docs, metas):
                            src = meta.get("source", "unknown")
                            lines.append(f"--- Chunk from: {src} ---")
                            lines.append(doc)
                        lines.append("[END CONTEXT]")
                        vector_context = "\n".join(lines)
                        print(f"\n  Retrieved {len(docs)} chunk(s) from '{collection_name}'.")
            except ImportError:
                print("\nWARNING: chromadb not installed. Run VECTORIZE.bat to install it.\n")
            except Exception as e:
                print(f"\nWARNING: ChromaDB query failed: {e}\n")

    # Build API messages
    full_prompt = (vector_context + "\n\n" + prompt_text).strip() if vector_context else prompt_text
    messages = build_messages(full_prompt, files)

    # Estimate input tokens from the serialized payload
    payload_text = json.dumps(messages)
    est_input_tokens = estimate_tokens(payload_text)

    # --- Dry run ---
    if args.dry_run:
        print("\n-- DRY RUN (no API call) --")
        print(f"\nEstimated input tokens: ~{est_input_tokens:,}")
        est_output = min(max_tokens or 4096, 4096)
        print(f"Assumed output tokens : ~{est_output:,}")
        print()
        print(format_cost(model, est_input_tokens, est_output))
        print("\nPrompt preview (first 500 chars):")
        print("-" * 40)
        print(full_prompt[:500])
        print("-" * 40)
        return

    # --- Real call ---
    try:
        import openai
    except ImportError:
        sys.exit(
            "ERROR: The 'openai' package is not installed.\n"
            "Run:  pip install openai"
        )

    client = openai.OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    print("\nSending request to DeepSeek ...")
    t0 = time.time()

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    try:
        response = client.chat.completions.create(**kwargs)
    except openai.AuthenticationError:
        sys.exit("ERROR: Invalid API key. Check config.txt.")
    except openai.RateLimitError:
        sys.exit("ERROR: Rate limited. Wait a moment and try again.")
    except openai.APIError as e:
        sys.exit(f"ERROR: DeepSeek API error: {e}")

    elapsed = time.time() - t0
    reply = response.choices[0].message.content
    usage = response.usage

    # --- Output ---
    print(f"\nResponse received in {elapsed:.1f}s\n")
    print("=" * 60)
    print(reply)
    print("=" * 60)

    # Save to file
    out_path = save_output(reply, model)
    print(f"\nSaved to: {out_path}")

    # Cost breakdown
    in_tok = usage.prompt_tokens if usage else est_input_tokens
    out_tok = usage.completion_tokens if usage else 0
    print("\n--- Cost Estimate ---")
    print(format_cost(model, in_tok, out_tok))
    print()


if __name__ == "__main__":
    main()
