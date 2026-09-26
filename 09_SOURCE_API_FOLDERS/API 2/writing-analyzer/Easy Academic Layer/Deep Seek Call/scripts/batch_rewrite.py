"""
Theophysics Batch Rewriter v1.0
Sends cleaned markdown through DeepSeek for 9th-grade and academic rewrites.

Usage:
    python batch_rewrite.py                  (run both passes)
    python batch_rewrite.py --level easy     (9th grade only)
    python batch_rewrite.py --level academic (academic only)
    python batch_rewrite.py --dry-run        (count files + estimate cost)
    python batch_rewrite.py --limit 5        (process only first N files)
"""

import os
import sys
import json
import time
import pathlib
import argparse
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ENGINE_DIR = SCRIPT_DIR.parent.parent.parent  # writing-analyzer root
CONFIG_PATH = ENGINE_DIR / "config.txt"

CLEANED_DIR = pathlib.Path(r"X:\conversion_station\HTML to Markdown\cleaned")
EASY_OUT = SCRIPT_DIR.parent / "outbox" / "easy"
ACADEMIC_OUT = SCRIPT_DIR.parent / "outbox" / "academic"

PROMPT_9TH = SCRIPT_DIR.parent / "prompts" / "9th_grade_rewrite.txt"
PROMPT_ACADEMIC = SCRIPT_DIR.parent / "prompts" / "academic_rewrite.txt"

LOG_FILE = SCRIPT_DIR.parent / "rewrite_log.txt"

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

PRICING = {
    "deepseek-chat": (0.00027, 0.00110),
    "deepseek-reasoner": (0.00055, 0.00219),
    "o3": (0.01000, 0.04000),
    "o3-mini": (0.00110, 0.00440),
    "gpt-4o": (0.00250, 0.01000),
}

# ── Config ────────────────────────────────────────────────────────────────
def parse_config(path):
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

def estimate_tokens(text):
    return max(1, len(text) // 4)

# ── Core rewrite function ─────────────────────────────────────────────────
def rewrite_file(client, model, temperature, max_tokens, prompt_text, article_text, retries=3):
    """Send article to DeepSeek with the given prompt. Returns (response_text, usage_dict)."""
    messages = [
        {"role": "user", "content": prompt_text + "\n\n---\n\n" + article_text}
    ]

    for attempt in range(retries):
        try:
            kwargs = {
                "model": model,
                "messages": messages,
            }
            # o3 doesn't support temperature
            if not model.startswith("o") and temperature is not None:
                kwargs["temperature"] = temperature
            if max_tokens:
                if model.startswith("o"):
                    kwargs["max_completion_tokens"] = max_tokens
                else:
                    kwargs["max_tokens"] = max_tokens

            response = client.chat.completions.create(**kwargs)
            reply = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }
            return reply, usage

        except Exception as e:
            err_str = str(e)
            if "rate" in err_str.lower() or "429" in err_str:
                wait = 2 ** (attempt + 1)
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    ERROR on attempt {attempt+1}: {e}")
                if attempt == retries - 1:
                    return None, {"prompt_tokens": 0, "completion_tokens": 0}
                time.sleep(2)
    return None, {"prompt_tokens": 0, "completion_tokens": 0}

# ── Main ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Batch rewrite markdown through DeepSeek")
    parser.add_argument("--level", choices=["easy", "academic", "both"], default="both")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source", type=str, default="", help="Override source directory")
    parser.add_argument("--limit", type=int, default=0, help="Process only first N files (0=all)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--outdir", type=str, default="", help="Override output base directory")
    parser.add_argument("--engine", choices=["deepseek", "openai"], default="deepseek", help="Which API to use")
    parser.add_argument("--prompt", type=str, default="", help="Override prompt file path (uses this for all passes)")
    args = parser.parse_args()

    cfg = parse_config(CONFIG_PATH)

    if args.engine == "openai":
        api_key = cfg.get("OPENAI_API_KEY", "")
        model = cfg.get("OPENAI_MODEL", "o3")
        base_url = "https://api.openai.com/v1"
        max_tokens = int(cfg.get("OPENAI_MAX_TOKENS", "16000") or "0")
        temperature = 1  # o3 doesn't support temperature, set to default
    else:
        api_key = cfg.get("DEEPSEEK_API_KEY", "")
        model = cfg.get("MODEL", "deepseek-chat")
        base_url = DEEPSEEK_BASE_URL
        max_tokens = int(cfg.get("MAX_TOKENS", "4096") or "0")
        if max_tokens < 8192:
            max_tokens = 8192
        temperature = float(cfg.get("TEMPERATURE", "0.3"))

    # Collect markdown files
    source_dir = pathlib.Path(args.source) if args.source else CLEANED_DIR
    md_files = sorted(source_dir.rglob("*.md"))
    if args.limit > 0:
        md_files = md_files[:args.limit]

    # Load prompts
    if args.prompt:
        custom_prompt = pathlib.Path(args.prompt).read_text(encoding="utf-8")
        prompt_easy = custom_prompt
        prompt_acad = custom_prompt
    else:
        prompt_easy = PROMPT_9TH.read_text(encoding="utf-8") if PROMPT_9TH.exists() else ""
        prompt_acad = PROMPT_ACADEMIC.read_text(encoding="utf-8") if PROMPT_ACADEMIC.exists() else ""

    # Determine which passes to run
    passes = []
    if args.outdir:
        out_base = pathlib.Path(args.outdir)
        easy_out = out_base / "easy"
        acad_out = out_base / "academic"
    else:
        easy_out = EASY_OUT
        acad_out = ACADEMIC_OUT

    if args.level in ("easy", "both"):
        passes.append(("easy", prompt_easy, easy_out))
    if args.level in ("academic", "both"):
        passes.append(("academic", prompt_acad, acad_out))

    # Estimate total tokens for dry run
    total_input_chars = sum(f.read_text(encoding="utf-8", errors="replace").__len__() for f in md_files)
    est_input_per_file = total_input_chars // max(len(md_files), 1)
    est_tokens_per_file = estimate_tokens("x" * (est_input_per_file + 2000))  # +prompt overhead

    print("=" * 60)
    print("  Theophysics Batch Rewriter")
    print("=" * 60)
    print(f"  Source:       {source_dir}")
    print(f"  Files:        {len(md_files)}")
    print(f"  Passes:       {[p[0] for p in passes]}")
    print(f"  Model:        {model}")
    print(f"  Temperature:  {temperature}")
    total_calls = len(md_files) * len(passes)
    print(f"  Total calls:  {total_calls}")

    # Cost estimate
    if model in PRICING:
        in_rate, out_rate = PRICING[model]
        est_in = est_tokens_per_file * total_calls
        est_out = 3000 * total_calls  # assume ~3K output tokens per rewrite
        est_cost = (est_in / 1000) * in_rate + (est_out / 1000) * out_rate
        print(f"  Est. cost:    ${est_cost:.2f}")
    print("=" * 60)

    if args.dry_run:
        print("\n  DRY RUN — no API calls made.")
        return

    if not api_key or api_key.startswith("sk-PASTE"):
        sys.exit("ERROR: No valid API key in config.txt")

    # Init client
    try:
        import openai
    except ImportError:
        sys.exit("ERROR: pip install openai")

    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    # Processing loop
    log_lines = [f"=== Batch Rewrite — {datetime.datetime.now().isoformat()} ===\n"]
    total_in_tokens = 0
    total_out_tokens = 0
    total_cost = 0.0
    succeeded = 0
    failed = 0

    for pass_name, prompt_text, out_dir in passes:
        print(f"\n{'─'*60}")
        print(f"  PASS: {pass_name.upper()}")
        print(f"{'─'*60}")

        for idx, md_path in enumerate(md_files):
            rel_path = md_path.relative_to(source_dir)
            out_path = out_dir / rel_path

            # Skip if already processed (resume support) unless --force
            if not args.force and out_path.exists() and out_path.stat().st_size > 100:
                print(f"  [{idx+1}/{len(md_files)}] SKIP (exists): {rel_path}")
                continue

            article = md_path.read_text(encoding="utf-8", errors="replace")

            # Skip tiny files (indexes, READMEs under 200 chars)
            if len(article.strip()) < 200:
                print(f"  [{idx+1}/{len(md_files)}] SKIP (tiny): {rel_path}")
                continue

            print(f"  [{idx+1}/{len(md_files)}] {pass_name}: {rel_path}...", end=" ", flush=True)

            result, usage = rewrite_file(client, model, temperature, max_tokens, prompt_text, article)

            if result:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(result, encoding="utf-8")
                succeeded += 1

                in_tok = usage["prompt_tokens"]
                out_tok = usage["completion_tokens"]
                total_in_tokens += in_tok
                total_out_tokens += out_tok

                if model in PRICING:
                    cost = (in_tok / 1000) * PRICING[model][0] + (out_tok / 1000) * PRICING[model][1]
                    total_cost += cost
                    print(f"OK ({in_tok}+{out_tok} tok, ${cost:.4f})")
                else:
                    print(f"OK ({in_tok}+{out_tok} tok)")

                log_lines.append(f"OK  {pass_name} {rel_path} in={in_tok} out={out_tok}\n")
            else:
                failed += 1
                print("FAILED")
                log_lines.append(f"FAIL {pass_name} {rel_path}\n")

            # Small delay to avoid rate limits
            time.sleep(0.5)

    # Summary
    summary = f"""
{'='*60}
BATCH REWRITE SUMMARY
{'='*60}
Succeeded:        {succeeded}
Failed:           {failed}
Total input tok:  {total_in_tokens:,}
Total output tok: {total_out_tokens:,}
Total cost:       ${total_cost:.4f}
Easy output:      {EASY_OUT}
Academic output:  {ACADEMIC_OUT}
{'='*60}
"""
    print(summary)
    log_lines.append(summary)
    LOG_FILE.write_text("".join(log_lines), encoding="utf-8")
    print(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
