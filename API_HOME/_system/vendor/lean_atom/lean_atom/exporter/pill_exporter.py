"""Write Lean theorems as YAML proof pills (mothership face/veins format).

One pill per theorem/lemma. The face is the thin, greppable part; the veins
carry the exact Lean text, the compiler receipt, the trust audit and the
definitions the statement uses. Only Lean's own build result can put a pill
in status `lean_passed` -- nothing here is AI-derived.
"""

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Same namespace as mothership/tools/atom_to_pill.py so uuids line up.
PROJECT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "faiththruphysics.com")
PROOF_KINDS = ("theorem", "lemma")
DEFINITION_KINDS = ("def", "structure", "inductive", "abbrev", "class", "axiom")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_'.]*")


class _Dumper(yaml.SafeDumper):
    pass


def _str_repr(dumper, value):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _str_repr)


def _loads(value, default):
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


TRAILING_COMMENT = re.compile(r"(\s*(/-.*?-/|--[^\n]*))+\s*\Z", re.S)


def _trim_trailing_comments(proof: str) -> str:
    """The scanner runs a declaration until the next one starts, so the next
    declaration's doc comment can trail the proof. Drop it."""
    return TRAILING_COMMENT.sub("", proof).strip()


def _latest_builds(db_path: str) -> Dict[str, Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT b.* FROM builds b
        JOIN (SELECT declaration_id, MAX(id) AS max_id FROM builds GROUP BY declaration_id) m
          ON b.id = m.max_id
    """).fetchall()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(builds)")]
    conn.close()
    return {r["declaration_id"]: {c: r[c] for c in cols} for r in rows}


def _status(build: Dict[str, Any] | None, trust: str | None) -> str:
    if not build:
        return "not_built"
    if build.get("build_result") != "PASSED":
        return "lean_" + str(build.get("build_result", "failed")).lower()
    if trust == "PROOF_ESCAPE":
        return "lean_passed_with_sorry"
    return "lean_passed"


def _definitions_used(statement: str, defs_by_name: Dict[str, List[Dict[str, Any]]],
                      namespace: str) -> List[Dict[str, str]]:
    """Definitions from this corpus whose names appear in the statement."""
    used, seen = [], set()
    for tok in IDENT.findall(statement or ""):
        for cand in (tok, tok.split(".")[-1]):
            for d in defs_by_name.get(cand, []):
                # Prefer a definition from the same namespace when names repeat.
                if d["fully_qualified_name"] in seen:
                    continue
                if len(defs_by_name[cand]) > 1 and d["namespace"] != namespace:
                    continue
                seen.add(d["fully_qualified_name"])
                used.append({"name": d["fully_qualified_name"], "kind": d["declaration_kind"],
                             "file": d["relative_path"], "line": d["start_line"]})
    return used


# Claim Evidence Lane Framework: primary lane inferred from file + theorem
# names. First match wins; anything unmatched is `other` for a later pass.
LANE_RULES = [
    ("master_equation", ("master_equation", "masterderivation", "chi", "final_lean4_from_excel")),
    ("trinity", ("trinity", "maxwell", "perichor")),
    ("ten_laws", ("ten_law", "tenlaw", "law_")),
    ("consciousness", ("observer", "witness", "conscious", "self_reference", "selfreference", "phi_")),
    ("crown", ("fracture", "grace", "cross", "resurrection", "truth")),
    ("morality", ("justice", "mercy", "moral", "accountab", "liabilit", "forgiv", "guilt", "repair",
                  "restoration", "reconcil", "substitution", "costbearing", "fall", "death",
                  "temporalfinal", "evil", "good", "love", "peace", "joy", "fruit", "beatitude")),
    ("axioms", ("axiom", "premiseablation", "premise", "proofchain", "substrate", "kernel",
                "definition", "divineorder")),
    ("meta", ("adversarial", "comparison", "negativeinventory", "audit", "atlas", "ablation")),
]


def infer_lane(rel_path: str, fq_name: str) -> str:
    hay = f"{rel_path} {fq_name}".lower()
    for lane, keys in LANE_RULES:
        if any(k in hay for k in keys):
            return lane
    return "other"


def build_rails(d: Dict[str, Any], face: Dict[str, Any], receipt: Dict[str, Any] | None,
                also_in: List[str]) -> Dict[str, Any]:
    """The 10 rails of the Claim Evidence Lane Framework for a Lean theorem."""
    passed = face["status"] == "lean_passed"
    present = []
    if receipt:
        present.append({
            "lane": "lean_formal",
            "item": receipt.get("command"),
            "result": receipt.get("result"),
            "receipt_hash": receipt.get("receipt_hash"),
        })
    gaps = []
    if not passed:
        gaps.append("lean_formal: no passing Lean build recorded for this theorem")
    gaps.append("transitive axiom audit (#print axioms) not yet recorded")
    gaps.append("bridge_mapping: any theology/physics reading beyond the Lean model needs its own graded bridge")
    return {
        "framework": "Claim Evidence Lane Framework",
        "1_claim": (d.get("formal_statement") or "").strip(),
        "2_framework_lane": infer_lane(d["relative_path"], d["fully_qualified_name"]),
        "2_lane_basis": "inferred from file and theorem name; review before canon",
        "3_physics_claim_type": "mathematical_formalism",
        "4_defense_class": "DERIVATION",
        "5_evidence_needed": ["lean_formal"],
        "6_evidence_present": present,
        "7_evidence_gap": gaps,
        "8_kill_condition": (
            f"Breaks if `lake env lean {d['relative_path']}` fails with this statement unchanged, "
            f"or if #print axioms {d['fully_qualified_name']} shows sorryAx or an axiom outside the declared bundle."
        ),
        "9_story_rendering": {
            "text": None,
            "note": "Kept separate. Story is never counted as proof.",
        },
        "10_beacon": {
            "uuid": face["uuid"],
            "node_id": face["node_id"],
            "receipt_hash": receipt.get("receipt_hash") if receipt else None,
            "also_in": also_in,
        },
    }


def build_pill(d: Dict[str, Any], build: Dict[str, Any] | None,
               defs_by_name: Dict[str, List[Dict[str, Any]]], project: str,
               also_in: List[str] | None = None) -> Dict[str, Any]:
    node_id = f"tp:lean/{project}/{d['fully_qualified_name']}"
    statement = (d.get("formal_statement") or "").strip()
    face = {
        "uuid": str(uuid.uuid5(PROJECT_NAMESPACE, node_id)),
        "node_id": node_id,
        "name": d["fully_qualified_name"],
        "term": d["declaration_name"],
        "plain": statement,
        "status": _status(build, d.get("primary_trust_status")),
        "target_type": "proof",
    }
    receipt = None
    if build:
        receipt = {
            "tool": "lean",
            "command": build.get("build_command"),
            "result": build.get("build_result"),
            "exit_code": build.get("exit_code"),
            "lean_version": build.get("lean_version"),
            "receipt_hash": build.get("receipt_hash"),
            "checked_at": build.get("checked_at") or build.get("created_at"),
        }
    veins = {
        "record_type": "truth_kernel_record_v1",
        "declaration_kind": d["declaration_kind"],
        "namespace": d.get("namespace") or "",
        "exact_proposition": statement,
        "premise_set": _loads(d.get("variables_json"), []),
        "definitions_used": _definitions_used(statement, defs_by_name, d.get("namespace") or ""),
        "proof_script": _trim_trailing_comments(d.get("proof_script") or ""),
        "entailment_status": "LEAN_CHECKED" if face["status"] == "lean_passed" else "NOT_ESTABLISHED",
        "formal_receipts": [receipt] if receipt else [],
        "trust": {
            "status": d.get("primary_trust_status") or "NOT_AUDITED",
            "sorry_count": d.get("sorry_count") or 0,
            "admit_count": d.get("admit_count") or 0,
            "note": "Text audit of this declaration only; run #print axioms for transitive dependencies.",
        },
        "source": {
            "project": project,
            "file": d["relative_path"],
            "lines": [d.get("start_line"), d.get("end_line")],
            "file_sha256": d.get("source_hash"),
        },
        "interpretation": {
            "status": "NONE",
            "note": "What this proves in theology/physics terms is not stated here. Add it as a separate, labelled claim link.",
        },
        "human_ruling_required": True,
    }
    rails = build_rails(d, face, receipt, also_in or [])
    face["lane"] = rails["2_framework_lane"]
    face["defense_class"] = rails["4_defense_class"]
    return {"face": face, "rails": rails, "veins": veins}


BLOCK_COMMENT = re.compile(r"/-.*?-/", re.S)
LINE_COMMENT = re.compile(r"--[^\n]*")
SCAN_EXTS = {".json", ".jsonld", ".jsonl", ".yaml", ".yml", ".md", ".txt", ".csv", ".lean"}
SKIP_SCAN_DIRS = {".git", ".lake", "node_modules", "__pycache__", "_archive", "retired",
                  ".pytest_cache", "build"}
NODE_ID_KEYS = re.compile(r'"?(nodeID|claimID|node_id|claim_id|@id)"?\s*[:=]\s*"?([^",\s}]+)')


def node_id_for(project: str, d: Dict[str, Any]) -> str:
    return f"tp:lean/{project}/{d['fully_qualified_name']}"


def _code_idents(d: Dict[str, Any]) -> set:
    text = f"{d.get('formal_statement') or ''}\n{d.get('proof_script') or ''}"
    text = LINE_COMMENT.sub("", BLOCK_COMMENT.sub("", text))
    return set(IDENT.findall(text))


def _resolve(tok: str, d: Dict[str, Any], by_short: Dict[str, List[Dict[str, Any]]],
             by_fq: Dict[str, Dict[str, Any]]):
    """Map an identifier used inside `d` to the declaration it names, or None."""
    if tok in by_fq:
        return by_fq[tok]
    short = tok.split(".")[-1]
    cands = by_short.get(short, [])
    if not cands:
        return None
    for pick in (lambda c: c["relative_path"] == d["relative_path"],
                 lambda c: c.get("namespace") == d.get("namespace")):
        chosen = [c for c in cands if pick(c)]
        if chosen:
            return chosen[0]
    # Unique name corpus-wide is safe; ambiguous names are skipped, not guessed.
    names = {c["fully_qualified_name"] for c in cands}
    return cands[0] if len(names) == 1 else None


def scan_mentions(scan_roots: List[str], searchable: Dict[str, str]) -> Dict[str, List[Dict[str, str]]]:
    """Read-only scan of other nodes for Lean names. Returns node_id -> mentions."""
    hits: Dict[str, List[Dict[str, str]]] = {}
    for root in scan_roots:
        root_path = Path(root)
        if not root_path.exists():
            continue
        for path in root_path.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SCAN_EXTS:
                continue
            if any(part in SKIP_SCAN_DIRS for part in path.parts):
                continue
            if path.name.endswith(".pill.yaml") and "PROOF" in path.parts:
                continue  # our own pills
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            found = set(IDENT.findall(text)) & searchable.keys()
            if not found:
                continue
            ext_node = NODE_ID_KEYS.search(text)
            for tok in found:
                hits.setdefault(searchable[tok], []).append({
                    "file": str(path),
                    "node_id": ext_node.group(2) if ext_node else None,
                    "matched": tok,
                })
    return hits


def _definition_pill(d, build, project, lane, edges):
    node_id = node_id_for(project, d)
    is_assumption = d["declaration_kind"] == "axiom" or (
        d["declaration_kind"] == "structure" and re.search(r"bundle|axiom", d["declaration_name"], re.I))
    status = _status(build, d.get("primary_trust_status"))
    receipt = None
    if build:
        receipt = {"tool": "lean", "command": build.get("build_command"), "result": build.get("build_result"),
                   "lean_version": build.get("lean_version"), "receipt_hash": build.get("receipt_hash")}
    face = {
        "uuid": str(uuid.uuid5(PROJECT_NAMESPACE, node_id)),
        "node_id": node_id,
        "name": d["fully_qualified_name"],
        "term": d["declaration_name"],
        "plain": (d.get("formal_statement") or "").strip(),
        "status": status,
        "target_type": "definition",
        "lane": lane,
        "defense_class": "AXIOM" if is_assumption else "ROOT",
    }
    rails = {
        "framework": "Claim Evidence Lane Framework",
        "1_claim": face["plain"],
        "2_framework_lane": lane,
        "2_lane_basis": "inferred from file and name; review before canon",
        "3_physics_claim_type": "mathematical_formalism",
        "4_defense_class": face["defense_class"],
        "5_evidence_needed": ["lean_formal"],
        "6_evidence_present": [{"lane": "lean_formal", "item": receipt["command"], "result": receipt["result"],
                                "receipt_hash": receipt["receipt_hash"]}] if receipt else [],
        "7_evidence_gap": ([] if status == "lean_passed" else ["no passing Lean build recorded"]) + [
            "a Lean definition only fixes meaning inside the model; its real-world reading needs a bridge"],
        "8_kill_condition": f"Breaks if `lake env lean {d['relative_path']}` no longer type-checks this definition.",
        "9_story_rendering": {"text": None, "note": "Kept separate. Story is never counted as proof."},
        "10_beacon": {"uuid": face["uuid"], "node_id": node_id,
                      "receipt_hash": receipt["receipt_hash"] if receipt else None},
    }
    veins = {
        "declaration_kind": d["declaration_kind"],
        "namespace": d.get("namespace") or "",
        "exact_form": face["plain"],
        "body": _trim_trailing_comments(d.get("proof_script") or ""),
        "source": {"project": project, "file": d["relative_path"],
                   "lines": [d.get("start_line"), d.get("end_line")], "file_sha256": d.get("source_hash")},
        "human_ruling_required": True,
    }
    return {"face": face, "rails": rails, "edges": edges, "veins": veins}


def _write(dest: Path, pill: Dict[str, Any], counts: Dict[str, int]) -> None:
    body = yaml.dump(pill, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)
    if dest.exists() and dest.read_text(encoding="utf-8") == body:
        counts["unchanged"] += 1
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    counts["written"] += 1


def export_pills(repo, db_path: str, out_dir: str, project: str,
                 scan_roots: List[str] | None = None, graph_copy: str | None = None) -> Dict[str, int]:
    from .briefs import load_theorem_lines
    decls = repo.list_declarations(project)
    builds = _latest_builds(db_path)
    explained = load_theorem_lines(out_dir)
    defs_by_name: Dict[str, List[Dict[str, Any]]] = {}
    by_short: Dict[str, List[Dict[str, Any]]] = {}
    by_fq: Dict[str, Dict[str, Any]] = {}
    for d in decls:
        if d["declaration_kind"] in DEFINITION_KINDS:
            defs_by_name.setdefault(d["declaration_name"], []).append(d)
        if d["declaration_kind"] in PROOF_KINDS + DEFINITION_KINDS:
            by_short.setdefault(d["declaration_name"], []).append(d)
            by_fq.setdefault(d["fully_qualified_name"], d)
    nodes = [d for d in decls if d["declaration_kind"] in PROOF_KINDS + DEFINITION_KINDS]

    # --- Lean -> Lean edges (statement + proof body, comments stripped) ---
    uses: Dict[str, set] = {}
    used_by: Dict[str, set] = {}
    for d in nodes:
        me = node_id_for(project, d)
        for tok in _code_idents(d):
            target = _resolve(tok, d, by_short, by_fq)
            if target is None or target["fully_qualified_name"] == d["fully_qualified_name"]:
                continue
            tid = node_id_for(project, target)
            uses.setdefault(me, set()).add(tid)
            used_by.setdefault(tid, set()).add(me)

    # --- Other nodes -> Lean (read-only name scan) ---
    # Only distinctive names: full names, or short names with an underscore or
    # internal capital, at least 8 chars, and unique in the corpus.
    searchable: Dict[str, str] = {}
    for fq, d in by_fq.items():
        searchable[fq] = node_id_for(project, d)
        short = d["declaration_name"]
        if (len(short) >= 8 and ("_" in short or re.search(r"[a-z][A-Z]", short))
                and len({c["fully_qualified_name"] for c in by_short[short]}) == 1):
            searchable[short] = node_id_for(project, d)
    mentions = scan_mentions(scan_roots or [], searchable)

    def edges_for(d):
        me = node_id_for(project, d)
        return {
            "uses": sorted(uses.get(me, [])),
            "used_by": sorted(used_by.get(me, [])),
            "mentioned_in": mentions.get(me, [])[:50],
        }

    out = Path(out_dir)
    counts = {"written": 0, "unchanged": 0, "lean_passed": 0, "other_status": 0,
              "definition_pills": 0, "edges": sum(len(v) for v in uses.values()),
              "outside_mentions": sum(len(v) for v in mentions.values())}
    index = []
    used_paths = set()
    copies: Dict[tuple, List[str]] = {}
    for d in nodes:
        key = (d["fully_qualified_name"], (d.get("formal_statement") or "").strip())
        copies.setdefault(key, []).append(d["relative_path"])

    graph_nodes = {}
    for d in nodes:
        is_proof = d["declaration_kind"] in PROOF_KINDS
        rel_dir = Path(d["relative_path"]).with_suffix("")
        base = out if is_proof else out / "00_LEAN_DEFINITIONS"
        dest = base / rel_dir / f"{d['declaration_name']}.pill.yaml"
        if dest in used_paths:
            dest = base / rel_dir / f"{d['fully_qualified_name']}.pill.yaml"
        used_paths.add(dest)
        lane = infer_lane(d["relative_path"], d["fully_qualified_name"])
        if is_proof:
            key = (d["fully_qualified_name"], (d.get("formal_statement") or "").strip())
            also_in = [p for p in copies.get(key, []) if p != d["relative_path"]]
            pill = build_pill(d, builds.get(d["id"]), defs_by_name, project, also_in)
            pill = {"face": pill["face"], "rails": pill["rails"], "edges": edges_for(d), "veins": pill["veins"]}
            counts["lean_passed" if pill["face"]["status"] == "lean_passed" else "other_status"] += 1
        else:
            pill = _definition_pill(d, builds.get(d["id"]), project, lane, edges_for(d))
            counts["definition_pills"] += 1
        exp = explained.get((d["relative_path"], d["declaration_name"]))
        if exp and exp.get("plain"):
            # Readable meaning, kept apart from the rails: an explanation, not evidence.
            pill = {**{k: v for k, v in pill.items() if k != "veins"},
                    "explanation": {"plain": exp["plain"], "role": exp.get("role"), "brief": exp["brief"],
                                    "written_by": exp.get("model"), "written_at": exp.get("generated_at"),
                                    "status": "AI explanation - not evidence; review before citing"},
                    "veins": pill["veins"]}
            counts["explained"] = counts.get("explained", 0) + 1
        _write(dest, pill, counts)
        rel = dest.relative_to(out).as_posix()
        index.append({"uuid": pill["face"]["uuid"], "node_id": pill["face"]["node_id"],
                      "type": pill["face"]["target_type"], "status": pill["face"]["status"],
                      "lane": pill["face"]["lane"], "path": rel})
        gid = pill["face"]["node_id"]
        if gid not in graph_nodes:  # file copies share one node
            graph_nodes[gid] = {"node_id": gid, "uuid": pill["face"]["uuid"], "name": d["fully_qualified_name"],
                                "type": pill["face"]["target_type"], "kind": d["declaration_kind"],
                                "status": pill["face"]["status"], "lane": pill["face"]["lane"],
                                "file": d["relative_path"], "pill": rel, "copies": []}
        else:
            graph_nodes[gid]["copies"].append(rel)

    edge_list = [{"from": a, "to": b, "type": "uses"} for a, bs in uses.items() for b in sorted(bs)]
    edge_list += [{"from": m.get("node_id") or m["file"], "to": nid, "type": "mentions", "file": m["file"]}
                  for nid, ms in mentions.items() for m in ms]
    graph = {"generated_at": datetime.now(timezone.utc).isoformat(), "project": project,
             "nodes": list(graph_nodes.values()), "edges": edge_list}
    graph_text = json.dumps(graph, ensure_ascii=False, indent=1)
    (out / "00_LEAN_GRAPH.json").write_text(graph_text, encoding="utf-8")
    if graph_copy:
        Path(graph_copy).write_text(graph_text, encoding="utf-8")

    manifest = {
        "generated_at": graph["generated_at"],
        "project": project,
        "pill_count": len(index),
        "counts": counts,
        "graph": "00_LEAN_GRAPH.json",
        "pills": index,
    }
    (out / "00_PROOF_PILLS_INDEX.yaml").write_text(
        yaml.dump(manifest, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
    return counts
