#!/usr/bin/env python3
"""
portable_preference_kernel.py

Portable Preference Kernel (PPK / DPK)
======================================

A tiny private model that learns David's operating preferences without storing
raw personal data.

It stores:
- feature/action weights
- counts
- route preferences
- confidence stats

It does NOT store:
- file contents
- clipboard contents
- screenshots
- emails
- raw browser pages
- passwords
- bank data

Core idea:
    context_features -> suggested action / route -> human accepts/edits -> reward update

Use cases:
- file-intelligence.station routing
- station recommendations
- naming/action preferences
- daily AI session preference summaries
- portable identity kernel copied between machines

This is deliberately simple first:
- pure Python, no required ML dependency
- optional River can be added later
- JSON model file is portable

Examples:
    python portable_preference_kernel.py predict --features examples/sample_features.json
    python portable_preference_kernel.py learn --features examples/sample_features.json --action "route:claim-extractor.station" --reward 1
    python portable_preference_kernel.py export-summary
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_MODEL_PATH = Path(os.getenv("PPK_MODEL_PATH", "portable_preference_kernel.json"))


SENSITIVE_KEYS = {
    "text", "content", "clipboard", "clipboard_text", "raw_text", "body",
    "email", "password", "token", "api_key", "secret", "screenshot", "image",
}


DEFAULT_ACTIONS = [
    "route:metadata-extractor.station",
    "route:section-splitter.station",
    "route:claim-extractor.station",
    "route:7q-classifier.station",
    "route:paper-proof-grader.station",
    "route:math-layer.station",
    "route:math-translation-layer.station",
    "route:fruits-spirit-canon.station",
    "route:readability-rewriter.station",
    "route:html-article.station",
    "route:obsidian-export.station",
    "route:graph-linker.station",
    "route:sbert-embedder.station",
]


def _safe_value(v: Any) -> Any:
    """Keep only small, non-sensitive feature values."""
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v if abs(v) < 10_000_000 else "large_int"
    if isinstance(v, float):
        if math.isfinite(v):
            return round(v, 4)
        return "nonfinite"
    if isinstance(v, str):
        v = v.strip()
        if len(v) > 80:
            # Hash long strings instead of storing raw content.
            return "hash:" + hashlib.sha256(v.encode("utf-8", errors="ignore")).hexdigest()[:16]
        return v
    if isinstance(v, list):
        out = []
        for item in v[:20]:
            out.append(_safe_value(item))
        return out
    if isinstance(v, dict):
        return sanitize_features(v)
    return str(type(v).__name__)


def sanitize_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """Remove raw personal data and keep only portable feature signals."""
    clean = {}
    for k, v in (features or {}).items():
        lk = str(k).lower()
        if any(s in lk for s in SENSITIVE_KEYS):
            # Keep only a hash/length where useful, never raw content.
            if isinstance(v, str):
                clean[f"{k}_len"] = len(v)
                clean[f"{k}_hash"] = hashlib.sha256(v.encode("utf-8", errors="ignore")).hexdigest()[:16]
            continue
        clean[k] = _safe_value(v)
    return clean


def flatten_features(features: Dict[str, Any]) -> List[str]:
    """Convert nested feature dict into stable feature tokens."""
    features = sanitize_features(features)
    tokens = []

    def walk(prefix: str, obj: Any):
        if isinstance(obj, dict):
            for k, v in sorted(obj.items()):
                walk(f"{prefix}.{k}" if prefix else str(k), v)
        elif isinstance(obj, list):
            for item in obj[:20]:
                walk(prefix, item)
        elif isinstance(obj, bool):
            tokens.append(f"{prefix}={int(obj)}")
        elif isinstance(obj, (int, float)):
            # bucket numeric values so model generalizes.
            if prefix.endswith(("word_count", "chars", "length", "size")):
                if obj < 500: bucket = "tiny"
                elif obj < 2000: bucket = "short"
                elif obj < 8000: bucket = "medium"
                elif obj < 30000: bucket = "long"
                else: bucket = "huge"
                tokens.append(f"{prefix}_bucket={bucket}")
            elif prefix in {"hour", "time_of_day"}:
                hour = int(obj) % 24
                if 0 <= hour < 6: bucket = "night"
                elif 6 <= hour < 12: bucket = "morning"
                elif 12 <= hour < 18: bucket = "afternoon"
                else: bucket = "evening"
                tokens.append(f"{prefix}_bucket={bucket}")
            else:
                tokens.append(f"{prefix}≈{round(float(obj), 2)}")
        else:
            val = str(obj).strip().lower().replace(" ", "_")
            if val:
                tokens.append(f"{prefix}={val}")

    walk("", features)
    return tokens


class PortablePreferenceKernel:
    """Tiny portable contextual action predictor."""

    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH):
        self.model_path = Path(model_path)
        self.data = {
            "schema": "theophysics.portable_preference_kernel.v1",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": None,
            "actions": sorted(DEFAULT_ACTIONS),
            "bias": {},
            "weights": {},   # action -> feature -> weight
            "counts": {},    # action -> count
            "events_seen": 0,
            "privacy": {
                "stores_raw_content": False,
                "stores_feature_weights_only": True,
                "sensitive_keys_filtered": sorted(SENSITIVE_KEYS),
            },
        }
        self.load()

    def load(self) -> None:
        if self.model_path.exists():
            self.data.update(json.loads(self.model_path.read_text(encoding="utf-8")))

    def save(self) -> None:
        self.data["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.model_path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def learn(self, features: Dict[str, Any], action: str, reward: float = 1.0, lr: float = 0.25) -> Dict[str, Any]:
        """Update action preference from a rewarded/corrected event.

        reward:
            +1.0 accepted
            +0.5 partially useful
            -1.0 rejected
        """
        clean = sanitize_features(features)
        tokens = flatten_features(clean)
        self.data["actions"] = sorted(set(self.data.get("actions", [])) | {action})
        self.data.setdefault("weights", {}).setdefault(action, {})
        self.data.setdefault("bias", {}).setdefault(action, 0.0)
        self.data.setdefault("counts", {}).setdefault(action, 0)

        # bias learns global action preference.
        self.data["bias"][action] += lr * reward
        for tok in tokens:
            old = self.data["weights"][action].get(tok, 0.0)
            self.data["weights"][action][tok] = round(old + lr * reward, 6)

        self.data["counts"][action] += 1
        self.data["events_seen"] = int(self.data.get("events_seen", 0)) + 1
        self.save()

        return {
            "status": "learned",
            "action": action,
            "reward": reward,
            "feature_count": len(tokens),
            "stored_raw_content": False,
        }

    def score_action(self, features: Dict[str, Any], action: str) -> float:
        tokens = flatten_features(features)
        score = float(self.data.get("bias", {}).get(action, 0.0))
        weights = self.data.get("weights", {}).get(action, {})
        for tok in tokens:
            score += float(weights.get(tok, 0.0))
        return score

    def predict(self, features: Dict[str, Any], top_k: int = 5) -> Dict[str, Any]:
        clean = sanitize_features(features)
        tokens = flatten_features(clean)
        actions = self.data.get("actions", DEFAULT_ACTIONS)
        scored = [(a, self.score_action(clean, a)) for a in actions]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Convert scores to softmax-ish confidence.
        top = scored[:top_k]
        if not top:
            return {"recommendations": [], "features_used": tokens}

        max_s = max(s for _, s in top)
        exp = [(a, math.exp(min(8, s - max_s))) for a, s in top]
        denom = sum(v for _, v in exp) or 1.0
        recs = []
        for (action, raw), (_, ev) in zip(top, exp):
            recs.append({
                "action": action,
                "score": round(raw, 4),
                "confidence": round(ev / denom, 4),
                "reason": self.explain(clean, action, limit=5),
            })

        return {
            "schema": "theophysics.ppk.prediction.v1",
            "recommendations": recs,
            "features_used": tokens,
            "stored_raw_content": False,
        }

    def explain(self, features: Dict[str, Any], action: str, limit: int = 5) -> List[Dict[str, Any]]:
        tokens = flatten_features(features)
        weights = self.data.get("weights", {}).get(action, {})
        hits = [(tok, weights.get(tok, 0.0)) for tok in tokens if weights.get(tok, 0.0) != 0]
        hits.sort(key=lambda x: abs(x[1]), reverse=True)
        return [{"feature": tok, "weight": round(w, 4)} for tok, w in hits[:limit]]

    def export_summary(self) -> Dict[str, Any]:
        actions = []
        for action in self.data.get("actions", []):
            actions.append({
                "action": action,
                "count": self.data.get("counts", {}).get(action, 0),
                "bias": round(self.data.get("bias", {}).get(action, 0.0), 4),
                "top_features": sorted(
                    [
                        {"feature": k, "weight": v}
                        for k, v in self.data.get("weights", {}).get(action, {}).items()
                    ],
                    key=lambda x: abs(x["weight"]),
                    reverse=True
                )[:10]
            })
        return {
            "schema": "theophysics.ppk.summary.v1",
            "model_path": str(self.model_path),
            "events_seen": self.data.get("events_seen", 0),
            "updated_at": self.data.get("updated_at"),
            "privacy": self.data.get("privacy", {}),
            "actions": actions,
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("predict")
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--top-k", type=int, default=5)

    l = sub.add_parser("learn")
    l.add_argument("--features", type=Path, required=True)
    l.add_argument("--action", required=True)
    l.add_argument("--reward", type=float, default=1.0)

    s = sub.add_parser("export-summary")

    args = ap.parse_args()
    kernel = PortablePreferenceKernel(args.model_path)

    if args.cmd == "predict":
        features = json.loads(args.features.read_text(encoding="utf-8"))
        print(json.dumps(kernel.predict(features, args.top_k), indent=2, ensure_ascii=False))
    elif args.cmd == "learn":
        features = json.loads(args.features.read_text(encoding="utf-8"))
        print(json.dumps(kernel.learn(features, args.action, args.reward), indent=2, ensure_ascii=False))
    elif args.cmd == "export-summary":
        print(json.dumps(kernel.export_summary(), indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
