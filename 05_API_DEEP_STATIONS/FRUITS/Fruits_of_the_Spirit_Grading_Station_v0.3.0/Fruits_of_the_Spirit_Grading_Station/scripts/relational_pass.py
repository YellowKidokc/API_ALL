"""relational_pass.py -- Stage 3b: the Relational Fruit Map.

Answers the template's question: "Who is this paper teaching the reader to
become -- and how does it teach them to treat each person, group, or
institution it discusses?"

Call structure (DeepSeek, json_object mode, temperature 0.2):
  A. setup call (1x)      paper head + evenly sampled skim -> metadata, actors
                          & targets, stakeholders, entity roster
  B. passage calls (Nx)   chunks of ~2500 words (paragraph boundaries); each
                          returns actor->target passages with EXACT quotations
                          and sentence indices
  C. synthesis call (1x)  verified passages + roster -> relationship matrix,
                          counterfeit fruit, reader impact, repair map, paper
                          summary, entity treatments

Every passage quotation is verified against the source sentences after the
call: exact / whitespace+quote-normalized / corrected (found elsewhere in the
corpus, indices fixed) / dropped (unverifiable -- never presented as data).

The Sentence Layer sheet is enriched ONLY where verified passages give
evidence (actor/target/speaker/standard/self-applied propagated to the covered
sentences); spans are not re-graded.

Outputs:
  grading_out/<paper>.relational.json   canonical data + manifest (prompt
                                        shas, template sha, tokens, cost)
  grading_out/<paper>.relational.xlsx   copy of the template workbook
                                        (scripts/templates/relational_fruit_map_
                                        template.xlsx) with the ten sheets
                                        populated as VALUES
Cache:
  grading_out/<paper>.relcache.json     per-call response cache keyed on
                                        sha256(prompt sha + payload)

Inputs:
  --paper <path>   the graded paper (needs .lexicon.json; .spans.json used
                   for ledger linkage when present)
  --limit N        passage-extraction pilot: only the first N chunks
"""

import argparse
import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import requests

sys.stdout.reconfigure(encoding="utf-8")

STATION_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
OUT_DIR = STATION_DIR / "grading_out"
WEIGHTS_PATH = SCRIPTS_DIR / "weights.json"
TEMPLATE_PATH = SCRIPTS_DIR / "templates" / "relational_fruit_map_template.xlsx"
PROMPT_SETUP = SCRIPTS_DIR / "prompts" / "relational_setup_v1.0.txt"
PROMPT_PASSAGES = SCRIPTS_DIR / "prompts" / "relational_passages_v1.0.txt"
PROMPT_SYNTH = SCRIPTS_DIR / "prompts" / "relational_synthesis_v1.0.txt"

BASE_URL = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"
TEMPERATURE = 0.2
TIMEOUT_S = 240
CONCURRENCY = 2
CHUNK_WORDS = 2500
CHUNK_WORDS_HARD = 3200
MAX_PASSAGES_PER_CHUNK = 12

RATE_HIT, RATE_MISS, RATE_OUT = 0.07, 0.27, 1.10  # USD per 1M tokens

FRUITS = ["love", "joy", "peace", "patience", "kindness",
          "goodness", "faithfulness", "gentleness", "self-control"]
RESULTS = ["FRUIT", "ANTI_FRUIT", "COUNTERFEIT", "MIXED", "UNKNOWN"]
READER_TYPES = ["Outsider", "Wounded reader", "Insider", "Opponent",
                "Scholar", "Person being criticized"]
ENTITY_KINDS = ["person", "group", "institution", "narrator", "audience"]
SUFFICIENCY = ["SUFFICIENT", "PARTIAL", "INSUFFICIENT_CONTEXT"]

QUOTE_MAX = 300


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


def load_prompt(path):
    if not path.exists():
        sys.exit(f"ERROR: missing prompt file: {path}")
    text = path.read_text(encoding="utf-8")
    return text, sha256_text(text)


# ---------------------------------------------------------------------------
# DeepSeek API with per-call disk cache
# ---------------------------------------------------------------------------

class RelationalClient:
    def __init__(self, api_key, cache_path):
        self.session = requests.Session()
        self.api_key = api_key
        self.cache_path = cache_path
        self.cache = {}
        if cache_path.exists():
            try:
                self.cache = json.loads(cache_path.read_text(encoding="utf-8"))
            except ValueError:
                self.cache = {}
        self.dirty = False

    def _save_cache(self):
        if self.dirty:
            self.cache_path.write_text(
                json.dumps(self.cache, ensure_ascii=False), encoding="utf-8")
            self.dirty = False

    def call(self, prompt_text, prompt_sha, payload_obj, max_tokens, label):
        payload = json.dumps(payload_obj, ensure_ascii=False)
        key = sha256_text(prompt_sha + "\n" + payload)
        if key in self.cache:
            entry = self.cache[key]
            return entry["response"], entry.get("usage") or {}, True
        body = {
            "model": MODEL,
            "temperature": TEMPERATURE,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": payload},
            ],
            "response_format": {"type": "json_object"},
        }
        last_err = None
        for attempt in (1, 2):
            try:
                r = self.session.post(
                    f"{BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}",
                             "Content-Type": "application/json"},
                    json=body, timeout=TIMEOUT_S)
                if r.status_code == 400:
                    body.pop("response_format", None)
                    r = self.session.post(
                        f"{BASE_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}",
                                 "Content-Type": "application/json"},
                        json=body, timeout=TIMEOUT_S)
                r.raise_for_status()
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                obj = extract_json(content)
                usage = data.get("usage") or {}
                usage = {k: usage.get(k) for k in
                         ("prompt_tokens", "completion_tokens", "total_tokens",
                          "prompt_cache_hit_tokens", "prompt_cache_miss_tokens")}
                self.cache[key] = {"response": obj, "usage": usage, "label": label,
                                   "cached_at": now_iso()}
                self.dirty = True
                self._save_cache()
                return obj, usage, False
            except (json.JSONDecodeError, ValueError) as e:
                last_err = f"{type(e).__name__}: {e}"
                body["messages"].append(
                    {"role": "user",
                     "content": "Your previous reply was not valid strict JSON of the "
                                "required shape. Reply with ONLY the JSON object."})
            except requests.RequestException as e:
                last_err = f"request error: {e}"
                break
        raise RuntimeError(f"API call failed for {label}: {last_err}")


def extract_json(content):
    content = content.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.S)
    if m:
        content = m.group(1)
    return json.loads(content)


# ---------------------------------------------------------------------------
# Chunking, payload builders
# ---------------------------------------------------------------------------

def build_chunks(sentences, target_words=CHUNK_WORDS, hard_words=CHUNK_WORDS_HARD):
    chunks, current, words = [], [], 0
    for s in sentences:
        w = s.get("word_count") or len(s["text"].split())
        if current and (words >= hard_words
                        or (words >= target_words and s["paragraph"] != current[-1]["paragraph"])):
            chunks.append(current)
            current, words = [], 0
        current.append(s)
        words += w
    if current:
        chunks.append(current)
    return chunks


def skim_sentences(sentences, cap=90):
    if len(sentences) <= cap:
        return [{"idx": s["idx"], "text": s["text"][:200]} for s in sentences]
    step = len(sentences) / cap
    picked = [sentences[int(i * step)] for i in range(cap)]
    return [{"idx": s["idx"], "text": s["text"][:200]} for s in picked]


def setup_payload(stem, lex, stats_doc):
    sents = lex["sentences"]
    head = "\n".join(s["text"] for s in sents)[:3000]
    sbk = {s["key"]: s for s in stats_doc["stats"]} if stats_doc else {}
    return {
        "file_stem": stem,
        "head_of_paper": head,
        "skim_sampled_sentences": skim_sentences(sents),
        "document_stats": {
            "sentences": len(sents),
            "words": sbk.get("volume.words", {}).get("value"),
            "paragraphs": lex.get("paragraph_count"),
        },
    }


def chunk_payload(chunk_sents, roster_names, paper_title):
    return {
        "paper": paper_title,
        "entity_roster": roster_names,
        "chunk_sentences": [{"idx": s["idx"], "text": s["text"]} for s in chunk_sents],
        "max_passages": MAX_PASSAGES_PER_CHUNK,
    }


def synthesis_payload(setup, entities, passages):
    compact = [{
        "id": p["id"], "actor": p["actor"], "target": p["target"],
        "fruit": p["fruit"], "result": p["result"], "mechanism": p["mechanism"],
        "importance": p["importance"], "confidence": p["confidence"],
        "quotation": p["quotation"],
    } for p in passages]
    return {
        "paper": setup.get("paper_title", ""),
        "medium": setup.get("medium", ""),
        "intended_audience": setup.get("intended_audience", ""),
        "entity_roster": [{"name": e["name"], "kind": e["kind"],
                           "roles_seen": e.get("roles_seen", [])} for e in entities],
        "verified_passages": compact,
    }


# ---------------------------------------------------------------------------
# Validation and quote verification
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")
_QUOTE_MAP = str.maketrans({
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "…": "...", "—": "--", "–": "-",
})


def norm_text(s):
    return _WS.sub(" ", str(s).translate(_QUOTE_MAP)).strip().lower()


def verify_quote(quote, s_start, s_end, sent_by_idx):
    """Return (status, s_start, s_end). status: exact|normalized|corrected|failed."""
    quote = str(quote).strip()
    if not quote:
        return "failed", s_start, s_end
    try:
        s_start, s_end = int(s_start), int(s_end)
    except (TypeError, ValueError):
        return "failed", s_start, s_end
    if s_end < s_start:
        s_start, s_end = s_end, s_start
    rng = [sent_by_idx[i]["text"] for i in range(s_start, s_end + 1) if i in sent_by_idx]
    joined = " ".join(rng)
    if quote in joined:
        return "exact", s_start, s_end
    nq = norm_text(quote)
    if nq and nq in norm_text(joined):
        return "normalized", s_start, s_end
    # search the whole corpus for the (normalized) quote and correct indices
    hits = [i for i, s in sent_by_idx.items() if nq and nq in norm_text(s["text"])]
    if not hits:
        # quote may span adjacent sentences: sliding 3-sentence window
        idxs = sorted(sent_by_idx)
        for k, i in enumerate(idxs):
            for j in idxs[k:k + 3]:
                if nq in norm_text(" ".join(sent_by_idx[x]["text"]
                                            for x in idxs[k:idxs.index(j) + 1])):
                    hits = list(range(i, j + 1))
                    break
            if hits:
                break
    if hits:
        return "corrected", min(hits), max(hits)
    return "failed", s_start, s_end


def norm_fruit(v):
    v = str(v or "").strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {"selfcontrol": "self-control", "self-control": "self-control"}
    v = aliases.get(v, v)
    return v if v in FRUITS else None


def norm_result(v):
    v = str(v or "").strip().upper().replace("-", "_").replace(" ", "_")
    return v if v in RESULTS else "UNKNOWN"


def clamp(v, lo, hi, default):
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        return default


def validate_passage(raw, roster_lc):
    """Coerce one model passage into canonical form, or raise ValueError."""
    p = {}
    p["sent_idx_start"] = int(raw["sent_idx_start"])
    p["sent_idx_end"] = int(raw["sent_idx_end"])
    p["quotation"] = str(raw.get("quotation", "")).strip()[:QUOTE_MAX]
    if not p["quotation"]:
        raise ValueError("empty quotation")
    p["actor"] = str(raw.get("actor", "")).strip()
    p["target"] = str(raw.get("target", "")).strip()
    if not p["actor"] or not p["target"]:
        raise ValueError("actor/target missing")
    p["speaker"] = str(raw.get("speaker", "narrator")).strip() or "narrator"
    fruit = norm_fruit(raw.get("fruit"))
    if not fruit:
        raise ValueError(f"invalid fruit: {raw.get('fruit')}")
    p["fruit"] = fruit
    p["result"] = norm_result(raw.get("result"))
    for k in ("mechanism", "power_relationship", "who_benefits",
              "who_bears_cost", "standard_expressed", "explanation", "possible_repair"):
        p[k] = str(raw.get(k, "")).strip()
    sa = str(raw.get("self_applied", "N/A")).strip().upper()
    p["self_applied"] = sa if sa in ("YES", "NO", "N/A") else "N/A"
    p["importance"] = int(clamp(raw.get("importance"), 1, 5, 3))
    p["confidence"] = round(clamp(raw.get("confidence"), 0.0, 1.0, 0.5), 2)
    # canonicalize actor/target against the roster when possible
    for k in ("actor", "target"):
        p[k] = roster_lc.get(p[k].lower(), p[k])
    return p


# ---------------------------------------------------------------------------
# Aggregation: matrix, fruit profile, sentence-layer enrichment, entities
# ---------------------------------------------------------------------------

def aggregate_matrix(passages, synthesis_cells):
    """Deterministic (actor,target)->treatment from passages, merged with
    validated synthesis proposals."""
    by_pair = {}
    for p in passages:
        by_pair.setdefault((p["actor"], p["target"]), []).append(p)

    def aggregate(plist):
        rs = {p["result"] for p in plist if p["result"] != "UNKNOWN"}
        if not rs:
            return None
        if len(rs) == 1:
            return next(iter(rs))
        return "MIXED"

    cells = {}
    for (a, t), plist in by_pair.items():
        tr = aggregate(plist)
        if tr:
            cells[(a, t)] = {"actor": a, "target": t, "treatment": tr,
                             "passage_refs": [p["id"] for p in plist],
                             "note": "", "source": "passages"}
    valid_ids = {p["id"] for p in passages}
    for c in synthesis_cells or []:
        try:
            a, t = str(c["actor"]).strip(), str(c["target"]).strip()
            tr = norm_result(c.get("treatment"))
            refs = [r for r in c.get("passage_refs", []) if r in valid_ids]
        except (KeyError, TypeError):
            continue
        if not a or not t or tr == "UNKNOWN" or not refs:
            continue
        if (a, t) in cells:
            cells[(a, t)]["note"] = str(c.get("note", "")).strip()
            cells[(a, t)]["source"] = "passages+synthesis"
        else:
            cells[(a, t)] = {"actor": a, "target": t, "treatment": tr,
                             "passage_refs": refs,
                             "note": str(c.get("note", "")).strip(),
                             "source": "synthesis"}
    return [cells[k] for k in sorted(cells, key=lambda k: (k[0].lower(), k[1].lower()))]


def enrich_sentence_layer(sentences, passages, audience):
    """Propagate passage fields to covered sentences; highest-importance
    passage wins per sentence. Returns {idx: enrichment}."""
    enriched = {}
    for p in sorted(passages, key=lambda p: (p["importance"], p["confidence"])):
        for i in range(p["sent_idx_start"], p["sent_idx_end"] + 1):
            enriched[i] = {
                "speaker": p["speaker"], "actor": p["actor"], "target": p["target"],
                "audience": audience, "standard_expressed": p["standard_expressed"],
                "applied_to_whom": p["target"], "self_applied": p["self_applied"],
                "fruit": p["fruit"], "result": p["result"],
                "rationale": p["explanation"], "confidence": p["confidence"],
                "passage_id": p["id"],
            }
    return enriched


def fruit_profile(passages, enriched):
    rows = []
    for f in FRUITS:
        covered = [i for i, e in enriched.items() if e["fruit"] == f]
        plist = [p for p in passages if p["fruit"] == f]
        genuine = sum(1 for i in covered if enriched[i]["result"] == "FRUIT")
        anti_cf = sum(1 for i in covered if enriched[i]["result"] in ("ANTI_FRUIT", "COUNTERFEIT"))
        mixed = sum(1 for i in covered if enriched[i]["result"] == "MIXED")
        strength = round(sum(p["importance"] for p in plist) / len(plist), 1) if plist else "—"
        unc = round(sum(enriched[i]["confidence"] for i in covered) / len(covered), 2) if covered else "—"
        tgt = {}
        for i in covered:
            t = enriched[i]["target"]
            tgt[t] = tgt.get(t, 0) + 1
        dom = ", ".join(t for t, _ in sorted(tgt.items(), key=lambda kv: -kv[1])[:2]) or "—"
        rows.append({"fruit": f, "coverage": len(covered), "genuine": genuine,
                     "anti_counterfeit": anti_cf, "strength": strength,
                     "conflict": mixed, "uncertainty": unc, "dominant_targets": dom})
    return rows


def build_entities(setup_entities, sentences, passages, synth_treatments):
    treat = {str(t.get("entity", "")).lower(): t for t in synth_treatments or []}
    out = []
    for e in setup_entities:
        name = str(e.get("name", "")).strip()
        if not name:
            continue
        aliases = [a.strip() for a in re.split(r"[,;/]", str(e.get("aliases", ""))) if a.strip()]
        kind = str(e.get("kind", "")).strip().lower()
        if kind not in ENTITY_KINDS:
            kind = "group"
        mentions = 0
        if kind not in ("narrator", "audience"):
            pats = [re.compile(r"\b" + re.escape(a.lower()) + r"\b") for a in [name] + aliases if len(a) > 2]
            for s in sentences:
                low = s["text"].lower()
                if any(p.search(low) for p in pats):
                    mentions += 1
        else:
            mentions = len(sentences) if kind == "narrator" else 0
        sub = sum(1 for p in passages
                  if p["actor"].lower() == name.lower() or p["target"].lower() == name.lower())
        t = treat.get(name.lower(), {})
        suff = str(t.get("evidence_sufficiency", "")).upper()
        if suff not in SUFFICIENCY:
            suff = "SUFFICIENT" if mentions >= 5 else "PARTIAL" if mentions >= 2 else "INSUFFICIENT_CONTEXT"
        out.append({
            "id": str(e.get("id", f"E{len(out)+1}")), "name": name, "kind": kind,
            "aliases": str(e.get("aliases", "")),
            "roles_seen": e.get("roles_seen", []),
            "mentions": mentions, "substantive_passages": sub,
            "how_treated": str(t.get("how_treated", "")),
            "evidence_sufficiency": suff,
            "confidence": round(clamp(t.get("confidence"), 0.0, 1.0, 0.5), 2),
        })
    return out


def link_spans(p, spans):
    if not spans:
        return []
    return [sp["span_id"] for sp in spans
            if sp["sent_idx_start"] <= p["sent_idx_end"]
            and sp["sent_idx_end"] >= p["sent_idx_start"]]


# ---------------------------------------------------------------------------
# XLSX writer -- populate a copy of the template with VALUES
# ---------------------------------------------------------------------------

def clear_range(ws, min_row, max_row, min_col, max_col):
    for row in ws.iter_rows(min_row=min_row, max_row=max_row,
                            min_col=min_col, max_col=max_col):
        for c in row:
            c.value = None


def write_xlsx(template_path, out_path, data):
    wb = openpyxl.load_workbook(template_path)
    setup = data["setup"]
    passages = data["passages"]
    entities = data["entities"]
    enriched = {int(k): v for k, v in data["sentence_layer"]["enriched"].items()}
    sentences = data["_sentences"]  # popped before JSON serialization

    # ---- Evaluation Setup ----
    ws = wb["Evaluation Setup"]
    ws["B5"] = setup.get("paper_title", "")
    ws["B6"] = setup.get("series", "")
    ws["B7"] = setup.get("author_speaker", "")
    ws["B8"] = setup.get("intended_audience", "")
    ws["B9"] = data["manifest"]["finished_at"][:10]
    clear_range(ws, 13, 60, 2, 5)
    for k, a in enumerate(data["actors_targets"]):
        r = 13 + k
        ws.cell(row=r, column=1, value=a.get("id", f"A{k+1}"))
        ws.cell(row=r, column=2, value=a.get("name", ""))
        ws.cell(row=r, column=3, value=a.get("kind", ""))
        ws.cell(row=r, column=4, value=a.get("role", ""))
        ws.cell(row=r, column=5, value=a.get("notes", ""))
    clear_range(ws, 28, 60, 2, 5)
    for k, s in enumerate(data["stakeholders"]):
        r = 28 + k
        ws.cell(row=r, column=1, value=s.get("id", f"S{k+1}"))
        ws.cell(row=r, column=2, value=s.get("stakeholder", ""))
        ws.cell(row=r, column=3, value=s.get("how_affected", ""))
        ws.cell(row=r, column=4, value=s.get("benefit_cost", ""))
        ws.cell(row=r, column=5, value=s.get("notes", ""))

    # ---- Entity Register ----
    ws = wb["Entity Register"]
    clear_range(ws, 5, 120, 1, 10)
    for k, e in enumerate(entities):
        r = 5 + k
        ws.cell(row=r, column=1, value=e["id"])
        ws.cell(row=r, column=2, value=e["name"])
        ws.cell(row=r, column=3, value=e["kind"])
        ws.cell(row=r, column=4, value=e["aliases"])
        ws.cell(row=r, column=5, value=", ".join(e["roles_seen"]))
        ws.cell(row=r, column=6, value=e["mentions"])
        ws.cell(row=r, column=7, value=e["substantive_passages"])
        ws.cell(row=r, column=8, value=e["how_treated"])
        ws.cell(row=r, column=9, value=e["evidence_sufficiency"])
        ws.cell(row=r, column=10, value=e["confidence"])

    # ---- Passage Ratings ----
    ws = wb["Passage Ratings"]
    clear_range(ws, 5, 120, 1, 16)
    ws.cell(row=4, column=15, value="Source sentences (idx)")
    ws.cell(row=4, column=16, value="Ledger spans")
    for k, p in enumerate(passages):
        r = 5 + k
        ws.cell(row=r, column=1, value=p["id"])
        ws.cell(row=r, column=2, value=p["quotation"])
        ws.cell(row=r, column=3, value=p["actor"])
        ws.cell(row=r, column=4, value=p["target"])
        ws.cell(row=r, column=5, value=p["fruit"])
        ws.cell(row=r, column=6, value=p["result"])
        ws.cell(row=r, column=7, value=p["mechanism"])
        ws.cell(row=r, column=8, value=p["power_relationship"])
        ws.cell(row=r, column=9, value=p["who_benefits"])
        ws.cell(row=r, column=10, value=p["who_bears_cost"])
        ws.cell(row=r, column=11, value=p["importance"])
        ws.cell(row=r, column=12, value=p["confidence"])
        ws.cell(row=r, column=13, value=p["explanation"])
        ws.cell(row=r, column=14, value=p["possible_repair"])
        ws.cell(row=r, column=15, value=f's{p["sent_idx_start"]}–s{p["sent_idx_end"]}')
        ws.cell(row=r, column=16, value=", ".join(str(i) for i in p["span_ids"]))

    # ---- Sentence Layer ----
    ws = wb["Sentence Layer"]
    clear_range(ws, 5, max(260, 5 + len(sentences)), 1, 19)
    texts = [s["text"] for s in sentences]
    for k, s in enumerate(sentences):
        r = 5 + k
        i = s["idx"]
        ws.cell(row=r, column=1, value=k + 1)
        ws.cell(row=r, column=3, value=s["paragraph"])
        ws.cell(row=r, column=5, value=texts[k - 1] if k > 0 else "")
        ws.cell(row=r, column=6, value=s["text"])
        ws.cell(row=r, column=7, value=texts[k + 1] if k < len(texts) - 1 else "")
        e = enriched.get(i)
        if e:
            ws.cell(row=r, column=8, value=e["speaker"])
            ws.cell(row=r, column=9, value=e["actor"])
            ws.cell(row=r, column=10, value=e["target"])
            ws.cell(row=r, column=12, value=e["audience"])
            ws.cell(row=r, column=13, value=e["standard_expressed"])
            ws.cell(row=r, column=14, value=e["applied_to_whom"])
            ws.cell(row=r, column=15, value=e["self_applied"])
            ws.cell(row=r, column=16, value=e["fruit"])
            ws.cell(row=r, column=17, value=e["result"])
            ws.cell(row=r, column=18, value=e["rationale"])
            ws.cell(row=r, column=19, value=e["confidence"])

    # ---- Relationship Matrix ----
    ws = wb["Relationship Matrix"]
    clear_range(ws, 4, 14, 2, 13)   # target header formulas
    clear_range(ws, 5, 14, 1, 1)    # actor name formulas
    names = [a.get("name", "") for a in data["actors_targets"]][:12]
    cellmap = {(c["actor"], c["target"]): c["treatment"]
               for c in data["relationship_matrix"]}
    for k, name in enumerate(names):
        ws.cell(row=4, column=2 + k, value=name)
        ws.cell(row=5 + k, column=1, value=name)
    for ri, a in enumerate(names):
        for ci, t in enumerate(names):
            if ri == ci:
                continue
            ws.cell(row=5 + ri, column=2 + ci,
                    value=cellmap.get((a, t), "—"))

    # ---- Fruit Profile ----
    ws = wb["Fruit Profile"]
    prof = {r["fruit"]: r for r in data["fruit_profile"]}
    for r in range(5, 14):
        fname = ws.cell(row=r, column=1).value
        if fname not in prof:
            continue
        p = prof[fname]
        ws.cell(row=r, column=2, value=p["coverage"])
        ws.cell(row=r, column=3, value=p["genuine"])
        ws.cell(row=r, column=4, value=p["anti_counterfeit"])
        ws.cell(row=r, column=5, value=p["strength"])
        ws.cell(row=r, column=6, value=p["conflict"])
        ws.cell(row=r, column=7, value=p["uncertainty"])
        ws.cell(row=r, column=8, value=p["dominant_targets"])

    # ---- Counterfeit Fruit ----
    ws = wb["Counterfeit Fruit"]
    clear_range(ws, 5, 30, 1, 6)
    cf = data["counterfeit"]
    if not cf:
        ws.cell(row=5, column=1, value="none found")
    for k, c in enumerate(cf):
        r = 5 + k
        ws.cell(row=r, column=1, value=", ".join(c.get("passage_refs", [])))
        ws.cell(row=r, column=2, value=c.get("fruit_claimed", ""))
        ws.cell(row=r, column=3, value=c.get("companion_missing", ""))
        ws.cell(row=r, column=4, value=c.get("result_produced", ""))
        ws.cell(row=r, column=5, value=c.get("target_harmed", ""))
        ws.cell(row=r, column=6, value=c.get("notes", ""))

    # ---- Reader Impact ----
    ws = wb["Reader Impact"]
    ri = data["reader_impact"]
    for r in range(5, 11):
        rtype = ws.cell(row=r, column=1).value
        d = ri.get(rtype)
        if not d:
            continue
        ws.cell(row=r, column=2, value=d.get("likely_experience", ""))
        ws.cell(row=r, column=3, value=d.get("fruit_received", ""))
        ws.cell(row=r, column=4, value=d.get("harm_risked", ""))
        ws.cell(row=r, column=5, value=", ".join(d.get("key_passages", [])))

    # ---- Repair Map ----
    ws = wb["Repair Map"]
    clear_range(ws, 5, 30, 1, 5)
    rm = data["repair_map"]
    if not rm:
        ws.cell(row=5, column=1, value="none found")
    for k, m in enumerate(rm):
        r = 5 + k
        ws.cell(row=r, column=1, value=", ".join(m.get("passage_refs", [])))
        ws.cell(row=r, column=2, value=m.get("passage", ""))
        ws.cell(row=r, column=3, value=m.get("fruit_missing", ""))
        ws.cell(row=r, column=4, value=m.get("how_to_repair", ""))
        ws.cell(row=r, column=5, value=m.get("priority", ""))

    # ---- Paper Summary (merged anchor cells) ----
    ws = wb["Paper Summary"]
    ps = data["paper_summary"]
    ws["A5"] = ps.get("thesis", "")
    ws["A8"] = ps.get("greatest_strength", "")
    ws["A10"] = ps.get("greatest_danger", "")
    ws["A12"] = ps.get("most_important_asymmetry", "")
    ws["A14"] = ps.get("most_revealing_passage", "")
    ws["A16"] = ps.get("recommended_revision", "")
    m = data["manifest"]
    ws["A18"] = (f"Generated {m['finished_at']} by relational_pass.py · model {m['model']} "
                 f"temp {m['temperature']} · prompts setup {m['prompts']['setup']['sha256'][:12]} / "
                 f"passages {m['prompts']['passages']['sha256'][:12]} / "
                 f"synthesis {m['prompts']['synthesis']['sha256'][:12]} · "
                 f"template sha {m['template_sha256'][:12]} · "
                 f"quotes: {m['quotes_exact']} exact, {m['quotes_normalized']} normalized, "
                 f"{m['quotes_corrected']} corrected, {m['quotes_dropped']} dropped")

    # ---- Data Sources ----
    ws = wb["Data Sources"]
    r = ws.max_row + 1
    ws.cell(row=r, column=1, value="all ten sheets")
    ws.cell(row=r, column=2, value=data["paper"])
    ws.cell(row=r, column=3, value=data["paper_name"])
    ws.cell(row=r, column=4, value=f"DeepSeek API ({m['model']})")
    ws.cell(row=r, column=5, value="setup + per-chunk passage extraction + synthesis")
    ws.cell(row=r, column=6, value=f"temp {m['temperature']}, {m['chunks']} chunks, json mode")
    ws.cell(row=r, column=7, value=m["finished_at"])
    ws.cell(row=r, column=8, value="David")
    ws.cell(row=r, column=9, value=len(passages))
    ws.cell(row=r, column=10, value=(
        f"quote verification: {m['quotes_exact']} exact / {m['quotes_normalized']} normalized / "
        f"{m['quotes_corrected']} corrected / {m['quotes_dropped']} dropped"))
    ws.cell(row=r, column=11, value="Relational Fruit Map stage (relational_pass.py)")

    wb.save(out_path)


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Stage 3b: Relational Fruit Map (DeepSeek API).")
    ap.add_argument("--paper", required=True, help="Path to the graded paper.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Passage-extraction pilot: only the first N chunks.")
    args = ap.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        sys.exit("ERROR: DEEPSEEK_API_KEY env var is not set.")
    if not TEMPLATE_PATH.exists():
        sys.exit(f"ERROR: template not found: {TEMPLATE_PATH}")

    paper_path = Path(args.paper)
    stem = paper_path.stem
    lex_path = OUT_DIR / f"{stem}.lexicon.json"
    spans_path = OUT_DIR / f"{stem}.spans.json"
    stats_path = OUT_DIR / f"{stem}.stats.json"
    if not lex_path.exists():
        sys.exit(f"ERROR: Stage 1 output not found: {lex_path}\nRun lexicon_pass.py first.")
    lex = json.loads(lex_path.read_text(encoding="utf-8"))
    spans_doc = json.loads(spans_path.read_text(encoding="utf-8")) if spans_path.exists() else None
    stats_doc = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else None
    sentences = lex["sentences"]
    sent_by_idx = {s["idx"]: s for s in sentences}

    prompts = {}
    for key, path in (("setup", PROMPT_SETUP), ("passages", PROMPT_PASSAGES),
                      ("synthesis", PROMPT_SYNTH)):
        text, sha = load_prompt(path)
        prompts[key] = {"file": str(path), "text": text, "sha256": sha}

    client = RelationalClient(api_key, OUT_DIR / f"{stem}.relcache.json")
    usages = []

    # ---- Call A: setup -----------------------------------------------------
    print("[rel] call A: setup + entity roster")
    setup, u, cached = client.call(prompts["setup"]["text"], prompts["setup"]["sha256"],
                                   setup_payload(stem, lex, stats_doc), 2000, "setup")
    usages.append(u)
    print(f"[rel]   title={setup.get('paper_title', '?')!r} "
          f"actors={len(setup.get('actors_targets', []))} "
          f"entities={len(setup.get('entities', []))} {'(cached)' if cached else ''}")

    roster_names = [e.get("name", "") for e in setup.get("entities", []) if e.get("name")]
    roster_lc = {n.lower(): n for n in roster_names}
    for a in setup.get("actors_targets", []):
        n = a.get("name", "")
        if n and n.lower() not in roster_lc:
            roster_lc[n.lower()] = n
            roster_names.append(n)

    # ---- Call B: passages per chunk ----------------------------------------
    chunks = build_chunks(sentences)
    if args.limit is not None:
        chunks = chunks[:args.limit]
    print(f"[rel] call B: {len(chunks)} chunks (~{CHUNK_WORDS} words each)")
    title = setup.get("paper_title", stem)

    def do_chunk(ci, chunk):
        payload = chunk_payload(chunk, roster_names, title)
        obj, usage, cached = client.call(prompts["passages"]["text"],
                                         prompts["passages"]["sha256"],
                                         payload, 3000, f"chunk_{ci}")
        return ci, obj, usage, cached

    chunk_results = {}
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {pool.submit(do_chunk, ci, ch): ci for ci, ch in enumerate(chunks)}
        for fut in as_completed(futures):
            ci, obj, usage, cached = fut.result()
            chunk_results[ci] = obj
            usages.append(usage)
            print(f"[rel]   chunk {ci+1}/{len(chunks)}: "
                  f"{len(obj.get('passages', []))} passages {'(cached)' if cached else ''}")

    # ---- merge, validate, verify quotes ------------------------------------
    passages, dropped = [], []
    q_exact = q_norm = q_corr = 0
    for ci in sorted(chunk_results):
        for raw in chunk_results[ci].get("passages", []):
            try:
                p = validate_passage(raw, roster_lc)
            except (ValueError, KeyError, TypeError) as e:
                dropped.append({"raw": raw, "reason": f"validation: {e}", "chunk": ci})
                continue
            status, p["sent_idx_start"], p["sent_idx_end"] = verify_quote(
                p["quotation"], p["sent_idx_start"], p["sent_idx_end"], sent_by_idx)
            if status == "failed":
                dropped.append({"raw": raw, "reason": "quote_not_found", "chunk": ci})
                continue
            p["quote_check"] = status
            q_exact += status == "exact"
            q_norm += status == "normalized"
            q_corr += status == "corrected"
            passages.append(p)
    passages.sort(key=lambda p: (p["sent_idx_start"], -p["importance"]))
    for k, p in enumerate(passages):
        p["id"] = f"P{k+1:02d}"
    spans = spans_doc["spans"] if spans_doc else []
    for p in passages:
        p["span_ids"] = link_spans(p, spans)
    print(f"[rel] passages: {len(passages)} verified "
          f"(exact={q_exact} normalized={q_norm} corrected={q_corr}), "
          f"{len(dropped)} dropped")

    # ---- Call C: synthesis ---------------------------------------------------
    print("[rel] call C: synthesis")
    synth, u, cached = client.call(
        prompts["synthesis"]["text"], prompts["synthesis"]["sha256"],
        synthesis_payload(setup, setup.get("entities", []), passages),
        4000, "synthesis")
    usages.append(u)
    print(f"[rel]   matrix cells={len(synth.get('relationship_matrix', []))} "
          f"counterfeit={len(synth.get('counterfeit', []))} "
          f"repairs={len(synth.get('repair_map', []))} {'(cached)' if cached else ''}")

    # ---- aggregation ---------------------------------------------------------
    matrix = aggregate_matrix(passages, synth.get("relationship_matrix"))
    audience = setup.get("intended_audience", "")
    enriched = enrich_sentence_layer(sentences, passages, audience)
    prof = fruit_profile(passages, enriched)
    entities = build_entities(setup.get("entities", []), sentences, passages,
                              synth.get("entity_treatment"))

    # reader impact / repair map normalization
    reader_impact = {}
    for rt in READER_TYPES:
        d = (synth.get("reader_impact") or {}).get(rt) or {}
        reader_impact[rt] = {
            "likely_experience": str(d.get("likely_experience", "none found")),
            "fruit_received": str(d.get("fruit_received", "none")),
            "harm_risked": str(d.get("harm_risked", "none")),
            "key_passages": [str(x) for x in d.get("key_passages", [])],
        }
    repair_map = [{
        "passage_refs": [str(x) for x in m.get("passage_refs", [])],
        "passage": str(m.get("passage", "")),
        "fruit_missing": norm_fruit(m.get("fruit_missing")) or str(m.get("fruit_missing", "")),
        "how_to_repair": str(m.get("how_to_repair", "")),
        "priority": str(m.get("priority", "")).upper()
        if str(m.get("priority", "")).upper() in ("HIGH", "MEDIUM", "LOW") else "MEDIUM",
    } for m in synth.get("repair_map", [])]
    counterfeit = [{
        "passage_refs": [str(x) for x in c.get("passage_refs", [])],
        "fruit_claimed": str(c.get("fruit_claimed", "")),
        "companion_missing": str(c.get("companion_missing", "")),
        "result_produced": str(c.get("result_produced", "")),
        "target_harmed": str(c.get("target_harmed", "")),
        "notes": str(c.get("notes", "")),
    } for c in synth.get("counterfeit", [])]
    paper_summary = {k: str((synth.get("paper_summary") or {}).get(k, ""))
                     for k in ("thesis", "greatest_strength", "greatest_danger",
                               "most_important_asymmetry", "most_revealing_passage",
                               "recommended_revision")}

    # ---- manifest ------------------------------------------------------------
    tok = lambda k: sum((u or {}).get(k) or 0 for u in usages)
    tokens = {"prompt": tok("prompt_tokens"), "completion": tok("completion_tokens"),
              "total": tok("total_tokens"), "cache_hit": tok("prompt_cache_hit_tokens"),
              "cache_miss": tok("prompt_cache_miss_tokens")}
    cost = (tokens["cache_hit"] * RATE_HIT + tokens["cache_miss"] * RATE_MISS
            + tokens["completion"] * RATE_OUT) / 1e6
    manifest = {
        "model": MODEL, "base_url": BASE_URL, "temperature": TEMPERATURE,
        "prompts": {k: {"file": v["file"], "sha256": v["sha256"]} for k, v in prompts.items()},
        "weights_file": str(WEIGHTS_PATH),
        "weights_sha256": sha256_file(WEIGHTS_PATH) if WEIGHTS_PATH.exists() else None,
        "template_file": str(TEMPLATE_PATH),
        "template_sha256": sha256_file(TEMPLATE_PATH),
        "lexicon_json": str(lex_path), "lexicon_sha256": sha256_file(lex_path),
        "spans_json": str(spans_path) if spans_path.exists() else None,
        "spans_sha256": sha256_file(spans_path) if spans_path.exists() else None,
        "started_at": None, "finished_at": now_iso(),
        "chunks": len(chunks), "api_calls": 2 + len(chunks),
        "tokens": tokens, "cost_usd_est": round(cost, 4),
        "passages_found": len(passages) + len(dropped),
        "passages_verified": len(passages), "passages_dropped": len(dropped),
        "quotes_exact": q_exact, "quotes_normalized": q_norm,
        "quotes_corrected": q_corr, "quotes_dropped": len(dropped),
        "sentence_layer_enriched": len(enriched),
    }

    data = {
        "paper": str(paper_path), "paper_name": stem, "stage": "relational_pass_v1",
        "manifest": manifest,
        "setup": setup,
        "actors_targets": setup.get("actors_targets", []),
        "stakeholders": setup.get("stakeholders", []),
        "entities": entities,
        "passages": passages,
        "dropped_passages": dropped,
        "sentence_layer": {"enriched_count": len(enriched),
                           "enriched": {str(k): v for k, v in sorted(enriched.items())}},
        "relationship_matrix": matrix,
        "fruit_profile": prof,
        "counterfeit": counterfeit,
        "reader_impact": reader_impact,
        "repair_map": repair_map,
        "paper_summary": paper_summary,
    }

    json_path = OUT_DIR / f"{stem}.relational.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[rel] wrote {json_path} ({json_path.stat().st_size // 1024} KB)")

    xlsx_path = OUT_DIR / f"{stem}.relational.xlsx"
    data["_sentences"] = sentences
    write_xlsx(TEMPLATE_PATH, xlsx_path, data)
    del data["_sentences"]
    print(f"[rel] wrote {xlsx_path} ({xlsx_path.stat().st_size // 1024} KB)")
    print(f"[rel] tokens: {tokens['total']:,} "
          f"(cache_hit {tokens['cache_hit']:,}) · est cost ${cost:.4f}")
    print(f"[rel] thesis: {paper_summary['thesis']}")


if __name__ == "__main__":
    main()
