"""LLM provider wrappers for the CKG runner."""

from __future__ import annotations

import dataclasses
import json
import os
import time
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover - tests run without live calls
    requests = None


@dataclasses.dataclass
class ProviderResult:
    """Normalized wrapper for a provider's response."""

    content: str
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)
    finish_reason: str | None = None
    model: str | None = None


class _BaseProvider:
    """Shared scaffolding for HTTP-based providers."""

    name: str = "base"
    default_model: str = ""
    api_url: str = ""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        timeout: int = 120,
        max_retries: int = 3,
    ):
        self.model = model or self.default_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.calls = 0
        self.api_key = api_key
        if self.api_key is None:
            env_var = f"{self.name.upper()}_API_KEY"
            self.api_key = os.environ.get(env_var, "").strip()

    def _post(self, payload: dict[str, Any], headers: dict[str, str]) -> ProviderResult:
        if requests is None:
            raise RuntimeError(
                "The 'requests' package is required for live provider calls."
            )
        last_error: Exception = RuntimeError("Provider call failed")
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    raise ValueError("Provider returned no choices")
                message = choices[0].get("message", {})
                text = message.get("content", "")
                if not text.strip():
                    raise ValueError("Provider returned empty content")
                return ProviderResult(
                    content=text,
                    metadata=data,
                    finish_reason=choices[0].get("finish_reason"),
                    model=data.get("model", self.model),
                )
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
        raise RuntimeError(
            f"{self.name} provider failed after {self.max_retries} attempts: {last_error}"
        )

    def _apply_json_mode(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Enable JSON mode if the provider supports it."""
        return payload

    def complete(
        self, prompt: str, system_prompt: str | None = None, json_mode: bool = False, **kwargs: Any
    ) -> ProviderResult:
        raise NotImplementedError


class DeepSeekProvider(_BaseProvider):
    """DeepSeek API provider (https://api.deepseek.com)."""

    name = "deepseek"
    default_model = "deepseek-chat"
    api_url = "https://api.deepseek.com/chat/completions"

    def _apply_json_mode(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload["response_format"] = {"type": "json_object"}
        return payload

    def complete(
        self, prompt: str, system_prompt: str | None = None, json_mode: bool = False, **kwargs: Any
    ) -> ProviderResult:
        if not self.api_key:
            raise RuntimeError("DeepSeek API key not configured")
        self.calls += 1
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
            # Without this DeepSeek stops at its ~4K default and long papers
            # come back as JSON cut off mid-object. 8192 is deepseek-chat's max.
            "max_tokens": kwargs.get("max_tokens", 8192),
        }
        if json_mode:
            payload = self._apply_json_mode(payload)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        return self._post(payload, headers)


class OpenRouterProvider(_BaseProvider):
    """OpenRouter API provider (https://openrouter.ai/api/v1)."""

    name = "openrouter"
    default_model = "google/gemini-2.5-flash"
    api_url = "https://openrouter.ai/api/v1/chat/completions"

    def _apply_json_mode(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload["response_format"] = {"type": "json_object"}
        return payload

    def complete(
        self, prompt: str, system_prompt: str | None = None, json_mode: bool = False, **kwargs: Any
    ) -> ProviderResult:
        if not self.api_key:
            raise RuntimeError("OpenRouter API key not configured")
        self.calls += 1
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
        }
        if json_mode:
            payload = self._apply_json_mode(payload)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://faiththruphysics.com",
            "X-OpenRouter-Title": "Faith Through Physics CKG Runner",
        }
        return self._post(payload, headers)


class OpenAIProvider(_BaseProvider):
    """OpenAI API provider (https://api.openai.com/v1)."""

    name = "openai"
    default_model = "gpt-4o"
    api_url = "https://api.openai.com/v1/chat/completions"

    def _apply_json_mode(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload["response_format"] = {"type": "json_object"}
        return payload

    def complete(
        self, prompt: str, system_prompt: str | None = None, json_mode: bool = False, **kwargs: Any
    ) -> ProviderResult:
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured")
        self.calls += 1
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
        }
        if json_mode:
            payload = self._apply_json_mode(payload)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        return self._post(payload, headers)


class FakeProvider:
    """Test provider that returns a fixture without network calls.

    If ``fixture`` is supplied, it is returned for every call. Otherwise the
    provider returns a map-shaped fixture when the prompt asks for a map and
    a section-shaped fixture for all other prompts.
    """

    name = "fake"
    model = "fixture"

    def __init__(self, fixture: dict[str, Any] | None = None):
        self.fixture = fixture
        self.calls = 0

    def _map_fixture(self) -> dict[str, Any]:
        return {
            "title": "Fixture paper",
            "domain": "Tests",
            "project": "CKG",
            "purpose": "paper",
            "summary": "A fixture paper for offline testing.",
            "keywords": ["fixture"],
            "objects": [
                {
                    "key": "C1",
                    "type": "CLAIM",
                    "register": "TEST",
                    "quote": "True",
                    "statement": "Fixture claim",
                    "reason": "Fixture reason",
                }
            ],
            "unmapped": [],
        }

    def _section_fixture(self) -> dict[str, Any]:
        return {
            "status": "AI_PROPOSED",
            "reason": "Fixture only",
            "markdown": "Fixture analysis; no actual verification.",
            "object_keys": ["C1"],
        }

    def complete(
        self, prompt: str, system_prompt: str | None = None, json_mode: bool = False, **kwargs: Any
    ) -> ProviderResult:
        self.calls += 1
        if self.fixture is not None:
            data = self.fixture
        elif "Map this document as JSON" in prompt:
            data = self._map_fixture()
        else:
            data = self._section_fixture()
        return ProviderResult(json.dumps(data))


def _config_dir(root: Path) -> Path:
    """Return CONFIG dir, preferring the hidden _BACKSIDE location."""
    hidden = root.parent / "_BACKSIDE" / "CKG" / "CONFIG"
    if hidden.exists():
        return hidden
    legacy = root / "CONFIG"
    if legacy.exists():
        return legacy
    return hidden


def load_local_keys(root: Path) -> dict[str, str]:
    """Read optional CONFIG/keys.local.json and overlay environment variables."""
    keys: dict[str, str] = {}
    local = _config_dir(root) / "keys.local.json"
    if local.exists():
        try:
            keys.update(json.loads(local.read_text(encoding="utf-8-sig")))
        except json.JSONDecodeError:
            pass
    for name in ("DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY"):
        keys[name] = os.environ.get(name, keys.get(name, "")).strip()
    return keys


def provider_from_config(config: dict[str, Any], root: Path) -> _BaseProvider:
    """Instantiate the provider selected in CONFIG/ckg.json."""
    keys = load_local_keys(root)
    provider_name = config.get("provider", "deepseek").lower()
    model = config.get("model")
    if provider_name == "deepseek":
        return DeepSeekProvider(model=model, api_key=keys.get("DEEPSEEK_API_KEY"))
    if provider_name == "openrouter":
        return OpenRouterProvider(model=model, api_key=keys.get("OPENROUTER_API_KEY"))
    if provider_name == "openai":
        return OpenAIProvider(model=model, api_key=keys.get("OPENAI_API_KEY"))
    raise ValueError(f"Unknown provider: {provider_name}")
