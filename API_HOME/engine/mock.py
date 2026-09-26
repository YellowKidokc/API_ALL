"""Deterministic fake replies for --provider mock.

Used only to test plumbing (menu -> gateway -> station -> outputs) without API
keys or cost. Every reply is marked MOCK so it can never be mistaken for a real
analysis. Stations put a machine-readable line in their prompts (IDS: ..., ITEM: ...)
that the handlers below read.
"""
from __future__ import annotations

import hashlib
import json
import re

FRUITS = ["love", "joy", "peace", "patience", "kindness", "goodness", "faithfulness", "gentleness", "self_control"]


def _prompt(messages: list[dict]) -> str:
    return "\n".join(str(m.get("content", "")) for m in messages)


def _ids(prompt: str) -> list[str]:
    match = re.search(r"^IDS: (.+)$", prompt, re.M)
    return [x.strip() for x in match.group(1).split(",")] if match else []


def _num(seed: str, lo: int, hi: int) -> int:
    return lo + int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % (hi - lo + 1)


def _line(prompt: str, key: str, default: str = "") -> str:
    match = re.search(rf"^{key}: (.+)$", prompt, re.M)
    return match.group(1).strip() if match else default


def respond(task: str, messages: list[dict]) -> str:
    prompt = _prompt(messages)
    handler = HANDLERS.get(task) or (openai_bundle if task.startswith("oa_") else None)
    data = handler(prompt) if handler else {"mock": True, "text": f"MOCK reply for task '{task or 'unnamed'}'."}
    if isinstance(data, str):
        return data
    data.setdefault("mock", True)
    return json.dumps(data)


def fruits_sentences(p: str) -> dict:
    return {"sentences": [{"id": i, "v": [_num(i + f, -2, 2) for f in FRUITS], "why": {"love": "MOCK reason"}} for i in _ids(p)]}


def fruits_verdict(p: str) -> dict:
    return {"verdict": "MOCK verdict", "gates": {"truth_evidence": "pass", "contradiction": "pass", "agency_noncoercion": "pass"},
            "dimensions": {f: {"score": _num(f, 0, 4), "evidence": ["S001"]} for f in FRUITS},
            "stress_tests": [], "veto": False, "repairs": ["MOCK repair"]}


def master_equation(p: str) -> dict:
    slots = ["G", "M", "E", "S_eff", "T", "K", "R", "Q", "F", "C"]
    seed = _line(p, "RUN", "1")
    return {"core_relation": {"sentence": "MOCK core relation", "quote": "S001"},
            "product_test": {"answer": ["multiplicative", "additive"][_num(seed, 0, 1)], "quote": "S001", "reason": "MOCK"},
            "slots": [{"slot": s, "plays_role": "MOCK", "quote": "S001", "fit": ["direct", "analogous", "stretched", "absent"][_num(s + seed, 0, 3)]} for s in slots],
            "breaks": [], "extra_factors": [], "analog_strength": _num(seed, 2, 4), "confidence": "low", "one_line": "MOCK analog"}


def axiom_nodes(p: str) -> dict:
    return {"engaged": [{"node": "A1.1", "alignment": "aligned", "quote": "S001", "sentence_ids": ["S001"], "confidence": 0.5}],
            "unmapped_claims": [], "primary_mode": "MOCK"}


def coherence(p: str) -> dict:
    return {"score": 6.5, "dimensions": {"internal_consistency": {"score": 7, "reason": "MOCK", "sentence_ids": ["S001"]}},
            "contradictions": [], "tensions": [], "missing_definitions": []}


def story_paper(p: str) -> dict:
    paras = _ids(p)
    return {"hook": {"quote": "MOCK", "score": 3, "better_hook": None, "rewrite": ""}, "through_line": "MOCK through-line",
            "paragraphs": [{"id": x, "role": "setup", "serves": "yes", "reason": "", "out_of_order": False} for x in paras],
            "proposed_order": [], "drift": [], "contradictions": [], "landing": {"verdict": "yes", "reason": "MOCK"},
            "verdict": "COHERENT", "fixes": []}


def story_series(p: str) -> dict:
    return {"through_line": "MOCK series", "papers": [], "handoffs": [], "repeats": [], "missing_beats": [],
            "contradictions": [], "proposed_order": [], "verdict": "COHERENT", "fixes": []}


def story_lines(p: str) -> dict:
    return {"lines": [{"id": x, "line": f"MOCK line for {x}", "words": 4} for x in _ids(p)],
            "signature": ["MOCK signature"], "series_line": "MOCK"}


def tagger(p: str) -> dict:
    tags = [t.strip() for t in _line(p, "TAGS").split("|") if t.strip()]
    return {"tags": [{"tag": t, "score": _num(t + p[:200], 0, 10), "reason": "MOCK reason", "quote_or_ts": "MOCK quote"} for t in tags]}


def extract_arguments(p: str) -> dict:
    item = _line(p, "ITEM", "item")
    topic = _line(p, "TOPIC", "topic")
    base = ["the empty tomb is attested early", "the disciples sincerely believed they saw Jesus alive",
            "the conversion of Paul requires explanation", "hallucination theory fails for group appearances"]
    return {"arguments": [{"claim": base[(i + _num(item, 0, 3)) % 4] + f" ({topic})", "steps": ["MOCK premise", "MOCK inference"],
                           "kind": "historical", "attributed_to": ["MOCK scholar"], "quote_or_ts": "MOCK quote",
                           "strength": _num(item + str(i), 3, 9), "strength_reason": "MOCK", "objections": ["MOCK objection"],
                           "replies": ["MOCK reply"]} for i in range(2)]}


def synthesize_cluster(p: str) -> dict:
    return {"title": "MOCK argument", "strongest_form": "MOCK strongest formulation", "steps": ["MOCK"],
            "lineage": [{"who": "MOCK scholar", "where": "MOCK", "relation": "source"}],
            "objections": [{"objection": "MOCK", "best_reply": "MOCK", "reply_strength": 3}],
            "evidence_strength": 3, "rigor": 3, "uncertain_citations": [], "one_line": "MOCK"}


def synthesis_overview(p: str) -> dict:
    return {"overview_markdown": "MOCK overview. Nothing here is a real analysis.", "ranking": [], "gaps_in_the_field": []}


def gap_match(p: str) -> dict:
    return {"coverage": ["covered", "partial", "missing"][_num(p[-200:], 0, 2)], "david_claims": [], "note": "MOCK",
            "expand": "MOCK suggestion"}


def prior_art(p: str) -> dict:
    return {"status": ["prior_art", "original", "parallel"][_num(p[-200:], 0, 2)], "matches": [], "cite_suggestion": "MOCK",
            "unverified_literature": []}


def own_claims(p: str) -> dict:
    return {"claims": [{"claim": "MOCK own claim", "quote": "S001", "sentence_ids": ["S001"]}]}


def yt_summary(p: str) -> dict:
    qs = re.findall(r"^\d+\. (.+)$", p.split("QUESTIONS:", 1)[-1].split("ITEM:", 1)[0], re.M)
    return {"summary": "MOCK base-layer summary.", "answers": [{"question": q, "answer": "MOCK", "timestamps": ["00:01"]} for q in qs],
            "people_and_sources": [{"name": "MOCK scholar", "role": "cited", "timestamp": "00:09"}], "topics": ["resurrection"],
            "focus_findings": []}


def yt_deep(p: str) -> dict:
    return {"arguments": [{"title": "MOCK argument", "premises": ["MOCK"], "unstated_premises": [], "conclusion": "MOCK",
                           "strength": 6, "strength_reason": "MOCK", "make_stronger": "MOCK", "timestamps": ["00:09"]}],
            "claims_checked": [], "unaddressed_objection": "MOCK", "fallacies_and_moves": [], "scholarship": [],
            "theophysics_relevance": [], "detail_answers": [], "focus_findings": []}


def openai_bundle(p: str) -> dict:
    keys = [k.strip() for k in _line(p, "KEYS").split(",") if k.strip()]
    return {k: {"mock": True, "station": k, "note": "MOCK station output"} for k in keys}


HANDLERS = {
    "fruits_sentences": fruits_sentences, "fruits_verdict": fruits_verdict, "master_equation": master_equation,
    "axiom_nodes": axiom_nodes, "coherence": coherence, "story_paper": story_paper, "story_series": story_series,
    "story_lines": story_lines, "tagger": tagger, "extract_arguments": extract_arguments,
    "synthesize_cluster": synthesize_cluster, "synthesis_overview": synthesis_overview, "gap_match": gap_match,
    "prior_art": prior_art, "own_claims": own_claims, "yt_summary": yt_summary, "yt_deep": yt_deep,
}
