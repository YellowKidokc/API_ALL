#!/usr/bin/env python3
"""
feature_extractor.py
====================
Batch a folder of source files into structured χ/Fruit packets (JSONL).

Usage:
  python feature_extractor.py --source-dir INBOX --workbook "X:\\...\7Q Full Method.xlsx"

Outputs:
  - feature_packets.jsonl (default: features/feature_packets.jsonl)
  - feature_summary.json   (default: features/feature_summary.json)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import pathlib
from collections import Counter
from typing import Any, Dict, Iterable, List, Tuple

try:
    import openpyxl  # type: ignore
except Exception:  # pragma: no cover
    openpyxl = None  # type: ignore


TEXT_EXTS = {".txt", ".md", ".mdx", ".html", ".htm", ".rst", ".rstx", ".markdown", ".log", ".json"}
DEFAULT_FIAT = {
    "Love": ["love", "benevolent", "kind", "gracious", "compassion"],
    "Joy": ["joy", "delight", "thankful", "hopeful", "celebrate"],
    "Peace": ["peace", "calm", "reconcile", "restful", "serene"],
    "Patience": ["patience", "patient", "thorough", "careful", "steady"],
    "Kindness": ["kind", "kindness", "gentle", "compassion", "merciful"],
    "Goodness": ["good", "help", "constructive", "beneficial", "uplifting"],
    "Faithfulness": ["faithful", "consistent", "reliable", "dependable"],
    "Gentleness": ["gentle", "restraint", "soft", "humble", "mercy"],
    "SelfControl": ["self-control", "self control", "temperance", "discipline", "restraint"],
}
DEFAULT_ANTI_MAP = {
    "Love": "Hatred",
    "Joy": "Despair",
    "Peace": "Anxiety",
    "Patience": "Impatience",
    "Kindness": "Cruelty",
    "Goodness": "Corruption",
    "Faithfulness": "Betrayal",
    "Gentleness": "Harshness",
    "SelfControl": "Addiction",
}


def parse_config(path: pathlib.Path) -> Dict[str, str]:
    cfg: Dict[str, str] = {}
    if not path.exists():
        return cfg
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            cfg[k.strip()] = v.strip()
    return cfg


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in re.findall(r"[a-z']+", text.lower())]


def _safe_float(v: Any, fallback: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return fallback


def _count_hits(words: List[str], terms: Iterable[str]) -> int:
    hay = set(words)
    # multi-word terms: fallback to substring in whole text at parse time
    return sum(1 for t in terms if not t or " " in t and t in " ".join(words) or t in hay)


def _load_fruit_axes(workbook_path: pathlib.Path) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Load Fruit and Anti-Fruit dictionaries.

    Accept two formats:
      1) axis in col A, term in col B
      2) wide sheet: axis in header row and terms in columns
    """
    if openpyxl is None:
        return DEFAULT_FIAT.copy(), DEFAULT_FIAT.copy()
    if not workbook_path.exists():
        return DEFAULT_FIAT.copy(), DEFAULT_FIAT.copy()

    try:
        wb = openpyxl.load_workbook(workbook_path, data_only=True, read_only=True)
    except Exception:
        return DEFAULT_FIAT.copy(), DEFAULT_FIAT.copy()

    def read_sheet(name: str) -> Dict[str, List[str]]:
        if name not in wb.sheetnames:
            return {}
        ws = wb[name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return {}
        if len(rows[0]) < 2:
            return {}

        # Wide format: first row are axis names.
        first = [str(c).strip() if c is not None else "" for c in rows[0]]
        if first[0].lower() in {"axis", "fruit", "term"} and first[1]:
            out: Dict[str, List[str]] = {}
            for row in rows[1:]:
                for axis, term in zip(first, row):
                    if not axis:
                        continue
                    t = str(term).strip() if term else ""
                    if not t:
                        continue
                    out.setdefault(axis, []).extend(_split_terms(t))
            return out

        # Axis-first format: col0 axis, col1 term
        out: Dict[str, List[str]] = {}
        for row in rows[1:]:
            axis = str(row[0]).strip() if row and row[0] else ""
            if not axis:
                continue
            term_cells = [str(v).strip() for v in row[1:] if v]
            for t in term_cells:
                out.setdefault(axis, []).extend(_split_terms(t))
        return out

    pos = read_sheet("Fruit")
    anti = read_sheet("Anti-Fruit")
    anti = {k: v for k, v in anti.items() if v}
    if not pos or not anti:
        return DEFAULT_FIAT.copy(), DEFAULT_FIAT.copy()
    # dedupe
    pos = {k: sorted(set(v)) for k, v in pos.items()}
    anti = {k: sorted(set(v)) for k, v in anti.items()}
    # keep only overlapping axes when possible
    axes = sorted(set(pos) | set(anti))
    return {a: pos.get(a, []) for a in axes}, {a: anti.get(a, []) for a in axes}


def _split_terms(raw: str) -> List[str]:
    parts: List[str] = []
    for part in re.split(r"[;,]", raw):
        p = part.strip().lower()
        if p:
            parts.append(p)
    return parts


def compute_fruit_profile(
    text: str,
    fruit_map: Dict[str, List[str]],
    anti_map: Dict[str, List[str]],
    anti_penalty_weight: float = 1.35,
) -> Dict[str, Any]:
    words = tokenize(text)
    joined = " ".join(words)
    fruit_scores: Dict[str, float] = {}
    for axis in sorted(set(fruit_map) | set(anti_map)):
        pos = fruit_map.get(axis, [])
        neg = anti_map.get(axis, [])
        p_hits = _count_hits(words, pos)
        n_hits = _count_hits(words, neg)
        denom = max(1.0, max(len(pos), len(neg), 1))
        raw = (p_hits - anti_penalty_weight * n_hits) / (denom + 1) + 0.5
        fruit_scores[axis] = clamp01(raw)
        # keep substring style bonus for big phrases
        if " " in joined:
            for phrase in [t for t in pos if " " in t]:
                if phrase in joined:
                    fruit_scores[axis] = clamp01(fruit_scores[axis] + 0.05)
            for phrase in [t for t in neg if " " in t]:
                if phrase in joined:
                    fruit_scores[axis] = clamp01(fruit_scores[axis] - 0.05 * anti_penalty_weight)

    def score_delta(v: float) -> float:
        return round(v - 0.5, 4)

    fruit_sorted = sorted(
        (
            {
                "axis": axis,
                "score": round(score, 4),
                "delta_from_neutral": score_delta(score),
            }
            for axis, score in fruit_scores.items()
        ),
        key=lambda d: abs(d["delta_from_neutral"]),
        reverse=True,
    )
    anti_sorted = sorted(
        (
            {
                "axis": DEFAULT_ANTI_MAP.get(axis, f"anti-{axis}"),
                "score": round(1.0 - score["score"], 4),
                "from_axis": axis,
                "delta_from_neutral": round(0.5 - score["score"], 4),
            }
            for axis, score in fruit_scores.items()
        ),
        key=lambda d: abs(d["delta_from_neutral"]),
        reverse=True,
    )
    return {
        "fruit_axis_scores": fruit_sorted,
        "anti_axis_scores": anti_sorted,
    }


def run_chi_for_file(
    evaluator_path: pathlib.Path,
    file_path: pathlib.Path,
    workbook_path: pathlib.Path,
    source: str,
) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        td_path = pathlib.Path(td)
        json_path = td_path / f"chi_run_{file_path.name}.json"
        cmd = [
            sys.executable,
            str(evaluator_path),
            "--input",
            str(file_path),
            "--workbook",
            str(workbook_path),
            "--source",
            source,
            "--json",
            str(json_path),
        ]
        proc = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            cwd=str(evaluator_path.parent),
        )
        if proc.returncode != 0:
            raise RuntimeError(f"χ evaluator failed for {file_path}: {proc.stderr.strip()[:1200]}")
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        return payload


def iter_claim_packets(
    payload: Dict[str, Any],
    source_file: pathlib.Path,
    fruit_lex: Tuple[Dict[str, List[str]], Dict[str, List[str]]],
    anti_penalty_weight: float = 1.35,
) -> List[Dict[str, Any]]:
    claims = payload.get("claims", []) or []
    fruit_map, anti_map = fruit_lex
    packets: List[Dict[str, Any]] = []
    for idx, claim in enumerate(claims, 1):
        claim_id = str(claim.get("id", idx))
        text = str(claim.get("claim_text", ""))[:2200]
        fruit_payload = compute_fruit_profile(text, fruit_map, anti_map, anti_penalty_weight=anti_penalty_weight)
        claim_baseline = {
            "packet_id": f"{source_file.stem}::{claim_id}",
            "source_file": str(source_file),
            "source_tag": str(claim.get("source", source_file.stem)),
            "claim_id": claim_id,
            "claim_index": idx,
            "claim_text": text,
            "claim_char_len": len(text),
            "chi_static": _safe_float(claim.get("chi_static")),
            "chi_gradient": _safe_float(claim.get("chi_gradient")),
            "chi_direction": str(claim.get("chi_direction", "")),
            "chi_verdict": str(claim.get("chi_verdict", "")),
            "chi_confidence": _safe_float(claim.get("chi_confidence", 0.0)),
            "fruit_score": _safe_float(claim.get("fruit_score", 0.0)),
            "fruit_bias_strength": _safe_float(claim.get("fruit_bias_strength", 0.0)),
            "truth_score": _safe_float(claim.get("truth_score", 0.0)),
            "truth_components": {
                "S": _safe_float(claim.get("S", 0.0)),
                "E": _safe_float(claim.get("E", 0.0)),
                "L": _safe_float(claim.get("L", 0.0)),
                "D": _safe_float(claim.get("D", 0.0)),
                "P": _safe_float(claim.get("P", 0.0)),
                "C": _safe_float(claim.get("C", 0.0)),
            },
            "channel_features": {
                "weakest": [s for s in str(claim.get("weakest_channels", "")).split(",") if s],
                "strongest": [s for s in str(claim.get("strongest_channels", "")).split(",") if s],
                "zero_channels": [s for s in str(claim.get("zero_channels", "")).split(",") if s],
                "chi_effective_mean": _safe_float(claim.get("chi_effective_mean", 0.0)),
                "chi_effective_std": _safe_float(claim.get("chi_effective_std", 0.0)),
                "chi_pos_mean": _safe_float(claim.get("chi_pos_mean", 0.0)),
                "chi_neg_mean": _safe_float(claim.get("chi_neg_mean", 0.0)),
                "chi_confidence_mean": _safe_float(claim.get("chi_confidence_mean", 0.0)),
            },
            "fruit_ranking": {
                "fruits": fruit_payload["fruit_axis_scores"][:8],
                "anti_fruits": fruit_payload["anti_axis_scores"][:8],
            },
            "run_meta": {
                "run_id": payload_run_id(payload),
            },
        }
        packets.append(claim_baseline)
    return packets


def payload_run_id(payload: Dict[str, Any]) -> str:
    run = payload.get("run", {})
    if isinstance(run, dict):
        return str(run.get("timestamp", "unknown"))
    return "unknown"


def extract_from_source(
    source_dir: pathlib.Path,
    evaluator_path: pathlib.Path,
    workbook_path: pathlib.Path,
    top_k_axes: int,
    anti_penalty_weight: float,
) -> List[Dict[str, Any]]:
    fruit_lex = _load_fruit_axes(workbook_path)
    packets: List[Dict[str, Any]] = []
    file_paths = sorted(
        p for p in source_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in TEXT_EXTS and p.name != ".gitkeep"
    )
    for file_path in file_paths:
        try:
            payload = run_chi_for_file(
                evaluator_path=evaluator_path,
                file_path=file_path,
                workbook_path=workbook_path,
                source=str(file_path.relative_to(source_dir)),
            )
            file_packets = iter_claim_packets(payload, file_path, fruit_lex, anti_penalty_weight=anti_penalty_weight)
            for p in file_packets:
                # trim ranking to requested top_k_axes
                p["fruit_ranking"]["fruits"] = p["fruit_ranking"]["fruits"][:top_k_axes]
                p["fruit_ranking"]["anti_fruits"] = p["fruit_ranking"]["anti_fruits"][:top_k_axes]
            packets.extend(file_packets)
        except Exception as exc:
            packets.append({
                "packet_id": f"{file_path.stem}::failed",
                "source_file": str(file_path),
                "source_tag": str(file_path.name),
                "claim_id": "failed",
                "claim_index": 0,
                "claim_text": "",
                "claim_char_len": 0,
                "chi_static": 0.0,
                "chi_gradient": 0.0,
                "chi_direction": "failed",
                "chi_verdict": "error",
                "chi_confidence": 0.0,
                "fruit_score": 0.0,
                "fruit_bias_strength": 0.0,
                "truth_score": 0.0,
                "truth_components": {},
                "channel_features": {},
                "fruit_ranking": {"fruits": [], "anti_fruits": []},
                "run_meta": {"error": str(exc)},
            })
    return packets


def write_summary(packets: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not packets:
        return {"total_packets": 0}

    def mean(v: List[float]) -> float:
        return round(sum(v) / len(v), 6) if v else 0.0

    chi_vals = [_safe_float(p.get("chi_static", 0.0)) for p in packets]
    fruit_vals = [_safe_float(p.get("fruit_score", 0.0)) for p in packets]
    truth_vals = [_safe_float(p.get("truth_score", 0.0)) for p in packets]
    verdict_counts: Dict[str, int] = {}
    for p in packets:
        verdict_counts[str(p.get("chi_verdict", "unknown"))] = verdict_counts.get(str(p.get("chi_verdict", "unknown")), 0) + 1
    return {
        "total_packets": len(packets),
        "chi_static_mean": mean(chi_vals),
        "fruit_score_mean": mean(fruit_vals),
        "truth_score_mean": mean(truth_vals),
        "chi_verdict_counts": verdict_counts,
        "source_counts": dict(Counter(str(p.get("source_file", "unknown")) for p in packets)),
    }


def write_excel_bundle(
    packets: List[Dict[str, Any]],
    summary: Dict[str, Any],
    out_dir: pathlib.Path,
    out_name: str = "feature_bundle.xlsx",
) -> pathlib.Path:
    if openpyxl is None:
        raise RuntimeError("openpyxl not available; cannot write Excel bundle.")

    wb = openpyxl.Workbook()
    ws_packets = wb.active
    ws_packets.title = "Packets"
    ws_packets.append([
        "packet_id",
        "source_file",
        "claim_id",
        "claim_index",
        "claim_char_len",
        "chi_static",
        "chi_gradient",
        "chi_direction",
        "chi_verdict",
        "chi_confidence",
        "fruit_score",
        "fruit_bias_strength",
        "truth_score",
        "truth_S",
        "truth_E",
        "truth_L",
        "truth_D",
        "truth_P",
        "truth_C",
        "run_id",
        "fruit_top_axes",
        "anti_fruit_top_axes",
        "packet_json",
    ])
    for p in packets:
        truth = p.get("truth_components", {})
        fruits = p.get("fruit_ranking", {}).get("fruits", [])
        anti = p.get("fruit_ranking", {}).get("anti_fruits", [])
        ws_packets.append([
            p.get("packet_id"),
            p.get("source_file"),
            p.get("claim_id"),
            p.get("claim_index"),
            p.get("claim_char_len"),
            p.get("chi_static"),
            p.get("chi_gradient"),
            p.get("chi_direction"),
            p.get("chi_verdict"),
            p.get("chi_confidence"),
            p.get("fruit_score"),
            p.get("fruit_bias_strength"),
            p.get("truth_score"),
            truth.get("S"),
            truth.get("E"),
            truth.get("L"),
            truth.get("D"),
            truth.get("P"),
            truth.get("C"),
            (p.get("run_meta") or {}).get("run_id"),
            "; ".join(f'{i["axis"]}:{i["score"]}' for i in fruits),
            "; ".join(f'{i["axis"]}:{i["score"]}' for i in anti),
            json.dumps(p, ensure_ascii=False),
        ])

    ws_summary = wb.create_sheet("Summary")
    ws_summary.append(["metric", "value"])
    for key, value in summary.items():
        if key == "source_counts":
            continue
        ws_summary.append([key, json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value])

    ws_sources = wb.create_sheet("SourceCounts")
    ws_sources.append(["source_file", "packet_count"])
    for src, count in summary.get("source_counts", {}).items():
        ws_sources.append([src, count])

    ws_model = wb.create_sheet("TruthAndChannels")
    ws_model.append([
        "packet_id",
        "source_file",
        "weakest_channels",
        "strongest_channels",
        "zero_channels",
        "chi_effective_mean",
        "chi_effective_std",
        "chi_pos_mean",
        "chi_neg_mean",
        "chi_confidence_mean",
    ])
    for p in packets:
        ch = p.get("channel_features", {})
        ws_model.append([
            p.get("packet_id"),
            p.get("source_file"),
            ", ".join(p.get("channel_features", {}).get("zero_channels", [])),
            ", ".join(p.get("channel_features", {}).get("strongest", [])),
            ", ".join(ch.get("weakest", [])),
            ch.get("chi_effective_mean"),
            ch.get("chi_effective_std"),
            ch.get("chi_pos_mean"),
            ch.get("chi_neg_mean"),
            ch.get("chi_confidence_mean"),
        ])

    out_path = out_dir / out_name
    wb.save(out_path)
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create χ/7Q feature packets for model review.")
    parser.add_argument("--source-dir", default=None, help="Folder with source files")
    parser.add_argument("--evaluator", default=None, help="Path to chi_evaluator_7q.py")
    parser.add_argument("--workbook", default=None, help="Path to 7Q Full Method.xlsx")
    parser.add_argument("--out-dir", default="features", help="Output folder")
    parser.add_argument("--packets-file", default="feature_packets.jsonl", help="Packet JSONL filename")
    parser.add_argument("--summary-file", default="feature_summary.json", help="Summary filename")
    parser.add_argument("--top-axes", type=int, default=5, help="Top fruit/anti-fruit axes to keep")
    parser.add_argument("--anti-penalty", type=float, default=None, help="Override anti-fruit penalty (default from config)")
    return parser.parse_args()


def main() -> int:
    cfg = parse_config(pathlib.Path(__file__).with_name("config.txt"))
    args = parse_args()

    base = pathlib.Path(cfg.get("WORK_DIR", pathlib.Path(__file__).parent))
    source_dir = pathlib.Path(args.source_dir or cfg.get("SOURCE_DIR", "INBOX"))
    if not source_dir.is_absolute():
        source_dir = (base / source_dir).resolve()
    evaluator_path = pathlib.Path(args.evaluator or cfg.get("CHI_EVALUATOR_PATH", ""))
    workbook_path = pathlib.Path(args.workbook or cfg.get("CHI_WORKBOOK_PATH", ""))

    if not evaluator_path.exists():
        print(f"ERROR: χ evaluator not found: {evaluator_path}", file=sys.stderr)
        return 1
    if not workbook_path.exists():
        print(f"ERROR: workbook not found: {workbook_path}", file=sys.stderr)
        return 1

    anti_penalty = (
        float(args.anti_penalty)
        if args.anti_penalty is not None
        else float(cfg.get("ANTI_FRUIT_PENALTY", "1.35") or "1.35")
    )

    out_dir = pathlib.Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (base / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    packets = extract_from_source(
        source_dir=source_dir,
        evaluator_path=evaluator_path,
        workbook_path=workbook_path,
        top_k_axes=args.top_axes,
        anti_penalty_weight=anti_penalty,
    )
    packets_path = out_dir / args.packets_file
    with packets_path.open("w", encoding="utf-8") as handle:
        for p in packets:
            handle.write(json.dumps(p, ensure_ascii=False) + "\n")

    summary = write_summary(packets)
    summary_path = out_dir / args.summary_file
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    excel_path = write_excel_bundle(
        packets=packets,
        summary=summary,
        out_dir=out_dir,
    )

    print(f"Packet file: {packets_path}")
    print(f"Summary   : {summary_path}")
    print(f"Excel     : {excel_path}")
    print(f"Packets   : {len(packets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
