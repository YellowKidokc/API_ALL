#!/usr/bin/env python3
"""
run_review_models.py
====================
Send feature packets to DeepSeek + OpenAI and save model review outputs.
Models do not see formulas; they only see ranked fruits/anti-fruits + χ/7Q metrics.
"""

from __future__ import annotations

import argparse
import json
import time
import pathlib
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    import openpyxl  # type: ignore
except Exception:  # pragma: no cover
    openpyxl = None  # type: ignore


def parse_config(path: pathlib.Path) -> Dict[str, str]:
    cfg = {}
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run model review passes on feature packets.")
    parser.add_argument("--packets", default=None, help="Path to packets JSONL")
    parser.add_argument("--reviews-dir", default="reviews", help="Output folder")
    parser.add_argument("--prompt-template", default="prompts/claim_review_prompt.txt", help="Prompt template")
    parser.add_argument("--max-items", type=int, default=0, help="Max packets to run (0 = all)")
    parser.add_argument("--top-models", default="openai,deepseek", help="Comma-separated list: openai,deepseek")
    parser.add_argument("--run-id", default=None, help="Optional run id folder name")
    return parser.parse_args()


def fill_prompt(template: str, packet: Dict[str, Any], packet_num: int) -> str:
    packet_block = json.dumps(packet, ensure_ascii=False, indent=2)
    return template.replace("{{packet_json}}", packet_block).replace("{{packet_num}}", str(packet_num))


def safe_file_token(value: Any) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]", "_", str(value))
    return token[:120] if token else "packet"


def read_packets(path: pathlib.Path) -> List[Dict[str, Any]]:
    data = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


def parse_api_response(content: str) -> Dict[str, Any]:
    if not content:
        return {"coherence_score": None, "fruit_bias_score": None, "confidence": None, "label": None, "rationale": [], "dominant_signal": "", "dominant_risk": ""}
    try:
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        parsed = json.loads(text)
        return {
            "coherence_score": parsed.get("coherence_score"),
            "fruit_bias_score": parsed.get("fruit_bias_score"),
            "confidence": parsed.get("confidence"),
            "label": parsed.get("label"),
            "rationale": parsed.get("rationale", []),
            "dominant_signal": parsed.get("dominant_signal", ""),
            "dominant_risk": parsed.get("dominant_risk", ""),
        }
    except Exception:
        return {
            "coherence_score": None,
            "fruit_bias_score": None,
            "confidence": None,
            "label": None,
            "rationale": [content[:1200]],
            "dominant_signal": "",
            "dominant_risk": "",
        }


def call_openai_chat(
    model: str,
    key: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    base_url: Optional[str] = None,
) -> Tuple[str, int, int, float]:
    import openai  # type: ignore

    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if model.startswith("o1") or model.startswith("o3"):
        kwargs["max_completion_tokens"] = max_tokens or 1024
    else:
        kwargs["max_tokens"] = max_tokens or 1024
        kwargs["temperature"] = temperature

    client = openai.OpenAI(api_key=key, base_url=base_url) if base_url else openai.OpenAI(api_key=key)
    t0 = time.time()
    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as exc:
        raise RuntimeError(f"OpenAI API error ({model}): {exc}") from exc
    elapsed = time.time() - t0
    content = (resp.choices[0].message.content or "").strip()
    usage = resp.usage
    in_tok = usage.prompt_tokens if usage else 0
    out_tok = usage.completion_tokens if usage else 0
    return content, in_tok, out_tok, elapsed


def call_deepseek(
    model: str,
    key: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> Tuple[str, int, int, float]:
    import openai  # type: ignore

    client = openai.OpenAI(api_key=key, base_url="https://api.deepseek.com")
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            temperature=temperature,
            max_tokens=max_tokens or 1024,
        )
    except Exception as exc:
        raise RuntimeError(f"DeepSeek API error ({model}): {exc}") from exc
    elapsed = time.time() - t0
    content = (resp.choices[0].message.content or "").strip()
    usage = resp.usage
    in_tok = usage.prompt_tokens if usage else 0
    out_tok = usage.completion_tokens if usage else 0
    return content, in_tok, out_tok, elapsed


def main() -> int:
    cfg = parse_config(pathlib.Path(__file__).with_name("config.txt"))
    args = parse_args()

    base = pathlib.Path(cfg.get("WORK_DIR", pathlib.Path(__file__).parent))
    packets_path = pathlib.Path(args.packets or base / "features" / "feature_packets.jsonl")
    prompt_path = pathlib.Path(args.prompt_template)
    if not prompt_path.exists():
        prompt_path = base / args.prompt_template
    if not packets_path.exists():
        print(f"ERROR: packets not found: {packets_path}", file=sys.stderr)
        return 1

    reviews_root = pathlib.Path(args.reviews_dir)
    if not reviews_root.is_absolute():
        reviews_root = base / reviews_root
    run_id = args.run_id or time.strftime("%Y%m%d_%H%M%S")
    out_dir = reviews_root / f"run_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    max_items = args.max_items
    packets = read_packets(packets_path)
    if max_items and max_items > 0:
        packets = packets[:max_items]

    template = prompt_path.read_text(encoding="utf-8")
    top_models = {s.strip().lower() for s in args.top_models.split(",") if s.strip()}

    openai_key = cfg.get("OPENAI_API_KEY", "")
    deepseek_key = cfg.get("DEEPSEEK_API_KEY", "")

    merged: List[Dict[str, Any]] = []

    for i, packet in enumerate(packets, 1):
        packet_id = str(packet.get("packet_id", f"packet-{i}"))
        prompt = fill_prompt(template, packet, i)

        result: Dict[str, Any] = {
            "packet_id": packet_id,
            "packet": packet,
            "models": {},
        }
        safe_pid = safe_file_token(packet_id)

        # DeepSeek
        if "deepseek" in top_models and deepseek_key and "PASTE" not in deepseek_key:
            try:
                content, in_tok, out_tok, elapsed = call_deepseek(
                    model=cfg.get("DEEPSEEK_MODEL", "deepseek-chat"),
                    key=deepseek_key,
                    prompt=prompt,
                    max_tokens=int(cfg.get("DEEPSEEK_MAX_TOKENS", "1024") or "1024"),
                    temperature=float(cfg.get("DEEPSEEK_TEMPERATURE", "0.2") or "0.2"),
                )
                parsed = parse_api_response(content)
                result["models"]["deepseek"] = {
                    "raw": content,
                    "parsed": parsed,
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "latency_s": round(elapsed, 3),
                }
                (out_dir / f"{safe_pid}_deepseek.txt").write_text(content, encoding="utf-8")
            except Exception as exc:
                result["models"]["deepseek"] = {"error": str(exc)}

        # OpenAI
        if "openai" in top_models and openai_key and "PASTE" not in openai_key:
            try:
                content, in_tok, out_tok, elapsed = call_openai_chat(
                    model=cfg.get("OPENAI_MODEL", "o3-mini"),
                    key=openai_key,
                    prompt=prompt,
                    max_tokens=int(cfg.get("OPENAI_MAX_TOKENS", "1024") or "1024"),
                    temperature=float(cfg.get("OPENAI_TEMPERATURE", "0.2") or "0.2"),
                    base_url=None,
                )
                parsed = parse_api_response(content)
                result["models"]["openai"] = {
                    "raw": content,
                    "parsed": parsed,
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "latency_s": round(elapsed, 3),
                }
                (out_dir / f"{safe_pid}_openai.txt").write_text(content, encoding="utf-8")
            except Exception as exc:
                result["models"]["openai"] = {"error": str(exc)}

        merged.append(result)

    merged_path = out_dir / "model_reviews.jsonl"
    with merged_path.open("w", encoding="utf-8") as handle:
        for rec in merged:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")

    excel_path = out_dir / "model_reviews.xlsx"
    if openpyxl is not None:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "ModelReviews"
        ws.append([
            "packet_id",
            "source_file",
            "claim_id",
            "chi_verdict",
            "chi_static",
            "fruit_score",
            "truth_score",
            "model",
            "label",
            "coherence_score",
            "fruit_bias_score",
            "confidence",
            "dominant_signal",
            "dominant_risk",
            "input_tokens",
            "output_tokens",
            "latency_s",
            "rationale",
            "raw_response",
        ])

        for rec in merged:
            packet = rec.get("packet", {})
            base_row = [
                rec.get("packet_id"),
                packet.get("source_file"),
                packet.get("claim_id"),
                packet.get("chi_verdict"),
                packet.get("chi_static"),
                packet.get("fruit_score"),
                packet.get("truth_score"),
            ]
            for model_name, payload in rec.get("models", {}).items():
                parsed = payload.get("parsed", {})
                ws.append(
                    base_row + [
                        model_name,
                        parsed.get("label"),
                        parsed.get("coherence_score"),
                        parsed.get("fruit_bias_score"),
                        parsed.get("confidence"),
                        parsed.get("dominant_signal", ""),
                        parsed.get("dominant_risk", ""),
                        payload.get("input_tokens"),
                        payload.get("output_tokens"),
                        payload.get("latency_s"),
                        "; ".join(str(x) for x in (parsed.get("rationale", []) or [])),
                        payload.get("raw", ""),
                    ]
                )
            if not rec.get("models"):
                ws.append(base_row + ["", "", "", "", "", "", "", "", "", "", "", "", ""])

    ws_summary = wb.create_sheet("RunSummary")
    ws_summary.append(["run_id", "packet_count"])
        ws_summary.append([run_id, len(merged)])
        ws_summary.append(["requested_models", ", ".join(sorted(top_models))])
        ws_summary.append(["success_records", summary["result_count"]])

        wb.save(excel_path)
    else:
        excel_path = out_dir / "model_reviews.xlsx.missing_openpyxl"

    summary = {
        "run_id": run_id,
        "packet_count": len(merged),
        "requested_models": sorted(top_models),
        "result_count": sum(1 for rec in merged if rec["models"]),
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Run folder: {out_dir}")
    print(f"Merged    : {merged_path}")
    print(f"Excel     : {excel_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
