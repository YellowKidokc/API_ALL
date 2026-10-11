"""span_judge.py -- Stage 3 of the Fruits of the Spirit grading pipeline.

Span-level judgment pass using the DeepSeek chat API. Groups Stage 1 sentences
into spans (~3 sentences each, never crossing a blank-line paragraph break),
sends each span plus its Stage 1 lexicon hits as evidence, and collects a
strict-JSON judgment per span.

Also (re)generates the station's system prompt file
scripts/prompts/fruits_system_v0.3.0.txt from the rubric
scripts/rubric/fruits_rubric_v0.3.0.json, quoting the nine fruit mechanisms
and five veto conditions verbatim.

Inputs:
  --paper <path>   the graded paper (its .lexicon.json must exist in
                   grading_out/; run lexicon_pass.py first)
  --limit N        grade only the first N spans (pilot mode)

Output:
  grading_out/<paper>.spans.json  (per-span judgments + run manifest with
  model, prompt sha256, rubric sha256, lexicon-cache sha256, timestamps)
  grading_out/diagnostics/        raw invalid API responses (never presented
                                  as grades)

API: DeepSeek chat completions, model deepseek-chat, temperature 0.1,
max_tokens 2000, response_format json_object (falls back if unsupported),
concurrency 2, timeout 240s, one retry on invalid JSON.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

STATION_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
OUT_DIR = STATION_DIR / "grading_out"
DIAG_DIR = OUT_DIR / "diagnostics"
RUBRIC_PATH = SCRIPTS_DIR / "rubric" / "fruits_rubric_v0.3.0.json"
PROMPT_PATH = SCRIPTS_DIR / "prompts" / "fruits_system_v0.3.0.txt"
LEXICON_CACHE = SCRIPTS_DIR / "lexicon_cache.json"
WEIGHTS_PATH = SCRIPTS_DIR / "weights.json"

BASE_URL = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"
TEMPERATURE = 0.1
MAX_TOKENS = 2000
TIMEOUT_S = 240
CONCURRENCY = 2

ROLES = ["CLAIM", "EVIDENCE", "MECHANISM", "DEFINITION",
         "OBJECTION", "CONCESSION", "BOUNDARY", "RHETORIC"]

PROMPT_VERSION = "v0.3.1"


def load_weights():
    """Load scripts/weights.json (the tuning file). Fail loudly if missing."""
    if not WEIGHTS_PATH.exists():
        sys.exit(f"ERROR: tuning file not found: {WEIGHTS_PATH}\n"
                 "weights.json holds the category weights and tunables; restore it.")
    with open(WEIGHTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# System prompt (built from the rubric; mechanisms and vetoes quoted verbatim)
# ---------------------------------------------------------------------------

def build_system_prompt(rubric):
    fruit_lines = []
    for fr in rubric["fruits"]:
        fruit_lines.append(
            f'- {fr["id"]} ({fr["name"]}): mechanism: "{fr["mechanism"]}"\n'
            f'  anti-fruit: {fr["anti_fruit"]}\n'
            f'  counterfeit: {fr["counterfeit"]}'
        )
    veto_lines = "\n".join(f"- {v}" for v in rubric["veto_conditions"])
    gate_lines = "\n".join(
        f'- {g["id"]} ({"HARD" if g["hard"] else "soft"}): {g["question"]}'
        for g in rubric["gates"]
    )
    role_lines = ", ".join(ROLES)
    return f"""You are the Fruits of the Spirit span-mode grader {PROMPT_VERSION} (rubric {rubric["rubric_id"]}).

You grade OBSERVABLE TEXT ONLY. Rules you must never break:
- No inference about hidden motives, salvation status, or divine origin.
- Vocabulary is not character evidence; match signals to mechanisms, not vibes.
- Where evidence is missing, say so explicitly. Never invent precision.
- Return STRICT JSON ONLY. No prose, no markdown fences, no commentary.

THE NINE FRUIT MECHANISMS (verbatim from the rubric):
{chr(10).join(fruit_lines)}

GATES:
{gate_lines}

THE FIVE VETO CONDITIONS (verbatim from the rubric):
{veto_lines}

For each span you receive the span text and a lexicon-evidence block (per-sentence
matched terms per category, claim-strength counts, hedge/absolute counts). Treat the
lexicon hits as evidence pointers, not verdicts; confirm or discount them against the
actual span text.

Assign the span exactly one rhetorical role from: {role_lines}.

FRUIT SIGNAL RULES (strict):
- A fruit_signal may map a span to a fruit ONLY when the span engages that fruit's
  mechanism as quoted above. A bare mention of the fruit's name or vocabulary is NOT
  a signal. If no mechanism is engaged, omit the signal entirely.
- Each signal carries TWO polarity fields:
  * "polarity": "+" if the mechanism is expressed/present, "-" if its anti-fruit is.
  * "polarity_kind": "enacted" if the text itself exhibits the fruit or anti-fruit
    (the writing/speaker does the thing), or "about" if the text merely reports,
    discusses, or describes it in the world (e.g. a study finding, a quoted third
    party, a historical trend).
- Do not map a term to a fruit axis it does not belong to. If an anti-fruit concept
  has no clean axis, say so in uncertainty_note instead of forcing a mapping.

Respond with ONE JSON object of exactly this shape:
{{
  "role": one of {role_lines},
  "fruit_signals": [{{"fruit_id": "fruit.<axis>", "polarity": "+" or "-",
                      "polarity_kind": "enacted" or "about",
                      "strength": 1-4, "evidence_quote": "<verbatim substring of the span>"}}],
  "gate_flags": ["<gate_id>", ...],
  "veto_flags": ["<veto condition name>", ...],
  "counterfeit_suspect": true or false,
  "confidence": 0.0-1.0,
  "uncertainty_note": "<what is missing or ambiguous; empty string if nothing>"
}}
Use fruit_id values fruit.love, fruit.joy, fruit.peace, fruit.patience, fruit.kindness,
fruit.goodness, fruit.faithfulness, fruit.gentleness, fruit.self_control.
Empty arrays are correct when there is no signal. Evidence quotes must be verbatim
substrings of the span text."""


def ensure_prompt_file(rubric):
    prompt = build_system_prompt(rubric)
    if not PROMPT_PATH.exists() or PROMPT_PATH.read_text(encoding="utf-8") != prompt:
        PROMPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROMPT_PATH.write_text(prompt, encoding="utf-8")
        print(f"[span] wrote system prompt: {PROMPT_PATH}")
    return prompt


# ---------------------------------------------------------------------------
# Span construction
# ---------------------------------------------------------------------------

def build_spans(sentences, target):
    """Group consecutive sentences into spans of ~target sentences, never
    crossing a paragraph break."""
    spans = []
    current = []
    for s in sentences:
        if current and (s["paragraph"] != current[-1]["paragraph"] or len(current) >= target):
            spans.append(current)
            current = []
        current.append(s)
    if current:
        spans.append(current)
    return spans


def span_evidence(span_sents):
    per_sent = []
    for s in sentences_compact(span_sents):
        per_sent.append(s)
    totals = {}
    for cat in ("fruit", "anti_fruit", "grounding", "contradiction", "jargon", "propaganda"):
        terms = sorted({t for s in span_sents for t in s["categories"][cat]["matched_terms"]})
        if terms:
            totals[cat] = {"hits": sum(s["categories"][cat]["hits"] for s in span_sents),
                           "matched_terms": terms}
    cs = {k: sum(s["claim_strength"][k] for s in span_sents)
          for k in ("weak", "moderate", "strong", "forbidden")}
    return {"per_sentence": per_sent, "category_totals": totals,
            "claim_strength": cs,
            "hedges": sum(s["hedges"] for s in span_sents),
            "absolutes": sum(s["absolutes"] for s in span_sents)}


def sentences_compact(span_sents):
    out = []
    for s in span_sents:
        matched = {c: s["categories"][c]["matched_terms"]
                   for c in ("fruit", "anti_fruit", "grounding", "contradiction", "jargon", "propaganda")
                   if s["categories"][c]["matched_terms"]}
        out.append({"idx": s["idx"], "matched": matched,
                    "claim_strength": {k: v for k, v in s["claim_strength"].items() if v},
                    "hedges": s["hedges"], "absolutes": s["absolutes"]})
    return out


# ---------------------------------------------------------------------------
# DeepSeek API
# ---------------------------------------------------------------------------

def extract_json(content):
    """Parse a model response as JSON, tolerating markdown fences."""
    content = content.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.S)
    if m:
        content = m.group(1)
    return json.loads(content)


def call_api(session, api_key, system_prompt, user_payload, use_json_mode=True):
    body = {
        "model": MODEL,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload},
        ],
    }
    if use_json_mode:
        body["response_format"] = {"type": "json_object"}
    r = session.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
        json=body,
        timeout=TIMEOUT_S,
    )
    if r.status_code == 400 and use_json_mode:
        # json mode unsupported / rejected: retry the call without it
        return call_api(session, api_key, system_prompt, user_payload, use_json_mode=False)
    r.raise_for_status()
    data = r.json()
    usage = data.get("usage") or {}
    usage = {k: usage.get(k) for k in
             ("prompt_tokens", "completion_tokens", "total_tokens",
              "prompt_cache_hit_tokens", "prompt_cache_miss_tokens")}
    return data["choices"][0]["message"]["content"], use_json_mode, usage


_diag_lock = threading.Lock()


def save_diagnostic(span_id, raw, reason):
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    path = DIAG_DIR / f"span_{span_id:04d}_{reason}.txt"
    with _diag_lock:
        path.write_text(raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    return str(path)


def validate_judgment(obj):
    if not isinstance(obj, dict):
        raise ValueError("judgment is not a JSON object")
    for key in ("role", "fruit_signals", "gate_flags", "veto_flags",
                "counterfeit_suspect", "confidence", "uncertainty_note"):
        if key not in obj:
            raise ValueError(f"missing key: {key}")
    if obj["role"] not in ROLES:
        raise ValueError(f"invalid role: {obj['role']}")
    return obj


def grade_span(session, api_key, system_prompt, span_id, span_sents):
    text = "\n".join(s["text"] for s in span_sents)
    user_payload = json.dumps({
        "span_id": span_id,
        "span_text": text,
        "lexicon_evidence": span_evidence(span_sents),
    }, ensure_ascii=False)
    record = {
        "span_id": span_id,
        "sent_idx_start": span_sents[0]["idx"],
        "sent_idx_end": span_sents[-1]["idx"],
        "text": text,
    }
    last_raw, last_err = None, None
    for attempt in (1, 2):
        try:
            raw, json_mode, usage = call_api(session, api_key, system_prompt, user_payload)
            last_raw = raw
            judgment = validate_judgment(extract_json(raw))
            record.update({"status": "ok", "judgment": judgment,
                           "attempts": attempt, "json_mode": json_mode,
                           "usage": usage})
            return record
        except (json.JSONDecodeError, ValueError) as e:
            last_err = f"{type(e).__name__}: {e}"
            if attempt == 1:
                save_diagnostic(span_id, last_raw or "", "invalid_json_attempt1")
                user_payload = json.dumps({
                    "span_id": span_id,
                    "span_text": text,
                    "lexicon_evidence": span_evidence(span_sents),
                    "correction": ("Your previous reply was not valid strict JSON of the "
                                   "required shape. Reply with ONLY the JSON object."),
                }, ensure_ascii=False)
        except requests.RequestException as e:
            last_err = f"request error: {e}"
            save_diagnostic(span_id, last_err, "api_error")
            break
    diag = save_diagnostic(span_id, last_raw or last_err or "", "invalid_final")
    record.update({"status": "invalid", "judgment": None,
                   "error": last_err, "diagnostic_file": diag})
    return record


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Stage 3: span-level judgment pass (DeepSeek API).")
    ap.add_argument("--paper", required=True, help="Path to the graded paper.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Grade only the first N spans (pilot).")
    args = ap.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        sys.exit("ERROR: DEEPSEEK_API_KEY env var is not set.")

    paper_path = Path(args.paper)
    lex_path = OUT_DIR / f"{paper_path.stem}.lexicon.json"
    if not lex_path.exists():
        sys.exit(f"ERROR: Stage 1 output not found: {lex_path}\nRun lexicon_pass.py first.")
    with open(lex_path, encoding="utf-8") as f:
        lex = json.load(f)

    with open(RUBRIC_PATH, encoding="utf-8") as f:
        rubric = json.load(f)
    tuning = load_weights()
    system_prompt = ensure_prompt_file(rubric)

    spans = build_spans(lex["sentences"], int(tuning.get("span_size", 3)))
    total_spans = len(spans)
    if args.limit is not None:
        spans = spans[:args.limit]
    print(f"[span] {total_spans} spans total; grading {len(spans)} "
          f"(model={MODEL}, concurrency={CONCURRENCY})")

    manifest = {
        "model": MODEL,
        "base_url": BASE_URL,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "prompt_version": PROMPT_VERSION,
        "prompt_file": str(PROMPT_PATH),
        "prompt_sha256": sha256_text(system_prompt),
        "rubric_file": str(RUBRIC_PATH),
        "rubric_sha256": sha256_file(RUBRIC_PATH),
        "weights_file": str(WEIGHTS_PATH),
        "weights_sha256": sha256_file(WEIGHTS_PATH),
        "lexicon_cache_file": str(LEXICON_CACHE),
        "lexicon_cache_sha256": sha256_file(LEXICON_CACHE) if LEXICON_CACHE.exists() else None,
        "lexicon_json": str(lex_path),
        "started_at": now_iso(),
        "limit": args.limit,
        "spans_total": total_spans,
        "spans_graded": len(spans),
    }

    started = now_iso()
    session = requests.Session()
    results = {}
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {
            pool.submit(grade_span, session, api_key, system_prompt, i, span): i
            for i, span in enumerate(spans)
        }
        done = 0
        for fut in as_completed(futures):
            rec = fut.result()
            results[rec["span_id"]] = rec
            done += 1
            flag = "ok" if rec["status"] == "ok" else f"INVALID ({rec.get('error')})"
            print(f"[span] {done}/{len(spans)} span {rec['span_id']} "
                  f"s{rec['sent_idx_start']}-s{rec['sent_idx_end']}: {flag}")

    manifest["finished_at"] = now_iso()
    manifest["started_at"] = started
    manifest["ok"] = sum(1 for r in results.values() if r["status"] == "ok")
    manifest["invalid"] = sum(1 for r in results.values() if r["status"] != "ok")
    tok = lambda k: sum((r.get("usage") or {}).get(k) or 0 for r in results.values())
    manifest["tokens"] = {
        "prompt": tok("prompt_tokens"),
        "completion": tok("completion_tokens"),
        "total": tok("total_tokens"),
        "cache_hit": tok("prompt_cache_hit_tokens"),
        "cache_miss": tok("prompt_cache_miss_tokens"),
    }

    out_path = OUT_DIR / f"{paper_path.stem}.spans.json"
    payload = {
        "paper": str(paper_path),
        "paper_name": paper_path.stem,
        "stage": "span_judge_v1",
        "manifest": manifest,
        "spans": [results[i] for i in sorted(results)],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"[span] ok={manifest['ok']} invalid={manifest['invalid']} -> {out_path}")


if __name__ == "__main__":
    main()
