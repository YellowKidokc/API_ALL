#!/usr/bin/env python3
"""
llm_client.py — one client, many providers. v1.0 · POF 2828
DeepSeek AND Kimi both speak OpenAI-compatible /chat/completions.
Swap providers by config, never by code. Key comes from env ONLY.

USAGE
  from llm_client import complete
  out = complete("deepseek", prompt, json_mode=True)
  out = complete("kimi",     prompt, json_mode=True)   # same call, other lane

ENV (set in shell or GitHub Secrets — NEVER in the repo):
  DEEPSEEK_API_KEY   -> https://api.deepseek.com
  MOONSHOT_API_KEY   -> https://api.moonshot.ai   (Kimi)
"""
import json, os, sys, urllib.request

PROVIDERS = {
    "deepseek": {"url": "https://api.deepseek.com/chat/completions",
                 "key": "DEEPSEEK_API_KEY", "model": "deepseek-chat"},
    "kimi":     {"url": "https://api.moonshot.ai/v1/chat/completions",
                 "key": "MOONSHOT_API_KEY", "model": "kimi-k2-0905-preview"},
}


def complete(provider, prompt, system=None, json_mode=False, model=None, timeout=120):
    p = PROVIDERS[provider]
    key = os.environ.get(p["key"])
    if not key:
        raise RuntimeError(f"{p['key']} not set — export it or use GitHub Secrets")
    body = {"model": model or p["model"],
            "messages": ([{"role": "system", "content": system}] if system else []) +
                       [{"role": "user", "content": prompt}],
            "temperature": 0.2}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(p["url"], data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.load(r)
    return resp["choices"][0]["message"]["content"]


def complete_both(prompt, system=None, json_mode=True):
    """The stack-up: same prompt down both lanes. Returns {provider: output}."""
    out = {}
    for name in PROVIDERS:
        try:
            out[name] = complete(name, prompt, system=system, json_mode=json_mode)
        except Exception as e:
            out[name] = f"ERROR: {e}"
    return out


if __name__ == "__main__":
    # smoke test: `python llm_client.py deepseek "Say OK"`
    who = sys.argv[1] if len(sys.argv) > 1 else "deepseek"
    msg = sys.argv[2] if len(sys.argv) > 2 else "Reply with exactly: OK"
    print(complete(who, msg))
