#!/usr/bin/env python3
"""
organize_and_retake_folders.py
Gently rereads processed documents in OUTBOX:
1. Normalizes and validates titles (removes raw slug artifacts, formatting noise).
2. Preserves the exact original incoming structure under OUTBOX/00_ORIGINAL_STRUCTURE/
3. Categorizes and places copies into deep, explicit thematic domain folders under OUTBOX/01_CATEGORIZED_DOMAINS/
   (supporting multi-domain copies when a paper spans 2 or 3 distinct domains).
4. Builds three independent discovery facets under OUTBOX/03_DISCOVERY_FACETS/:
   technical domain, precise subject tag, and plain-language reader category.
5. Emits a transparent JSON & CSV audit receipt of all actions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
INTAKE_ROOT = SCRIPTS_DIR.parent
INBOX = INTAKE_ROOT / "INBOX"
OUTBOX = INTAKE_ROOT / "OUTBOX"
ORIGINALS_STRUCT = OUTBOX / "00_ORIGINAL_STRUCTURE"
CATEGORIZED_DIR = OUTBOX / "01_CATEGORIZED_DOMAINS"
FACETS_DIR = OUTBOX / "03_DISCOVERY_FACETS"
LOGS_DIR = SCRIPTS_DIR / "LOGS"
ROUTED_ROOT_NAMES = {
    "00_ORIGINAL_STRUCTURE", "01_CATEGORIZED_DOMAINS", "02_EVIDENCE_MATRIX",
    "03_DISCOVERY_FACETS",
}

# High-resolution domain definitions based on Theophysics architecture
DOMAINS = [
    {
        "folder": "01_COSMOLOGY_AND_GR/Friedmann_Chi_Coupling_and_H0_Tension",
        "keywords": ["friedmann", "cosmology", "h0", "dark energy", "recombination", "big bang", "expansion", "cosmic"],
    },
    {
        "folder": "02_QUANTUM_INFORMATION/Landauer_Bound_and_Decoherence_Loss",
        "keywords": ["landauer", "quantum", "decoherence", "entropy", "erasure", "shannon", "lindblad", "kolmogorov"],
    },
    {
        "folder": "03_LOGOS_EPISTEMOLOGY/Refiners_Fire_and_Knowledge_Wisdom_Transform",
        "keywords": ["refiner", "wisdom", "dunning-kruger", "omega", "epistemic", "pharisee", "humility", "fear of the lord", "grounding", "what grounds"],
    },
    {
        "folder": "04_NEUROTHEOLOGY_AND_DECISION/Three_Pathways_and_Neurochemical_Discernment",
        "keywords": ["three pathways", "dopamine", "vmpfc", "oxytocin", "cortisol", "conviction", "condemnation", "neuroscience", "emotion", "decision"],
    },
    {
        "folder": "05_BIBLICAL_HERMENEUTICS/Blood_Covenant_Quantum_Information_Carrier",
        "keywords": ["blood", "covenant", "leviticus", "kippur", "atonement", "negentropic input", "carrier wave"],
    },
    {
        "folder": "06_TRINITARIAN_ONTOLOGY/Three_Observers_and_Triune_Ground",
        "keywords": ["trinity", "triune", "three observers", "three-in-one", "father", "son", "logos", "number from being", "relation"],
    },
    {
        "folder": "07_SYSTEMIC_COHERENCE/Nine_Fruits_Generative_Grammar",
        "keywords": ["fruits", "love generates", "privation", "coherence", "destruction test", "generative grammar", "galatians"],
    },
    {
        "folder": "08_RECOVERY_AND_PSYCHOLOGY/12_Step_vs_CBT_Surrender_Mechanics",
        "keywords": ["addiction", "surrender", "12-step", "cbt", "alcoholics anonymous", "placebo", "psychology", "replication crisis"],
    },
    {
        "folder": "09_AXIOM_CHAIN_AND_FORMAL_AUDIT/Lean4_and_Z3_Verification_Routes",
        "keywords": ["axiom", "lean", "z3", "formal", "derivation", "proof", "ledger", "triage", "closure", "omega"],
    },
    {
        "folder": "10_WATCHER_AND_MEASUREMENT/Temporal_Direction_and_Boundary_Operators",
        "keywords": ["watcher", "temporal direction", "time", "boundary operator", "measurement", "arrow of time", "question that dies"],
    },
    {
        "folder": "11_STRUCTURAL_MECHANICS/X_Bracing_and_Ground_Anchor_Stability",
        "keywords": ["shed", "jack", "brace", "anchor", "hi-lift", "load", "foundation", "structural"],
    },
]

# Plain-language shelves answer "where would a normal reader look for this?"
# They are intentionally broader and more numerous than technical domains.
READER_CATEGORIES = [
    ("Arguments_for_God", ["argument for god", "existence of god", "god is", "ground of existence", "first cause"]),
    ("Starting_Points_and_Axioms", ["axiom", "starting point", "begins somewhere", "admitted root", "foundation"]),
    ("Truth_and_How_We_Know", ["truth", "epistem", "knowledge", "know", "rational accessibility"]),
    ("Logic_and_Reason", ["logic", "reason", "inference", "contradiction", "retorsion"]),
    ("Meaning_and_Purpose", ["meaning", "purpose", "teleology", "orientation", "why are we here"]),
    ("The_Trinity", ["trinity", "triune", "father", "son", "holy spirit", "perichoresis"]),
    ("Jesus_and_the_Logos", ["christ", "jesus", "logos", "word became flesh", "incarnation"]),
    ("Creation", ["creation", "created order", "creator", "genesis", "ordered gift"]),
    ("Physics_and_Faith", ["physics", "theophysics", "physical law", "cosmology", "quantum"]),
    ("Science_and_Religion", ["science", "scientism", "scientific method", "general revelation"]),
    ("Information_and_Reality", ["information", "shannon", "signal", "channel", "encoding"]),
    ("Mathematics_and_God", ["mathematics", "number", "arithmetic", "mathematical truth"]),
    ("Consciousness_and_the_Mind", ["consciousness", "mind", "observer", "subjective experience", "awareness"]),
    ("Free_Will", ["free will", "freedom", "agency", "choice", "trust-space"]),
    ("Why_Evil_Exists", ["evil", "theodicy", "privation", "vandal", "serpent"]),
    ("Suffering_and_Cost", ["suffering", "cost", "victim", "wound", "pain"]),
    ("Justice_and_Mercy", ["justice", "mercy", "moral ledger", "debt", "restitution"]),
    ("Sin_and_the_Fall", ["sin", "the fall", "fallen", "damaged receiver", "corruption"]),
    ("Grace_and_Repair", ["grace", "repair", "restoration", "external input", "negentropy"]),
    ("The_Cross_and_Atonement", ["cross", "atonement", "cost bearer", "sacrifice", "crucifixion"]),
    ("Forgiveness", ["forgiveness", "forgive", "reconciliation", "without erasure"]),
    ("Resurrection", ["resurrection", "empty tomb", "same one returns", "future has a body"]),
    ("Identity_and_Personhood", ["identity", "personhood", "same person", "continuity", "image of god"]),
    ("Life_After_Death", ["after death", "eternal life", "resurrection body", "survival"]),
    ("Love_and_Relationship", ["love", "relationship", "communion", "otherness", "relational"]),
    ("Character_and_Virtue", ["virtue", "character", "fruit of the spirit", "faithfulness", "self-control"]),
    ("Counterfeits_and_Deception", ["counterfeit", "deception", "lie", "false", "camouflage"]),
    ("Moral_Reality", ["moral", "goodness", "ought", "conscience", "amorality"]),
    ("Order_Chaos_and_Entropy", ["entropy", "order", "chaos", "decoherence", "disorder"]),
    ("Evidence_and_Proof", ["evidence", "proof", "establish", "falsif", "verification"]),
    ("Objections_and_Alternative_Views", ["objection", "rival", "alternative", "counterexample", "materialism"]),
    ("What_Lean_Proves", ["lean4", "lean proof", "formalization", "theorem", "proof assistant"]),
    ("What_Science_Can_and_Cannot_Say", ["does not prove", "does not establish", "method is not metaphysics", "boundary"]),
    ("Worldview_Comparison", ["worldview", "rival root", "comparative", "explanatory cost", "brute fact"]),
    ("The_Four_Debts", ["four debts", "existence debt", "distinction debt", "relation debt", "orientation debt"]),
    ("Measurement_and_the_Watcher", ["measurement", "watcher", "boundary operator", "observer effect", "temporal direction"]),
    ("Time_and_History", ["time", "history", "append-only", "temporal", "record"]),
    ("Bible_and_Revelation", ["scripture", "revelation", "bible", "i am", "self-disclosure"]),
    ("Human_Dignity", ["dignity", "human life", "person", "victim", "not reducible"]),
    ("Healing_and_Recovery", ["healing", "recovery", "restored life", "repair", "transformation"]),
    ("Trust_and_Faith", ["trust", "faith", "faithfulness", "belief", "reliance"]),
    ("Hope_and_New_Creation", ["hope", "new creation", "future", "renewal", "consummation"]),
    ("AI_and_Machine_Consciousness", ["artificial intelligence", "machine consciousness", "ai ", "nonbiological"]),
    ("Biology_and_Life", ["biology", "biological", "life", "organism", "genetic"]),
    ("Cosmology_and_Origins", ["cosmology", "big bang", "recombination", "universe", "origin"]),
    ("Practical_Christian_Life", ["christian life", "discipleship", "practice", "lived", "daily"]),
    ("Methods_and_Claim_Control", ["methodology", "claim control", "evidence tier", "epistemic mode", "audit"]),
    ("Open_Questions", ["open question", "unresolved", "remains open", "unknown", "would change verdict"]),
]


def unc_path(p: Path | str) -> str:
    s = str(p)
    if os.name != "nt":
        return s
    if s.startswith("\\\\?\\"):
        return s
    if s.startswith("\\\\"):
        return "\\\\?\\UNC\\" + s[2:]
    return "\\\\?\\" + os.path.abspath(s)


def sha256_path(path: Path | str) -> str:
    digest = hashlib.sha256()
    with open(unc_path(path), "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text_safe(path: Path | str) -> str:
    with open(unc_path(path), "r", encoding="utf-8", errors="replace") as stream:
        return stream.read()


def safe_copy(src: Path, dst: Path) -> dict[str, str]:
    """Create a verified copy only when needed; never overwrite different content."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    src_u = unc_path(src)
    source_hash = sha256_path(src)
    selected = dst
    if os.path.exists(unc_path(selected)):
        if sha256_path(selected) == source_hash:
            return {"destination": str(selected), "status": "present", "sha256": source_hash}
        selected = dst.with_name(f"{dst.stem}-{source_hash[:8]}{dst.suffix}")
        if os.path.exists(unc_path(selected)) and sha256_path(selected) == source_hash:
            return {"destination": str(selected), "status": "present_collision_copy", "sha256": source_hash}
    dst_u = unc_path(selected)
    with open(src_u, "rb") as f_in:
        with open(dst_u, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    if sha256_path(selected) != source_hash:
        raise RuntimeError(f"copy verification failed: {selected}")
    return {"destination": str(selected), "status": "created", "sha256": source_hash}


def load_receipt_titles() -> dict[str, str]:
    titles = {}
    csv_file = OUTBOX / "SEMANTIC_RENAME_RECEIPT_20260903-115501.csv"
    if csv_file.exists():
        try:
            with open(csv_file, encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    old = str(row.get("old_name") or "").strip()
                    title = str(row.get("title") or "").strip()
                    if old and title:
                        titles[old] = title
        except Exception:
            pass
    return titles


RECEIPT_TITLES = load_receipt_titles()


def clean_title(path: Path, raw: str | None, text: str) -> str:
    if path.name in RECEIPT_TITLES:
        return RECEIPT_TITLES[path.name]

    t = str(raw or "").strip().strip('"\'')
    if not t or t.lower() in ("ckg_evaluation:", "untitled", "none"):
        m = re.search(r"(?m)^#\s+(.+)$", text)
        if m and m.group(1).strip().lower() != "ckg_evaluation:":
            t = m.group(1).strip()
        else:
            stem = path.stem.removesuffix(".knowledge").removesuffix(".epistemic")
            stem = re.sub(r"^\d+[\-_a-zA-Z0-9]*[\-_]", "", stem)
            stem = re.sub(r"[\-_]\d+[\-_]\d+$", "", stem)
            t = stem.replace("-", " ").replace("_", " ").title()

    t = re.sub(r"^\d+[\-_a-zA-Z0-9]*[\-_]", "", t)
    t = re.sub(r"[\-_]\d+[\-_]\d+$", "", t)
    t = re.sub(r"\.(knowledge|epistemic|md|txt)$", "", t, flags=re.I)
    t = " ".join(t.split())
    if t.islower():
        t = t.title()
    return t


def title_filename(title: str, source_hash: str, source_name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-").lower()[:110] or "untitled"
    kind = ".epistemic.md" if source_name.lower().endswith(".epistemic.md") else (
        ".knowledge.md" if source_name.lower().endswith(".knowledge.md") else Path(source_name).suffix.lower()
    )
    return f"{slug}-{source_hash[:8]}{kind}"


def load_analysis(path: Path) -> dict[str, Any]:
    if not path.name.lower().endswith(".epistemic.md"):
        return {}
    sidecar = path.with_suffix(".json")
    try:
        value = json.loads(read_text_safe(sidecar))
        return value if isinstance(value, dict) else {}
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}


def infer_content_types(text: str) -> list[str]:
    lower = text.lower()
    if any(token in lower for token in ("user:", "assistant:", "human:", "claude:", "gemini:")):
        return ["AI_RELATIONAL"]
    if any(token in lower for token in ("```python", "```typescript", "api endpoint", "deployment", "schema", "configuration")):
        return ["INFRASTRUCTURE"]
    if any(token in lower for token in ("character", "scene", "chapter", "narrator", "plot")):
        return ["STORY_OR_NARRATIVE"]
    if any(token in lower for token in ("theophysics", "master equation", "axiom", "logos", "god", "grace")):
        return ["FRAMEWORK"]
    return ["GENERAL_RESEARCH"]


def infer_epistemic_roles(text: str) -> list[str]:
    lower = text.lower()
    rules = [
        ("CLAIM_OR_ARGUMENT", ("claim", "therefore", "argument", "conclusion")),
        ("EVIDENCE_OR_SOURCE", ("evidence", "citation", "source", "observed", "data")),
        ("FORMALIZATION", ("lean", "theorem", "lemma", "proof", "z3")),
        ("OBJECTION_OR_COUNTERMODEL", ("objection", "countermodel", "counterexample", "rival")),
        ("METHOD_OR_GOVERNANCE", ("method", "workflow", "schema", "canon", "audit")),
        ("STORY_OR_EXPLANATION", ("story", "narrative", "reader", "chapter")),
    ]
    found = [label for label, terms in rules if any(term in lower for term in terms)]
    return found[:4] or ["UNRESOLVED_ROLE"]


def parse_metadata(content: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", content, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"\'')
                if k in ("title", "type", "status", "canon_status", "source_file", "source_sha256", "run_id"):
                    meta[k] = v
                elif k in ("tags", "header_tags", "technical_domains", "subject_tags", "reader_categories"):
                    try:
                        parsed = json.loads(v)
                        values = parsed if isinstance(parsed, list) else [parsed]
                    except (json.JSONDecodeError, TypeError):
                        values = [item.strip().strip('"\'[]') for item in v.split(",") if item.strip()]
                    target = "tags" if k in ("tags", "header_tags") else k
                    meta[target] = [str(item).strip() for item in values if str(item).strip()]
    return meta


def folder_label(value: str, fallback: str = "Unassigned") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return cleaned[:90] or fallback


def unique_labels(values: list[str], limit: int = 3) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for value in values:
        label = folder_label(value)
        key = label.lower()
        if key not in seen:
            seen.add(key)
            found.append(label)
        if len(found) >= limit:
            break
    return found


def match_reader_categories(text_to_search: str) -> list[str]:
    lower = text_to_search.lower()
    scored = []
    for folder, keywords in READER_CATEGORIES:
        hits = sum(1 for keyword in keywords if keyword in lower)
        if hits:
            scored.append((folder, hits))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return [folder for folder, _ in scored[:3]] or ["General_Questions_About_Reality"]


def match_domains(text_to_search: str) -> list[str]:
    lower = text_to_search.lower()
    matched = []
    for d in DOMAINS:
        hits = sum(1 for kw in d["keywords"] if kw in lower)
        if hits >= 2 or (hits >= 1 and any(kw in lower for kw in d["keywords"][:2])):
            matched.append((d["folder"], hits))
    
    matched.sort(key=lambda x: x[1], reverse=True)
    if not matched:
        return ["99_GENERAL_AND_UNASSIGNED/Unclassified_Evidence"]
    
    selected = [matched[0][0]]
    for folder, hits in matched[1:3]:
        if hits >= 2:
            selected.append(folder)
    return selected


def organize_all(dry_run: bool = False, source_paths: list[Path] | None = None,
                 write_receipt: bool = True) -> dict[str, Any]:
    sources: list[Path] = []
    if source_paths is not None:
        sources.extend(Path(path) for path in source_paths)
    else:
        scan_roots = [OUTBOX / "00_ALL_PROCESSED_ARTICLES", OUTBOX / "04_EPISTEMIC_INTAKE_V2"]
        for scan_root in scan_roots:
            if scan_root.exists():
                for ext in ("*.knowledge.md", "*.epistemic.md"):
                    sources.extend(scan_root.rglob(ext))
        if not sources:
            for ext in ("*.knowledge.md", "*.epistemic.md"):
                sources.extend(OUTBOX.rglob(ext))

    filtered_sources: list[Path] = []
    seen_source_hashes: set[str] = set()
    for source in sources:
        if any(part in ROUTED_ROOT_NAMES for part in source.parts):
            continue
        try:
            source_hash = sha256_path(source)
        except OSError:
            continue
        if source_hash not in seen_source_hashes:
            seen_source_hashes.add(source_hash)
            filtered_sources.append(source)

    records: list[dict[str, Any]] = []
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    print(f"Discovered {len(filtered_sources)} processed document(s) in OUTBOX.")

    for path in filtered_sources:
        text = read_text_safe(path)
        meta = parse_metadata(text)
        analysis = load_analysis(path)
        call_1 = analysis.get("call_1") if isinstance(analysis.get("call_1"), dict) else {}
        call_3 = analysis.get("call_3") if isinstance(analysis.get("call_3"), dict) else {}

        raw_title = call_3.get("final_title") or call_1.get("document_title") or meta.get("title", "")
        clean = clean_title(path, raw_title, text)
        title_issues: list[str] = []
        if not clean or len(clean) < 4:
            title_issues.append("missing_or_too_short")
        if len(clean) > 140:
            title_issues.append("over_140_characters")
        if clean.lower() in {"untitled", "analysis", "document", "paper", "ckg evaluation"}:
            title_issues.append("generic_title")

        src_file = meta.get("source_file", "")
        rel_sub = Path()
        if src_file and "INBOX" in src_file:
            try:
                rel_sub = Path(src_file.split("INBOX", 1)[1].lstrip("\\/")).parent
            except Exception:
                rel_sub = Path()
        elif path.parent != OUTBOX:
            try:
                rel_sub = path.relative_to(OUTBOX).parent
            except Exception:
                rel_sub = Path()

        source_identity_hash = str(meta.get("source_sha256") or analysis.get("source_integrity", {}).get("sha256") or sha256_path(path))
        routed_name = title_filename(clean, source_identity_hash, path.name)
        orig_dest_dir = ORIGINALS_STRUCT / rel_sub
        orig_dest_file = orig_dest_dir / routed_name

        search_corpus = f"{clean}\n{meta.get('tags', [])}\n{text[:4000]}"
        assigned_domains = match_domains(search_corpus)

        model_domains = unique_labels(list(call_1.get("technical_domains") or meta.get("technical_domains") or []))
        technical_facets = model_domains or unique_labels([Path(value).parts[0] for value in assigned_domains])
        subject_facets = unique_labels(list(call_1.get("subject_tags") or meta.get("subject_tags") or meta.get("tags") or []))
        if not subject_facets:
            subject_facets = ["Needs_Subject_Review"]
        reader_facets = unique_labels(list(call_1.get("reader_categories") or meta.get("reader_categories") or []))
        if not reader_facets:
            reader_facets = match_reader_categories(search_corpus)
        content_types = infer_content_types(f"{clean}\n{text[:12000]}")
        epistemic_roles = infer_epistemic_roles(f"{clean}\n{text[:12000]}")

        cat_dests: list[Path] = []
        for dom in assigned_domains:
            dom_dir = CATEGORIZED_DIR / dom
            cat_dests.append(dom_dir / routed_name)

        facet_dests: list[Path] = []
        for axis, labels in (
            ("00_CONTENT_TYPE", content_types),
            ("01_TECHNICAL_DOMAIN", technical_facets),
            ("02_PRECISE_SUBJECT", subject_facets),
            ("03_READER_CATEGORY", reader_facets),
            ("04_EPISTEMIC_ROLE", epistemic_roles),
        ):
            for label in labels:
                facet_dests.append(FACETS_DIR / axis / label / routed_name)

        destinations = [orig_dest_file, *cat_dests, *facet_dests]
        copy_results: list[dict[str, str]] = []
        if not dry_run:
            copy_results = [safe_copy(path, destination) for destination in destinations]

        rec = {
            "source_path": str(path),
            "original_filename": path.name,
            "cleaned_title": clean,
            "title_status": "REVIEW" if title_issues else "VERIFIED",
            "title_issues": title_issues,
            "routed_filename": routed_name,
            "analysis_sidecar_present": bool(analysis),
            "original_structure_dest": str(orig_dest_file),
            "categorized_dests": [str(d) for d in cat_dests],
            "assigned_domains": assigned_domains,
            "technical_domains": technical_facets,
            "subject_tags": subject_facets,
            "reader_categories": reader_facets,
            "content_types": content_types,
            "epistemic_roles": epistemic_roles,
            "discovery_facet_dests": [str(d) for d in facet_dests],
            "copy_results": copy_results,
            "sha256": sha256_path(path),
        }
        records.append(rec)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    json_log = LOGS_DIR / f"organization-receipt-{timestamp}.json"
    csv_log = LOGS_DIR / f"organization-receipt-{timestamp}.csv"

    if not dry_run and write_receipt:
        with open(unc_path(json_log), "w", encoding="utf-8") as f:
            f.write(json.dumps(records, indent=2, ensure_ascii=False))
        with open(unc_path(csv_log), "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["original_filename", "cleaned_title", "title_status", "title_issues", "routed_filename", "analysis_sidecar_present", "assigned_domains", "technical_domains", "subject_tags", "reader_categories", "content_types", "epistemic_roles", "original_structure_dest", "categorized_dests", "discovery_facet_dests", "copy_statuses"])
            writer.writeheader()
            for r in records:
                writer.writerow({
                    "original_filename": r["original_filename"],
                    "cleaned_title": r["cleaned_title"],
                    "title_status": r["title_status"],
                    "title_issues": "; ".join(r["title_issues"]),
                    "routed_filename": r["routed_filename"],
                    "analysis_sidecar_present": r["analysis_sidecar_present"],
                    "assigned_domains": "; ".join(r["assigned_domains"]),
                    "technical_domains": "; ".join(r["technical_domains"]),
                    "subject_tags": "; ".join(r["subject_tags"]),
                    "reader_categories": "; ".join(r["reader_categories"]),
                    "content_types": "; ".join(r["content_types"]),
                    "epistemic_roles": "; ".join(r["epistemic_roles"]),
                    "original_structure_dest": r["original_structure_dest"],
                    "categorized_dests": "; ".join(r["categorized_dests"]),
                    "discovery_facet_dests": "; ".join(r["discovery_facet_dests"]),
                    "copy_statuses": "; ".join(item["status"] for item in r["copy_results"]),
                })

    return {
        "processed_count": len(records),
        "dry_run": dry_run,
        "records": records,
        "json_receipt": str(json_log) if not dry_run and write_receipt else None,
        "csv_receipt": str(csv_log) if not dry_run and write_receipt else None
    }


def main():
    parser = argparse.ArgumentParser(description="Organize OUTBOX files into original structure and deep domain folders.")
    parser.add_argument("--dry-run", action="store_true", help="Preview categorization and title cleanup without copying files.")
    parser.add_argument("--source", action="append", type=Path, help="Process one completed output immediately; may be repeated.")
    args = parser.parse_args()

    result = organize_all(dry_run=args.dry_run, source_paths=args.source)
    print(f"\nCompleted organization pass: {result['processed_count']} files processed (dry_run={result['dry_run']}).")
    if not args.dry_run:
        print(f"Receipts saved to:\n  {result['json_receipt']}\n  {result['csv_receipt']}")
        try:
            api_builder = SCRIPTS_DIR / "build_master_classification_api.py"
            if api_builder.exists():
                print("Rebuilding master classification API...")
                import subprocess
                subprocess.run([sys.executable, str(api_builder)], check=True)
        except Exception as e:
            print(f"Note: Classification API rebuild encountered: {e}")


if __name__ == "__main__":
    main()
