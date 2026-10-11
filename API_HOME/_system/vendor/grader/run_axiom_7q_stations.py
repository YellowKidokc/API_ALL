from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "OUTPUT"
STATION_ROOT = OUTPUT / "station-runs" / datetime.now().strftime("axiom-7q-%Y%m%d_%H%M%S")


AXIOM_RULES = [
    ("truth_ground", "Truth / Logos ground", ["truth", "logos", "coherence", "person"]),
    ("information_substrate", "Information substrate", ["information", "algorithmic", "mutual information", "substrate"]),
    ("observer_actualization", "Observer / measurement", ["observer", "measurement", "observe", "qrng"]),
    ("grace_repair", "Grace / negentropy / repair", ["grace", "negentropy", "repair", "restoration"]),
    ("entropy_thermo", "Entropy / thermodynamic constraint", ["entropy", "thermodynamic", "shannon", "noise"]),
    ("falsifiability", "Falsification / kill condition", ["falsification", "falsifiable", "fails", "failure", "kill"]),
    ("master_equation", "Master Equation / chi field", ["master equation", "χ", "chi", "field"]),
    ("moral_conservation", "Moral conservation", ["moral", "justice", "fairness", "duty", "sacrifice"]),
    ("experiment_protocol", "Experimental protocol", ["experiment", "protocol", "randomization", "pre-commitment", "hash"]),
    ("model_coupling", "Model coupling / susceptibility", ["coupling", "susceptibility", "model", "slope"]),
]


def read_claims(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def axiom_hits(text: str) -> list[dict]:
    lower = text.lower()
    hits = []
    for node_id, label, terms in AXIOM_RULES:
        matched = [t for t in terms if t.lower() in lower]
        if matched:
            hits.append({"node_id": node_id, "label": label, "matched_terms": matched})
    return hits


def forward_score(row: dict) -> dict:
    q_cols = ["Q1_identity", "Q2_scope", "Q3_mechanism", "Q4_evidence", "Q5_falsifiability", "Q6_boundary", "Q7_listener_risk"]
    raw = {q: row.get(q, "") for q in q_cols}
    score = 0
    score += 1 if raw["Q1_identity"] == "clear" else 0
    score += 1 if raw["Q2_scope"] == "bounded" else 0
    score += 1 if raw["Q3_mechanism"] == "present" else 0
    score += 1 if raw["Q4_evidence"] == "present" else 0
    score += 1 if raw["Q5_falsifiability"] == "present" else 0
    score += 1 if raw["Q6_boundary"] == "present" else 0
    score += 1 if raw["Q7_listener_risk"] == "normal" else 0
    return {"score": score, "max_score": 7, "raw": raw}


def reverse_verdict(row: dict) -> dict:
    weaknesses = []
    if row.get("Q4_evidence") != "present":
        weaknesses.append("missing_evidence")
    if row.get("Q5_falsifiability") != "present":
        weaknesses.append("missing_kill_condition")
    if row.get("Q3_mechanism") != "present":
        weaknesses.append("missing_mechanism")
    if row.get("Q2_scope") != "bounded":
        weaknesses.append("overbroad_scope")
    if row.get("Q6_boundary") != "present":
        weaknesses.append("missing_boundary")
    if row.get("Q7_listener_risk") == "high":
        weaknesses.append("high_listener_risk")

    if "missing_evidence" in weaknesses and "missing_kill_condition" in weaknesses:
        status = "FAIL_REVIEW"
    elif len(weaknesses) >= 3:
        status = "WEAKENED"
    elif weaknesses:
        status = "SURVIVES_WITH_REPAIRS"
    else:
        status = "SURVIVES"
    return {"status": status, "weaknesses": weaknesses}


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_md(path: Path, payload: dict) -> None:
    lines = [
        f"# {payload['paper_id']} - Axiom + 7Q Station Pass",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Claims: {payload['claim_count']}",
        f"- Average 7Q forward score: {payload['forward_summary']['average_score']}/7",
        f"- Reverse verdicts: {payload['reverse_summary']['status_counts']}",
        f"- Axiom/concept hits: {payload['axiom_summary']['hit_counts']}",
        "",
        "## Top Repairs",
        "",
    ]
    for item, count in payload["reverse_summary"]["weakness_counts"].most_common(10):
        lines.append(f"- {item}: {count}")
    lines += ["", "## Claim Rows", ""]
    for row in payload["claims"]:
        lines += [
            f"### Claim {row['index']}: {row['section']}",
            "",
            f"- Forward: {row['forward']['score']}/7",
            f"- Reverse: {row['reverse']['status']} ({', '.join(row['reverse']['weaknesses']) or 'no major weakness'})",
            f"- Axiom hits: {', '.join(h['label'] for h in row['axiom_hits']) or 'none'}",
            f"- Claim: {row['claim'][:500]}",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


def process_file(path: Path) -> dict:
    rows = read_claims(path)
    paper_id = rows[0]["paper_id"] if rows else path.stem.replace(".claim-audit", "")
    paper_dir = STATION_ROOT / paper_id
    paper_dir.mkdir(parents=True, exist_ok=True)

    claims = []
    forward_scores = []
    reverse_statuses = Counter()
    weakness_counts = Counter()
    hit_counts = Counter()

    for i, row in enumerate(rows, 1):
        text = f"{row.get('section','')} {row.get('one_sentence_claim','')} {row.get('nearby_equation','')}"
        hits = axiom_hits(text)
        for h in hits:
            hit_counts[h["node_id"]] += 1
        forward = forward_score(row)
        reverse = reverse_verdict(row)
        forward_scores.append(forward["score"])
        reverse_statuses[reverse["status"]] += 1
        weakness_counts.update(reverse["weaknesses"])
        claims.append({
            "index": i,
            "section": row.get("section", ""),
            "claim": row.get("one_sentence_claim", ""),
            "maturity": row.get("claim_maturity_label", ""),
            "axiom_hits": hits,
            "forward": forward,
            "reverse": reverse,
        })

    payload = {
        "schema_version": "paper-proof-grader.axiom_7q_station.v1",
        "paper_id": paper_id,
        "source_claim_audit": str(path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_count": len(claims),
        "axiom_summary": {"hit_counts": dict(hit_counts)},
        "forward_summary": {
            "average_score": round(sum(forward_scores) / len(forward_scores), 2) if forward_scores else 0,
            "score_counts": dict(Counter(forward_scores)),
        },
        "reverse_summary": {
            "status_counts": dict(reverse_statuses),
            "weakness_counts": weakness_counts,
        },
        "claims": claims,
    }
    # JSON cannot serialize Counter in nested payload directly.
    payload["reverse_summary"]["weakness_counts"] = dict(weakness_counts)

    write_json(paper_dir / "axiom-7q-stations.json", payload)
    # For markdown, restore a Counter-like object for most_common convenience.
    payload_for_md = dict(payload)
    payload_for_md["reverse_summary"] = dict(payload["reverse_summary"])
    payload_for_md["reverse_summary"]["weakness_counts"] = Counter(payload["reverse_summary"]["weakness_counts"])
    write_md(paper_dir / "axiom-7q-stations.md", payload_for_md)
    return payload


def main() -> int:
    STATION_ROOT.mkdir(parents=True, exist_ok=True)
    files = sorted(OUTPUT.glob("0*.claim-audit.csv"))
    manifests = [process_file(p) for p in files]
    index = {
        "schema_version": "paper-proof-grader.axiom_7q_batch.v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "station_root": str(STATION_ROOT),
        "paper_count": len(manifests),
        "papers": [
            {
                "paper_id": m["paper_id"],
                "claim_count": m["claim_count"],
                "average_forward_score": m["forward_summary"]["average_score"],
                "reverse_status_counts": m["reverse_summary"]["status_counts"],
                "axiom_hit_counts": m["axiom_summary"]["hit_counts"],
            }
            for m in manifests
        ],
    }
    write_json(STATION_ROOT / "batch-index.json", index)
    lines = ["# Axiom + 7Q Batch Index", "", f"Generated: {index['generated_at']}", ""]
    for p in index["papers"]:
        lines += [
            f"## {p['paper_id']}",
            f"- Claims: {p['claim_count']}",
            f"- Average 7Q forward: {p['average_forward_score']}/7",
            f"- Reverse: {p['reverse_status_counts']}",
            f"- Axiom hits: {p['axiom_hit_counts']}",
            "",
        ]
    (STATION_ROOT / "batch-index.md").write_text("\n".join(lines), encoding="utf-8")
    print(STATION_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
