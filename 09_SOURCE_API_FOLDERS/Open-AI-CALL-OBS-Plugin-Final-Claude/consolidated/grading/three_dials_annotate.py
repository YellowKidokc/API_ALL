#!/usr/bin/env python3
"""three_dials_annotate.py — classify an article's load-bearing statements with the
Three Dials, and write the understanding ON TOP of the untouched original article.

Created 2026-09-16 (Claude, with David). Status: TESTED one-for-one.

Rule this script enforces (and every pipeline should):
  * The original article is preserved byte-for-byte in OUTBOX/00_ORIGINALS_PRESERVED
    with its SHA-256. It is never edited, moved, or summarized-over.
  * Output = one file: understanding block on top, `---`, then the full original
    article below, unchanged. You always have the base article + its classifications.

THE THREE DIALS
  1 KIND      foundation | checkable | bridge | practice_story
  2 STRENGTH  (bridges only) illustrates < resembles < corresponds < same_mechanism < demonstrated
  3 STANDING  draft | supported | canon | disputed | superseded   (AI may only PROPOSE)

Usage
  python three_dials_annotate.py "path\\to\\article.md"
  python three_dials_annotate.py "article.md" --model deepseek-reasoner
Needs: DEEPSEEK_API_KEY in environment.  pip: requests
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import article_stack

ROOT = Path(__file__).resolve().parents[1]
PRESERVED = ROOT / "OUTBOX" / "00_ORIGINALS_PRESERVED"
ANNOTATED = ROOT / "OUTBOX" / "ANNOTATED_THREE_DIALS"
API_URL = "https://api.deepseek.com/chat/completions"

KINDS = ["foundation", "checkable", "bridge", "practice_story"]
STRENGTHS = ["illustrates", "resembles", "corresponds", "same_mechanism", "demonstrated"]
STANDINGS = ["draft", "supported", "canon", "disputed", "superseded"]
BADGE = {"foundation": "🟦", "checkable": "🟩", "bridge": "🔗", "practice_story": "🟪"}

SYSTEM = """You annotate Theophysics articles (Christian theology + physics/math/neuroscience).
You are NOT asked to agree or disagree with the theology. Theological premises are admitted
starting points of the framework. Your job is to label what KIND each load-bearing statement is,
so that no statement quietly claims more than it has earned.

THE THREE DIALS
1. kind:
   - foundation     = admitted starting point or definition (theological premise, framework definition). Not proven; declared.
   - checkable      = math, data, a source, or an experiment could confirm or refute it.
   - bridge         = connects two domains (e.g. theology <-> physics, scripture <-> neuroscience).
   - practice_story = something done (a practice/protocol) or told (narrative, illustration). Judged by faithfulness, not proof.
2. strength (ONLY for bridge; null otherwise), a ladder:
   illustrates < resembles < corresponds < same_mechanism < demonstrated
   - "claimed_strength" = the rung the article's WORDING asserts ("proves", "is", "shows" = high rungs).
   - "earned_strength"  = the rung the article actually SUPPORTS with argument/evidence present in the text.
   If claimed > earned, that is a "rung_jump" — the most important thing to flag.
3. proposed_standing: draft | supported | canon | disputed | superseded
   You may only PROPOSE. For checkable claims, base it on your knowledge of the literature and say so.

Rules:
- Pick only LOAD-BEARING statements: ones the argument depends on, or that readers would quote. 8-25 of them.
- "quote" MUST be copied EXACTLY, character for character, from the article (one sentence or clause). No paraphrase.
- Be concrete and honest in "status_note": what is well supported, weak, likely wrong, or untestable. Name the kind of evidence.
- This is a STRENGTHENING pass, not a falsification pass. Do not write kill conditions.
  "strengthen_by": the single most useful thing that would move it UP the ladder or up in standing
  (a citation, a derivation, a named mechanism, a scope statement, a better verb).
  "connects_to": other statements IN THIS ARTICLE (by id) or well-known findings / scripture / theorems it
  naturally links to or is supported by — look actively for real connections.
- Flag provenance problems (AI chat residue, "let me present this to David", placeholders, duplicated sections).
Return JSON only."""

SCHEMA_HINT = {
    "document": {
        "title": "string",
        "one_line_thesis": "string",
        "summary": "3-5 sentences",
        "strongest_anchor": "the best-supported load-bearing statement and why",
        "weakest_brick": "the load-bearing statement most likely to be knocked down and why",
        "provenance_flags": ["string"],
    },
    "statements": [{
        "id": 1,
        "quote": "exact text from article",
        "section": "nearest heading",
        "kind": "foundation|checkable|bridge|practice_story",
        "domains": ["theology", "physics"],
        "claimed_strength": "illustrates|resembles|corresponds|same_mechanism|demonstrated|null",
        "earned_strength": "same ladder or null",
        "proposed_standing": "draft|supported|canon|disputed|superseded",
        "status_note": "string",
        "strengthen_by": "string",
        "connects_to": ["#3", "Shannon 1948: information requires distinguishable states", "John 1:1"],
    }],
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def call_deepseek(article: str, model: str) -> tuple[dict, dict]:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        sys.exit("DEEPSEEK_API_KEY is not set in this environment.")
    user = ("Annotate this article. Respond with JSON matching this shape:\n"
            + json.dumps(SCHEMA_HINT, ensure_ascii=False, indent=1)
            + "\n\n===== ARTICLE START =====\n" + article + "\n===== ARTICLE END =====")
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
        "temperature": 0.1,
        "max_tokens": 8000,
    }
    if model == "deepseek-chat":
        payload["response_format"] = {"type": "json_object"}
    last = None
    for attempt in range(1, 4):
        try:
            r = requests.post(API_URL, json=payload, timeout=300,
                              headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            r.raise_for_status()
            res = r.json()
            text = res["choices"][0]["message"]["content"]
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
            return json.loads(text), res.get("usage", {})
        except Exception as e:  # network / JSON errors → retry
            last = e
            print(f"  attempt {attempt} failed: {e}")
            time.sleep(3 * attempt)
    raise RuntimeError(f"DeepSeek call failed: {last}")


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def verify_quotes(statements: list[dict], article: str) -> None:
    """Deterministic check: the AI's quote must really be in the article."""
    flat = norm_ws(article)
    for s in statements:
        q = s.get("quote") or ""
        if q and q in article:
            s["quote_check"] = "exact"
        elif q and norm_ws(q) in flat:
            s["quote_check"] = "exact_except_whitespace"
        else:
            s["quote_check"] = "NOT_FOUND"


def rung(x):
    return STRENGTHS.index(x) if x in STRENGTHS else -1


def yaml_str(s) -> str:
    return json.dumps("" if s is None else str(s), ensure_ascii=False)


def render(doc: dict, stmts: list[dict], src: Path, sha: str, preserved: Path, model: str, usage: dict) -> str:
    d = doc or {}
    counts = {k: sum(1 for s in stmts if s.get("kind") == k) for k in KINDS}
    jumps = [s for s in stmts if s.get("kind") == "bridge" and rung(s.get("claimed_strength")) > rung(s.get("earned_strength")) >= 0]
    missing = [s for s in stmts if s.get("quote_check") == "NOT_FOUND"]

    fm = [
        "---",
        "three_dials:",
        "  schema: three-dials.v1",
        f"  source_path: {yaml_str(src)}",
        f"  source_sha256: {sha}",
        f"  original_preserved_at: {yaml_str(preserved)}",
        f"  annotated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"  model: deepseek/{model}",
        f"  tokens: {usage.get('total_tokens', 0)}",
        "  review_status: ai_proposed_pending_david",
        f"  counts: {{foundation: {counts['foundation']}, checkable: {counts['checkable']}, bridge: {counts['bridge']}, practice_story: {counts['practice_story']}}}",
        f"  rung_jumps: {len(jumps)}",
        f"  quotes_not_found: {len(missing)}",
        "---",
        "",
    ]
    out = fm + [
        f"# 🧭 Understanding — {d.get('title') or src.stem}",
        "",
        "> **AI-proposed annotations, pending David's review.** The original article is below the line, unchanged.",
        "",
        f"**Thesis:** {d.get('one_line_thesis', '')}",
        "",
        f"{d.get('summary', '')}",
        "",
        f"- **Strongest anchor:** {d.get('strongest_anchor', '')}",
        f"- **Weakest brick:** {d.get('weakest_brick', '')}",
    ]
    for f in d.get("provenance_flags") or []:
        out.append(f"- ⚠️ **Provenance:** {f}")
    if jumps:
        out += ["", "## ⚠️ Rung jumps (wording claims more than the text earns)", ""]
        for s in jumps:
            out.append(f"- **#{s['id']}** claims *{s['claimed_strength']}*, earns *{s['earned_strength']}* — “{s['quote']}”")
    out += ["", "## Load-bearing statements", "",
            "| # | Statement | Kind | Strength (claimed → earned) | Proposed standing | Status | Strengthen by | Connects to |",
            "|---|---|---|---|---|---|---|---|"]
    for s in stmts:
        k = s.get("kind", "?")
        strength = "—"
        if k == "bridge":
            strength = f"{s.get('claimed_strength')} → {s.get('earned_strength')}"
        q = (s.get("quote") or "").replace("|", "\\|").replace("\n", " ")
        if s.get("quote_check") == "NOT_FOUND":
            q += " ⚠️*quote not found in article*"
        cell = lambda v: str(v or "").replace("|", "\\|").replace("\n", " ")
        out.append(f"| {s.get('id')} | “{q}” | {BADGE.get(k, '')} {k} · {', '.join(s.get('domains') or [])} | {strength} | "
                   f"{cell(s.get('proposed_standing'))} | {cell(s.get('status_note'))} | {cell(s.get('strengthen_by') or s.get('needs'))} | "
                   f"{cell('; '.join(s.get('connects_to') or []))} |")
    out += ["", "*Kinds:* 🟦 foundation (declared) · 🟩 checkable · 🔗 bridge · 🟪 practice / story. "
            "*Ladder:* illustrates < resembles < corresponds < same_mechanism < demonstrated.",
            ""]
    return "\n".join(out)


def ckg_record(result: dict, stmts: list[dict], src: Path, sha: str, original: bytes, model: str, usage: dict) -> dict:
    """Record importable by nerve atoms/ckg-import.js (Axiom Builder → Import CKG JSON).
    Unknown fields are preserved by the importer, so the full dials ride along on each predicate."""
    d = result.get("document") or {}
    return {
        "format": "three-dials-ckg/v1",
        "title": d.get("title") or src.stem,
        "node_id": src.stem,
        "object_type": "CLAIM",
        "status": "CANDIDATE_DRAFT",
        "admitted_to_canon": False,
        "source_file": str(src),
        "source_sha256": sha,
        "preserved_source": {"text": original.decode("utf-8", errors="replace"), "sha256": sha},
        "truth_predicates": [{
            "id": f"P{s.get('id')}",
            "statement": s.get("quote", ""),
            "role": s.get("kind", ""),
            "formal": "",
            "three_dials": {k: s.get(k) for k in ("kind", "domains", "claimed_strength", "earned_strength",
                                                   "proposed_standing", "status_note", "strengthen_by",
                                                   "connects_to", "section", "quote_check")},
        } for s in stmts],
        "answers": {},
        "universal_gate": {},
        "report_fields": {
            "Central claim": d.get("one_line_thesis", ""),
            "Summary": d.get("summary", ""),
            "Strongest anchor": d.get("strongest_anchor", ""),
            "Weakest brick": d.get("weakest_brick", ""),
            "Provenance flags": "\n".join(d.get("provenance_flags") or []),
        },
        "annotation": {"model": f"deepseek/{model}", "usage": usage,
                       "review_status": "ai_proposed_pending_david",
                       "annotated_at": datetime.now().isoformat(timespec="seconds")},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("article")
    ap.add_argument("--model", default="deepseek-chat", choices=["deepseek-chat", "deepseek-reasoner"])
    args = ap.parse_args()

    src = Path(args.article)
    # 1. Preserve the original, byte-for-byte, before anything else (peels any old stack).
    raw, sha, preserved = article_stack.preserve(src)
    article = raw.decode("utf-8", errors="replace")
    print(f"preserved  {preserved}")

    # 2. Ask DeepSeek for the Three Dials.
    print(f"calling    deepseek/{args.model} on {src.name} ({len(article):,} chars) …")
    t0 = time.time()
    result, usage = call_deepseek(article, args.model)
    print(f"answered   in {time.time() - t0:.0f}s · tokens {usage.get('total_tokens')}")
    stmts = result.get("statements") or []
    verify_quotes(stmts, article)

    # 3. Understanding on top, original article below — untouched.
    ANNOTATED.mkdir(parents=True, exist_ok=True)
    header = render(result.get("document") or {}, stmts, src, sha, preserved, args.model, usage)
    stem = src.stem.replace(".annotated", "")
    out_path = article_stack.write_stacked(ANNOTATED / f"{stem}.annotated{src.suffix}", header, raw)
    json_path = ANNOTATED / f"{stem}.ckg.json"
    json_path.write_text(json.dumps(ckg_record(result, stmts, src, sha, raw, args.model, usage),
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json       {json_path}  (Axiom Builder → Import CKG JSON)")

    jumps = sum(1 for s in stmts if s.get("kind") == "bridge" and rung(s.get("claimed_strength")) > rung(s.get("earned_strength")) >= 0)
    nf = sum(1 for s in stmts if s.get("quote_check") == "NOT_FOUND")
    print(f"statements {len(stmts)} · rung jumps {jumps} · quotes not found {nf}")
    print(f"written    {out_path}")


if __name__ == "__main__":
    main()
