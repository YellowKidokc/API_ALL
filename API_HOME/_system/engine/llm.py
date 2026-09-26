"""The only place ONE_MENU talks to an LLM API.

Two routes, one policy:
  * When ONE_MENU.bat runs, engine/gateway.py is listening on 127.0.0.1 and every
    call from every station, new or legacy, goes through it. The gateway owns the
    single global limiter, so papers x output ranges x arms x stations can never
    multiply past settings.max_concurrent_calls.
  * When a station script is run on its own (no gateway), calls use the in-process
    limiter below with the same retry policy.

Retry: 429 / 5xx / timeout / network errors retry with exponential backoff and
jitter (settings.retry.attempts). If more than ~10% of calls fail within a minute,
the limiter halves concurrency, then creeps back up by one per minute. Every
change is written to LOGS/limiter.log.

Provider "mock" never touches the network. It returns deterministic, clearly
labelled fake output (engine/mock.py) so the plumbing can be tested without keys.
"""
from __future__ import annotations

import json
import os
import random
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .paths import inside

def _load_providers() -> dict[str, dict]:
    raw = json.loads(inside("config", "providers.json").read_text(encoding="utf-8"))
    out = {}
    for name, spec in raw.items():
        if name.startswith("_"):
            continue
        if spec.get("alias_of"):
            out[name] = {**raw[spec["alias_of"]], **{k: v for k, v in spec.items() if k != "alias_of"}}
        else:
            out[name] = spec
    return out


# Every provider, from config/providers.json. "free" is an alias for OpenRouter's free models.
PROVIDERS = _load_providers()


def settings() -> dict[str, Any]:
    return json.loads(inside("config", "settings.json").read_text(encoding="utf-8"))


def log(message: str) -> None:
    path = inside("LOGS", "limiter.log")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} {message}\n")


class AdaptiveLimiter:
    """Counting semaphore whose ceiling halves when errors pass 10% in a minute."""

    def __init__(self, maximum: int = 30, error_rate: float = 0.10, window: float = 60.0):
        self.maximum = max(1, int(maximum))
        self.current = self.maximum
        self.active = 0
        self.error_rate = error_rate
        self.window = window
        self.events: deque[tuple[float, bool]] = deque()
        self.last_change = time.monotonic()
        self._cond = threading.Condition()

    def __enter__(self):
        with self._cond:
            while self.active >= self.current:
                self._cond.wait()
            self.active += 1
        return self

    def __exit__(self, *_):
        with self._cond:
            self.active -= 1
            self._cond.notify_all()

    def record(self, failed: bool) -> None:
        now = time.monotonic()
        with self._cond:
            self.events.append((now, failed))
            while self.events and self.events[0][0] < now - self.window:
                self.events.popleft()
            failures = sum(1 for _, bad in self.events if bad)
            if len(self.events) >= 10 and failures / len(self.events) > self.error_rate:
                new = max(1, self.current // 2)
                if new < self.current:
                    log(f"limiter {self.current} -> {new} ({failures}/{len(self.events)} calls failed in the last minute)")
                    self.current = new
                self.events.clear()
                self.last_change = now
            elif self.current < self.maximum and now - self.last_change >= self.window:
                self.current += 1
                self.last_change = now
                log(f"limiter creeping back up to {self.current}")
            self._cond.notify_all()


_LIMITER: AdaptiveLimiter | None = None
_LIMITER_LOCK = threading.Lock()


def configure(maximum: int) -> AdaptiveLimiter:
    global _LIMITER
    with _LIMITER_LOCK:
        if _LIMITER is None or _LIMITER.maximum != maximum:
            _LIMITER = AdaptiveLimiter(maximum)
        return _LIMITER


def limiter() -> AdaptiveLimiter:
    return _LIMITER or configure(settings().get("max_concurrent_calls", 30))


class Retryable(Exception):
    pass


def forward(provider: str, rest: str, body: bytes, headers: dict[str, str], timeout: float) -> tuple[int, bytes, str]:
    """One HTTP round trip to the real provider. Injects the key from the environment."""
    spec = PROVIDERS.get(provider)
    if not spec:
        raise ValueError(f"Unknown provider '{provider}'. Known: {', '.join(PROVIDERS)}")
    key = os.environ.get(spec["key"], "")
    out = {k: v for k, v in headers.items() if k.lower() not in ("host", "content-length", "connection", "accept-encoding")}
    auth = out.get("Authorization") or out.get("authorization") or ""
    if provider == "anthropic":
        if key and not out.get("x-api-key"):
            out["x-api-key"] = key
    elif key and (not auth or auth.strip().lower() in ("bearer", "bearer none", "bearer gateway", "bearer ")):
        out.pop("authorization", None)
        out["Authorization"] = f"Bearer {key}"
    if not key and not auth and not out.get("x-api-key") and not spec.get("no_key"):
        raise RuntimeError(f"Missing {spec['key']} (set it as an environment variable)")
    request = urllib.request.Request(f"{spec['base']}/{rest.lstrip('/')}", data=body, headers=out, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(), response.headers.get("Content-Type", "application/json")
    except urllib.error.HTTPError as exc:
        payload = exc.read()
        if exc.code == 429 or exc.code >= 500:
            raise Retryable(f"HTTP {exc.code}: {payload[:300]!r}") from exc
        return exc.code, payload, exc.headers.get("Content-Type", "application/json")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise Retryable(f"{type(exc).__name__}: {exc}") from exc


def forward_with_policy(provider: str, rest: str, body: bytes, headers: dict[str, str],
                        lim: AdaptiveLimiter | None = None) -> tuple[int, bytes, str, int, str | None]:
    """forward() inside the limiter, with retries. Returns status, body, type, attempts, error."""
    policy = settings().get("retry", {})
    attempts = int(policy.get("attempts", 3))
    base = float(policy.get("base_seconds", 1.0))
    ceiling = float(policy.get("max_seconds", 30.0))
    timeout = float(settings().get("request_timeout_seconds", 180))
    lim = lim or limiter()
    last = ""
    for attempt in range(1, attempts + 1):
        try:
            with lim:
                status, payload, ctype = forward(provider, rest, body, headers, timeout)
            lim.record(status >= 400)
            return status, payload, ctype, attempt, None if status < 400 else f"HTTP {status}"
        except Retryable as exc:
            last = str(exc)
            lim.record(True)
            if attempt < attempts:
                time.sleep(min(ceiling, base * 2 ** (attempt - 1)) * (0.75 + random.random() * 0.5))
        except RuntimeError as exc:  # missing key: no point retrying
            return 0, b"", "text/plain", attempt, str(exc)
    return 0, b"", "text/plain", attempts, last


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    attempts: int = 0
    elapsed_seconds: float = 0.0
    started_at: str = ""
    error: str | None = None
    task: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def _parse_completion(payload: bytes) -> tuple[str, int, int]:
    data = json.loads(payload)
    text = data["choices"][0]["message"]["content"] or ""
    usage = data.get("usage") or {}
    return text, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))


def allowed(provider: str) -> bool:
    return provider in settings().get("allowed_providers", list(PROVIDERS) + ["mock"])


def fallback_chain(provider: str, model: str) -> list[tuple[str, str]]:
    """The provider asked for first, then settings.fallback (by default a free
    OpenRouter model) when the first fails after its retries or has no key."""
    chain = [(provider, model)]
    if provider in ("mock",) or os.environ.get("ONE_MENU_NO_FALLBACK"):
        return chain
    for entry in settings().get("fallback", []):
        pair = (entry["provider"], entry["model"])
        if pair not in chain:
            chain.append(pair)
    return chain


def call(messages: list[dict[str, str]], *, provider: str = "deepseek", model: str = "deepseek-chat",
         temperature: float | None = None, max_tokens: int | None = None, json_mode: bool = False,
         task: str = "", station: str = "") -> LLMResult:
    """One chat call, trying the fallback chain in order. The result names the
    provider and model that actually answered; earlier failures are kept in extra."""
    failures = []
    result = None
    if not allowed(provider):
        return LLMResult("", provider, model, error=f"provider '{provider}' is not allowed (settings.json allowed_providers)", task=task)
    for prov, mod in fallback_chain(provider, model):
        if not allowed(prov):
            continue
        result = _call_one(messages, provider=prov, model=mod, temperature=temperature, max_tokens=max_tokens,
                           json_mode=json_mode, task=task, station=station)
        if result.ok:
            break
        failures.append({"provider": prov, "model": mod, "error": result.error})
    if failures and result is not None:
        result.extra["fallback_failures"] = failures
    return result


def _call_one(messages: list[dict[str, str]], *, provider: str, model: str,
              temperature: float | None, max_tokens: int | None, json_mode: bool,
              task: str, station: str) -> LLMResult:
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    if provider == "mock" and os.environ.get("ONE_MENU_GATEWAY"):
        raw = json.dumps({"model": "mock", "messages": messages}).encode("utf-8")
        status, payload, attempts, error = _via_gateway(os.environ["ONE_MENU_GATEWAY"], station or "engine", "mock",
                                                         "chat/completions", raw, {"Content-Type": "application/json",
                                                                                   "X-One-Menu-Task": task, "X-One-Menu-Focus": "engine"})
        if error or status >= 400:
            return LLMResult("", "mock", "mock", attempts=attempts, started_at=started, error=error or f"HTTP {status}", task=task)
        text, pt, ct = _parse_completion(payload)
        return LLMResult(text, "mock", "mock", pt, ct, attempts, time.monotonic() - t0, started, None, task)
    if provider == "mock":
        from .mock import respond
        text = respond(task, messages)
        return LLMResult(text, "mock", "mock", sum(len(m["content"]) // 4 for m in messages), len(text) // 4,
                         1, time.monotonic() - t0, started, None, task)
    spec = PROVIDERS.get(provider)
    if not spec or not spec["chat"]:
        return LLMResult("", provider, model, error=f"Provider '{provider}' has no chat route", started_at=started, task=task)
    body: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
    if temperature is not None:
        body["temperature"] = temperature
    if max_tokens:
        body["max_tokens"] = max_tokens
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    raw = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json", "X-One-Menu-Task": task, "X-One-Menu-Focus": "engine"}
    gateway = os.environ.get("ONE_MENU_GATEWAY", "")
    if gateway:
        status, payload, attempts, error = _via_gateway(gateway, station or "engine", provider, spec["chat"], raw, headers)
    else:
        status, payload, _, attempts, error = forward_with_policy(provider, spec["chat"], raw, headers)
    elapsed = time.monotonic() - t0
    if error or status >= 400:
        detail = error or f"HTTP {status}: {payload[:300]!r}"
        return LLMResult("", provider, model, attempts=attempts, elapsed_seconds=elapsed, started_at=started, error=detail, task=task)
    try:
        text, pt, ct = _parse_completion(payload)
    except (KeyError, IndexError, ValueError) as exc:
        return LLMResult("", provider, model, attempts=attempts, elapsed_seconds=elapsed, started_at=started,
                         error=f"Unreadable reply: {exc}", task=task)
    return LLMResult(text, provider, model, pt, ct, attempts, elapsed, started, None, task)


def _via_gateway(gateway: str, station: str, provider: str, rest: str, body: bytes,
                 headers: dict[str, str]) -> tuple[int, bytes, int, str | None]:
    url = f"{gateway.rstrip('/')}/s/{station}/{provider}/{rest}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    timeout = float(settings().get("request_timeout_seconds", 180)) * 4
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            attempts = int(response.headers.get("X-One-Menu-Attempts", "1"))
            return response.status, response.read(), attempts, None
    except urllib.error.HTTPError as exc:
        attempts = int(exc.headers.get("X-One-Menu-Attempts", "1"))
        return exc.code, exc.read(), attempts, exc.headers.get("X-One-Menu-Error") or f"HTTP {exc.code}"
    except (urllib.error.URLError, OSError) as exc:
        return 0, b"", 1, f"Gateway unreachable: {exc}"


def extract_json(text: str) -> Any:
    """Parse a JSON reply, tolerating ``` fences and prose around the object."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0]
    try:
        return json.loads(cleaned)
    except ValueError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = cleaned.find(opener), cleaned.rfind(closer)
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except ValueError:
                continue
    raise ValueError("Reply is not JSON")


def call_json(messages: list[dict[str, str]], **kwargs: Any) -> tuple[Any, LLMResult]:
    """call() and parse JSON. One repair retry if the reply isn't valid JSON."""
    result = call(messages, json_mode=True, **kwargs)
    if not result.ok:
        return None, result
    try:
        return extract_json(result.text), result
    except ValueError:
        repair = messages + [{"role": "assistant", "content": result.text},
                             {"role": "user", "content": "That reply was not valid JSON. Return only the JSON object, nothing else."}]
        second = call(repair, json_mode=True, **kwargs)
        second.prompt_tokens += result.prompt_tokens
        second.completion_tokens += result.completion_tokens
        if not second.ok:
            return None, second
        try:
            return extract_json(second.text), second
        except ValueError:
            second.error = "Reply was not valid JSON after one repair attempt"
            return None, second


def receipt(result: LLMResult, **context: Any) -> dict[str, Any]:
    data = asdict(result)
    data.pop("text", None)
    return {**context, **data, "tokens": result.tokens, "finished_at": datetime.now(timezone.utc).isoformat()}
