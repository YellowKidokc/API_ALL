#!/usr/bin/env python3
"""
process_axiom_pipeline.py
=========================
Dedicated High-Speed Parallel Engine for AXIOMS (Sealed v2.3 Chain + 6-Layer Lens).

Takes Axiom source notes from 'inbox' (or a series folder):
1. Runs OpenRouter in parallel (4 workers default).
2. OpenRouter extracts:
   - Front Identity (Canonical ID, Legacy ID, Core Set, Tier, Epistemic status)
   - Formal & Self-Refutation Math (LaTeXKaTeX math blocks, Lean/Z3 boundary)
   - 5 Governing Questions
   - Six-Layer Explanatory Lens (Rhetorical, Metaphysical, Theological, Scientific, Mathematical, Encyclopedia)
   - Dependency Spine (Upstream, Blast radius, Downstream v2.3 links)
   - Warrant Panel (Claim, Evidence, Proof, Counterevidence, Kill condition)
   - Dynamics & Orientation (Ascent, Translation, Descent)
   - Bridges & Reality Mirror
3. Generates:
   - '[Axiom]_AXIOM_COMPANION.md' (Exact match to David's A1.1 canonical template)
   - 'axiom-draft-*.json' (Structured JSON with all axiom layers)
   - 'nerve-draft-*.json' (Compatible draft snapshot for ATOM Builder Import)
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

AXIOM_PROMPT = """You are the Lead Ontological Architect and Canonization Engineer for Theophysics.
Analyze the provided Axiom text and extract the rigorous components for the canonical AXIOM COMPANION template.

Follow these strict rules:
1. "God Is" is the admitted root of the system. Do not pretend to derive God from a secular premise or symbols alone.
2. Formulate the minimal formal and mathematical statement (e.g., âˆƒx, Domain != âˆ…) and self-refutation trap if applicable.
3. Provide the full Six-Layer Explanatory Lens.
4. Answer the 5 Governing Questions without dodging.

Return ONLY valid JSON matching this exact structure:
{
  "canonical_id": "e.g. A1.1",
  "legacy_id": "e.g. AX-001",
  "human_label": "e.g. Existence",
  "epistemic_status": "primitive | core_axiom | derived_lemma | definition",
  "v2_3_tier": "Tier 0: Roots / no dependencies | Tier 1 | Tier 2",
  "domain": "Primordial | Physical | Metaphysical | Informational",
  "formal_definition": "Precise formal definition of what this axiom claims",
  "math_core": "e.g. \\\\exists x \\\\quad \\\\mathrm{Domain} \\\\neq \\\\varnothing",
  "math_word_equation": "Plain meaning of the mathematical core",
  "self_refutation_proof": "Step-by-step logic showing why denying this presupposes it",
  "common_sense_meaning": "Plain-language explanation for a normal reader",
  "governing_questions": {
    "answers": "What question does this atom answer?",
    "solves": "What problem does this atom solve?",
    "breaks_if_false": "What breaks if this atom is false, weak, or misplaced?",
    "lets_next_carry": "What does this atom let the next atom carry?",
    "unresolved": "What remains unresolved after this atom?"
  },
  "what_this_solves": "The empty-domain problem or explanatory burden this addresses",
  "why_this_matters": "Why this must be explicit rather than smuggled in",
  "six_layer_lens": {
    "rhetorical": "Human/linguistic trap showing the sentence destroys itself if denied",
    "metaphysical": "Ontological baseline and comparison with secular realism/idealism",
    "theological": "Theological mapping (e.g. creation ex nihilo) and explicit boundary reminder",
    "scientific": "How physics/science presupposes this (e.g. Hilbert space, quantum vacuum)",
    "mathematical": "Formal logic/set theory encoding without deriving from deeper premises",
    "encyclopedia": "External philosophy reference (Leibniz, Heidegger, Buddhist sunyata distinction)"
  },
  "dependency_spine": {
    "direct_upstream": ["None (foundational) or listed nodes"],
    "direct_downstream": ["Next nodes in chain e.g. A1.2"],
    "blast_radius": "STRUCTURAL | LOCAL | INERT"
  },
  "warrant": {
    "claim": "The exact claim statement",
    "evidence": "Self-refutation trap, metaphysical floor, formal primitive",
    "proof_test": "Formal logic proof or primitive specification",
    "counterevidence": "Radical nothingness challenges or rival stopping points",
    "kill_condition": "Show absolute nothingness is coherent and stable",
    "assumptions": ["Assumptions required for assertion"]
  },
  "orientation": {
    "ascent": "From ordinary experience upward to the minimal primitive",
    "translation": "Translates ordinary language into formal logic notation",
    "descent": "Returns formal primitive back to common-sense discourse"
  },
  "bridges": {
    "home_domain": "Primordial / foundational ontology",
    "native_domains": ["Philosophy", "Formal logic"],
    "bridge_candidates": ["Theology: creation", "Physics: structured state prerequisite", "Information: probability space"]
  }
}
Do NOT wrap in markdown fences. Output clean JSON only."""

def call_openrouter(text: str, filename: str) -> dict:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is not set.")
    user_prompt = f"AXIOM SOURCE FILE: {filename}\n\n=== TEXT ===\n{text[:25000]}\n=== END TEXT ==="
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": AXIOM_PROMPT},
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
            "X-Title": "Lean Floor Axiom Builder",
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
        return json.loads(text)
    except Exception:
        if json_repair:
            return json_repair.loads(text)
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end+1])
        raise

def render_axiom_companion_md(data: dict, filename: str, source_sha: str) -> str:
    cid = data.get("canonical_id", "A1.x")
    label = data.get("human_label", Path(filename).stem)
    gq = data.get("governing_questions", {})
    lens = data.get("six_layer_lens", {})
    spine = data.get("dependency_spine", {})
    warrant = data.get("warrant", {})
    orient = data.get("orientation", {})
    bridges = data.get("bridges", {})

    return f"""# {cid} â€” {label}

> Human-readable companion for the generated production record: [[{filename}]]  
> Sealed chain authority: [[00_DERIVATION_AND_TEST_RECORD/AXIOM_CHAIN_MASTER_v2.3_SEALED.md]]

---

## 0. Front Identity Layer

### 0A. Production-Confirmed Identity

| Field | Value |
|---|---|
| Production file | [[{filename}]] |
| Canonical ID | `{cid}` |
| Legacy ID | `{data.get("legacy_id", "AX-xxx")}` |
| Human label | {label} |
| Mode | `AX_CORE` |
| Atlas object type | Axiom |
| Epistemic status | `{data.get("epistemic_status", "primitive")}` |
| Domain | {data.get("domain", "Primordial")} |
| Source SHA-256 | `{source_sha}` |
| Generated-source date | {datetime.now().strftime("%Y-%m-%d")} |
| Canonical source filename | `{filename}` |

### 0B. Sealed v2.3 Chain Placement

| Field | Value |
|---|---|
| Strict core status | {data.get("epistemic_status", "Bedrock primitive")} |
| v2.3 core set | Sealed Axiom Chain v2.3 |
| Tier | {data.get("v2_3_tier", "Tier 0: Roots / no dependencies")} |
| Dependency status | {", ".join(spine.get("direct_upstream", ["None"]))} |
| Derived status | Foundational / Not derived |
| v2.3 caution | Tiers are thematic groupings, not strict topological layers. |

---

## 1. Atom Meaning Block

### Formal Definition

{data.get("formal_definition", "")}

### Mathematical / Structural Form

> [!math] Mathematical Core
> $${data.get("math_core", "\\\\exists x \\\\quad \\\\mathrm{Domain} \\\\neq \\\\varnothing")}$$
>
> **Word equation:** {data.get("math_word_equation", "There is at least one entity in the domain under consideration.")}

> [!math] Self-Refutation Form
> {data.get("self_refutation_proof", "Attempting to assert the negation of this proposition requires a proposition, truth-condition, or asserting entity, thereby presupposing the domain.")}

Boundary:
> This formal structure establishes the minimal nonempty-domain claim. It does not identify what exists, why it exists, or whether the existent ground is God.

### Common-Sense Meaning

{data.get("common_sense_meaning", "")}

### Governing Questions

1. **What question does this atom answer?**  
   {gq.get("answers", "")}

2. **What problem does this atom solve?**  
   {gq.get("solves", "")}

3. **What breaks if this atom is false, weak, or misplaced?**  
   **{spine.get("blast_radius", "STRUCTURAL")}:** {gq.get("breaks_if_false", "")}

4. **What does this atom let the next atom carry?**  
   {gq.get("lets_next_carry", "")}

5. **What remains unresolved after this atom?**  
   {gq.get("unresolved", "")}

### What This Solves

{data.get("what_this_solves", "")}

### Why This Matters

{data.get("why_this_matters", "")}

### Candidate / Canon Boundary

- Current production status: `AX_CORE`, primitive.
- Sealed v2.3 status: Core primitive candidate.
- Canon admission by this page: None. This page is a support companion, not a canon ruling.
- Theological root boundary: "God Is" is the project's admitted axiom/root. Formal symbols state the floor from which the admitted root is engaged.

---

## 2. Six-Layer Explanatory Lens

### 2.1 Rhetorical / Human Layer
{lens.get("rhetorical", "")}

### 2.2 Metaphysical Layer
{lens.get("metaphysical", "")}

### 2.3 Theological Layer
{lens.get("theological", "")}

### 2.4 Scientific Layer
{lens.get("scientific", "")}

### 2.5 Mathematical / Formal Layer
{lens.get("mathematical", "")}

### 2.6 Encyclopedia / External-Reference Layer
{lens.get("encyclopedia", "")}

---

## 3. Dependency Spine

```text
UPSTREAM [{", ".join(spine.get("direct_upstream", ["NONE"]))}] 
  -> CURRENT ATOM [{cid} â€” {label}] 
  -> DOWNSTREAM [{", ".join(spine.get("direct_downstream", ["NEXT"]))}]
```

- Dependency depth: 0 â€” Root / primitive
- Blast radius: **{spine.get("blast_radius", "STRUCTURAL")}**

---

## 4. Warrant Panel

| Warrant Field | Fill |
|---|---|
| Claim | {warrant.get("claim", "")} |
| Evidence | {warrant.get("evidence", "")} |
| Proof / test | {warrant.get("proof_test", "")} |
| Counterevidence | {warrant.get("counterevidence", "")} |
| Kill condition | {warrant.get("kill_condition", "")} |
| Assumptions | {", ".join(warrant.get("assumptions", []))} |
| Evidence strength | Very strong as a presuppositional floor |
| Native grade | `AX_CORE`; primitive |
| Normalized grade | v2.3 strict core primitive |

---

## 5. Orientation Panel

```text
ASCENT | TRANSLATION | DESCENT
```

| Orientation | Fill |
|---|---|
| Ascent | {orient.get("ascent", "")} |
| Translation | {orient.get("translation", "")} |
| Descent | {orient.get("descent", "")} |

---

## 6. Bridges

| Bridge Field | Fill |
|---|---|
| Home domain | {bridges.get("home_domain", "Primordial ontology")} |
| Native domains | {", ".join(bridges.get("native_domains", ["Philosophy", "Logic"]))} |
| Bridge candidates | {", ".join(bridges.get("bridge_candidates", []))} |
| Admitted bridges | [None â€” awaiting human ruling] |

---

## Boundary Reminder

This page renders meaning, support, and provenance for a human reader. It does not classify, grade, admit, or promote anything by itself.
"""

def process_file(path: Path) -> dict:
    print(f"[*] Processing Axiom: {path.name} via OpenRouter ({OPENROUTER_MODEL})...")
    text = path.read_text(encoding="utf-8", errors="replace")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    data = call_openrouter(text, path.name)
    cid = data.get("canonical_id", path.stem)
    print(f"[âœ“] Completed Axiom: {path.name} -> '{cid} {data.get('human_label', '')}'")
    return {"filename": path.name, "path": path, "raw_text": text, "sha": sha, "data": data}


def build_axiom_draft_snapshot(results: list[dict]) -> dict:
    atoms = {}
    html = {}
    counter = 1

    for r in results:
        data = r["data"]
        cid = data.get("canonical_id", f"A{counter}")
        label = data.get("human_label", "Axiom")
        aid = f"A{str(counter).zfill(3)}"
        claim_uuid = str(uuid.uuid4())
        atoms[aid] = {
            "uuid": claim_uuid,
            "otype": "CLAIM",
            "fam": cid,
            "reg": "math",
            "exported": False,
            "uuid_history": []
        }
        vals = {
            "fam": cid,
            "st_tech": data.get("formal_definition", ""),
            "st_plain": data.get("common_sense_meaning", ""),
            "eq": data.get("math_core", ""),
            "scope": data.get("domain", "Primordial"),
            "purpose": data.get("what_this_solves", ""),
            "why": data.get("why_this_matters", ""),
            "negation": data.get("warrant", {}).get("counterevidence", ""),
            "kill": data.get("warrant", {}).get("kill_condition", ""),
            "counter": data.get("warrant", {}).get("counterevidence", ""),
            "e_dep": ", ".join(data.get("dependency_spine", {}).get("direct_upstream", [])),
            "blast": data.get("dependency_spine", {}).get("blast_radius", ""),
            "raw": r.get("raw_text", ""),
            "src_uri": r.get("filename", ""),
            "src_span": f"Canonical Axiom Node {cid}"
        }
        terms = []
        if data.get("math_core"):
            terms.append({
                "m": data.get("math_core", ""),
                "p": data.get("math_word_equation", ""),
                "t": data.get("six_layer_lens", {}).get("theological", "")
            })
        html[aid] = {
            "vals": vals,
            "tg": {
                "cclass": "floor-axiom",
                "status": "draft",
                "terminus": "PRIMITIVE" if "primitive" in str(data.get("epistemic_status", "")).lower() else "NONE"
            },
            "terms": terms,
            "ledger": [],
            "lnks": []
        }
        counter += 1

    return {
        "format": "nerve-editable-draft/1.0.0",
        "exported_at": datetime.now().isoformat(),
        "authority": "EDITABLE DRAFT — NOT VALIDATED — NOT ADMITTED",
        "nerve_draft": {
            "n": counter - 1,
            "atoms": atoms,
            "html": html
        }
    }

def main():
    parser = argparse.ArgumentParser(description="AXIOM COMPANION Parallel Pipeline Runner")
    parser.add_argument("--base", default=None, help="Base ATOM BUILDER directory")
    parser.add_argument("--folder", help="Custom folder containing Axiom markdown files")
    parser.add_argument("--file", help="Single Axiom file")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers (default: 4)")
    args = parser.parse_args()

    # Portable self-relative location
    if args.base:
        base_dir = Path(args.base.strip(' "'))
    else:
        # Default to parent of scripts directory (where this script lives)
        base_dir = Path(__file__).resolve().parent.parent
    inbox_dir = Path(args.folder) if args.folder else (base_dir / "INBOX")
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    outbox_dir = base_dir / "OUTBOX" / f"{today_str}_AXIOMS"
    outbox_dir.mkdir(parents=True, exist_ok=True)

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(list(inbox_dir.glob("*.md")) + list(inbox_dir.glob("*.txt")))

    if not files:
        print(f"[!] No files found in: {inbox_dir}")
        sys.exit(0)

    print(f"============================================================")
    print(f"ðŸ›ï¸ AXIOM COMPANION PIPELINE: Processing {len(files)} Axiom(s)")
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
                print(f"[!] Error on {f.name}: {e}")

    if not results:
        print("[!] No axioms were successfully processed.")
        sys.exit(1)

    results.sort(key=lambda x: x["filename"])

    for r in results:
        data = r["data"]
        cid = data.get("canonical_id", Path(r["filename"]).stem).replace(".", "_")
        md_filename = f"{cid}_{data.get('human_label', 'Axiom')}_COMPANION.md"
        md_text = render_axiom_companion_md(data, r["filename"], r["sha"])
        (outbox_dir / md_filename).write_text(md_text, encoding="utf-8")

    # Save aggregated raw JSON
    json_filename = f"axioms_raw_{timestamp_str}.json"
    (outbox_dir / json_filename).write_text(json.dumps([r["data"] for r in results], indent=2), encoding="utf-8")

    # Save Nerve-importable draft JSON
    draft_snapshot = build_axiom_draft_snapshot(results)
    nerve_draft_file = outbox_dir / f"nerve-draft_{timestamp_str}_axioms.json"
    nerve_draft_file.write_text(json.dumps(draft_snapshot, indent=2), encoding="utf-8")
    (outbox_dir / "LATEST_AXIOM_DRAFT.json").write_text(json.dumps(draft_snapshot, indent=2), encoding="utf-8")
    print(f"   Exported Nerve Draft JSON: {nerve_draft_file.name}")

    print(f"\n============================================================")
    print(f"âœ… AXIOM BATCH COMPLETE!")
    print(f"   Successfully generated {len(results)} Axiom Companion file(s) in:")
    print(f"   {outbox_dir}")
    print(f"============================================================")

if __name__ == "__main__":
    main()
