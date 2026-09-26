#!/usr/bin/env python3
"""Evidence-rich Fruits of the Spirit batch grader.

The JSON result is authoritative. Markdown is a deterministic rendering of JSON.
No API key is ever read from config; config names environment variables only.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import glob
import hashlib
import html
import json
import math
import os
import pathlib
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


SPEC_VERSION = "0.3.0"
FRUIT_IDS = [
    "fruit.love", "fruit.joy", "fruit.peace", "fruit.patience",
    "fruit.kindness", "fruit.goodness", "fruit.faithfulness",
    "fruit.gentleness", "fruit.self_control",
]
GATE_IDS = [
    "gate.truth_evidence", "gate.contradiction", "gate.scope",
    "gate.falsifiability", "gate.bridge_validity", "gate.provenance",
    "gate.agency_noncoercion",
]
HARD_GATES = {"gate.truth_evidence", "gate.contradiction", "gate.agency_noncoercion"}
STRESS_IDS = ["source", "cost", "endurance", "relation", "power", "correction", "outsider", "succession"]
ALLOWED_STRESS = {"PASS", "WARN", "FAIL", "UNKNOWN"}
OUTPUT_LOCK = threading.Lock()


class StationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Provider:
    name: str
    api_kind: str
    base_url: str
    model: str
    api_key_env: str
    temperature: float | None
    max_output_tokens: int | None
    output_token_parameter: str | None


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json_atomic(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_text_atomic(path: pathlib.Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def resolve_from(base: pathlib.Path, raw: str) -> pathlib.Path:
    expanded = os.path.expandvars(raw)
    if os.name != "nt":
        expanded = expanded.replace("\\", os.sep)
    p = pathlib.Path(expanded)
    return p if p.is_absolute() else (base / p).resolve()


def load_config(config_path: pathlib.Path) -> tuple[dict[str, Any], pathlib.Path]:
    config_path = config_path.resolve()
    config = read_json(config_path)
    return config, config_path.parent


def extract_text(path: pathlib.Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    if suffix in {".html", ".htm"}:
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
        raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
        return html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))
    if suffix == ".docx":
        try:
            from docx import Document  # type: ignore
        except ImportError as exc:
            raise StationError("python-docx is required to read DOCX files") from exc
        doc = Document(str(path))
        blocks = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                blocks.append("\t".join(cell.text for cell in row.cells))
        return "\n".join(blocks)
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError as exc:
            raise StationError("pypdf is required to read PDF files") from exc
        reader = PdfReader(str(path))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    raise StationError(f"Unsupported input type: {suffix}")


def discover_sources(input_dir: pathlib.Path, config: dict[str, Any]) -> list[pathlib.Path]:
    if not input_dir.exists():
        raise StationError(f"Input directory not found: {input_dir}")
    allowed = {x.lower() for x in config.get("include_extensions", [])}
    excluded = [x.lower() for x in config.get("exclude_name_contains", [])]
    files = []
    for p in input_dir.rglob("*"):
        lowered = p.name.lower()
        if p.is_file() and p.suffix.lower() in allowed and not any(x in lowered for x in excluded):
            files.append(p)
    return sorted(files, key=lambda p: str(p).lower())


def active_providers(config: dict[str, Any]) -> list[Provider]:
    providers = []
    for item in config.get("providers", []):
        env_name = item.get("api_key_env", "")
        if env_name and os.environ.get(env_name):
            raw_temperature = item.get("temperature")
            model = os.environ.get(item.get("model_env", ""), item["model"])
            providers.append(Provider(
                name=item["name"], api_kind=item.get("api_kind", "chat_completions"),
                base_url=item["base_url"].rstrip("/"), model=model,
                api_key_env=env_name, temperature=None if raw_temperature is None else float(raw_temperature),
                max_output_tokens=int(item["max_output_tokens"]) if item.get("max_output_tokens") else None,
                output_token_parameter=item.get("output_token_parameter"),
            ))
    return providers


def workbook_manifest(config: dict[str, Any]) -> list[dict[str, Any]]:
    raw_dir = os.path.expandvars(config.get("workbook_directory", ""))
    if not raw_dir:
        return []
    directory = pathlib.Path(raw_dir)
    if not directory.exists():
        return [{"directory": raw_dir, "status": "UNAVAILABLE_IN_CURRENT_ENVIRONMENT"}]
    found: list[pathlib.Path] = []
    for pattern in config.get("workbook_patterns", []):
        found.extend(pathlib.Path(p) for p in glob.glob(str(directory / pattern)))
    unique = sorted(set(p.resolve() for p in found if p.is_file()), key=lambda p: p.name.lower())
    return [{"name": p.name, "path": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size} for p in unique]


def compact_schema_for_prompt(schema: dict[str, Any]) -> str:
    return json.dumps(schema, ensure_ascii=False, separators=(",", ":"))


def build_user_prompt(source: pathlib.Path, source_text: str, rubric: dict[str, Any], schema: dict[str, Any], mode: str) -> str:
    target_stub = {
        "type": "paper", "title": source.stem, "domain": "unknown; infer conservatively",
        "unit": "complete supplied document", "comparison_class": "paper of similar purpose and evidence burden",
        "population_boundary": "persons and groups explicitly represented in the supplied document; report omissions",
        "time_window": None,
    }
    return (
        "Evaluate the source below. Return JSON conforming to the schema.\n\n"
        f"AGGREGATION MODE: {mode}\n"
        f"TARGET STUB: {json.dumps(target_stub, ensure_ascii=False)}\n\n"
        f"RUBRIC: {json.dumps(rubric, ensure_ascii=False)}\n\n"
        f"JSON SCHEMA: {compact_schema_for_prompt(schema)}\n\n"
        f"SOURCE FILE: {source.name}\nSOURCE SHA256: {sha256_file(source)}\n\n"
        "--- BEGIN SOURCE ---\n" + source_text + "\n--- END SOURCE ---\n"
    )


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise StationError("API response did not contain a JSON object")
        value = json.loads(text[start:end + 1])
    if not isinstance(value, dict):
        raise StationError("API response JSON root is not an object")
    return value


def call_provider(provider: Provider, system_prompt: str, user_prompt: str, timeout: int) -> tuple[dict[str, Any], dict[str, Any]]:
    if provider.api_kind != "chat_completions":
        raise StationError(f"Unsupported api_kind: {provider.api_kind}")
    body = {
        "model": provider.model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if provider.temperature is not None:
        body["temperature"] = provider.temperature
    if provider.max_output_tokens and provider.output_token_parameter:
        body[provider.output_token_parameter] = provider.max_output_tokens
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        provider.base_url + "/chat/completions", data=data, method="POST",
        headers={"Authorization": "Bearer " + os.environ[provider.api_key_env], "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(2000).decode("utf-8", errors="replace")
        raise StationError(f"{provider.name} HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise StationError(f"{provider.name} connection error: {exc.reason}") from exc
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise StationError(f"{provider.name} returned an unexpected response shape") from exc
    metadata = {"provider": provider.name, "model": payload.get("model", provider.model), "usage": payload.get("usage")}
    return extract_json_object(content), metadata


def validate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("spec_version") != SPEC_VERSION:
        errors.append(f"spec_version must equal {SPEC_VERSION}")
    profile = report.get("fruit_profile")
    if not isinstance(profile, list) or len(profile) != 9:
        errors.append("fruit_profile must contain exactly nine assessments")
    else:
        ids = [x.get("fruit_id") for x in profile if isinstance(x, dict)]
        if set(ids) != set(FRUIT_IDS) or len(ids) != len(set(ids)):
            errors.append("fruit_profile must contain each canonical fruit_id exactly once")
        for item in profile:
            if not isinstance(item, dict):
                errors.append("fruit assessment must be an object")
                continue
            if not isinstance(item.get("score"), int) or not 0 <= item["score"] <= 4:
                errors.append(f"{item.get('fruit_id')}: score must be integer 0..4")
            confidence = item.get("confidence")
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                errors.append(f"{item.get('fruit_id')}: confidence must be 0..1")
            stress = item.get("stress_tests", {})
            if set(stress) != set(STRESS_IDS) or any(str(v).upper() not in ALLOWED_STRESS for v in stress.values()):
                errors.append(f"{item.get('fruit_id')}: all eight stress tests are required")
            for field in ("positive_evidence", "counterevidence"):
                if not isinstance(item.get(field), list):
                    errors.append(f"{item.get('fruit_id')}: {field} must be a list")
    gates = report.get("gate_results")
    if not isinstance(gates, list):
        errors.append("gate_results must be a list")
    else:
        ids = [x.get("gate_id") for x in gates if isinstance(x, dict)]
        if set(ids) != set(GATE_IDS):
            errors.append("gate_results must contain all seven canonical gates exactly once")
        for gate in gates:
            if gate.get("status") not in ALLOWED_STRESS:
                errors.append(f"{gate.get('gate_id')}: invalid status")
    if report.get("epistemic_status") not in {"SUPPORTED", "CONDITIONAL", "MODEL_WITNESSED", "UNRESOLVED", "CONTRADICTED"}:
        errors.append("invalid epistemic_status")
    if report.get("system_status") not in {"ROBUST", "COHERENT_BUT_FRAGILE", "REPAIRABLE", "HIGH_SIGNAL_DECEPTION", "BLOCKED"}:
        errors.append("invalid system_status")
    return errors


def normalize_and_recompute(report: dict[str, Any], source: pathlib.Path, rubric_hash: str, prompt_hash: str, provider_meta: dict[str, Any]) -> dict[str, Any]:
    report["spec_version"] = SPEC_VERSION
    profile = report["fruit_profile"]
    profile.sort(key=lambda x: FRUIT_IDS.index(x["fruit_id"]))
    scores = [int(x["score"]) for x in profile]
    normalized = [x / 4.0 for x in scores]
    arithmetic = sum(normalized) / len(normalized)
    epsilon = 0.05
    geometric = math.prod((x + epsilon) / (1.0 + epsilon) for x in normalized) ** (1.0 / 9.0)
    multiplicative = math.prod(normalized)
    minimum_index = min(range(9), key=lambda i: scores[i])
    vetoes = []
    for gate in report.get("gate_results", []):
        gate["hard"] = gate.get("gate_id") in HARD_GATES
        if gate["hard"] and gate.get("status") == "FAIL":
            vetoes.append(f"unresolved hard-gate failure: {gate['gate_id']}")
    for assessment in profile:
        counterfeit = assessment.get("counterfeit") or {}
        if counterfeit.get("flag") and counterfeit.get("severity") == "SEVERE":
            vetoes.append(f"severe counterfeit mechanism: {assessment['fruit_id']}")
    aggregation = report.setdefault("aggregation", {})
    aggregation.update({
        "mode": aggregation.get("mode", "gated_profile"),
        "arithmetic_summary": round(arithmetic, 4),
        "geometric_balance": round(geometric, 4),
        "multiplicative_coherence": round(multiplicative, 6),
        "minimum_fruit": {"fruit_id": FRUIT_IDS[minimum_index], "score": scores[minimum_index]},
        "vetoes": sorted(set(vetoes)),
    })
    if vetoes and report.get("system_status") not in {"HIGH_SIGNAL_DECEPTION", "BLOCKED"}:
        report["system_status"] = "BLOCKED"
    report["formal_receipt"] = {
        "receipt_type": "FORMAL_EVALUATION_RECEIPT",
        "proof_status": "RULE_DERIVED_FROM_RECORDED_ASSESSMENTS",
        "source_sha256": sha256_file(source), "rubric_sha256": rubric_hash, "prompt_sha256": prompt_hash,
        "provider": provider_meta.get("provider"), "model": provider_meta.get("model"),
        "premises": [
            "P1: the evaluated source is fixed by source_sha256",
            "P2: all nine Fruit dimensions are present on the 0..4 scale",
            "P3: all seven gates are recorded independently of the Fruit scores",
            "P4: evidence uncertainty remains explicit rather than being imputed",
        ],
        "deductions": [
            "D1: arithmetic_summary is the mean of the nine scores normalized by four",
            "D2: geometric_balance penalizes low dimensions and is non-authoritative",
            "D3: unresolved hard-gate failures and severe counterfeit mechanisms create explicit vetoes",
            "D4: a contradiction changes the verdict only through its classified severity, resolution, and consequence",
        ],
        "conclusion": f"epistemic_status={report.get('epistemic_status')}; system_status={report.get('system_status')}; veto_count={len(vetoes)}",
        "scope_boundary": "This receipt proves deterministic application of the declared rubric to recorded model assessments. It does not prove hidden motive, salvation status, divine origin, or empirical validity beyond the cited evidence.",
        "generated_at": utc_now(),
    }
    report["run_metadata"] = {"provider": provider_meta.get("provider"), "model": provider_meta.get("model"), "generated_at": utc_now()}
    return report


def evidence_lines(items: Any) -> list[str]:
    if not items:
        return ["- None cited."]
    lines = []
    for item in items:
        quote = str(item.get("quote_or_event", "")).replace("\n", " ").strip()
        lines.append(f"- **{item.get('ref_id', '?')}** ({item.get('evidence_type', '?')}, {item.get('location', '?')}): “{quote}” — {item.get('link_reason', '')}")
    return lines


def render_markdown(report: dict[str, Any], source: pathlib.Path, source_text: str) -> str:
    target = report.get("target", {})
    agg = report.get("aggregation", {})
    lines = [
        "# Fruits of the Spirit Evaluation", "",
        f"**Target:** {target.get('title', source.stem)}  ",
        f"**Epistemic status:** {report.get('epistemic_status')}  ",
        f"**System status:** {report.get('system_status')}  ",
        f"**Confidence:** {report.get('confidence')}  ",
        f"**Mode:** {agg.get('mode')}  ",
        f"**Arithmetic summary:** {agg.get('arithmetic_summary')}  ",
        f"**Geometric balance:** {agg.get('geometric_balance')}  ",
        "", "## Fruit profile", "",
        "| Fruit | Score (0–4) | Confidence | Coverage | Counterfeit |",
        "|---|---:|---:|---:|---|",
    ]
    for item in report.get("fruit_profile", []):
        cf = item.get("counterfeit", {})
        lines.append(f"| {item['fruit_id'].split('.')[-1].replace('_',' ').title()} | {item.get('score')} | {item.get('confidence')} | {item.get('evidence_coverage')} | {'Yes' if cf.get('flag') else 'No'} |")
    lines.extend(["", "## Gates", "", "| Gate | Status | Hard | Rationale |", "|---|---|---|---|"])
    for gate in report.get("gate_results", []):
        rationale = str(gate.get("rationale", "")).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {gate.get('gate_id')} | {gate.get('status')} | {gate.get('hard')} | {rationale} |")
    lines.extend(["", "## Contradictions and mixed states", ""])
    if report.get("contradictions"):
        for item in report["contradictions"]:
            lines.append(f"- **{item.get('classification')}** — load-bearing: {item.get('load_bearing')}; resolved: {item.get('resolved')}. {item.get('fruit_relation')} Consequence: {item.get('consequence')}")
    else:
        lines.append("- No contradiction was evidenced in the supplied boundary.")
    for item in report.get("fruit_profile", []):
        lines.extend(["", f"## {item['fruit_id'].split('.')[-1].replace('_',' ').title()}: {item.get('score')}/4", "", item.get("rationale", ""), "", "### Positive evidence", ""])
        lines.extend(evidence_lines(item.get("positive_evidence")))
        lines.extend(["", "### Counterevidence", ""])
        lines.extend(evidence_lines(item.get("counterevidence")))
    lines.extend(["", "## Vetoes", ""])
    lines.extend([f"- {x}" for x in agg.get("vetoes", [])] or ["- None."])
    lines.extend(["", "## Missing evidence", ""])
    lines.extend([f"- {x}" for x in report.get("missing_evidence", [])] or ["- None recorded."])
    lines.extend(["", "## Repair path", ""])
    lines.extend([f"- {x}" for x in report.get("repair_path", [])] or ["- No repair action recorded."])
    receipt = report.get("formal_receipt", {})
    lines.extend(["", "## Formal evaluation receipt", "", f"**Proof status:** {receipt.get('proof_status')}  ", f"**Conclusion:** {receipt.get('conclusion')}  ", "", receipt.get("scope_boundary", ""), "", "## Original source", "", f"**File:** `{source.name}`", "", "---", "", source_text.rstrip(), ""])
    return "\n".join(lines)


def process_one(index: int, source: pathlib.Path, output_root: pathlib.Path, config: dict[str, Any], providers: list[Provider], rubric: dict[str, Any], schema: dict[str, Any], system_prompt: str, force: bool) -> dict[str, Any]:
    started = time.time()
    provider = providers[index % len(providers)]
    paper_dir = output_root / source.stem
    result_path = paper_dir / f"{source.stem}.fruits.json"
    markdown_path = paper_dir / f"{source.stem}.fruits.md"
    run_path = paper_dir / f"{source.stem}.run.json"
    if result_path.exists() and not force:
        try:
            existing = read_json(result_path)
            if not validate_report(existing):
                return {"source": str(source), "status": "SKIPPED_VALID", "result": str(result_path)}
        except Exception:
            pass
    run = {"source": str(source), "source_sha256": sha256_file(source), "started_at": utc_now(), "provider": provider.name, "model": provider.model, "status": "RUNNING"}
    write_json_atomic(run_path, run)
    try:
        source_text = extract_text(source).strip()
        max_chars = int(config.get("max_input_characters", 90000))
        if not source_text:
            raise StationError("No extractable text")
        if len(source_text) > max_chars:
            raise StationError(f"Extracted text has {len(source_text)} characters; configured maximum is {max_chars}. Chunking requires a separate evidence-merging pass and is not performed silently.")
        user_prompt = build_user_prompt(source, source_text, rubric, schema, config.get("aggregation_mode", "gated_profile"))
        last_error: Exception | None = None
        response: dict[str, Any] | None = None
        provider_meta: dict[str, Any] = {}
        for attempt in range(int(config.get("retry_count", 2)) + 1):
            try:
                response, provider_meta = call_provider(provider, system_prompt, user_prompt, int(config.get("request_timeout_seconds", 240)))
                errors = validate_report(response)
                if errors:
                    raise StationError("Schema validation: " + "; ".join(errors))
                break
            except Exception as exc:
                last_error = exc
                if attempt < int(config.get("retry_count", 2)):
                    time.sleep(min(2 ** attempt, 8))
        if response is None or last_error and validate_report(response):
            raise last_error or StationError("No valid response")
        response = normalize_and_recompute(response, source, sha256_bytes(json.dumps(rubric, sort_keys=True).encode()), sha256_bytes(system_prompt.encode()), provider_meta)
        final_errors = validate_report(response)
        if final_errors:
            write_json_atomic(paper_dir / f"{source.stem}.invalid.json", response)
            raise StationError("Post-normalization validation: " + "; ".join(final_errors))
        write_json_atomic(result_path, response)
        write_text_atomic(markdown_path, render_markdown(response, source, source_text))
        run.update({"status": "SUCCEEDED", "completed_at": utc_now(), "elapsed_seconds": round(time.time() - started, 3), "result_json": str(result_path), "result_markdown": str(markdown_path), "schema_valid": True, "usage": provider_meta.get("usage")})
        write_json_atomic(run_path, run)
        return {"source": str(source), "status": "SUCCEEDED", "result": str(result_path)}
    except Exception as exc:
        run.update({"status": "FAILED", "completed_at": utc_now(), "elapsed_seconds": round(time.time() - started, 3), "schema_valid": False, "error": str(exc)})
        write_json_atomic(run_path, run)
        return {"source": str(source), "status": "FAILED", "error": str(exc), "receipt": str(run_path)}


def validate_station(config: dict[str, Any], base: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any]]:
    rubric_path = resolve_from(base, config["rubric_file"])
    schema_path = resolve_from(base, config["schema_file"])
    prompt_path = resolve_from(base, config["system_prompt_file"])
    missing = [str(p) for p in (rubric_path, schema_path, prompt_path) if not p.exists()]
    if missing:
        raise StationError("Missing station files: " + ", ".join(missing))
    rubric, schema = read_json(rubric_path), read_json(schema_path)
    prompt = prompt_path.read_text(encoding="utf-8-sig")
    if [x.get("id") for x in rubric.get("fruits", [])] != FRUIT_IDS:
        raise StationError("Rubric Fruit IDs or order do not match the canonical nine")
    if {x.get("id") for x in rubric.get("gates", [])} != set(GATE_IDS):
        raise StationError("Rubric gates do not match the canonical seven")
    canonical_specs = []
    for candidate in config.get("canonical_spec_candidates", []):
        path = resolve_from(base, candidate)
        if path.exists() and path.is_file():
            canonical_specs.append({"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    manifest = {
        "station_version": config.get("station_version"), "validated_at": utc_now(),
        "rubric": {"path": str(rubric_path), "sha256": sha256_file(rubric_path)},
        "schema": {"path": str(schema_path), "sha256": sha256_file(schema_path)},
        "prompt": {"path": str(prompt_path), "sha256": sha256_file(prompt_path)},
        "canonical_specs": canonical_specs or [{"status": "NOT_FOUND"}],
        "workbooks": workbook_manifest(config),
    }
    return rubric, schema, prompt, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Fruits of the Spirit evidence grader")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--input", help="Override input directory")
    parser.add_argument("--output", help="Override output directory")
    parser.add_argument("--workers", type=int)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        config, base = load_config(pathlib.Path(args.config))
        rubric, schema, system_prompt, manifest = validate_station(config, base)
        input_dir = resolve_from(base, args.input or config["input_dir"])
        output_root = resolve_from(base, args.output or config["output_dir"])
        if args.validate_only:
            manifest["input_dir"] = str(input_dir)
            manifest["input_status"] = "AVAILABLE" if input_dir.exists() else "UNAVAILABLE"
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 0 if input_dir.exists() else 2
        providers = active_providers(config)
        if not providers:
            raise StationError("No active API provider. Set one configured API key environment variable.")
        sources = discover_sources(input_dir, config)
        limit = args.limit if args.limit is not None else int(config.get("default_limit", 2))
        if limit > 0:
            sources = sources[:limit]
        if not sources:
            raise StationError(f"No supported source files found in {input_dir}")
        workers = args.workers if args.workers is not None else int(config.get("default_workers", 2))
        if not 1 <= workers <= 12:
            raise StationError("workers must be between 1 and 12")
        output_root.mkdir(parents=True, exist_ok=True)
        manifest.update({"input_dir": str(input_dir), "output_dir": str(output_root), "workers": workers, "limit": limit, "providers": [{"name": p.name, "model": p.model, "api_key_env": p.api_key_env} for p in providers], "sources": [{"path": str(p), "sha256": sha256_file(p)} for p in sources]})
        write_json_atomic(output_root / "_run_manifest.json", manifest)
        print(f"Grading {len(sources)} paper(s) with {workers} worker(s).")
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(process_one, i, source, output_root, config, providers, rubric, schema, system_prompt, args.force) for i, source in enumerate(sources)]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                with OUTPUT_LOCK:
                    print(f"[{result['status']}] {result['source']}")
        summary = {"completed_at": utc_now(), "total": len(results), "succeeded": sum(x["status"] == "SUCCEEDED" for x in results), "skipped": sum(x["status"].startswith("SKIPPED") for x in results), "failed": sum(x["status"] == "FAILED" for x in results), "results": sorted(results, key=lambda x: x["source"].lower())}
        write_json_atomic(output_root / "_batch_summary.json", summary)
        print(json.dumps({k: summary[k] for k in ("total", "succeeded", "skipped", "failed")}, indent=2))
        return 1 if summary["failed"] else 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
