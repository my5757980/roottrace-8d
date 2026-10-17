import asyncio
import json

import httpx
import pytest
from pydantic import BaseModel

from app.config import RoleConfig, Settings
from app.llm.client import ALLOWED_FIELDS, LLMClient, LLMError, RateLimiter, extract_json


class Out(BaseModel):
    answer: str


def settings(**kw) -> Settings:
    role = RoleConfig(base_url="https://amd.example/v1", api_key="k", model="m")
    base = dict(text=role, vision=role, provider_label="AMD test", llm_mode_setting="live", max_concurrency=8,
                max_rpm=1000, timeout_s=10, max_attempts=3, reasoning_effort=None, case_ttl_s=60, max_cases=10,
                max_upload_mb=10, live_runs_per_ip=5, live_window_s=600)
    base.update(kw)
    return Settings(**base)


def reply(content: str, status: int = 200, headers: dict | None = None) -> httpx.Response:
    body = {"model": "m", "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7}}
    return httpx.Response(status, json=body if status == 200 else {"error": "x"}, headers=headers or {})


async def no_sleep(_s: float) -> None:
    return None


def run(coro):
    return asyncio.run(coro)


def test_extract_json_handles_fences_and_think_blocks():
    assert extract_json('<think>hmm</think>```json\n{"answer": "a"}\n```') == {"answer": "a"}
    assert extract_json('Sure! {"answer": "b {x}"} trailing') == {"answer": "b {x}"}
    with pytest.raises(ValueError):
        extract_json("no json here")


def test_success_parses_and_reports_usage():
    seen = []

    def handler(request: httpx.Request):
        seen.append(json.loads(request.content))
        return reply('```json\n{"answer": "ok"}\n```')

    client = LLMClient(settings(), transport=httpx.MockTransport(handler), sleep=no_sleep)
    out, trace = run(client.chat_json("text", [{"role": "user", "content": "hi"}], Out, "step"))
    assert out.answer == "ok"
    assert trace.prompt_tokens == 11 and trace.completion_tokens == 7 and trace.source == "live"
    assert set(seen[0]).issubset(ALLOWED_FIELDS)
    assert seen[0]["response_format"] == {"type": "json_object"}


def test_429_retry_after_is_honoured_then_succeeds():
    calls, sleeps = [], []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return reply("", status=429, headers={"Retry-After": "2"})
        return reply('{"answer": "ok"}')

    async def rec_sleep(s):
        sleeps.append(s)

    client = LLMClient(settings(), transport=httpx.MockTransport(handler), sleep=rec_sleep)
    out, trace = run(client.chat_json("text", [], Out, "step"))
    assert out.answer == "ok" and len(calls) == 2 and sleeps == [2.0] and trace.attempts == 2


def test_400_is_not_retried():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(400, text="bad request")

    client = LLMClient(settings(), transport=httpx.MockTransport(handler), sleep=no_sleep)
    with pytest.raises(LLMError) as err:
        run(client.chat_json("text", [], Out, "step"))
    assert err.value.code == "http_400" and len(calls) == 1 and err.value.trace is not None


def test_invalid_json_gets_exactly_one_corrective_retry():
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        return reply("not json at all")

    client = LLMClient(settings(), transport=httpx.MockTransport(handler), sleep=no_sleep)
    with pytest.raises(LLMError) as err:
        run(client.chat_json("text", [{"role": "user", "content": "x"}], Out, "step"))
    assert err.value.code == "invalid_output" and len(calls) == 2
    assert "corrected JSON" in calls[1]["messages"][-1]["content"]


def test_long_retry_after_fails_fast():
    def handler(request):
        return reply("", status=429, headers={"Retry-After": "3600"})

    client = LLMClient(settings(), transport=httpx.MockTransport(handler), sleep=no_sleep)
    with pytest.raises(LLMError) as err:
        run(client.chat_json("text", [], Out, "step"))
    assert "quota" in err.value.message


def test_semaphore_caps_concurrency():
    async def scenario():
        async def handler(request):
            await asyncio.sleep(0.02)
            return reply('{"answer": "ok"}')

        client = LLMClient(settings(max_concurrency=2), transport=httpx.MockTransport(handler), sleep=asyncio.sleep)
        await asyncio.gather(*(client.chat_json("text", [], Out, "s") for _ in range(6)))
        return client.max_in_flight_seen

    assert run(scenario()) <= 2


def test_rate_limiter_waits_when_budget_is_used():
    clock = [0.0]
    sleeps = []

    async def fake_sleep(s):
        sleeps.append(s)
        clock[0] += s

    async def scenario():
        rl = RateLimiter(2, 60.0, clock=lambda: clock[0], sleep=fake_sleep)
        for _ in range(3):
            await rl.acquire()

    run(scenario())
    assert sleeps and sleeps[0] == pytest.approx(60.0)
