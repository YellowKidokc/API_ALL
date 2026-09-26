"""Local relay that every station's API traffic passes through during a run.

ONE_MENU starts it on 127.0.0.1 (random port) and gives each station process
environment variables that point its SDK or HTTP calls here instead of at the
provider:

    DEEPSEEK_BASE_URL   http://127.0.0.1:<port>/s/<NN_STATION>/deepseek
    OPENAI_BASE_URL     http://127.0.0.1:<port>/s/<NN_STATION>/openai/v1
    OPENROUTER_BASE_URL http://127.0.0.1:<port>/s/<NN_STATION>/openrouter/v1
    MOONSHOT_BASE_URL   http://127.0.0.1:<port>/s/<NN_STATION>/moonshot/v1
    ANTHROPIC_BASE_URL  http://127.0.0.1:<port>/s/<NN_STATION>/anthropic
    ONE_MENU_GATEWAY    http://127.0.0.1:<port>

The relay forwards the request unchanged (adding the API key from the
environment if the caller sent none), through the one global limiter with the
retry policy from engine/llm.py, and appends a receipt line per call to
LOGS/calls-<run>.jsonl. Because every process shares this relay, concurrency is
global for the whole run, not per station.

For stations whose station.json sets "focus": "gateway" (legacy scripts whose
prompts we don't rewrite), the relay appends the run's focus block to the last
user message, so David's FOCUS.md and menu focus reach them too.
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from . import llm
from .paths import inside


class Stats:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.calls = self.failed = self.running = 0
        self.prompt_tokens = self.completion_tokens = 0
        self.by_station: dict[str, dict[str, int]] = {}

    def begin(self) -> None:
        with self.lock:
            self.running += 1

    def end(self, station: str, ok: bool, pt: int, ct: int) -> None:
        with self.lock:
            self.running -= 1
            self.calls += 1
            self.failed += 0 if ok else 1
            self.prompt_tokens += pt
            self.completion_tokens += ct
            row = self.by_station.setdefault(station, {"calls": 0, "failed": 0, "tokens": 0})
            row["calls"] += 1
            row["failed"] += 0 if ok else 1
            row["tokens"] += pt + ct

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {"calls": self.calls, "failed": self.failed, "running": self.running,
                    "tokens": self.prompt_tokens + self.completion_tokens,
                    "prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens,
                    "by_station": json.loads(json.dumps(self.by_station))}


class Gateway:
    def __init__(self, max_concurrent: int, run_id: str, mock: bool = False):
        self.limiter = llm.AdaptiveLimiter(max_concurrent)
        self.stats = Stats()
        self.focus: dict[str, str] = {}
        self.mock = mock
        self.receipts = inside("LOGS", f"calls-{run_id}.jsonl")
        self.receipts.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()
        gateway = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_):  # quiet; receipts are the log
                return

            def do_GET(self):
                body = json.dumps(gateway.stats.snapshot()).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                gateway.handle(self)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> "Gateway":
        self.thread.start()
        return self

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def env_for(self, station: str) -> dict[str, str]:
        root = f"{self.url}/s/{station}"
        return {
            "ONE_MENU_GATEWAY": self.url,
            "ONE_MENU_STATION": station,
            "DEEPSEEK_BASE_URL": f"{root}/deepseek",
            "OPENAI_BASE_URL": f"{root}/openai/v1",
            "OPENROUTER_BASE_URL": f"{root}/openrouter/v1",
            "MOONSHOT_BASE_URL": f"{root}/moonshot/v1",
            "ANTHROPIC_BASE_URL": f"{root}/anthropic",
        }

    # ------------------------------------------------------------------
    def handle(self, request: BaseHTTPRequestHandler) -> None:
        parts = request.path.split("?", 1)[0].strip("/").split("/")
        if len(parts) < 4 or parts[0] != "s":
            return self._reply(request, 404, b'{"error":"use /s/<station>/<provider>/<path>"}', "application/json", 1, "bad path")
        station, provider, rest = parts[1], parts[2], "/".join(parts[3:])
        body = request.rfile.read(int(request.headers.get("Content-Length", "0") or 0))
        headers = {k: v for k, v in request.headers.items()}
        task = headers.get("X-One-Menu-Task", "")
        engine_focus = headers.get("X-One-Menu-Focus") == "engine"
        for h in ("X-One-Menu-Task", "X-One-Menu-Focus"):
            headers.pop(h, None)
        before = len(body)
        body, model, streaming = self._prepare(station, body, engine_focus)
        focus_added = len(body) != before
        started = time.monotonic()
        self.stats.begin()
        if self.mock:
            status, payload, ctype, attempts, error = self._mock(task, body, streaming)
        else:
            status, payload, ctype, attempts, error = llm.forward_with_policy(provider, rest, body, headers, self.limiter)
        pt = ct = 0
        if status and status < 400:
            usage = {}
            try:
                if streaming or payload[:5] == b"data:":
                    for line in payload.decode("utf-8", "replace").splitlines():
                        if line.startswith("data:") and '"usage"' in line:
                            found = json.loads(line[5:].strip()).get("usage")
                            usage = found or usage
                else:
                    usage = json.loads(payload).get("usage") or {}
                pt = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
                ct = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
            except (ValueError, AttributeError):
                pass
        ok = error is None and 0 < status < 400
        self.stats.end(station, ok, pt, ct)
        from .goals import goal_id
        self._receipt({"goal_id": goal_id(station, task), "station": station, "provider": provider, "model": model, "task": task, "status": status,
                       "attempts": attempts, "error": error, "prompt_tokens": pt, "completion_tokens": ct,
                       "seconds": round(time.monotonic() - started, 2), "focus_added": focus_added, "streamed": streaming, "at": datetime.now(timezone.utc).isoformat()})
        if status == 0:
            payload = json.dumps({"error": {"message": error or "upstream failure", "type": "one_menu_gateway"}}).encode()
            status, ctype = 502, "application/json"
        self._reply(request, status, payload, ctype, attempts, error)

    def _prepare(self, station: str, body: bytes, engine_focus: bool) -> tuple[bytes, str, bool]:
        try:
            data = json.loads(body or b"{}")
        except ValueError:
            return body, "", False
        model = str(data.get("model", ""))
        streaming = bool(data.get("stream"))
        focus = "" if engine_focus else self.focus.get(station, "")
        if focus and isinstance(data.get("messages"), list):
            for message in reversed(data["messages"]):
                if message.get("role") == "user" and isinstance(message.get("content"), str):
                    message["content"] = message["content"].rstrip() + "\n\n" + focus + (
                        "\nIf the required reply format is JSON, put the focus findings in a top-level "
                        "\"focus_findings\" field instead of a markdown section.\n")
                    body = json.dumps(data).encode("utf-8")
                    break
        return body, model, streaming

    def _mock(self, task: str, body: bytes, streaming: bool):
        from .mock import respond
        data = json.loads(body or b"{}")
        messages = data.get("messages") or [{"role": "user", "content": ""}]
        text = respond(task, messages)
        usage = {"prompt_tokens": len(json.dumps(messages)) // 4, "completion_tokens": len(text) // 4}
        if streaming:  # OpenAI-style server-sent events, as the legacy streaming callers expect
            chunk = {"id": "mock", "object": "chat.completion.chunk", "model": "mock",
                     "choices": [{"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}]}
            end = {"id": "mock", "object": "chat.completion.chunk", "model": "mock",
                   "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}], "usage": usage}
            body = f"data: {json.dumps(chunk)}\n\ndata: {json.dumps(end)}\n\ndata: [DONE]\n\n".encode()
            return 200, body, "text/event-stream", 1, None
        reply = {"id": "mock", "object": "chat.completion", "model": "mock",
                 "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                 "usage": usage}
        return 200, json.dumps(reply).encode(), "application/json", 1, None

    def _receipt(self, row: dict[str, Any]) -> None:
        with self._write_lock, self.receipts.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    @staticmethod
    def _reply(request, status: int, payload: bytes, ctype: str, attempts: int, error: str | None) -> None:
        request.send_response(status)
        request.send_header("Content-Type", ctype or "application/json")
        request.send_header("Content-Length", str(len(payload)))
        request.send_header("X-One-Menu-Attempts", str(attempts))
        if error:
            request.send_header("X-One-Menu-Error", error.replace("\n", " ")[:200])
        request.end_headers()
        request.wfile.write(payload)


def read_stats(url: str) -> dict[str, Any]:
    import urllib.request
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def summary_line(stats: dict[str, Any]) -> str:
    return (f"calls {stats['calls']} · running {stats['running']} · failed {stats['failed']} · "
            f"tokens {stats['tokens']:,}")


def gateway_path() -> Path:
    return Path(__file__)
