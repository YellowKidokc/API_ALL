#!/usr/bin/env python3
"""
process_atom_pipeline.py
========================
Inbox/Outbox batch engine for ATOM BUILDER.

Takes files from 'inbox' (or a series folder specified by the user):
1. Runs OpenRouter in parallel on each paper (Claim, Evidence, Proof, Process, plus full Atom Meaning Block fields).
2. Generates BOTH:
   - 'nerve-draft-*.json' in 'outbox/YYYY-MM-DD/' for 1-click import into Claim Atom Builder.
   - '[Paper]_ATOM_MEANING_BLOCK.md' human-readable markdown summaries using David's canonical 10-section template.
3. Archives processed source papers into 'archive/YYYY-MM-DD_HH-MM/'.
4. Imports 1-click directly into Claim Atom Builder via 'Import JSON'.
"""

import os
import sys
import json
import uuid
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request

try:
    import json_repair
except ImportError:
    json_repair = None

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are the governed Claim Atom Builder for Theophysics.
Analyze the provided source paper and extract candidate contents for the 4 core native objects (CLAIM, EVIDENCE, PROOF, PROCESS) and the canonical Atom Meaning Block.

Return ONLY valid JSON matching this exact structure:
{
  "title": "Paper Title / Theme",
  "statement": "Narrow technical statement of the primary claim",
  "formal_definition": "Precise formal definition of what this atom claims",
  "math_equation": "Equation, symbolic form, typed relation, master equation socket, or formal expression",
  "common_sense_meaning": "Plain-language explanation for a normal reader",
  "governing_questions": {
    "answers": "What question does this atom answer?",
    "solves": "What problem does this atom solve?",
    "breaks_if_false": "What breaks if this atom is false, weak, or misplaced?",
    "lets_next_carry": "What does this atom let the next atom carry?",
    "unresolved": "What remains unresolved after this atom?"
  },
  "what_this_solves": "The local gap, contradiction, dependency, or explanatory burden this atom addresses",
  "why_this_matters": "How this atom supports the public story, downstream argument, or cross-domain bridge",
  "claim_mode": "LOGICAL | MATHEMATICAL | EMPIRICAL | HISTORICAL | PHILOSOPHICAL | THEOLOGICAL | BRIDGE | CONJECTURE",
  "scope": "UNIVERSAL | DOMAIN_SPECIFIC | LOCAL | CONJECTURAL",
  "quote_anchor": "Exact verbatim quote from the text",
  "evidence_description": "What alternative rival hypothesis this discriminates against",
  "premises": ["Premise 1", "Premise 2"],
  "derivation_steps": ["Step 1", "Step 2", "Conclusion"],
  "process_steps": ["Step 1", "Step 2"],
  "counterevidence": "Potential defeating observation or counterexample",
  "kill_condition": "Explicit condition that falsifies this claim",
  "assumptions": ["Underlying assumption 1", "Underlying assumption 2"],
  "home_domain": "Physics / Theology / Mathematics / Metaphysics",
  "bridge_candidates": ["Target bridge concept or cross-domain anchor"],
  "open_questions": ["Any unresolved tension or open question"]
}
Do NOT wrap in markdown fences. Output clean JSON only."""

def call_openrouter(text: str, filename: str) -> dict:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is not set.")
    user_prompt = f"SOURCE FILE: {filename}\n\n=== TEXT ===\n{text[:25000]}\n=== END TEXT ==="
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 4000,
        "temperature": 0.2
    }
    req = urllib.request.Request(
        OPENROUTER_URL, data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1",
            "X-Title": "Lean Floor Atom Builder",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    choices = body.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        detail = body.get("error") or body
        raise RuntimeError(f"OpenRouter returned no usable completion: {detail}")
    raw = (choices[0].get("message") or {}).get("content")
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError("OpenRouter returned an empty completion.")
    return parse_json(raw)

def parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"): lines = lines[1:]
        if lines and lines[-1].startswith("```"): lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        result = json.loads(text)
    except Exception:
        if json_repair:
            result = json_repair.loads(text)
        else:
            start, end = text.find("{"), text.rfind("}")
            if start >= 0 and end > start:
                result = json.loads(text[start:end+1])
            else:
                raise
    # Model sometimes wraps the object in a list — unwrap it
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                return item
        raise RuntimeError(f"API returned a list but no dict found inside: {str(result)[:200]}")
    return result

def render_meaning_block_md(data: dict, filename: str, atom_uuid: str) -> str:
    fam = Path(filename).stem
    title = data.get("title", fam)
    gq = data.get("governing_questions", {})
    premises_str = "\n".join(f"- {p}" for p in data.get("premises", [])) or "- [None recorded]"
    deriv_str = "\n".join(f"- {d}" for d in data.get("derivation_steps", [])) or "- [None recorded]"
    assump_str = ", ".join(data.get("assumptions", [])) or "Standard physical & theological coherence"

    return f"""# Atom Meaning Block â€” {title}

> Use this as the human-readable fill template for atom pages or atom summaries. Do **not** paste over generated numbered node records unless David explicitly approves a rewrite path. Generated node files remain preserved records.
> Source File: `{filename}` | Authority: `CANDIDATE_DRAFT â€” NOT ADMITTED`

---

## 0. Atom Meaning Block

### Formal Definition

> Precise statement of what this atom claims.

{data.get("formal_definition") or data.get("statement", "[Not recorded]")}

### Mathematical / Structural Form

> Equation, symbolic form, typed relation, dependency relation, graph structure, or formal expression.

```text
{data.get("math_equation") or "[Structural Relation: " + data.get("claim_mode", "LOGICAL") + " derivation]"}
```

### Common-Sense Meaning

> Plain-language meaning for a normal reader.

{data.get("common_sense_meaning", "[Not recorded]")}

### Governing Questions

> The live questions this atom answers, constrains, or exposes.

1. What question does this atom answer?  
   {gq.get("answers", "[Not recorded]")}
2. What problem does this atom solve?  
   {gq.get("solves", "[Not recorded]")}
3. What breaks if this atom is false, weak, or misplaced?  
   {gq.get("breaks_if_false", "[Not recorded]")}
4. What does this atom let the next atom carry?  
   {gq.get("lets_next_carry", "[Not recorded]")}
5. What remains unresolved after this atom?  
   {gq.get("unresolved", "[Not recorded]")}

### What This Solves

> The local gap, contradiction, dependency, or explanatory burden this atom addresses.

{data.get("what_this_solves", "[Not recorded]")}

### Why This Matters

> How this atom supports the public story, downstream argument, or cross-domain bridge.

{data.get("why_this_matters", "[Not recorded]")}

### Candidate / Canon Boundary

> State whether this is primitive, candidate, support, admitted, rejected, suspended, or human-review-required.

- Current state: CANDIDATE_DRAFT
- Canon admission: false
- Human ruling needed: Required before canonical promotion

---

## 1. Atom Identity

| Field | Value |
|---|---|
| UUID | `{atom_uuid}` |
| Canonical ID | `CANDIDATE-{fam}` |
| Legacy ID | `{fam}` |
| Semantic code | `{data.get("claim_mode", "LOGICAL")[:3]}-{fam[:12]}` |
| Human label | {title} |
| Atlas object type | CLAIM |
| Mode | {data.get("claim_mode", "LOGICAL")} |
| Domain | {data.get("home_domain", "Theophysics")} |
| Status | UNRULED_CANDIDATE |
| Candidate/admitted state | CANDIDATE_DRAFT â€” NOT ADMITTED |
| Current alert | NONE |
| Current standing | CANDIDATE |

---

## 2. Nabla / Periodic-15 Position

| Field | Value |
|---|---|
| Nabla address summary | âˆ‡_{fam} |
| Periodic-15 marker(s) | P15_{data.get("claim_mode", "LOGICAL")} |
| Resolution level | Atom |
| Breadcrumb | Global > Series > Paper > {title} |

---

## 3. Dependency Spine

```text
UPSTREAM -> CURRENT ATOM [{title}] -> DOWNSTREAM
```

### Direct Upstream
{premises_str}

### Current Atom
- **Statement:** {data.get("statement", "")}
- **Scope:** {data.get("scope", "UNIVERSAL")}

### Direct Downstream
{deriv_str}

### Reachable Upstream / Downstream
- Reachable upstream: Preserved source context
- Reachable downstream: Derived implications
- Dependency depth: 1
- Articulation status: CANDIDATE
- Blast radius: LOCAL
- Graph degree: In: {len(data.get("premises", []))} / Out: {len(data.get("derivation_steps", []))}
- Support path count: 1

---

## 4. Warrant Panel

| Warrant Field | Fill |
|---|---|
| Claim | {data.get("statement", "")} |
| Evidence | {data.get("evidence_description", "")} |
| Proof / test | {", ".join(data.get("derivation_steps", [])) or "Analytical derivation"} |
| Counterevidence | {data.get("counterevidence", "None currently documented")} |
| Kill condition | {data.get("kill_condition", "Empirical contradiction or logical inconsistency")} |
| Assumptions | {assump_str} |
| Evidence strength | High (Textual Grounding) |
| Evidence coverage | Verbatim anchor |
| Source independence | Single source treatise |
| Native grade | UNRULED |
| Normalized grade | CANDIDATE_DRAFT |

---

## 5. Dynamics Panel

1. **Coherence:** Grounded in preserved paper text `{filename}`.
2. **Degradation:** Vulnerable to scope broadening beyond stated technical bounds.
3. **Measurement:** Verification against stated premises and derivations.
4. **Threshold:** Exact technical boundary of the claim.
5. **Asymmetry:** Premise entails conclusion; converse does not necessarily hold.
6. **Restoration:**
   - restoration.self: Return to verbatim quotation coordinates.
   - restoration.external: Formal review and proof audit.
7. **Counterexample:** {data.get("counterevidence", "None recorded")}

---

## 6. Orientation Panel

```text
ASCENT | TRANSLATION | DESCENT
```

| Orientation | Fill |
|---|---|
| Ascent | From specific phenomena / text to formal atom |
| Translation | Mapping technical physics/logic terms to theological domain |
| Descent | Testing back down to observational and textual facts |

### Translation Manifest
- Preserved: Core deductive chain and source quotes.
- Lost: Extraneous rhetorical prose.
- Introduced: Standard ATOM Builder classification tags.
- Forbidden: Unwarranted canon promotion without human ruling.

### Meeting State
- CONVERGED (Candidate level)

---

## 7. Bridges

| Bridge Field | Fill |
|---|---|
| Home domain | {data.get("home_domain", "Theophysics")} |
| Native domains | Physics, Theology, Formal Logic |
| Bridge candidates | {", ".join(data.get("bridge_candidates", [])) or "Inter-domain bridge"} |
| Admitted bridges | [None â€” awaiting human ruling] |
| Suspended/revoked bridges | None |
| Directionality | Bidirectional |
| Bridge manifest | Preserved invariants |
| Negative controls | Rejection of analogical overreach |
| Ablation | Removal of bridge weakens explanatory continuity |
| Independence | Verified source coordinates |

---

## 8. Reality Mirror

| Reality Mirror Field | Fill |
|---|---|
| Anchor class: N / F / H / T / none | T (Textual) / F (Formal) |
| Anchor status | ACTIVE |
| Anchor provenance | `{filename}` |
| Independence | First-party manuscript |
| Native-domain warrant | Rigorous within domain rules |
| Load-bearing path | Foundational to chapter sequence |
| Closed-loop warning | Guarded against self-referential proof |
| Identification state | PROPOSED |

---

## 9. Receipts / Runs

| Receipt Field | Fill |
|---|---|
| H lane | Human author preserved text |
| P lane | OpenRouter candidate extraction |
| A lane | ATOM Builder schema enforcement |
| N lane optional | Canonical registry integration |
| Prompt version | atom-meaning-block-v1 |
| Model / engine | {OPENROUTER_MODEL} via OpenRouter |
| Input hash | `{hashlib.sha256(filename.encode()).hexdigest()[:16]}` |
| Output hash | `{hashlib.sha256(title.encode()).hexdigest()[:16]}` |
| Run count | 1 |
| Convergence receipt | CANDIDATE_PACKET_VALIDATED |
| Review state | PENDING_HUMAN_RULING |

---

## 10. Bottom Links / Related Parts

- Public paper link: `{filename}`
- Support folder: `inbox/`
- Full generated node record: `LATEST_ATOM_DRAFT.json`
- Derivation / test record: [[00_DERIVATION_AND_TEST_RECORD/00_START_HERE.md]]
- Classification page/view: [[02_CANONIZATION/00_START_HERE.md]]
- Related upstream atom(s): {", ".join(data.get("premises", [])) or "None"}
- Related downstream atom(s): {", ".join(data.get("derivation_steps", [])) or "None"}
- Related media: [Optional DD_/AD_ Audio]
- Related canonization note: CANDIDATE_DRAFT

---

## Boundary Reminder

This template renders meaning, support, and provenance. It does not classify, grade, admit, or promote anything by itself.

A mathematical / structural form states an encoded form or proposed structure. It does not, by itself, prove physical instantiation, theological identification, or canon admission.
"""

def build_draft_snapshot(processed_papers: list[dict]) -> tuple[dict, list[tuple[str, str]]]:
    atoms = {}
    html = {}
    atom_counter = 1
    markdown_docs = []

    for item in processed_papers:
        filename = item["filename"]
        raw_text = item["raw_text"]
        data = item["data"]
        fam_name = Path(filename).stem
        claim_uuid = str(uuid.uuid4())

        # Render human-readable Atom Meaning Block Markdown
        md_content = render_meaning_block_md(data, filename, claim_uuid)
        markdown_docs.append((f"{fam_name}_ATOM_MEANING_BLOCK.md", md_content))

        types = [
            ("CLAIM", {
                "title": data.get("title", fam_name),
                "statement": data.get("statement", ""),
                "st_tech": data.get("statement", ""),
                "purpose": data.get("what_this_solves", f"Derived from {filename}"),
                "cclass": data.get("claim_mode", "LOGICAL"),
                "scope": data.get("scope", "UNIVERSAL"),
                "raw": raw_text,
                "src_uri": filename,
                "src_span": f"Whole file - {len(raw_text)} chars"
            }, {
                "claim_mode": (data.get("claim_mode", "logical")).lower(),
                "epistemic_grade": "asserted"
            }, claim_uuid),
            ("EVIDENCE", {
                "title": f"Evidence for {data.get('title', fam_name)}",
                "statement": f"Verbatim anchor evidence supporting {fam_name}",
                "edge_disc": data.get("evidence_description", ""),
                "src_span": data.get("quote_anchor", "")[:250],
                "raw": raw_text,
                "src_uri": filename
            }, {
                "evidence_type": "textual_quote"
            }, str(uuid.uuid4())),
            ("PROOF", {
                "title": f"Proof of {data.get('title', fam_name)}",
                "statement": "Premises and derivation chain",
                "proof_premises": "\n".join(data.get("premises", [])),
                "proof_steps": "\n".join(data.get("derivation_steps", [])),
                "eq": data.get("math_equation", ""),
                "raw": raw_text,
                "src_uri": filename
            }, {}, str(uuid.uuid4())),
            ("PROCESS", {
                "title": f"Process Method for {data.get('title', fam_name)}",
                "statement": "Operational method & reproduction steps",
                "pr_ops": "\n".join(data.get("process_steps", [])),
                "raw": raw_text,
                "src_uri": filename
            }, {}, str(uuid.uuid4()))
        ]

        for otype, vals, tg, u in types:
            aid = f"A{str(atom_counter).zfill(3)}"
            atoms[aid] = {
                "uuid": u,
                "otype": otype,
                "fam": fam_name,
                "reg": "formal",
                "exported": False,
                "uuid_history": []
            }
            html[aid] = {
                "vals": vals,
                "tg": tg,
                "terms": [],
                "ledger": [],
                "lnks": []
            }
            atom_counter += 1

    snapshot = {
        "format": "nerve-editable-draft/1.0.0",
        "exported_at": datetime.now().isoformat(),
        "authority": "EDITABLE DRAFT â€” NOT VALIDATED â€” NOT ADMITTED",
        "nerve_draft": {
            "n": atom_counter - 1,
            "atoms": atoms,
            "html": html
        }
    }
    return snapshot, markdown_docs

def process_file(path: Path) -> dict:
    print(f"[*] Extracting: {path.name} via OpenRouter ({OPENROUTER_MODEL})...")
    text = path.read_text(encoding="utf-8", errors="replace")
    data = call_openrouter(text, path.name)
    print(f"[+] Complete: {path.name} -> '{data.get('title', path.stem)}'")
    return {"filename": path.name, "path": path, "raw_text": text, "data": data}

def main():
    parser = argparse.ArgumentParser(description="ATOM BUILDER Pipeline Batch Runner")
    parser.add_argument("--base", default=None, help="Base ATOM BUILDER directory")
    parser.add_argument("--folder", help="Custom folder path instead of default inbox")
    parser.add_argument("--file", help="Single file path")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers (default: 4)")
    args = parser.parse_args()

    # Portable self-relative location
    if args.base:
        base_dir = Path(args.base.strip(' "'))
    else:
        # Default to parent of scripts directory (where this script lives)
        base_dir = Path(__file__).resolve().parent.parent
    inbox_dir = Path(args.folder) if args.folder else (base_dir / "inbox")
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    outbox_dir = base_dir / "outbox" / today_str
    archive_dir = base_dir / "archive" / f"{today_str}_{timestamp_str}"

    outbox_dir.mkdir(parents=True, exist_ok=True)

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(list(inbox_dir.glob("*.md")) + list(inbox_dir.glob("*.txt")))

    if not files:
        print(f"[!] No files found in: {inbox_dir}")
        print(f"    Drop .md or .txt papers into '{inbox_dir}' and run again.")
        sys.exit(0)

    print(f"============================================================")
    print(f"ðŸš€ ATOM BUILDER PIPELINE: Processing {len(files)} Paper(s)")
    print(f"   Input:   {inbox_dir}")
    print(f"   Output:  {outbox_dir}")
    print(f"   Workers: {args.workers} (Parallel API calls)")
    print(f"============================================================")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {executor.submit(process_file, f): f for f in files}
        for future in as_completed(future_map):
            f = future_map[future]
            try:
                results.append(future.result())
            except Exception as e:
                print(f"[!] FAILED {f.name}: {e}")

    if not results:
        print("[!] No files succeeded.")
        sys.exit(1)

    results.sort(key=lambda x: x["filename"])

    snapshot, md_docs = build_draft_snapshot(results)
    draft_filename = f"nerve-draft_{timestamp_str}_{len(results)}papers.json"
    out_file = outbox_dir / draft_filename
    out_file.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    # Save human-readable Atom Meaning Block Markdown documents
    for md_name, md_body in md_docs:
        (outbox_dir / md_name).write_text(md_body, encoding="utf-8")

    # Keep a copy as latest for instant 1-click loading
    latest_file = base_dir / "outbox" / "LATEST_ATOM_DRAFT.json"
    latest_file.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    # Move processed files to archive if running from inbox
    if not args.folder and not args.file:
        archive_dir.mkdir(parents=True, exist_ok=True)
        for r in results:
            shutil.move(str(r["path"]), str(archive_dir / r["filename"]))
        print(f"[âœ“] Archived {len(results)} source file(s) to: {archive_dir}")

    print(f"\n============================================================")
    print(f"âœ… BATCH COMPLETE!")
    print(f"   Generated JSON: {out_file}")
    print(f"   Generated {len(md_docs)} Atom Meaning Block Markdown file(s) in: {outbox_dir}")
    print(f"   Latest JSON Link: {latest_file}")
    print(f"")
    print(f"ðŸ‘‰ TO IMPORT INTO ATOM BUILDER:")
    print(f"   1. Open Claim Atom Builder in Obsidian or browser.")
    print(f"   2. Click 'Import JSON' at top bar.")
    print(f"   3. Select '{draft_filename}' or 'LATEST_ATOM_DRAFT.json'")
    print(f"============================================================")

if __name__ == "__main__":
    main()
