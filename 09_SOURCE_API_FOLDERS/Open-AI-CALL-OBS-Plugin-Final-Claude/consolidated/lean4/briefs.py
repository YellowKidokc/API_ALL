"""Plain-language proof briefs for Lean files (DeepSeek).

One brief per distinct Lean file (by content hash, so file copies share a
brief). The brief explains what the file defines and proves in readable
language, one line per theorem, and -- just as important -- what it does NOT
show. It is an explanation, not evidence: the Lean receipt stays the evidence.

Stored as <out>/00_BRIEFS/<file>.brief.json (+ .md for reading). Pills pick the
per-theorem lines up as an `explanation` block on the next `pills` run.
"""

import hashlib
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

SYSTEM = (
    "You explain Lean 4 formalizations to an educated reader who does not read Lean. "
    "Be exact and plain. Never claim more than the Lean code proves. A Lean theorem only "
    "shows its statement follows from the definitions and hypotheses in the file; any "
    "reading about God, physics, morality or the real world is an interpretation that "
    "needs a separate bridge, and you must say so where it matters."
)

PROMPT = """Write a proof brief for this Lean 4 file. Return JSON only, with exactly these keys:

{{
  "title": "short human title for the file",
  "purpose": "2-4 sentences: what question this file formalizes and why",
  "definitions": [{{"name": "<Lean name>", "plain": "one sentence: what it means"}}],
  "theorems": [{{"name": "<Lean name exactly as declared>", "plain": "one sentence: what it shows, in plain words", "role": "main | supporting | countermodel | sanity_check"}}],
  "does_not_prove": ["specific things a reader might wrongly take this file to establish"],
  "assumptions": ["hypotheses/structure fields the results depend on, in plain words"],
  "how_to_cite": "one sentence a paper could use to cite this file honestly"
}}

Cover EVERY theorem and lemma in the file, using its exact declared name.

FILE: {path}
```lean
{code}
```"""


def _call(api_key: str, model: str, prompt: str) -> Dict[str, Any]:
    body = {"model": model, "temperature": 0.2, "max_tokens": 8192,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}
    last = None
    for attempt in range(4):
        try:
            r = requests.post(DEEPSEEK_URL, json=body, timeout=(20, 600),
                              headers={"Authorization": f"Bearer {api_key}"})
            r.raise_for_status()
            return json.loads(r.json()["choices"][0]["message"]["content"])
        except Exception as e:  # network hiccup, 429, cut-off JSON
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"DeepSeek failed: {last}")


def _render_md(b: Dict[str, Any]) -> str:
    lines = [f"# {b.get('title') or b['file']}", "",
             f"*Lean file:* `{b['file']}` · *Explanation written by {b['_model']} on {b['_generated_at'][:10]}. "
             "This is an explanation, not evidence — the Lean build receipt is the evidence.*", "",
             "## Purpose", "", b.get("purpose", ""), ""]
    if b.get("definitions"):
        lines += ["## Definitions", ""] + [f"- **{d['name']}** — {d['plain']}" for d in b["definitions"]] + [""]
    if b.get("theorems"):
        lines += ["## What it proves", ""] + [
            f"- **{t['name']}** ({t.get('role', '')}) — {t['plain']}" for t in b["theorems"]] + [""]
    if b.get("assumptions"):
        lines += ["## Depends on", ""] + [f"- {a}" for a in b["assumptions"]] + [""]
    if b.get("does_not_prove"):
        lines += ["## What it does NOT prove", ""] + [f"- {x}" for x in b["does_not_prove"]] + [""]
    if b.get("how_to_cite"):
        lines += ["## How to cite", "", b["how_to_cite"], ""]
    return "\n".join(lines)


def generate_briefs(root_dir: str, rel_paths: List[str], out_dir: str,
                    workers: int = 6, force: bool = False) -> Dict[str, int]:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is not set.")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    bdir = Path(out_dir) / "00_BRIEFS"
    bdir.mkdir(parents=True, exist_ok=True)

    # One brief per distinct file content.
    jobs: Dict[str, List[str]] = {}
    for rel in rel_paths:
        data = (Path(root_dir) / rel).read_bytes()
        jobs.setdefault(hashlib.sha256(data).hexdigest(), []).append(rel)

    counts = {"written": 0, "cached": 0, "failed": 0}

    def work(item):
        sha, rels = item
        rel = sorted(rels, key=len)[0]
        dest = bdir / (re.sub(r"[\\/]", "__", rel)[:-5] + ".brief.json")
        if not force and dest.exists():
            try:
                if json.loads(dest.read_text(encoding="utf-8")).get("file_sha256") == sha:
                    return "cached", rel
            except ValueError:
                pass
        code = (Path(root_dir) / rel).read_text(encoding="utf-8", errors="replace")
        brief = _call(api_key, model, PROMPT.format(path=rel, code=code))
        brief.update({"file": rel, "also_in": [r for r in rels if r != rel], "file_sha256": sha,
                      "_model": model, "_generated_at": datetime.now(timezone.utc).isoformat(),
                      "_kind": "AI explanation - not evidence"})
        dest.write_text(json.dumps(brief, indent=1, ensure_ascii=False), encoding="utf-8")
        dest.with_suffix("").with_suffix(".md").write_text(_render_md(brief), encoding="utf-8")
        return "written", rel

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for fut in [pool.submit(work, j) for j in jobs.items()]:
            try:
                status, rel = fut.result()
                counts[status] += 1
                print(f"  {status:<8} {rel}", flush=True)
            except Exception as e:
                counts["failed"] += 1
                print(f"  FAILED   {e}", flush=True)
    return counts


def load_theorem_lines(out_dir: str) -> Dict[tuple, Dict[str, Any]]:
    """(file, theorem short name) -> {plain, role, brief} for the pill exporter."""
    lines: Dict[tuple, Dict[str, Any]] = {}
    bdir = Path(out_dir) / "00_BRIEFS"
    if not bdir.exists():
        return lines
    for p in bdir.glob("*.brief.json"):
        try:
            b = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for rel in [b["file"]] + b.get("also_in", []):
            for t in b.get("theorems", []) + b.get("definitions", []):
                name = str(t.get("name", "")).split(".")[-1]
                lines[(rel, name)] = {"plain": t.get("plain"), "role": t.get("role"),
                                      "brief": "00_BRIEFS/" + p.name.replace(".brief.json", ".md"),
                                      "model": b.get("_model"), "generated_at": b.get("_generated_at")}
    return lines
