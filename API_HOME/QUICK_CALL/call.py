"""QUICK CALL: prompt.txt + every file in input/ -> DeepSeek -> output/. Standalone: copy the folder anywhere.

  python call.py            run (MODE=each: one call per file, side by side; MODE=together: one call)
  python call.py --dry-run  show what would be sent
  python call.py --redo     answer files again even when an answer exists
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
URL = os.environ.get("QUICK_CALL_URL", "https://api.deepseek.com/chat/completions")
TEXT = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".py", ".lean", ".tex", ".bib", ".yaml", ".yml",
        ".toml", ".ini", ".log", ".sql", ".rst", ".js", ".ts", ".srt", ".vtt"}


def settings() -> dict:
    out = {"MODE": "each", "WORKERS": "30", "MODEL": "deepseek-chat", "MAX_TOKENS": "8000", "TEMPERATURE": "0.3"}
    f = HERE / "settings.txt"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip().upper()] = v.strip()
    return out


def api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key and (HERE / "key.txt").exists():
        key = (HERE / "key.txt").read_text(encoding="utf-8").strip()
    return key


def prompt_text() -> str:
    lines = (HERE / "prompt.txt").read_text(encoding="utf-8").splitlines()
    return "\n".join(l for l in lines if not l.lstrip().startswith("#")).strip()


def inputs() -> list[Path]:
    folder = HERE / "input"
    return sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in TEXT and not p.name.startswith("."))


def call(key: str, cfg: dict, content: str) -> tuple[str, int]:
    body = json.dumps({"model": cfg["MODEL"], "messages": [{"role": "user", "content": content}],
                       "max_tokens": int(cfg["MAX_TOKENS"]), "temperature": float(cfg["TEMPERATURE"])}).encode()
    for attempt in range(4):
        req = urllib.request.Request(URL, body, {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read())
            return data["choices"][0]["message"]["content"], int(data.get("usage", {}).get("total_tokens", 0))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise RuntimeError(f"HTTP {e.code}: {e.read()[:300].decode(errors='replace')}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 3:
                raise RuntimeError(str(e)) from None
        time.sleep(2 ** (attempt + 1))
    raise RuntimeError("no answer")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    cfg, prompt, files = settings(), prompt_text(), inputs()
    out = HERE / "output"
    out.mkdir(exist_ok=True)
    tag = hashlib.sha256(prompt.encode()).hexdigest()[:6]   # a new prompt means new answers
    if not prompt:
        print("prompt.txt is empty.")
        return 1
    together = cfg["MODE"].lower() == "together" or not files
    if together:
        attached = "".join(f"\n\n===== FILE: {p.name} =====\n{p.read_text(encoding='utf-8', errors='replace')}" for p in files)
        jobs = [(f"answer - {datetime.now():%Y-%m-%d %H%M}.md", prompt + attached)]
    else:
        jobs = [(f"{p.stem} - answer {tag}.md", f"{prompt}\n\n===== FILE: {p.name} =====\n{p.read_text(encoding='utf-8', errors='replace')}")
                for p in files]
        skipped = [j for j in jobs if (out / j[0]).exists() and not a.redo]
        jobs = [j for j in jobs if j not in skipped]
        if skipped:
            print(f"{len(skipped)} file(s) already answered for this prompt (skipped; --redo to answer again).")
    plan = "one call with everything" if together else f"{len(jobs)} call(s), {cfg['WORKERS']} at once"
    print(f"{len(files)} file(s) in input · {plan} · {cfg['MODEL']}")
    for name, content in jobs:
        print(f"  {name}: {len(content):,} chars (~{len(content) // 4:,} tokens in)")
    if a.dry_run or not jobs:
        return 0
    key = api_key()
    if not key:
        print("No key: set DEEPSEEK_API_KEY (SETUP.bat does it) or put the key in key.txt next to call.py.")
        return 1
    failed, tokens = 0, 0

    def one(job):
        name, content = job
        started = time.time()
        text, used = call(key, cfg, content)
        tmp = out / (name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(out / name)                      # saved the moment it is done
        return name, used, time.time() - started

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, int(cfg["WORKERS"]))) as pool:
        futures = {pool.submit(one, j): j[0] for j in jobs}
        for n, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                name, used, secs = fut.result()
                tokens += used
                print(f"  [{n}/{len(jobs)}] OK  {name}  ({used:,} tokens, {secs:.0f}s)", flush=True)
            except Exception as exc:
                failed += 1
                print(f"  [{n}/{len(jobs)}] ERR {futures[fut]}: {exc}", flush=True)
    print(f"Done: {len(jobs) - failed} answered, {failed} failed, {tokens:,} tokens. Answers in {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
