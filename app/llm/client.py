"""OpenAI-compatible async chat client for AMD-hosted inference.

Targets the AMD TokenFactory API or a vLLM server on AMD Developer Cloud (MI300X). It sends only
the fields the AMD gateway accepts, keeps concurrency at or below the per-key allowance, keeps a
per-minute request budget, honors Retry-After, and validates JSON output against a schema.
"""

from __future__ import annotations

import asyncio
import json
import random
import re
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.models import TraceEntry

T = TypeVar("T", bound=BaseModel)

ALLOWED_FIELDS = {"model", "messages", "temperature", "top_p", "max_tokens", "response_format", "reasoning_effort", "stream"}
MAX_RETRY_AFTER_S = 45.0  # longer waits (e.g. a spend cap) fail fast so the caller can fall back


class LLMError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False, retry_after: float | None = None,
                 trace: TraceEntry | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.retryable = retryable
        self.retry_after = retry_after
        self.trace = trace


class RateLimiter:
    """Sliding-window limiter: at most `max_calls` acquisitions per `window_s` seconds."""

    def __init__(self, max_calls: int, window_s: float = 60.0, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], Awaitable[None]] = asyncio.sleep):
        self.max_calls = max_calls
        self.window_s = window_s
        self._clock = clock
        self._sleep = sleep
        self._calls: deque[float] = deque()
        self._lock: asyncio.Lock | None = None

    async def acquire(self) -> None:
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            while True:
                now = self._clock()
                while self._calls and now - self._calls[0] >= self.window_s:
                    self._calls.popleft()
                if len(self._calls) < self.max_calls:
                    self._calls.append(now)
                    return
                await self._sleep(max(0.05, self.window_s - (now - self._calls[0])))


_THINK_RE = re.compile(r"<think>.*?</think>", re.S | re.I)
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.S | re.I)


def extract_json(text: str) -> Any:
    """Parse the first JSON object in a model reply (tolerates think blocks and code fences)."""
    if text is None:
        raise ValueError("empty reply")
    cleaned = _THINK_RE.sub("", text).strip()
    fence = _FENCE_RE.search(cleaned)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    if start < 0:
        raise ValueError("no JSON object found in reply")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(cleaned[start:i + 1])
    raise ValueError("unbalanced JSON object in reply")


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LLMClient:
    """Async client shared by all analyses in the process."""

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None,
                 sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
                 clock: Callable[[], float] = time.monotonic, rng: random.Random | None = None):
        self.settings = settings
        self._transport = transport
        self._sleep = sleep
        self._clock = clock
        self._rng = rng or random.Random()
        self._sem: asyncio.Semaphore | None = None
        self._limiter = RateLimiter(settings.max_rpm, 60.0, clock=clock, sleep=sleep)
        self._http: httpx.AsyncClient | None = None
        self.in_flight = 0
        self.max_in_flight_seen = 0

    @property
    def source(self) -> str:
        return "live"

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(transport=self._transport, timeout=self.settings.timeout_s)
        return self._http

    async def aclose(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    def build_body(self, model: str, messages: list[dict], *, max_tokens: int, temperature: float,
                   json_mode: bool = True) -> dict[str, Any]:
        body: dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature,
                                "max_tokens": max_tokens}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if self.settings.reasoning_effort:
            body["reasoning_effort"] = self.settings.reasoning_effort
        return {k: v for k, v in body.items() if k in ALLOWED_FIELDS}

    async def _post_once(self, url: str, api_key: str, body: dict) -> httpx.Response:
        if self._sem is None:
            self._sem = asyncio.Semaphore(self.settings.max_concurrency)
        await self._limiter.acquire()
        async with self._sem:
            self.in_flight += 1
            self.max_in_flight_seen = max(self.max_in_flight_seen, self.in_flight)
            try:
                return await self._client().post(
                    url, json=body,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                )
            finally:
                self.in_flight -= 1

    async def _post_with_retries(self, url: str, api_key: str, body: dict) -> tuple[dict, int]:
        attempts = 0
        dropped_response_format = False
        while True:
            attempts += 1
            retry_after: float | None = None
            try:
                resp = await self._post_once(url, api_key, body)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                err = LLMError("network", f"{type(exc).__name__}: {exc}", retryable=True)
            else:
                if resp.status_code == 200:
                    try:
                        return resp.json(), attempts
                    except ValueError:
                        err = LLMError("bad_response", "response body is not JSON", retryable=True)
                else:
                    text = resp.text[:300]
                    retry_after = _parse_retry_after(resp.headers.get("Retry-After"))
                    if (resp.status_code == 400 and "response_format" in body and not dropped_response_format
                            and "response_format" in text.lower()):
                        body = {k: v for k, v in body.items() if k != "response_format"}
                        dropped_response_format = True
                        attempts -= 1
                        continue
                    retryable = resp.status_code == 429 or resp.status_code >= 500
                    err = LLMError(f"http_{resp.status_code}", text, retryable=retryable, retry_after=retry_after)
            if not err.retryable or attempts >= self.settings.max_attempts:
                err.message = f"{err.message} (after {attempts} attempt(s))"
                raise err
            if err.retry_after is not None and err.retry_after > MAX_RETRY_AFTER_S:
                raise LLMError(err.code, f"provider asked to wait {err.retry_after:.0f}s (quota exhausted)",
                               retryable=False, retry_after=err.retry_after)
            if err.retry_after is not None:
                delay = err.retry_after
            else:
                delay = self._rng.uniform(0, min(20.0, 1.5 * (2 ** (attempts - 1))))
            await self._sleep(delay)

    async def chat_json(self, role: str, messages: list[dict], schema: type[T], step: str, *,
                        max_tokens: int = 2000, temperature: float = 0.2) -> tuple[T, TraceEntry]:
        rc = self.settings.role(role)
        if not rc.ready:
            raise LLMError("not_configured", f"AMD endpoint for role '{role}' is not configured")
        url = rc.base_url.rstrip("/") + "/chat/completions"  # type: ignore[union-attr]
        body = self.build_body(rc.model, messages, max_tokens=max_tokens, temperature=temperature)  # type: ignore[arg-type]
        started = _now()
        t0 = self._clock()
        attempts_total = 0
        prompt_tokens = completion_tokens = 0
        corrected = False
        model_name = rc.model or ""

        def trace(status: str = "ok", error: str | None = None) -> TraceEntry:
            return TraceEntry(
                step=step, provider=self.settings.provider_label, model=model_name, source="live",
                started_at=started, latency_ms=int((self._clock() - t0) * 1000),
                prompt_tokens=prompt_tokens or None, completion_tokens=completion_tokens or None,
                attempts=max(1, attempts_total), status=status, error=error,  # type: ignore[arg-type]
            )

        while True:
            try:
                data, attempts = await self._post_with_retries(url, rc.api_key, body)  # type: ignore[arg-type]
            except LLMError as exc:
                attempts_total += self.settings.max_attempts
                exc.trace = trace("error", exc.message[:300])
                raise
            attempts_total += attempts
            usage = data.get("usage") or {}
            prompt_tokens += int(usage.get("prompt_tokens") or 0)
            completion_tokens += int(usage.get("completion_tokens") or 0)
            model_name = data.get("model") or model_name
            try:
                message = (data.get("choices") or [{}])[0].get("message") or {}
                content = message.get("content") or ""
                if not content.strip() and message.get("reasoning"):
                    content = str(message.get("reasoning"))
                parsed = schema.model_validate(extract_json(content))
                return parsed, trace()
            except (ValueError, ValidationError, AttributeError, IndexError) as exc:
                if corrected:
                    err = LLMError("invalid_output", f"model output failed validation twice: {str(exc)[:200]}")
                    err.trace = trace("error", err.message)
                    raise err
                corrected = True
                body = dict(body)
                body["messages"] = list(messages) + [
                    {"role": "assistant", "content": (content if 'content' in locals() else "")[:6000]},
                    {"role": "user", "content": "Your previous reply was not valid for the required JSON schema "
                                                f"({str(exc)[:300]}). Reply again with ONLY the corrected JSON object."},
                ]
