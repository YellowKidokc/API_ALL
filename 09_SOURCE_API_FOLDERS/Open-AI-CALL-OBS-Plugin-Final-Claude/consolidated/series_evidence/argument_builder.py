#!/usr/bin/env python3
"""argument_builder.py — BUILD ONE ARGUMENT UP, 1000%.

Created 2026-09-16 (Claude, with David). Status: TESTED one-for-one.

This is a BUILDING pass, not a falsification pass.

  1. Finds every converging argument group (from the latest BEST_ARGUMENTS run) that matches
     your phrase, e.g. "Logic comes from God".
  2. Makes a folder for the argument: OUTBOX/ARGUMENTS/<slug>/ and COPIES every paper that
     makes it into papers/ (merged-with-original versions when available). Nothing is moved.
  3. Asks DeepSeek to: judge originality (original / original synthesis / restatement / classical),
     trace where it stems from (thinkers, works, dates), name the dimensions present and missing,
     give ranked build steps (add a dimension, cite, quote, derive, define, example, speculative
     extension), supply quotes to verify, and write the strongest version of the argument.
     Every item is LABELED: ESTABLISHED | SUPPORTED | INTERPRETIVE | SPECULATIVE.
  4. Writes BUILD_<n>.md + build_<n>.json + sources_to_verify.csv. Running it again on the same
     argument starts a new round that builds on the previous one.

AI citations can be wrong: every citation and quote is marked verify=pending until checked.

  python argument_builder.py --find "Logic comes from God"
  python argument_builder.py --find "logic god" --list          # just show what matches
  python argument_builder.py --ranks 15 51 55 --name "Logic comes from God"
  python argument_builder.py --find "..." --model deepseek-reasoner
"""
from __future__ import annotations

import argparse
import csv
import glob
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
OUTBOX = ROOT / "OUTBOX"
ARGS_DIR = OUTBOX / "ARGUMENTS"
API_URL = "https://api.deepseek.com/chat/completions"
MAX_CONTEXT_CHARS = 70_000
STOP = set("the a an of to and or is are be from in on for with that this it its by as not no god's come comes came require requires required need needs make makes".split())

SYSTEM = """You are a research partner helping David BUILD a Theophysics argument (Christian theology + physics,
mathematics, logic, information theory). This is a STRENGTHENING pass, not a falsification pass: your job is to make
the argument as strong, well-grounded, well-cited, and multi-dimensional as it can honestly be. Do not write kill
conditions. Objections appear only as things to answer so the argument gets stronger.

Honesty rules (these make the argument stronger, not weaker):
- Label every build step and extension: ESTABLISHED (mainstream consensus / proven), SUPPORTED (good evidence or
  respected scholarship), INTERPRETIVE (theological or philosophical reading), SPECULATIVE (promising but unproven).
- Only cite real thinkers and real works you are confident exist. Give year and work title. NEVER invent page numbers.
- For quotes: give exact wording only if you are confident; otherwise paraphrase and set "exact": false.
  Every quote and citation gets "verify": true — David will check them.
- Originality: be precise. Classical arguments (e.g. Augustine, Leibniz, Plantinga, Lewis) should be credited; say
  exactly what, if anything, David's version ADDS (a new connection, formalization, domain bridge, synthesis).
Keep it tight so the JSON is complete: at most 8 lineage items, 8 build steps, 6 quotes, 5 objections,
3 speculative extensions, 10 built-argument lines. Keep each text field under 90 words.
Return JSON only."""

SCHEMA = {
    "argument_title": "short title",
    "steelman_statement": "the strongest one-paragraph statement of the argument",
    "originality": {
        "verdict": "original | original_synthesis | classical_restatement | classical_with_new_bridge",
        "explanation": "what is inherited and what is new",
        "what_david_adds": ["specific new moves in these papers"],
    },
    "lineage": [{
        "thinker": "", "work": "", "year": "", "relation": "source | parallel | anticipates | develops | contrasts",
        "how_it_connects": "", "confidence": "high | medium | low", "verify": True,
    }],
    "best_existing_version": {"quote": "exact text from the papers", "paper": "title", "why_best": ""},
    "dimensions": [{
        "dimension": "formal/mathematical | logical | empirical/physical | information-theoretic | classical philosophy | theological/exegetical | historical | experiential/psychological | other",
        "status": "strong | present | thin | missing",
        "what_to_add": "",
    }],
    "build_steps": [{
        "priority": 1,
        "type": "add_dimension | cite | quote | derive | define_term | answer_objection | add_example | tighten_premise | speculative_extension",
        "step": "what to do",
        "detail": "exactly how, with specifics",
        "sources": ["thinker, work (year)"],
        "label": "ESTABLISHED | SUPPORTED | INTERPRETIVE | SPECULATIVE",
    }],
    "quotes_to_use": [{"quote": "", "author": "", "work": "", "year": "", "exact": True, "use_for": "", "verify": True}],
    "objections_to_answer": [{"objection": "", "who_raises_it": "", "best_answer": "", "label": "SUPPORTED"}],
    "speculative_extensions": [{"idea": "", "why_promising": "", "what_would_ground_it": "", "label": "SPECULATIVE"}],
    "connections_in_corpus": ["other arguments in these papers this links to"],
    "built_argument": [{"n": 1, "premise_or_conclusion": "", "kind": "foundation | checkable | bridge | practice_story",
                        "label": "ESTABLISHED | SUPPORTED | INTERPRETIVE | SPECULATIVE", "support": ""}],
    "next_round_focus": "what the next build round should concentrate on",
}


# ── find matching argument groups ──────────────────────

def stem(w: str) -> str:
    for suf in ("ical", "ally", "ness", "ing", "ies", "es", "s", "al", "ic"):
        if len(w) > 5 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def toks(s: str) -> set[str]:
    return {stem(w) for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2}


def latest_clusters() -> tuple[dict, Path]:
    runs = sorted(glob.glob(str(OUTBOX / "BEST_ARGUMENTS" / "*" / "clusters.json")))
    if not runs:
        sys.exit("No BEST_ARGUMENTS run found. Run 10_BEST_ARGUMENTS_AND_WEAKNESSES.bat first.")
    return json.loads(Path(runs[-1]).read_text(encoding="utf-8")), Path(runs[-1])


def match_groups(clusters: dict, query: str, min_score: float) -> list[tuple[int, float, dict]]:
    q = toks(query)
    hits = []
    for rank, c in enumerate(clusters["arguments"], 1):
        texts = [c["representative"]] + [m["text"] for m in c["members"]]
        best = max(len(q & toks(t)) / len(q) for t in texts) if q else 0
        if best >= min_score:
            hits.append((rank, round(best, 2), c))
    return sorted(hits, key=lambda h: (-h[1], -h[2]["papers"]))


# ── gather papers + excerpts ───────────────────────────

def best_copy(rel: str) -> Path:
    merged = OUTBOX / "MERGED_WITH_ORIGINAL" / rel
    return merged if merged.exists() else OUTBOX / rel


def excerpts_for(path: Path, query_toks: set[str], statements: list[str], budget: int) -> str:
    raw = path.read_bytes()
    original = article_stack.original_of(raw).decode("utf-8", errors="replace")
    paras = [p.strip() for p in re.split(r"\n\s*\n", original) if len(p.strip()) > 80]
    scored = sorted(paras, key=lambda p: -len(query_toks & toks(p)))
    chosen, used = [], 0
    for p in scored:
        if len(query_toks & toks(p)) == 0 or used + len(p) > budget:
            continue
        chosen.append(p)
        used += len(p)
    return "\n".join(f"- ARGUMENT AS STATED: {s}" for s in statements) + "\n\nRELEVANT PASSAGES FROM THE ORIGINAL:\n" + "\n\n".join(chosen)


# ── API ────────────────────────────────────────────────

def call_deepseek(user: str, model: str) -> tuple[dict, dict]:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        sys.exit("DEEPSEEK_API_KEY is not set.")
    payload = {"model": model, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
               "max_tokens": 8000}
    if model == "deepseek-chat":
        payload["response_format"] = {"type": "json_object"}
        payload["temperature"] = 0.3
    last = None
    for attempt in range(1, 4):
        try:
            r = requests.post(API_URL, json=payload, timeout=600,
                              headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            r.raise_for_status()
            res = r.json()
            text = res["choices"][0]["message"]["content"].strip()
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
            if not text.startswith("{"):
                text = text[text.find("{"): text.rfind("}") + 1]
            return json.loads(text), res.get("usage", {})
        except Exception as e:
            last = e
            print(f"  attempt {attempt} failed: {e}")
            time.sleep(4 * attempt)
    raise RuntimeError(f"DeepSeek failed: {last}")


# ── render ─────────────────────────────────────────────

LABEL_ICON = {"ESTABLISHED": "🟩", "SUPPORTED": "🟦", "INTERPRETIVE": "🟪", "SPECULATIVE": "🟨"}


def render(b: dict, name: str, round_n: int, groups, papers, model, usage) -> str:
    o = b.get("originality") or {}
    L = [f"# 🏗️ Argument Build — {b.get('argument_title') or name}",
         f"*Round {round_n} · {datetime.now():%Y-%m-%d %H:%M} · deepseek/{model} · {usage.get('total_tokens', 0)} tokens · "
         f"{len(papers)} papers · {len(groups)} converging groups*", "",
         "> AI-built draft for David's review. 🟩 established · 🟦 supported · 🟪 interpretive · 🟨 speculative. "
         "**Every citation and quote is marked verify — check before publishing.**", "",
         "## The argument at full strength", "", b.get("steelman_statement", ""), "",
         "## Is it original?", "", f"**Verdict: {o.get('verdict', '?')}**", "", o.get("explanation", ""), ""]
    if o.get("what_david_adds"):
        L += ["**What your version adds:**"] + [f"- {x}" for x in o["what_david_adds"]] + [""]
    if b.get("lineage"):
        L += ["## Where it stems from", "", "| Thinker | Work (year) | Relation | How it connects | Confidence |", "|---|---|---|---|---|"]
        L += [f"| {x.get('thinker')} | *{x.get('work')}* ({x.get('year')}) | {x.get('relation')} | {x.get('how_it_connects')} | {x.get('confidence')} · verify |"
              for x in b["lineage"]]
        L.append("")
    be = b.get("best_existing_version") or {}
    if be.get("quote"):
        L += ["## Best version already in your papers", "", f"> {be['quote']}", "", f"— *{be.get('paper')}*. {be.get('why_best', '')}", ""]
    if b.get("dimensions"):
        icon = {"strong": "✅", "present": "☑️", "thin": "⚠️", "missing": "❌"}
        L += ["## Dimensions", "", "| Dimension | Status | What to add |", "|---|---|---|"]
        L += [f"| {d.get('dimension')} | {icon.get(d.get('status'), '')} {d.get('status')} | {d.get('what_to_add')} |" for d in b["dimensions"]]
        L.append("")
    if b.get("build_steps"):
        L += ["## Build it up — step by step", ""]
        for s in sorted(b["build_steps"], key=lambda s: s.get("priority", 99)):
            L += [f"### {s.get('priority')}. {LABEL_ICON.get(s.get('label'), '')} {s.get('step')}  `{s.get('type')}` · {s.get('label')}",
                  "", s.get("detail", "")]
            if s.get("sources"):
                L.append("*Sources (verify):* " + "; ".join(s["sources"]))
            L.append("")
    if b.get("quotes_to_use"):
        L += ["## Quotes to use (verify each)", ""]
        for q in b["quotes_to_use"]:
            mark = "exact wording" if q.get("exact") else "paraphrase — find exact wording"
            L += [f"> “{q.get('quote')}”", f"— **{q.get('author')}**, *{q.get('work')}* ({q.get('year')}) · {mark} · use for: {q.get('use_for')}", ""]
    if b.get("objections_to_answer"):
        L += ["## Objections to answer (so the argument gets stronger)", ""]
        L += [f"- **{x.get('objection')}** ({x.get('who_raises_it')}) → {x.get('best_answer')} *[{x.get('label')}]*" for x in b["objections_to_answer"]]
        L.append("")
    if b.get("speculative_extensions"):
        L += ["## 🟨 Speculative extensions (labeled — promising, not proven)", ""]
        L += [f"- **{x.get('idea')}** — {x.get('why_promising')} *What would ground it:* {x.get('what_would_ground_it')}" for x in b["speculative_extensions"]]
        L.append("")
    if b.get("built_argument"):
        L += ["## The built argument", "", "| # | Premise / conclusion | Kind | Label | Support |", "|---|---|---|---|---|"]
        L += [f"| {x.get('n')} | {x.get('premise_or_conclusion')} | {x.get('kind')} | {LABEL_ICON.get(x.get('label'), '')} {x.get('label')} | {x.get('support')} |"
              for x in b["built_argument"]]
        L.append("")
    if b.get("connections_in_corpus"):
        L += ["## Connects to"] + [f"- {x}" for x in b["connections_in_corpus"]] + [""]
    L += ["## Next round focus", "", b.get("next_round_focus", ""), "", "## Papers in this argument", ""]
    L += [f"- [[{p.name}]]" for p in papers]
    L += ["", "## Converging groups used", ""] + [f"- #{r} (match {s}, {c['papers']} papers): {c['representative']}" for r, s, c in groups]
    return "\n".join(L)


def slugify(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:60] or "argument"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--find", help='plain phrase, e.g. "Logic comes from God"')
    ap.add_argument("--ranks", type=int, nargs="*", help="use these converging-argument ranks from the report")
    ap.add_argument("--name", help="folder / argument name (defaults to --find)")
    ap.add_argument("--min-match", type=float, default=0.75, help="share of your words a group must contain (0.75 = all words for short phrases)")
    ap.add_argument("--list", action="store_true", help="only list matching groups")
    ap.add_argument("--model", default="deepseek-chat", choices=["deepseek-chat", "deepseek-reasoner"])
    args = ap.parse_args(argv)
    if not args.find and not args.ranks:
        ap.error("give --find or --ranks")

    clusters, cpath = latest_clusters()
    groups = []
    if args.find:
        groups += match_groups(clusters, args.find, args.min_match)
    for r in args.ranks or []:
        if 1 <= r <= len(clusters["arguments"]) and all(g[0] != r for g in groups):
            groups.append((r, 1.0, clusters["arguments"][r - 1]))
    print(f"using {cpath}")
    if args.find and not groups:
        partial = match_groups(clusters, args.find, 0.5)
        if partial:
            print("no group contains all your words — PARTIAL matches (add the numbers you want with --ranks):")
            for r, sc, c in partial[:25]:
                print(f"  #{r:<3} partial {sc:<4} {c['papers']} papers  {c['representative'][:100]}")
    for r, s, c in groups:
        print(f"  #{r:<3} match {s:<4} {c['papers']} papers  {c['representative'][:100]}")
    if args.list or not groups:
        if not groups:
            print("no matching groups — try fewer words, --min-match 0.5, or add --ranks N N from the report")
        return

    name = args.name or args.find or groups[0][2]["representative"]
    folder = ARGS_DIR / slugify(name)
    (folder / "papers").mkdir(parents=True, exist_ok=True)

    rel_files, statements = [], {}
    for _, _, c in groups:
        for m in c["members"]:
            rel_files.append(m["file"])
            statements.setdefault(m["file"], []).append(m["text"])
    rel_files = list(dict.fromkeys(rel_files))
    papers = []
    for rel in rel_files:
        src = best_copy(rel)
        if not src.exists():
            continue
        dest = folder / "papers" / src.name
        if not dest.exists():
            shutil.copy2(src, dest)
        papers.append(dest)
    print(f"folder   {folder}  ({len(papers)} papers copied)")

    qt = toks(name) | set().union(*(toks(s) for ss in statements.values() for s in ss))
    per_paper = max(2500, MAX_CONTEXT_CHARS // max(1, len(papers)))
    context = []
    for rel, dest in zip(rel_files, papers):
        context.append(f"===== PAPER: {dest.stem} =====\n" + excerpts_for(dest, toks(name) | toks(" ".join(statements.get(rel, []))), statements.get(rel, []), per_paper))
    prior = sorted(folder.glob("build_*.json"))
    round_n = len(prior) + 1
    prior_note = ""
    if prior:
        pb = json.loads(prior[-1].read_text(encoding="utf-8"))
        prior_note = ("\n\nPREVIOUS BUILD ROUND (go deeper; do not repeat — extend, add sources, fill missing dimensions):\n"
                      + json.dumps({k: pb.get(k) for k in ("steelman_statement", "originality", "dimensions", "next_round_focus", "built_argument")},
                                   ensure_ascii=False)[:12000])
    user = (f'ARGUMENT TO BUILD: "{name}"\n\nRespond with JSON in this shape:\n{json.dumps(SCHEMA, ensure_ascii=False, indent=1)}'
            f"{prior_note}\n\nTHE PAPERS THAT MAKE THIS ARGUMENT:\n\n" + "\n\n".join(context)[:MAX_CONTEXT_CHARS])

    print(f"calling  deepseek/{args.model} · round {round_n} · {len(user):,} chars …")
    t0 = time.time()
    build, usage = call_deepseek(user, args.model)
    print(f"answered in {time.time() - t0:.0f}s · tokens {usage.get('total_tokens')}")

    (folder / f"build_{round_n}.json").write_text(json.dumps({"argument": name, "round": round_n, "model": args.model,
        "usage": usage, "groups": [{"rank": r, "match": s, "representative": c["representative"]} for r, s, c in groups],
        "papers": [p.name for p in papers], **build}, ensure_ascii=False, indent=2), encoding="utf-8")
    md = render(build, name, round_n, groups, papers, args.model, usage)
    (folder / f"BUILD_{round_n}.md").write_text(md, encoding="utf-8")
    (folder / "BUILD_LATEST.md").write_text(md, encoding="utf-8")
    with open(folder / "sources_to_verify.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["round", "type", "author_or_thinker", "work", "year", "text_or_connection", "exact", "verified"])
        for x in build.get("lineage") or []:
            w.writerow([round_n, "lineage", x.get("thinker"), x.get("work"), x.get("year"), x.get("how_it_connects"), "", ""])
        for q in build.get("quotes_to_use") or []:
            w.writerow([round_n, "quote", q.get("author"), q.get("work"), q.get("year"), q.get("quote"), q.get("exact"), ""])
    print(f"verdict  {(build.get('originality') or {}).get('verdict')}")
    print(f"steps    {len(build.get('build_steps') or [])} · lineage {len(build.get('lineage') or [])} · quotes {len(build.get('quotes_to_use') or [])}")
    print(f"written  {folder / 'BUILD_LATEST.md'}")


if __name__ == "__main__":
    main()
