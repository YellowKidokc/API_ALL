#!/usr/bin/env python3
"""
artifact_manifest.py

Universal Artifact Manifest for file-intelligence.station.

Purpose:
    Turn FIS pipeline output into a standard handoff object every other station can consume.

Input:
    - path to file
    - optional FIS classification JSON
    - optional extracted text

Output:
    .fis_manifest.json containing:
    - artifact identity
    - safe metadata
    - detected features
    - recommended station routes
    - reasons
    - optional Portable Preference Kernel predictions

This is the missing contract between file-intelligence.station and the rest
of David's station network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

try:
    from portable_preference_kernel import PortablePreferenceKernel
except Exception:
    PortablePreferenceKernel = None


STATION_RULES = [
    ("metadata-extractor.station", "always useful after ingestion", lambda f: True),
    ("section-splitter.station", "long markdown/text/html document", lambda f: f["is_text_doc"] and f["word_count"] >= 400),
    ("claim-extractor.station", "claim language detected", lambda f: f["has_claim_language"]),
    ("7q-classifier.station", "claims detected; route to 7Q", lambda f: f["has_claim_language"]),
    ("paper-proof-grader.station", "paper-like document with claims/evidence", lambda f: f["is_paper_like"] and (f["has_claim_language"] or f["has_evidence_language"])),
    ("math-layer.station", "math/equation content detected", lambda f: f["has_math"]),
    ("math-translation-layer.station", "equations need reader-facing explanation", lambda f: f["has_math"]),
    ("fruits-spirit-canon.station", "fruit/coherence/virtue polarity terms detected", lambda f: f["has_fruit_terms"]),
    ("readability-rewriter.station", "paper/article likely needs reader layers", lambda f: f["is_paper_like"]),
    ("sbert-embedder.station", "text is suitable for vectorization", lambda f: f["is_text_doc"] and f["word_count"] > 100),
    ("graph-linker.station", "canonical/cross-domain terms detected", lambda f: f["has_canon_terms"]),
    ("html-article.station", "article/paper can be published", lambda f: f["is_paper_like"]),
    ("obsidian-export.station", "markdown/canon note should be vault-ready", lambda f: f["suffix"] in {".md", ".markdown", ".txt"}),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_read_text(path: Path, max_chars: int = 200000) -> str:
    if path.suffix.lower() in {".md", ".markdown", ".txt", ".html", ".htm", ".json", ".csv", ".py", ".lean"}:
        raw = path.read_text(encoding="utf-8", errors="replace")
        raw = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw)
        raw = re.sub(r"(?is)<style.*?>.*?</style>", " ", raw)
        raw = re.sub(r"(?is)<[^>]+>", " ", raw)
        return raw[:max_chars]
    return ""


def detect_features(path: Path, text: str, fis_result: Dict[str, Any] | None = None) -> Dict[str, Any]:
    lower = text.lower()
    suffix = path.suffix.lower()
    word_count = len(re.findall(r"\b[\w'-]+\b", text))

    features = {
        "file_name": path.name,
        "suffix": suffix,
        "size_bytes_bucket": (
            "tiny" if path.stat().st_size < 50_000 else
            "small" if path.stat().st_size < 500_000 else
            "medium" if path.stat().st_size < 5_000_000 else
            "large"
        ),
        "is_text_doc": suffix in {".md", ".markdown", ".txt", ".html", ".htm", ".json", ".csv", ".py", ".lean"},
        "is_paper_like": bool(re.search(r"\b(abstract|introduction|conclusion|references|methodology|thesis|paper)\b", lower)),
        "word_count": word_count,
        "has_yaml": text.lstrip().startswith("---"),
        "has_math": bool(re.search(r"(\$\$|\\\[|\\frac|\\int|\\sum|χ|\\chi|∫|∑|=)", text)),
        "has_claim_language": bool(re.search(r"\b(claim|thesis|argue|proves?|demonstrates?|therefore|hypothesis|axiom)\b", lower)),
        "has_evidence_language": bool(re.search(r"\b(evidence|data|study|review|meta-analysis|citation|source|observed|measured|replicated)\b", lower)),
        "has_falsifier_language": bool(re.search(r"\b(falsif|kill condition|defeat condition|would fail|counterexample)\b", lower)),
        "has_citations": bool(re.search(r"(\[[^\]]+\]\([^)]+\)|\[\d+\]|\(\d{4}\)|doi:|https?://)", text, re.I)),
        "has_tables": "|" in text and "---" in text,
        "has_scripture": bool(re.search(r"\b(john|romans|genesis|matthew|hebrews|colossians|galatians|revelation|psalm|proverbs)\s+\d+", lower)),
        "has_audio": bool(re.search(r"\.(mp3|wav|m4a|webm)", lower)),
        "has_images": bool(re.search(r"\.(png|jpg|jpeg|webp|gif)|!\[", lower)),
        "has_fruit_terms": bool(re.search(r"\b(love|joy|peace|patience|kindness|goodness|faithfulness|gentleness|self-control|grace|coherence|entropy)\b", lower)),
        "has_canon_terms": bool(re.search(r"\b(master equation|logos|chi|χ|trinity|resurrection|grace operator|justice|mercy|axiom|no-drift)\b", lower)),
        "domain_hint": (fis_result or {}).get("domain"),
        "subjects_hint": (fis_result or {}).get("subjects", []),
        "confidence_hint": (fis_result or {}).get("confidence"),
    }
    return features


def route_plan(features: Dict[str, Any]) -> List[Dict[str, Any]]:
    routes = []
    for station, reason, predicate in STATION_RULES:
        try:
            if predicate(features):
                routes.append({"station": station, "reason": reason, "confidence": 0.75})
        except Exception:
            continue
    return routes


def build_manifest(path: Path, fis_result: Dict[str, Any] | None = None, model_path: Path | None = None) -> Dict[str, Any]:
    text = safe_read_text(path)
    features = detect_features(path, text, fis_result)
    routes = route_plan(features)

    preference_prediction = None
    if PortablePreferenceKernel is not None and model_path:
        kernel = PortablePreferenceKernel(model_path)
        preference_prediction = kernel.predict(features, top_k=8)
        # Merge top route actions into route list.
        for rec in preference_prediction.get("recommendations", []):
            action = rec["action"]
            if action.startswith("route:"):
                station = action.split("route:", 1)[1]
                if not any(r["station"] == station for r in routes):
                    routes.append({
                        "station": station,
                        "reason": "portable preference kernel recommendation",
                        "confidence": rec["confidence"],
                        "preference_score": rec["score"],
                    })

    artifact_id = "art-" + sha256_file(path)[:16]
    return {
        "schema": "theophysics.artifact_manifest.v1",
        "artifact_id": artifact_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": {
            "path": str(path.resolve()),
            "name": path.name,
            "suffix": path.suffix.lower(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        },
        "fis": fis_result or {},
        "features": features,
        "routes": routes,
        "preference_prediction": preference_prediction,
        "privacy": {
            "contains_raw_text": False,
            "contains_content_hash_only": True,
            "safe_to_sync": True,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path)
    ap.add_argument("--fis-result", type=Path, default=None)
    ap.add_argument("--model-path", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    fis_result = None
    if args.fis_result and args.fis_result.exists():
        fis_result = json.loads(args.fis_result.read_text(encoding="utf-8"))

    manifest = build_manifest(args.file, fis_result, args.model_path)
    out = args.out or args.file.with_suffix(args.file.suffix + ".fis_manifest.json")
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
