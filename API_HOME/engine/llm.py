"""The only network LLM gateway: global adaptive concurrency, retry, and receipts."""
from __future__ import annotations
import asyncio, json, os, random, threading, time, urllib.error, urllib.request
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .paths import inside

@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    attempts: int
    elapsed_seconds: float
    started_at: str
    error: str | None = None

class AdaptiveLimiter:
    def __init__(self, maximum: int = 30):
        self.maximum=max(1, maximum); self.current=self.maximum
        self.active=0; self._cond=threading.Condition(); self.events: deque[tuple[float,bool]]=deque()
        self.last_increase=time.monotonic()
    def __enter__(self):
        with self._cond:
            while self.active >= self.current: self._cond.wait()
            self.active += 1
        return self
    def __exit__(self,*_):
        with self._cond: self.active-=1; self._cond.notify_all()
    def record(self, failed: bool):
        now=time.monotonic()
        with self._cond:
            self.events.append((now,failed))
            while self.events and self.events[0][0] < now-60: self.events.popleft()
            if len(self.events)>=5 and sum(x[1] for x in self.events)/len(self.events)>.10:
                new=max(1,self.current//2)
                if new < self.current: self.current=new; _log(f"limiter reduced to {new}")
                self.events.clear(); self.last_increase=now
            elif self.current < self.maximum and now-self.last_increase>=60:
                self.current+=1; self.last_increase=now; _log(f"limiter increased to {self.current}")
            self._cond.notify_all()

_LIMITER: AdaptiveLimiter | None=None

def configure(maximum: int) -> AdaptiveLimiter:
    global _LIMITER
    _LIMITER=AdaptiveLimiter(maximum); return _LIMITER

def limiter() -> AdaptiveLimiter:
    return _LIMITER or configure(30)

def _log(message: str):
    path=inside("LOGS","limiter.log"); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f: f.write(f"{datetime.now(timezone.utc).isoformat()} {message}\n")

def _request(provider: str, model: str, messages: list[dict[str,str]], timeout: float) -> dict[str,Any]:
    if provider == "deepseek":
        url="https://api.deepseek.com/chat/completions"; key=os.environ.get("DEEPSEEK_API_KEY","")
    elif provider == "openai":
        url="https://api.openai.com/v1/chat/completions"; key=os.environ.get("OPENAI_API_KEY","")
    else: raise ValueError(f"Unsupported provider: {provider}")
    if not key: raise RuntimeError(f"Missing {provider.upper()}_API_KEY")
    body=json.dumps({"model":model,"messages":messages,"stream":False}).encode()
    req=urllib.request.Request(url,data=body,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as response: return json.load(response)

def call(messages: list[dict[str,str]], *, provider="deepseek", model="deepseek-chat",
         attempts=3, base_seconds=1.0, max_seconds=30.0, timeout=180.0) -> LLMResult:
    start=time.monotonic(); started=datetime.now(timezone.utc).isoformat(); last=""
    for attempt in range(1,attempts+1):
        failed=False
        try:
            with limiter(): payload=_request(provider,model,messages,timeout)
            usage=payload.get("usage",{}); choice=payload["choices"][0]["message"]["content"]
            limiter().record(False)
            return LLMResult(choice,provider,model,int(usage.get("prompt_tokens",0)),int(usage.get("completion_tokens",0)),attempt,time.monotonic()-start,started)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, RuntimeError) as exc:
            last=f"{type(exc).__name__}: {exc}"; failed=True; limiter().record(True)
            retryable=not isinstance(exc,urllib.error.HTTPError) or exc.code==429 or exc.code>=500
            if attempt>=attempts or not retryable: break
            time.sleep(min(max_seconds,base_seconds*2**(attempt-1))*(.75+random.random()*.5))
    return LLMResult("",provider,model,0,0,attempt,time.monotonic()-start,started,last)

async def acall(*args, **kwargs) -> LLMResult:
    return await asyncio.to_thread(call,*args,**kwargs)

def receipt(result: LLMResult, **context: Any) -> dict[str,Any]:
    return {**context, **asdict(result), "finished_at":datetime.now(timezone.utc).isoformat(),
            "tokens":result.prompt_tokens+result.completion_tokens}
