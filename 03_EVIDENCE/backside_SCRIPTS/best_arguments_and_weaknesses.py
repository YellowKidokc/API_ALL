#!/usr/bin/env python3
"""best_arguments_and_weaknesses.py — mine every paper's best arguments, group the ones
that say the same thing across papers, and surface the shared weaknesses to build out.

Created 2026-09-16 (Claude, with David). Status: TESTED. No API calls — reads the analysis
the companions already contain (Primary argument, Extracted Truth Predicates, Argument
strengthening, Hidden premises, SCORECARD).

Outputs (OUTBOX/BEST_ARGUMENTS/<timestamp>/):
  REPORT.md                 printable: top converging arguments, top weakness themes, weakest sections
  argument_clusters.csv     every argument cluster (size, papers, avg paper score, members)
  weakness_clusters.csv     every weakness theme (papers affected, suggested stronger versions)
  papers.csv                one row per paper: score, #arguments, #weak links
  clusters.json             everything, machine-readable

  python best_arguments_and_weaknesses.py [--shelf FOR_SUBSTACK] [--threshold 0.45] [--top 20]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTBOX = ROOT / "OUTBOX"
MARKER = "<!-- ===== ORIGINAL ARTICLE BELOW - UNCHANGED"

STOP = set("""a an the and or of to in on for with by as is are was were be been it its this that these those
not no from at into than then there their they them which who whom what when where why how all any each
can could would should may might must will shall do does did has have had if but so such also only more most
very just about over under between within without through per via our we you your i he she his her one two""".split())


# Pipeline self-talk (routing / classifier / review-gate boilerplate), not David's arguments.
PIPELINE_NOISE = re.compile(r"(routing|routed|classif|content types?|automatic guess|scripts? (total|were)|archived to|artifact|auto-?guess|human (review|ruling)|meta-document|framework record|"
                            r"0\.\d+\s*<\s*0\.\d+|confidence|rubric|scorecard|template|companion|the document is|this document|"
                            r"skeleton outline|pipeline|ckg|api)", re.I)

# ── parsing companions ─────────────────────────────────

def section(text: str, heading: str) -> str:
    m = re.search(rf"^#{{2,3}}\s*[^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^#{{2,3}}\s|\Z)", text, re.M | re.S | re.I)
    return m.group(1) if m else ""


def table_rows(block: str) -> list[list[str]]:
    rows = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    return rows[1:] if rows else []   # drop header


def clean(s: str) -> str:
    s = re.sub(r"\$[^$]*\$", " ", s)
    s = re.sub(r"[`*_>\[\]]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_paper(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if MARKER in text:
        text = text[: text.find(MARKER)]
    title = (re.search(r'^clean_title:\s*"?([^"\n]+)', text, re.M) or re.search(r"^title:\s*\"?([^\"\n]+)", text, re.M))
    score = re.search(r"\*\*(\d+)/100\*\*", text)
    paper = {
        "file": str(path.relative_to(OUTBOX)) if OUTBOX in path.parents else str(path),
        "title": clean(title.group(1)) if title else path.stem,
        "score": int(score.group(1)) if score else None,
        "arguments": [], "weaknesses": [], "hidden_premises": [], "sections": {},
    }
    # primary argument steps
    for line in section(text, "Primary argument").splitlines():
        m = re.match(r"^\s*\d+\.\s+(.*?)(?:\s+`([^`]+)`)?\s*$", line)
        if m and len(m.group(1)) > 15:
            paper["arguments"].append({"text": clean(m.group(1)), "kind": "argument_step", "tag": (m.group(2) or "").strip()})
    # truth predicates
    for r in table_rows(section(text, "Extracted Truth Predicates")):
        if len(r) >= 2 and len(r[1]) > 10:
            paper["arguments"].append({"text": clean(r[1]), "kind": "truth_predicate",
                                       "tag": clean(r[2]) if len(r) > 2 else "", "warrant": clean(r[-1])})
    # weak links
    for r in table_rows(section(text, "Argument strengthening")):
        if r and len(r[0]) > 8:
            paper["weaknesses"].append({"text": clean(r[0]), "why": clean(r[1]) if len(r) > 1 else "",
                                        "stronger": clean(r[2]) if len(r) > 2 else "", "fix_source": clean(r[3]) if len(r) > 3 else ""})
    for r in table_rows(section(text, "Hidden premises")):
        if len(r) >= 2:
            paper["hidden_premises"].append({"text": clean(r[1]), "breaks": clean(r[3]) if len(r) > 3 else ""})
    for r in table_rows(section(text, "SCORECARD")):
        if len(r) >= 5 and re.match(r"S\d\d", r[0]):
            try:
                paper["sections"][f"{r[0]} {r[1]}"] = int(r[4])
            except ValueError:
                pass
    if not paper["arguments"] and not paper["weaknesses"]:
        return None
    return paper


# ── similarity (TF-IDF cosine, inverted index) ─────────

def tokens(s: str) -> list[str]:
    w = [t for t in re.findall(r"[a-zα-ωχ][a-z0-9α-ωχ'-]{2,}", s.lower()) if t not in STOP]
    return w + [f"{a}_{b}" for a, b in zip(w, w[1:])]


def cluster(items: list[dict], threshold: float, max_df_ratio: float = 0.08) -> list[list[int]]:
    n = len(items)
    tfs = [Counter(tokens(it["text"])) for it in items]
    df = Counter()
    for tf in tfs:
        df.update(tf.keys())
    idf = {t: math.log((1 + n) / (1 + d)) + 1 for t, d in df.items()}
    vecs = []
    for tf in tfs:
        v = {t: c * idf[t] for t, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1
        vecs.append({t: x / norm for t, x in v.items()})
    postings = defaultdict(list)
    max_df = max(3, int(n * max_df_ratio))
    for i, v in enumerate(vecs):
        for t, x in v.items():
            if df[t] <= max_df:
                postings[t].append((i, x))
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i, v in enumerate(vecs):
        acc = defaultdict(float)
        for t, x in v.items():
            if df[t] <= max_df:
                for j, y in postings[t]:
                    if j > i:
                        acc[j] += x * y
        for j, sim in acc.items():
            if sim >= threshold and items[i]["paper"] != items[j]["paper"]:
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    return sorted(groups.values(), key=len, reverse=True)


# ── report ─────────────────────────────────────────────

def summarize(groups, items, papers, kind):
    out = []
    for g in groups:
        pids = {items[i]["paper"] for i in g}
        if len(pids) < 2:
            continue
        scores = [papers[p]["score"] for p in pids if papers[p]["score"] is not None]
        members = [items[i] for i in g]
        rep = max(members, key=lambda m: (papers[m["paper"]]["score"] or 0, -len(m["text"])))
        entry = {
            "representative": rep["text"],
            "papers": len(pids),
            "mentions": len(g),
            "avg_paper_score": round(sum(scores) / len(scores), 1) if scores else None,
            "paper_titles": sorted({papers[p]["title"] for p in pids})[:30],
            "paper_files": sorted({papers[p]["file"] for p in pids}),
            "members": [{"text": m["text"], "paper": papers[m["paper"]]["title"], "file": papers[m["paper"]]["file"]} for m in members][:60],
        }
        if kind == "argument":
            tags = Counter(m.get("tag", "") for m in members if m.get("tag"))
            entry["tags"] = dict(tags.most_common(5))
            entry["classical_share"] = round(sum(1 for m in members if "CLASSICAL" in (m.get("tag") or "")) / len(members), 2)
        else:
            entry["stronger_versions"] = list(dict.fromkeys(m["stronger"] for m in members if m.get("stronger")))[:8]
            entry["why"] = list(dict.fromkeys(m["why"] for m in members if m.get("why")))[:5]
        out.append(entry)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shelf", default="FOR_SUBSTACK")
    ap.add_argument("--threshold", type=float, default=0.45)
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args(argv)

    files = sorted((OUTBOX / args.shelf).rglob("*.md"))
    papers, args_items, weak_items = [], [], []
    noise = 0
    for f in files:
        p = parse_paper(f)
        if not p:
            continue
        pid = len(papers)
        papers.append(p)
        for a in p["arguments"]:
            if PIPELINE_NOISE.search(a["text"]):
                noise += 1
                continue
            args_items.append({**a, "paper": pid})
        for w in p["weaknesses"]:
            if PIPELINE_NOISE.search(w["text"]):
                noise += 1
                continue
            weak_items.append({**w, "paper": pid})
    print(f"papers parsed {len(papers)} of {len(files)} · arguments {len(args_items)} · weak links {len(weak_items)} · pipeline-noise lines set aside {noise}")

    arg_clusters = summarize(cluster(args_items, args.threshold), args_items, papers, "argument")
    weak_clusters = summarize(cluster(weak_items, args.threshold * 0.85), weak_items, papers, "weakness")
    # strongest first: many papers × paper quality
    arg_clusters.sort(key=lambda c: (c["papers"] * (c["avg_paper_score"] or 40)), reverse=True)
    weak_clusters.sort(key=lambda c: (c["papers"], c["mentions"]), reverse=True)

    sec_scores = defaultdict(list)
    for p in papers:
        for s, v in p["sections"].items():
            sec_scores[s].append(v)
    weakest_sections = sorted(((s, round(sum(v) / len(v), 2), len(v)) for s, v in sec_scores.items() if len(v) >= 3), key=lambda x: x[1])

    out = OUTBOX / "BEST_ARGUMENTS" / datetime.now().strftime("%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    scored = [p["score"] for p in papers if p["score"] is not None]

    md = [f"# Best Arguments & Shared Weaknesses — {args.shelf}",
          f"*Generated {datetime.now():%Y-%m-%d %H:%M} · {len(papers)} papers · {len(args_items)} arguments · {len(weak_items)} weak links · "
          f"similarity threshold {args.threshold} · {noise} pipeline self-talk lines set aside · no API calls*", "",
          f"Average paper score: **{sum(scored) / len(scored):.1f}/100** across {len(scored)} scored papers." if scored else "", "",
          "## How to read this",
          "- **Converging arguments** = the same argument made independently in several papers. Convergence is a canon-readiness signal: these are your load-bearing ideas.",
          "- **Shared weaknesses** = the same weak link flagged in several papers. Fixing one theme strengthens every paper in it at once — that is the build-out list.",
          "- Grouping is statistical (word overlap), not semantic judgment. Check each group before acting on it.", "",
          f"## Top {args.top} converging arguments", ""]
    for i, c in enumerate(arg_clusters[: args.top], 1):
        md += [f"### {i}. {c['representative']}",
               f"**{c['papers']} papers** · {c['mentions']} mentions · avg paper score {c['avg_paper_score']} · classical anchors {int(c['classical_share'] * 100)}%",
               "", "Also said as:"]
        md += [f"- “{m['text']}” — *{m['paper']}*" for m in c["members"][1:5]]
        md.append("")
    md += [f"## Top {args.top} shared weaknesses to build out", ""]
    for i, c in enumerate(weak_clusters[: args.top], 1):
        md += [f"### {i}. {c['representative']}", f"**Affects {c['papers']} papers** ({c['mentions']} flags)", ""]
        if c["why"]:
            md.append(f"**Why it's weak:** {c['why'][0]}")
        if c["stronger_versions"]:
            md.append("**Stronger versions already proposed:**")
            md += [f"- {s}" for s in c["stronger_versions"][:4]]
        md += ["", "Papers: " + "; ".join(c["paper_titles"][:12]), ""]
    if weakest_sections:
        md += ["## Weakest scorecard sections across the corpus", "", "| Section | Avg net score | Papers |", "|---|---|---|"]
        md += [f"| {s} | {v} | {n} |" for s, v, n in weakest_sections]
    (out / "REPORT.md").write_text("\n".join(md), encoding="utf-8")

    with open(out / "argument_clusters.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "representative", "papers", "mentions", "avg_paper_score", "classical_share", "paper_titles"])
        for i, c in enumerate(arg_clusters, 1):
            w.writerow([i, c["representative"], c["papers"], c["mentions"], c["avg_paper_score"], c["classical_share"], " | ".join(c["paper_titles"])])
    with open(out / "weakness_clusters.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "weakness", "papers", "mentions", "why", "stronger_versions", "paper_titles"])
        for i, c in enumerate(weak_clusters, 1):
            w.writerow([i, c["representative"], c["papers"], c["mentions"], " | ".join(c["why"]), " | ".join(c["stronger_versions"]), " | ".join(c["paper_titles"])])
    with open(out / "papers.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["title", "score", "arguments", "weak_links", "hidden_premises", "file"])
        for p in sorted(papers, key=lambda p: -(p["score"] or 0)):
            w.writerow([p["title"], p["score"], len(p["arguments"]), len(p["weaknesses"]), len(p["hidden_premises"]), p["file"]])
    (out / "clusters.json").write_text(json.dumps({"arguments": arg_clusters, "weaknesses": weak_clusters,
                                                   "weakest_sections": weakest_sections}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"converging argument groups {len(arg_clusters)} · shared weakness themes {len(weak_clusters)}")
    print(f"report  {out / 'REPORT.md'}")


if __name__ == "__main__":
    main()
