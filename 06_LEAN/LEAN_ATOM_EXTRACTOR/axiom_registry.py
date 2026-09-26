"""
axiom_registry.py - One registry of every distinct Lean axiom, with facts first
(from Lean + Python) and descriptions second (DeepSeek, labelled as AI).

    python axiom_registry.py <AXIOMS dir>            # facts + DeepSeek + story
    python axiom_registry.py <AXIOMS dir> --facts    # facts only, no API calls

Reads  <AXIOMS>/compile/*.json      (from axiom_compile.py)
       axiom_files.json             (harvest rows: versions, copies, origins)
       lean_atoms.db                (main verified project, for "already proven")
       atoms repo axioms/01_canonical (AX-### spine, for correspondence)
Writes <AXIOMS>/pills/<lane>/<name>.pill.yaml   one pill per distinct axiom
       <AXIOMS>/00_AXIOM_REGISTRY.json / .csv
       <AXIOMS>/00_BY_STATUS.md, 00_BY_LANE.md, 00_BY_SPINE.md
       <AXIOMS>/00_AXIOM_STORY.md
"""

import csv
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

HERE = Path(__file__).parent
SPINE = r"D:\GitHub\Faith-through-physics-atoms\axioms\01_canonical"
NS = uuid.uuid5(uuid.NAMESPACE_DNS, "faiththruphysics.com")
DS_URL = "https://api.deepseek.com/chat/completions"
STANDARD = {"propext", "Classical.choice", "Quot.sound"}

# Fact-based statuses, strongest first. An axiom gets exactly one primary status.
STATUS_ORDER = [
    "ALREADY_PROVEN",          # a passing theorem has the same statement -> not needed as an axiom
    "POSSIBLE_CONTRADICTION",  # a passing theorem appears to prove its negation -> review
    "SUPERSEDED",              # only in older versions; the newest version of the file dropped it
    "LIVE_CORE",               # compiled theorems actually depend on it (#print axioms)
    "UNUSED_SPEC",             # compiled, but no theorem rests on it
    "UNVERIFIED",              # its file did not compile, so use is unknown
]


def norm(stmt: str) -> str:
    s = re.sub(r"--[^\n]*|/-.*?-/", "", stmt or "", flags=re.S)
    s = re.sub(r"^\s*(private\s+|protected\s+|noncomputable\s+)*axiom\s+\S+", "", s.strip())
    return re.sub(r"\s+", " ", s).strip()


def short(fq: str) -> str:
    return fq.split(".")[-1]


def load_compile(axdir):
    out = {}
    for p in glob.glob(os.path.join(axdir, "compile", "*.json")):
        r = json.load(open(p, encoding="utf-8"))
        out[r["file"]] = r
    return out


def load_proven():
    """Passing theorems from the main verified project: statement -> name."""
    c = sqlite3.connect(HERE / "lean_atoms.db")
    rows = c.execute("""SELECT d.fully_qualified_name, d.formal_statement FROM declarations d
                        JOIN builds b ON b.declaration_id = d.id
                        WHERE d.declaration_kind IN ('theorem','lemma') AND b.build_result = 'PASSED'""").fetchall()
    by_stmt, by_name = {}, {}
    for fq, st in rows:
        s = re.sub(r"^\s*(theorem|lemma)\s+\S+", "", st or "").strip()
        by_stmt[re.sub(r"\s+", " ", s)] = fq
        by_name[short(fq)] = fq
    return by_stmt, by_name


def load_spine():
    spine = []
    for p in sorted(glob.glob(os.path.join(SPINE, "AX-*.jsonld"))):
        d = json.load(open(p, encoding="utf-8"))
        spine.append({"id": d.get("nodeID", "").split("/")[-1], "name": d.get("name"),
                      "class": d.get("claimClass"), "statement": d.get("statementTechnical")})
    return spine


def build_facts(axdir):
    files = {i["file"]: i for i in json.load(open(HERE / "axiom_files.json", encoding="utf-8"))}
    compiled = load_compile(axdir)
    proven_stmt, proven_name = load_proven()

    # Passing theorems inside the harvest too (negation / same-statement checks).
    harvest_theorems = []
    for r in compiled.values():
        if r.get("status", "").startswith("PASSED"):
            for t in r.get("theorems", []):
                harvest_theorems.append((t["name"], r["file"]))

    groups = {}
    for fname, r in compiled.items():
        meta = files.get(fname, {})
        for a in r.get("axioms", []):
            key = (short(a["name"]), norm(a["statement"]))
            g = groups.setdefault(key, {
                "name": short(a["name"]), "full_names": set(), "statement": a["statement"].strip(),
                "normalized": key[1], "files": [], "used_by": set(), "compiled_in": [], "failed_in": []})
            g["full_names"].add(a["name"])
            g["files"].append({"file": fname, "version_rank": meta.get("version_rank"),
                               "versions_of_name": meta.get("versions_of_name"), "copies": meta.get("copies"),
                               "status": r.get("status"), "lines": a["lines"],
                               "origin": (meta.get("origins") or [None])[0]})
            (g["compiled_in"] if r.get("status", "").startswith("PASSED") else g["failed_in"]).append(fname)

    # Which compiled theorems rest on which axiom (after every group exists).
    for fname, r in compiled.items():
        for t in r.get("theorems", []):
            for used in t.get("custom_axioms") or []:
                for g in groups.values():
                    if used in g["full_names"]:
                        g["used_by"].add(f"{t['name']}  ({fname})")

    records = []
    for g in groups.values():
        flags = []
        stmt_key = re.sub(r"\s+", " ", g["normalized"])
        if stmt_key and stmt_key in proven_stmt:
            flags.append(("ALREADY_PROVEN", proven_stmt[stmt_key]))
        elif g["name"] in proven_name:
            # Same name only: a lead to review, not evidence the axiom is proven.
            flags.append(("NOTE_NAME_MATCHES_THEOREM", proven_name[g["name"]]))
        neg = [t for t, f in harvest_theorems if re.search(rf"(^|[._])(not_|no_){re.escape(g['name'])}$|{re.escape(g['name'])}_(false|fails|refuted)$", short(t))]
        neg += [t for t in proven_name.values() if re.search(rf"(^|[._])(not_|no_){re.escape(g['name'])}$", short(t))]
        if neg:
            flags.append(("POSSIBLE_CONTRADICTION", sorted(set(neg))))
        ranks = [f["version_rank"] or 1 for f in g["files"]]
        if ranks and min(ranks) > 1:
            flags.append(("SUPERSEDED", "only present in older versions of its file"))
        if g["used_by"]:
            flags.append(("LIVE_CORE", len(g["used_by"])))
        elif g["compiled_in"]:
            flags.append(("UNUSED_SPEC", "compiled; no theorem depends on it"))
        else:
            flags.append(("UNVERIFIED", "no containing file compiled"))
        primary = min((f[0] for f in flags if f[0] in STATUS_ORDER), key=STATUS_ORDER.index)
        nid = f"tp:lean-axiom/{g['name']}/{hashlib.sha256(g['normalized'].encode()).hexdigest()[:10]}"
        records.append({
            "uuid": str(uuid.uuid5(NS, f"lean-axiom:{g['name']}:{g['normalized']}")),
            "node_id": nid,
            "name": g["name"],
            "full_names": sorted(g["full_names"]),
            "statement": g["statement"],
            "primary_status": primary,
            "status_flags": [{"status": s, "detail": d} for s, d in flags],
            "used_by": sorted(g["used_by"]),
            "used_by_count": len(g["used_by"]),
            "appears_in": g["files"],
            "file_count": len(g["files"]),
            "compiled_in": sorted(set(g["compiled_in"])),
            "failed_in": sorted(set(g["failed_in"])),
        })
    records.sort(key=lambda r: (STATUS_ORDER.index(r["primary_status"]), -r["used_by_count"], r["name"]))
    return records


SYSTEM = ("You classify axioms from a Lean 4 formalization of a Christian theology-and-physics framework "
          "(Theophysics). Be exact and plain. An axiom is an assumption, never a proof. Do not claim more than "
          "the Lean statement says. Where the statement is only a placeholder (e.g. an opaque Prop or True), say so.")

PROMPT = """Classify each Lean axiom below. Return JSON: {{"axioms": [ ... one object per axiom, same order ... ]}}.
Each object has exactly these keys:
  "name": the axiom name as given,
  "plain": one or two sentences - what it assumes, in plain words,
  "axiom_type": one of floor | definitional | structural | bridge | empirical | theological | moral | mathematical | physical | placeholder,
  "lane": one of physics | master_equation | ten_laws | trinity | axioms | consciousness | morality | crown | story | meta | other,
  "register": one of formal | physical | theological | moral | philosophical | historical | mixed,
  "story_role": one of foundation | grounding | mechanism | bridge | consequence_assumed | boundary | scaffold,
  "strength": one of weak | moderate | strong  (how much the assumption asks the reader to grant),
  "could_be_theorem": true if it looks derivable from simpler definitions rather than needing to be assumed,
  "spine_match": the best matching AX id from the spine list below, or null,
  "spine_match_reason": short reason, or null,
  "recommendation": one of KEEP_CORE | MERGE_WITH_SPINE | REPLACE_WITH_THEOREM | DROP_DUPLICATE | DROP_PLACEHOLDER | REVIEW,
  "recommendation_reason": one sentence,
  "tags": 3-6 short keyword tags

FACTS (from Lean, do not contradict them): {facts}

AXIOM SPINE (canonical written axioms):
{spine}

AXIOMS:
{axioms}"""


def call(key, prompt, max_tokens=8192):
    body = {"model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"), "temperature": 0.2,
            "max_tokens": max_tokens, "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}
    last = None
    for attempt in range(4):
        try:
            r = requests.post(DS_URL, json=body, timeout=(20, 600), headers={"Authorization": f"Bearer {key}"})
            r.raise_for_status()
            return json.loads(r.json()["choices"][0]["message"]["content"])
        except Exception as e:
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(last)


def describe(records, spine):
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise SystemExit("DEEPSEEK_API_KEY not set")
    spine_txt = "\n".join(f"{s['id']} [{s['class']}] {s['name']}: {s['statement']}" for s in spine)
    batches = [records[i:i + 15] for i in range(0, len(records), 15)]

    def work(batch):
        facts = "; ".join(f"{r['name']}: status {r['primary_status']}, used by {r['used_by_count']} theorems"
                          for r in batch)
        ax = "\n".join(f"- {r['name']}: {r['statement']}" for r in batch)
        out = call(key, PROMPT.format(facts=facts, spine=spine_txt, axioms=ax)).get("axioms", [])
        by_name = {o.get("name"): o for o in out}
        return [(r, by_name.get(r["name"])) for r in batch]

    with ThreadPoolExecutor(max_workers=5) as pool:
        for fut in [pool.submit(work, b) for b in batches]:
            for r, o in fut.result():
                if o:
                    o.pop("name", None)
                    r["ai"] = {**o, "_model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
                               "_kind": "AI classification - not evidence; review before canon"}


STORY_PROMPT = """These are the Lean axioms of the Theophysics framework that compiled theorems actually depend on
(LIVE_CORE), plus the strongest unused specifications. Arrange them into ONE coherent story: the order in which a
reader should grant them, from first foundation to last. Group axioms that say the same thing. Point out gaps
(steps the story needs but no axiom supplies) and tensions (axioms that pull against each other).
Return JSON: {{"title": str, "summary": str,
  "chapters": [{{"heading": str, "axioms": [names], "narrative": str}}],
  "merged_groups": [{{"keep": name, "merge": [names], "reason": str}}],
  "gaps": [str], "tensions": [str]}}

{axioms}"""


def story(records):
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    pick = [r for r in records if r["primary_status"] == "LIVE_CORE"]
    pick += [r for r in records if r["primary_status"] == "UNUSED_SPEC"
             and (r.get("ai") or {}).get("recommendation") in ("KEEP_CORE", "MERGE_WITH_SPINE")][:60]
    ax = "\n".join(f"- {r['name']} [{r['primary_status']}, used by {r['used_by_count']}; "
                   f"{(r.get('ai') or {}).get('axiom_type')}; spine {(r.get('ai') or {}).get('spine_match')}]: "
                   f"{(r.get('ai') or {}).get('plain') or r['statement']}" for r in pick)
    return call(key, STORY_PROMPT.format(axioms=ax)), [r["name"] for r in pick]


class _D(yaml.SafeDumper):
    pass


_D.add_representer(str, lambda d, v: d.represent_scalar("tag:yaml.org,2002:str", v, style="|" if "\n" in v else None))


def write_outputs(axdir, records, story_obj=None, story_inputs=None):
    ax = Path(axdir)
    for r in records:
        ai = r.get("ai") or {}
        lane = ai.get("lane") or "unclassified"
        pill = {
            "face": {"uuid": r["uuid"], "node_id": r["node_id"], "name": r["name"],
                     "plain": ai.get("plain") or r["statement"], "status": r["primary_status"],
                     "target_type": "axiom", "lane": lane, "defense_class": "AXIOM"},
            "rails": {
                "framework": "Claim Evidence Lane Framework",
                "1_claim": r["statement"],
                "2_framework_lane": lane,
                "2_lane_basis": "AI classification; review before canon" if ai else "unclassified",
                "3_physics_claim_type": "mathematical_formalism",
                "4_defense_class": "AXIOM",
                "5_evidence_needed": ["none_needed (declared assumption)", "lean_formal for theorems that use it"],
                "6_evidence_present": [{"lane": "lean_formal", "item": f"used by {r['used_by_count']} compiled theorem(s)"}],
                "7_evidence_gap": (["declared, not derived"] +
                                   (["not used by any compiled theorem"] if not r["used_by"] else []) +
                                   (["containing file did not compile"] if not r["compiled_in"] else [])),
                "8_kill_condition": "Retire it if a passing theorem proves it from simpler definitions, or proves its negation.",
                "9_story_rendering": {"text": None, "note": "Kept separate. Story is never counted as proof."},
                "10_beacon": {"uuid": r["uuid"], "node_id": r["node_id"]},
            },
            "facts": {k: r[k] for k in ("primary_status", "status_flags", "used_by_count", "used_by",
                                        "file_count", "appears_in", "compiled_in", "failed_in", "full_names")},
            "classification": ai or {"status": "NOT_RUN"},
            "human_ruling": {"status": "pending", "keep_drop": None, "ruled_by": None, "date": None},
        }
        dest = ax / "pills" / lane / f"{r['name']}.pill.yaml"
        if dest.exists() and yaml.safe_load(dest.read_text(encoding="utf-8"))["face"]["uuid"] != r["uuid"]:
            dest = dest.with_name(f"{r['name']}__{r['uuid'][:8]}.pill.yaml")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(yaml.dump(pill, Dumper=_D, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
        r["pill"] = dest.relative_to(ax).as_posix()

    (ax / "00_AXIOM_REGISTRY.json").write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(), "count": len(records), "axioms": records},
        indent=1, ensure_ascii=False, default=list), encoding="utf-8")
    cols = ["name", "primary_status", "used_by_count", "file_count", "lane", "axiom_type", "register",
            "story_role", "strength", "could_be_theorem", "spine_match", "recommendation", "plain", "statement", "pill"]
    with open(ax / "00_AXIOM_REGISTRY.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in records:
            ai = r.get("ai") or {}
            w.writerow({"name": r["name"], "primary_status": r["primary_status"], "used_by_count": r["used_by_count"],
                        "file_count": r["file_count"], "lane": ai.get("lane"), "axiom_type": ai.get("axiom_type"),
                        "register": ai.get("register"), "story_role": ai.get("story_role"),
                        "strength": ai.get("strength"), "could_be_theorem": ai.get("could_be_theorem"),
                        "spine_match": ai.get("spine_match"), "recommendation": ai.get("recommendation"),
                        "plain": ai.get("plain"), "statement": r["statement"], "pill": r.get("pill")})

    def index(title, keyf, fname, note):
        groups = defaultdict(list)
        for r in records:
            groups[keyf(r) or "unclassified"].append(r)
        lines = [f"# {title}", "", note, ""]
        for k in sorted(groups, key=lambda k: (STATUS_ORDER.index(k) if k in STATUS_ORDER else 99, k)):
            lines += [f"## {k} ({len(groups[k])})", ""]
            for r in groups[k]:
                ai = r.get("ai") or {}
                lines.append(f"- **{r['name']}** — {ai.get('plain') or r['statement'][:160]} "
                             f"· used by {r['used_by_count']} · `{r.get('pill')}`")
            lines.append("")
        (ax / fname).write_text("\n".join(lines), encoding="utf-8")

    index("Lean axioms by status", lambda r: r["primary_status"], "00_BY_STATUS.md",
          "Status comes from Lean and Python facts only. ALREADY_PROVEN / SUPERSEDED / UNUSED_SPEC are candidates to "
          "retire; POSSIBLE_CONTRADICTION needs review; LIVE_CORE carries the compiled theorems.")
    index("Lean axioms by lane", lambda r: (r.get("ai") or {}).get("lane"), "00_BY_LANE.md",
          "Lane is an AI classification - review before canon.")
    index("Lean axioms by written-spine match", lambda r: (r.get("ai") or {}).get("spine_match"), "00_BY_SPINE.md",
          "Which AX-### floor axiom each Lean axiom appears to formalize (AI proposal). 'unclassified' = no match: "
          "either a new assumption the spine lacks, or scaffolding.")

    if story_obj:
        s = story_obj
        lines = [f"# {s.get('title', 'The axiom story')}", "",
                 "*Arranged by AI from the LIVE_CORE axioms and the strongest specifications. The order is a proposal "
                 "for review; each axiom's facts are in its pill.*", "", s.get("summary", ""), ""]
        for i, ch in enumerate(s.get("chapters", []), 1):
            lines += [f"## {i}. {ch.get('heading')}", "", ch.get("narrative", ""), "",
                      "Axioms: " + ", ".join(f"`{a}`" for a in ch.get("axioms", [])), ""]
        if s.get("merged_groups"):
            lines += ["## Proposed merges", ""] + [
                f"- keep **{m.get('keep')}**, merge {', '.join(m.get('merge', []))} — {m.get('reason')}"
                for m in s["merged_groups"]] + [""]
        if s.get("gaps"):
            lines += ["## Gaps (the story needs these, no axiom supplies them)", ""] + [f"- {g}" for g in s["gaps"]] + [""]
        if s.get("tensions"):
            lines += ["## Tensions", ""] + [f"- {t}" for t in s["tensions"]] + [""]
        lines += ["---", f"Inputs: {len(story_inputs or [])} axioms."]
        (ax / "00_AXIOM_STORY.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    axdir = sys.argv[1]
    facts_only = "--facts" in sys.argv
    records = build_facts(axdir)
    counts = defaultdict(int)
    for r in records:
        counts[r["primary_status"]] += 1
    print(f"{len(records)} distinct axioms:", dict(counts))
    story_obj = story_inputs = None
    if not facts_only:
        describe(records, load_spine())
        print("classified:", sum(1 for r in records if r.get("ai")))
        story_obj, story_inputs = story(records)
        print("story chapters:", len(story_obj.get("chapters", [])))
    write_outputs(axdir, records, story_obj, story_inputs)
    print("written to", axdir)


if __name__ == "__main__":
    main()
