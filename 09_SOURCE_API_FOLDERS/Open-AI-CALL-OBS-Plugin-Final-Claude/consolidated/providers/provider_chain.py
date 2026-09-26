"""
provider_chain.py — Shared LLM provider routing for all POF 2828 pipelines

Provider chain: try OpenRouter free tier first, latch to DeepSeek if exhausted.
Import this from any script that needs LLM calls.

Usage:
    from provider_chain import llm_call

    result = llm_call(system_prompt, user_content)
    # Returns the assistant message text, or raises after all providers fail.
"""
from __future__ import annotations
import json, os, threading, time, urllib.error, urllib.request
from typing import Any


def provider_spec(name: str) -> dict[str, str]:
    if name == "openrouter":
        return {
            "provider": "openrouter",
            "model": os.environ.get(
                "OPENROUTER_MODEL", "google/gemini-2.5-flash"
            ).strip() or "google/gemini-2.5-flash",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "key_name": "OPENROUTER_API_KEY",
        }
    if name == "deepseek":
        return {
            "provider": "deepseek",
            "model": os.environ.get(
                "DEEPSEEK_MODEL", "deepseek-chat"
            ).strip() or "deepseek-chat",
            "url": "https://api.deepseek.com/v1/chat/completions",
            "key_name": "DEEPSEEK_API_KEY",
        }
    raise RuntimeError(f"Unknown provider: {name}")


# ── Chain setup ──
PROVIDER_CHAIN = [
    p.strip().lower()
    for p in os.environ.get("EPISTEMIC_API_PROVIDER", "openrouter,deepseek").split(",")
    if p.strip()
] or ["openrouter", "deepseek"]

_SPECS = [provider_spec(n) for n in PROVIDER_CHAIN]
_INDEX = 0
_LOCK = threading.Lock()
MAX_RETRIES = 2


def _api_key(spec: dict) -> str:
    k = os.environ.get(spec["key_name"], "").strip()
    if not k:
        raise RuntimeError(f"No API key: set {spec['key_name']}")
    return k


def _headers(spec: dict) -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {_api_key(spec)}",
        "Content-Type": "application/json",
    }
    if spec["provider"] == "openrouter":
        h["HTTP-Referer"] = "https://faiththruphysics.com"
        h["X-Title"] = "Theophysics POF 2828"
    return h


def _latch_forward() -> bool:
    """Move to next provider. Returns False if chain exhausted."""
    global _INDEX
    with _LOCK:
        if _INDEX + 1 < len(_SPECS):
            old = _SPECS[_INDEX]["provider"]
            _INDEX += 1
            new = _SPECS[_INDEX]["provider"]
            print(f"  [PROVIDER] {old} exhausted → latching to {new}")
            return True
        return False


def current_provider() -> str:
    return _SPECS[_INDEX]["provider"]


def current_model() -> str:
    return _SPECS[_INDEX]["model"]


def llm_call(system: str, user: str, temperature: float = 0.3,
             max_tokens: int = 4000) -> str:
    """Send a chat completion. Tries current provider, latches on failure."""
    global _INDEX
    while True:
        spec = _SPECS[_INDEX]
        payload = json.dumps({
            "model": spec["model"],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }).encode("utf-8")
        for attempt in range(MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    spec["url"], data=payload,
                    headers=_headers(spec), method="POST",
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices") or []
                if not choices:
                    raise RuntimeError("Empty choices in response")
                content = choices[0].get("message", {}).get("content", "")
                if isinstance(content, list):
                    content = "".join(
                        str(p.get("text", "")) for p in content
                        if isinstance(p, dict)
                    )
                return content.strip()
            except (urllib.error.HTTPError, urllib.error.URLError,
                    RuntimeError, OSError, TimeoutError) as exc:
                err_msg = str(exc)
                if hasattr(exc, "read"):
                    try:
                        err_msg = exc.read().decode("utf-8", errors="replace")[:400]
                    except Exception:
                        pass
                print(f"  [{spec['provider']}] attempt {attempt+1} failed: {err_msg[:120]}")
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
                    continue
                # Retries exhausted on this provider
                break
        # Latch to next provider
        if not _latch_forward():
            raise RuntimeError(
                f"All providers exhausted. Last error: {err_msg[:200]}"
            )
