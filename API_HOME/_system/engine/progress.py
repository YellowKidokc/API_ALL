"""Live progress line: done / running / failed / remaining · tokens · time left."""
from __future__ import annotations

import sys
import threading
import time


class Progress:
    def __init__(self, total: int, label: str = "", stream=None):
        self.total = total
        self.label = label
        self.done = self.failed = self.running = self.tokens = 0
        self.started = time.monotonic()
        self.lock = threading.Lock()
        self.stream = stream or sys.stderr
        self._last = 0.0

    def start(self) -> None:
        with self.lock:
            self.running += 1
        self.show()

    def add_tokens(self, tokens: int) -> None:
        with self.lock:
            self.tokens += tokens

    def finish(self, ok: bool, tokens: int = 0) -> None:
        with self.lock:
            self.running -= 1
            self.done += 1 if ok else 0
            self.failed += 0 if ok else 1
            self.tokens += tokens
        self.show(force=True)

    def line(self) -> str:
        finished = self.done + self.failed
        remaining = max(0, self.total - finished - self.running)
        elapsed = time.monotonic() - self.started
        eta = "?"
        if finished:
            seconds = elapsed / finished * (self.total - finished)
            eta = f"{int(seconds // 60)}m{int(seconds % 60):02d}s"
        return (f"{self.label} done {self.done} · running {self.running} · failed {self.failed} · "
                f"remaining {remaining} · tokens {self.tokens:,} · left {eta}")

    def show(self, force: bool = False) -> None:
        now = time.monotonic()
        tty = self.stream.isatty()
        if now - self._last < (0.5 if tty else 5.0) and not (force and tty):
            return
        self._last = now
        if tty:
            self.stream.write("\r" + self.line()[:160].ljust(160))
        else:
            self.stream.write(self.line() + "\n")
        self.stream.flush()

    def close(self) -> None:
        if self.stream.isatty():
            self.stream.write("\n")
        self.stream.write(f"{self.label} finished in {time.monotonic() - self.started:.1f}s · {self.line()}\n")
        self.stream.flush()
