"""
synthesize_series.py — Series Proof Synthesizer v2.1
Recursively reads all proof files in a folder tree,
caps large files, chunks into multiple DeepSeek calls with running notes,
and produces a single synthesis markdown.

Usage:
  python synthesize_series.py --folder PATH --output PATH [--use-proxy]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
LOCAL_PROXY_URL = "http://192.168.1.177:9333/v1/chat/completions"

VALID_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".lean"}
MAX_CHUNK_CHARS = 80_000
MAX_NOTES_CHARS = 12_000
MAX_FILE_CHARS = 60_000   # per-file cap — large JSONs get truncated


# ---------------------------------------------------------------------------
# Recursive file reading
# ---------------------------------------------------------------------------
def read_all_files(folder: Path) -> list[dict]:
    files = []
    for f in sorted(folder.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() not in VALID_EXTENSIONS:
            continue
        if "SERIES_SYNTHESIS" in f.name or "WORKING_NOTES" in f.name:
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = f.relative_to(folder)
            original_size = len(content)
            if original_size > MAX_FILE_CHARS:
                content = content[:MAX_FILE_CHARS] + f"\n\n[TRUNCATED — {original_size:,} chars total, showing first {MAX_FILE_CHARS:,}]"
                print(f"  TRUNCATED: {rel} ({original_size:,} → {MAX_FILE_CHARS:,} chars)")
            files.append({"path": str(rel), "content": content, "size": len(content)})
        except Exception as e:
            print(f"  WARN: Could not read {f}: {e}")
    return files


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def chunk_files(files: list[dict], max_chars: int) -> list[list[dict]]:
    chunks = []
    current_chunk = []
    current_size = 0
    for f in files:
        entry_size = len(f["path"]) + len(f["content"]) + 50
        if current_size + entry_size > max_chars and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0
        current_chunk.append(f)
        current_size += entry_size
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def format_chunk(files: list[dict]) -> str:
    parts = []
    for f in files:
        parts.append(f"\n--- FILE: {f['path']} ---\n\n{f['content']}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a proof registry analyst for the Theophysics Research Initiative (POF 2828).
You are given Lean 4 proof briefs, pill.yaml proof receipts, atom.json theorem records, and related documentation from a formal verification program.

This is a real research initiative with Lean 4 machine-verified proofs. The proof receipts are machine-verified evidence, not claims.

YOUR JOB:

1. If anything was retired, repaired, or proven wrong — say so once, early, and move on. Don't dwell on it. Just: what was wrong, what replaced it, done.

2. ANOMALIES — give these real attention. Look for results that are surprising, structurally unusual, or that connect domains that shouldn't connect. Things nobody else would notice. Point them out. Say why they're unusual.

3. Everything else — clean inventory. What's proven, what depends on what, what's open. Tables are fine. Group however makes sense for the material.

4. Every claim references the specific file and theorem name that supports it.

5. Respect the "What it does NOT prove" sections exactly — do not overclaim. The guardrails in the briefs are there for a reason.

Be precise. Let the material speak. Don't force a structure — organize around what's actually there."""


def make_chunk_prompt(chunk_text, chunk_num, total_chunks, series_name, running_notes):
    if total_chunks == 1:
        return f"Synthesize the following proof series: {series_name}\n\n{chunk_text}"

    notes_section = ""
    if running_notes:
        notes_section = f"\nRUNNING NOTES FROM PREVIOUS CHUNKS:\n{running_notes}\n\n"

    if chunk_num < total_chunks:
        return (f"This is chunk {chunk_num} of {total_chunks} for proof series: {series_name}\n\n"
                f"{notes_section}"
                f"Read the following files and produce NOTES ONLY — do not write the final synthesis yet.\n"
                f"Capture: every theorem/definition/countermodel (name + one-line description), "
                f"any retired/repaired axioms, surprising connections, dependencies, gaps.\n"
                f"Format as structured bullet points.\n\n{chunk_text}")
    else:
        return (f"This is the FINAL chunk ({chunk_num} of {total_chunks}) for proof series: {series_name}\n\n"
                f"{notes_section}"
                f"Read the following files, integrate with your notes, and produce the FULL SYNTHESIS.\n\n"
                f"{chunk_text}")


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------
def call_deepseek(system_prompt, user_prompt, api_key=None, use_proxy=False):
    import urllib.request
    url = LOCAL_PROXY_URL if use_proxy else DEEPSEEK_API_URL
    headers = {"Content-Type": "application/json"}
    if api_key and not use_proxy:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 8000,
        "temperature": 0.3,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  API ERROR: {e}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Synthesize a series of proof files")
    parser.add_argument("--folder", required=True, help="Path to series folder (recursive)")
    parser.add_argument("--output", required=True, help="Path for output markdown")
    parser.add_argument("--api-key", default=None,
                        help="DeepSeek API key (or set DEEPSEEK_API_KEY env var)")
    parser.add_argument("--use-proxy", action="store_true",
                        help="Use local NAS proxy instead of direct API")
    args = parser.parse_args()

    folder = Path(args.folder)
    output = Path(args.output)
    api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY", "")

    if not folder.exists():
        print(f"ERROR: Folder {folder} does not exist.")
        sys.exit(1)

    print(f"Reading files recursively from {folder} ...")
    all_files = read_all_files(folder)
    if not all_files:
        print("ERROR: No valid files found (.md, .json, .yaml, .lean)")
        sys.exit(1)

    total_chars = sum(f["size"] for f in all_files)
    dirs = len(set(str(Path(f["path"]).parent) for f in all_files))
    print(f"  Found {len(all_files)} files across {dirs} directories")
    print(f"  Total content: {total_chars:,} chars")

    chunks = chunk_files(all_files, MAX_CHUNK_CHARS)
    print(f"  Split into {len(chunks)} chunk(s)")

    series_name = folder.name
    running_notes = ""
    final_result = None
    result = None

    for i, chunk in enumerate(chunks, 1):
        chunk_text = format_chunk(chunk)
        print(f"\n  Chunk {i}/{len(chunks)}: {len(chunk)} files ({len(chunk_text):,} chars)")

        user_prompt = make_chunk_prompt(chunk_text, i, len(chunks), series_name, running_notes)
        print(f"    Calling DeepSeek ({'proxy' if args.use_proxy else 'direct'}) ...")
        result = call_deepseek(SYSTEM_PROMPT, user_prompt, api_key, args.use_proxy)

        if result is None:
            print(f"    ERROR: Failed. Retrying...")
            result = call_deepseek(SYSTEM_PROMPT, user_prompt, api_key, args.use_proxy)
            if result is None:
                print(f"    ERROR: Retry failed. Skipping chunk {i}.")
                continue

        if i < len(chunks):
            running_notes += f"\n\n## Notes from chunk {i}\n{result}"
            if len(running_notes) > MAX_NOTES_CHARS:
                running_notes = running_notes[-MAX_NOTES_CHARS:]
            print(f"    Notes captured ({len(result):,} chars)")
        else:
            final_result = result
            print(f"    Synthesis received ({len(result):,} chars)")

    if len(chunks) == 1 and final_result is None:
        final_result = result

    if final_result is None:
        print("ERROR: No synthesis produced.")
        sys.exit(1)

    if len(chunks) > 1 and running_notes:
        notes_path = output.parent / f"{series_name}_WORKING_NOTES.md"
        notes_path.write_text(
            f"# {series_name} — Working Notes\n\n"
            f"*Generated during {len(chunks)}-chunk synthesis on "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
            f"{running_notes}", encoding="utf-8")
        print(f"\n  Working notes saved to {notes_path}")

    manifest = "\n".join(f"- `{f['path']}` ({f['size']:,} chars)" for f in all_files)
    header = (f"# {series_name} — Series Proof Synthesis\n\n"
              f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
              f"*Source: {len(all_files)} files from `{folder}` (recursive)*\n"
              f"*Provider: DeepSeek ({DEEPSEEK_MODEL})*\n"
              f"*Chunks: {len(chunks)}*\n\n"
              f"<details>\n<summary>File Manifest ({len(all_files)} files)</summary>\n\n"
              f"{manifest}\n\n</details>\n\n---\n\n")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(header + final_result, encoding="utf-8")
    print(f"\n  Synthesis written to {output}")
    print("DONE.")


if __name__ == "__main__":
    main()
