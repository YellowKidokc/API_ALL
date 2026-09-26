from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOGS = HERE / "LOGS"
HISTORY_PATH = LOGS / "openrouter-model-history.json"
PLAN_PATH = LOGS / "daily-api-plan.json"
CMD_PATH = LOGS / "daily-api-route.cmd"
MODELS_URL = "https://openrouter.ai/api/v1/models"
KEY_URL = "https://openrouter.ai/api/v1/key"
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
CALLS_PER_DOCUMENT = 3
DEFAULT_WORDS_PER_BATCH = 9000
FREE_TIER_DAILY_REQUESTS = 50
CREDITED_DAILY_REQUESTS = 1000


def env_or_registry(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value or os.name != "nt":
        return value
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            found, _ = winreg.QueryValueEx(key, name)
            return str(found).strip()
    except (FileNotFoundError, OSError):
        return ""


def request_json(url: str, *, payload: dict[str, Any] | None = None, timeout: int = 90) -> dict[str, Any]:
    key = env_or_registry("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured in the Windows user environment.")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://faiththruphysics.com",
        "X-OpenRouter-Title": "Faith Through Physics Daily API Gate",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:600]
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        for attempt in range(5):
            try:
                temp.replace(path)
                return
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.25 * (attempt + 1))
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass


def is_zero(value: Any) -> bool:
    try:
        return float(value or 0) == 0
    except (TypeError, ValueError):
        return False


def free_text_models() -> list[dict[str, Any]]:
    data = request_json(MODELS_URL).get("data", [])
    found: list[dict[str, Any]] = []
    for model in data:
        model_id = str(model.get("id", ""))
        pricing = model.get("pricing") or {}
        architecture = model.get("architecture") or {}
        inputs = architecture.get("input_modalities") or []
        outputs = architecture.get("output_modalities") or []
        if not model_id.endswith(":free"):
            continue
        if outputs and "text" not in outputs:
            continue
        if inputs and "text" not in inputs:
            continue
        found.append(model)
    return found


def model_score(model: dict[str, Any], priority: str, minimum_context: int) -> float:
    model_id = str(model.get("id", "")).lower()
    context = int(model.get("context_length") or 0)
    parameters = set(model.get("supported_parameters") or [])
    score = min(context, 500_000) / 10_000
    if context < minimum_context:
        score -= 1000
    if "response_format" in parameters or "structured_outputs" in parameters:
        score += 30
    if any(name in model_id for name in ("nemotron", "deepseek", "qwen", "glm")):
        score += 18
    if any(size in model_id for size in ("120b", "70b", "72b", "405b")):
        score += 12
    if priority == "quality":
        score += 12 if any(x in model_id for x in ("reason", "r1", "thinking", "nemotron")) else 0
    elif priority == "speed":
        score += 15 if any(x in model_id for x in ("mini", "small", "flash", "8b", "12b")) else 0
        score -= min(context, 500_000) / 40_000
    elif priority == "long":
        score += min(context, 1_000_000) / 5_000
    expiration = model.get("expiration_date")
    if expiration:
        try:
            expiration_time = datetime.fromisoformat(str(expiration).replace("Z", "+00:00"))
            if expiration_time.tzinfo is None:
                expiration_time = expiration_time.replace(tzinfo=timezone.utc)
            if expiration_time < datetime.now(timezone.utc) + timedelta(days=7):
                score -= 500
        except ValueError:
            pass
    return score


def extract_content(response: dict[str, Any]) -> tuple[str, str]:
    choices = response.get("choices") or []
    if not choices:
        raise RuntimeError("OpenRouter returned no choices")
    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        content = "".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    return str(content).strip(), str(response.get("model", ""))


def extract_object(text: str) -> dict[str, Any]:
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.I | re.S)
    candidate = fenced.group(1).strip() if fenced else text.strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(candidate[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("response was not one JSON object")
    return value


PROBES = [
    {
        "name": "strict-json-boundary",
        "prompt": (
            "Return only one JSON object with exactly these keys: sentinel, classification, boundary. "
            "Set sentinel to FTP-2828, classification to FORMAL_CONDITIONAL, and boundary to "
            "Lean proves the theorem from its assumptions; it does not prove the assumptions describe nature."
        ),
        "validate": lambda obj: obj == {
            "sentinel": "FTP-2828",
            "classification": "FORMAL_CONDITIONAL",
            "boundary": "Lean proves the theorem from its assumptions; it does not prove the assumptions describe nature.",
        },
    },
    {
        "name": "source-fidelity",
        "prompt": (
            "SOURCE: The blue lantern remained lit at 04:17, but this observation does not establish why. "
            "Return only JSON with keys quote and does_not_establish. quote must copy the complete SOURCE sentence "
            "exactly. does_not_establish must be the single word cause."
        ),
        "validate": lambda obj: obj.get("quote") == (
            "The blue lantern remained lit at 04:17, but this observation does not establish why."
        ) and str(obj.get("does_not_establish", "")).lower() == "cause",
    },
    {
        "name": "reference-comparison",
        "prompt": (
            "SOURCE: A local Lean theorem compiles from declared assumptions. No empirical observations were supplied. "
            "Return only JSON with keys supported, unsupported, and next_step. supported must state what the compilation "
            "establishes. unsupported must state what it does not establish about nature. next_step must name the kind of "
            "work required to connect the formal result to the physical world."
        ),
        # This benchmark is intentionally scored instead of requiring one exact phrase.
        # A semantically faithful answer may use different wording and still pass.
        "score": lambda obj: sum([
            any(word in str(obj.get("supported", "")).lower() for word in ("assumption", "theorem", "formal")),
            any(word in str(obj.get("unsupported", "")).lower() for word in ("nature", "empirical", "physical", "world")),
            any(word in str(obj.get("next_step", "")).lower() for word in ("empirical", "measurement", "observation", "experiment", "bridge")),
            set(obj) == {"supported", "unsupported", "next_step"},
        ]) / 4,
        "minimum_score": 0.90,
    },
]


def run_probe(model_id: str, probe: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "You are a deterministic epistemic preflight. Follow the requested JSON contract exactly."},
            {"role": "user", "content": probe["prompt"]},
        ],
        "temperature": 0,
        "max_tokens": 350,
        "response_format": {"type": "json_object"},
    }
    try:
        response = request_json(CHAT_URL, payload=payload)
        content, actual_model = extract_content(response)
        parsed = extract_object(content)
        score = float(probe["score"](parsed)) if "score" in probe else (1.0 if probe["validate"](parsed) else 0.0)
        minimum_score = float(probe.get("minimum_score", 1.0))
        passed = score >= minimum_score
        return {
            "name": probe["name"], "passed": passed, "latency_seconds": round(time.perf_counter() - started, 2),
            "score": round(score, 3), "minimum_score": minimum_score,
            "actual_model": actual_model, "observed": None if passed else parsed,
            "error": None if passed else "valid JSON but fell below the comparison threshold",
        }
    except Exception as exc:
        return {
            "name": probe["name"], "passed": False, "latency_seconds": round(time.perf_counter() - started, 2),
            "actual_model": "", "observed": None, "error": str(exc)[:700],
        }


def ask_workload(default_count: int) -> int:
    raw = input(f"How many documents should we allow today? [{default_count or 10}]: ").strip()
    if not raw:
        return default_count or 10
    value = int(raw)
    if value < 1:
        raise ValueError("Daily document count must be at least 1")
    return value


def ask_priority() -> str:
    raw = input("What matters most today? [1] quality  [2] speed  [3] long documents (default 1): ").strip()
    return {"1": "quality", "2": "speed", "3": "long", "": "quality"}.get(raw, "quality")


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily OpenRouter workload and free-model gate")
    parser.add_argument("--documents", type=int)
    parser.add_argument("--priority", choices=("quality", "speed", "long"))
    parser.add_argument("--candidate-count", type=int, default=3)
    parser.add_argument("--words-per-batch", type=int, default=DEFAULT_WORDS_PER_BATCH,
                        help="Maximum planned source words in one intact document batch")
    parser.add_argument("--no-probe", action="store_true", help="Discover and plan without spending test requests")
    parser.add_argument("--max-test-age-days", type=int, default=7)
    args = parser.parse_args()

    LOGS.mkdir(parents=True, exist_ok=True)
    inbox_count = sum(1 for p in (ROOT / "INBOX").rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt", ".html", ".htm"})
    documents = args.documents if args.documents is not None else ask_workload(inbox_count)
    if args.words_per_batch < 1000:
        raise ValueError("Words per batch must be at least 1,000")
    priority = args.priority or ask_priority()
    required_requests = documents * CALLS_PER_DOCUMENT
    key_info_envelope = request_json(KEY_URL)
    key_info = key_info_envelope.get("data", key_info_envelope)
    is_free_tier = bool(key_info.get("is_free_tier", True))
    platform_budget = FREE_TIER_DAILY_REQUESTS if is_free_tier else CREDITED_DAILY_REQUESTS
    free_budget = int(os.environ.get("OPENROUTER_FREE_DAILY_REQUESTS", str(platform_budget)))

    models = free_text_models()
    if not models:
        raise RuntimeError("OpenRouter reported no zero-cost text models.")
    minimum_context = {"quality": 32_000, "speed": 16_000, "long": 100_000}[priority]
    ranked = sorted(models, key=lambda m: model_score(m, priority, minimum_context), reverse=True)
    eligible = [m for m in ranked if int(m.get("context_length") or 0) >= minimum_context]
    if not eligible:
        raise RuntimeError(f"No current free model meets the {minimum_context:,}-token context floor.")

    history = load_json(HISTORY_PATH, {"models": {}})
    history.setdefault("models", {})
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.max_test_age_days)
    tested: list[dict[str, Any]] = []
    chosen: dict[str, Any] | None = None
    for model in eligible:
        model_id = str(model["id"])
        prior = history["models"].get(model_id, {})
        prior_time = prior.get("tested_at", "")
        recently_passed = False
        try:
            recently_passed = prior.get("status") == "PASS" and datetime.fromisoformat(prior_time) >= cutoff
        except (TypeError, ValueError):
            pass
        if recently_passed:
            chosen = model
            tested.append({"model": model_id, "status": "REUSED_PASS", "tested_at": prior_time})
            break
        if args.no_probe:
            if chosen is None:
                chosen = model
            continue
        if len([x for x in tested if x.get("status") != "REUSED_PASS"]) >= max(1, args.candidate_count):
            break
        probes = [run_probe(model_id, probe) for probe in PROBES]
        status = "PASS" if all(probe["passed"] for probe in probes) else "FAIL"
        record = {
            "model": model_id, "status": status, "tested_at": datetime.now(timezone.utc).isoformat(),
            "context_length": model.get("context_length"), "probes": probes,
        }
        history["models"][model_id] = record
        tested.append(record)
        atomic_json(HISTORY_PATH, history)
        if status == "PASS":
            chosen = model
            break

    if chosen is None:
        raise RuntimeError("No tested free model passed today's deterministic gate.")

    chosen_id = str(chosen["id"])
    probe_requests = sum(len(record.get("probes", [])) for record in tested)
    production_budget = max(0, free_budget - probe_requests)
    maximum_free_documents = production_budget // CALLS_PER_DOCUMENT
    allowed_documents = min(documents, maximum_free_documents)
    over_budget = required_requests > production_budget
    workers = 24 if priority == "speed" else 12
    plan = {
        "status": "READY_WITH_FREE_CAP" if over_budget else "READY",
        "created_at": datetime.now(timezone.utc).isoformat(), "date_local": datetime.now().astimezone().date().isoformat(),
        "requested_documents": documents, "allowed_free_documents": allowed_documents,
        "target_source_words_per_batch": args.words_per_batch,
        "target_source_word_range": [8000, args.words_per_batch],
        "planned_source_words": allowed_documents * args.words_per_batch,
        "calls_per_document": CALLS_PER_DOCUMENT, "estimated_requests": required_requests,
        "platform_free_request_budget": free_budget, "probe_requests_used": probe_requests,
        "production_request_budget": production_budget, "key_is_free_tier": is_free_tier,
        "priority": priority, "workers": workers, "openrouter_rpm": 20,
        "selected_model": chosen_id, "context_length": chosen.get("context_length"),
        "available_free_text_models": len(models), "eligible_models": len(eligible), "tests": tested,
        "warning": (f"Requested work exceeds the conservative free allowance; capped at {allowed_documents} documents." if over_budget else None),
        "authority": "ROUTING PLAN ONLY - NO CANON ADMISSION",
    }
    atomic_json(PLAN_PATH, plan)
    CMD_PATH.write_text(
        "@echo off\n"
        "set \"EPISTEMIC_API_PROVIDER=openrouter\"\n"
        f"set \"OPENROUTER_MODEL={chosen_id}\"\n"
        f"set \"DAILY_API_MAX_FILES={allowed_documents}\"\n"
        f"set \"DAILY_API_WORKERS={workers}\"\n",
        encoding="utf-8",
    )
    with CMD_PATH.open("a", encoding="utf-8") as route:
        route.write("set \"OPENROUTER_RPM=20\"\n")
    print("\nDAILY API GATE: READY")
    print(f"Free models discovered: {len(models)}; eligible: {len(eligible)}")
    print(f"Selected: {chosen_id} ({int(chosen.get('context_length') or 0):,} context)")
    print(f"Today's free-safe plan: {allowed_documents} document(s), {allowed_documents * CALLS_PER_DOCUMENT} production requests, {workers} workers")
    print(f"Batch size: preserve each document intact, targeting 8,000-{args.words_per_batch:,} source words per batch")
    if over_budget:
        print(f"CAP APPLIED: {documents} documents would require about {required_requests} requests; today's available production allowance is {production_budget}.")
    print(f"Receipt: {PLAN_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"DAILY API GATE: BLOCKED - {exc}", file=sys.stderr)
        raise SystemExit(1)
