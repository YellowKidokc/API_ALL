"""Provider adapters. Credentials are read only at call time and never serialized."""
from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable


class ProviderError(RuntimeError):
    def __init__(self, message: str, category: str = "provider", transient: bool = False, retry_after: float | None = None):
        super().__init__(message)
        self.category, self.transient, self.retry_after = category, transient, retry_after


@dataclass(frozen=True)
class ProviderResult:
    text: str
    usage: dict | None = None
    reported_cost: float | None = None
    response_id: str | None = None
    retries: int = 0


Transport = Callable[[str, dict[str, str], dict, float], tuple[int, dict[str, str], dict]]


def _http(url: str, headers: dict[str, str], payload: dict, timeout: float):
    request = urllib.request.Request(url, json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:500]
        return exc.code, dict(exc.headers), {"error": {"message": body}}
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderError(str(exc), "network", True) from exc


class Provider:
    """One explicit provider/model; this class never falls back to another."""

    SPECS = {
        "openai": ("https://api.openai.com/v1/responses", "OPENAI_API_KEY", "bearer"),
        "anthropic": ("https://api.anthropic.com/v1/messages", "ANTHROPIC_API_KEY", "anthropic"),
        "deepseek": ("https://api.deepseek.com/chat/completions", "DEEPSEEK_API_KEY", "bearer"),
        "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY", "bearer"),
    }

    def __init__(self, name: str, model: str, api_key: str, timeout: float = 120, retries: int = 3,
                 transport: Transport = _http, sleep: Callable[[float], None] = time.sleep):
        if name not in self.SPECS:
            raise ValueError(f"unsupported provider: {name}")
        if not model or not api_key:
            raise ValueError("provider model and credential are required")
        self.name, self.model, self._key = name, model, api_key
        self.timeout, self.retries, self.transport, self.sleep = timeout, retries, transport, sleep

    def complete(self, prompt: str, max_tokens: int, call_id: str) -> ProviderResult:
        url, _, auth = self.SPECS[self.name]
        headers = {"Content-Type": "application/json", "User-Agent": "portable-api-workbench/1"}
        if auth == "anthropic":
            headers.update({"x-api-key": self._key, "anthropic-version": "2023-06-01"})
            payload = {"model": self.model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
        else:
            headers["Authorization"] = f"Bearer {self._key}"
            payload = ({"model": self.model, "input": prompt, "max_output_tokens": max_tokens}
                       if self.name == "openai" else
                       {"model": self.model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens})
        # A stable client request id helps providers/support identify an ambiguous submission.
        headers["X-Client-Request-Id"] = call_id
        for attempt in range(self.retries + 1):
            status, response_headers, data = self.transport(url, headers, payload, self.timeout)
            if 200 <= status < 300:
                result = self._decode(data)
                return ProviderResult(result.text, result.usage, result.reported_cost, result.response_id, attempt)
            transient = status in {408, 409, 425, 429} or status >= 500
            if not transient or attempt == self.retries:
                category = "rate_limit" if status == 429 else ("authentication" if status in {401, 403} else "provider")
                raise ProviderError(f"{self.name} HTTP {status}: {data.get('error', {}).get('message', 'request failed')}", category, transient)
            retry_after = response_headers.get("Retry-After") or response_headers.get("retry-after")
            delay = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else min(30, 2 ** attempt + random.random())
            self.sleep(delay)
        raise AssertionError("unreachable")

    def _decode(self, data: dict) -> ProviderResult:
        try:
            if self.name == "openai":
                text = data.get("output_text") or "".join(
                    part.get("text", "") for item in data.get("output", []) for part in item.get("content", [])
                    if part.get("type") in {"output_text", "text"})
            elif self.name == "anthropic":
                text = "".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text")
            else:
                text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("malformed provider response", "corrupt_response") from exc
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("provider returned no text", "corrupt_response")
        return ProviderResult(text, data.get("usage"), data.get("cost"), data.get("id"))


class MockProvider:
    """Deterministic test/offline provider; no network or credits."""
    name, model = "mock", "mock-v1"
    def complete(self, prompt: str, max_tokens: int, call_id: str) -> ProviderResult:
        return ProviderResult("MOCK RESULT\n" + prompt[-min(240, len(prompt)):], {"input_tokens": None, "output_tokens": None})
