"""LLM provider layer: spec parsing, dispatch, and adapter request shapes (no network)."""

from types import SimpleNamespace

import pytest

from task2view.contracts.models import PipelineError
from task2view.llm import get_client, parse_spec, providers
from task2view.llm.base import LLMClient, parse_json
from task2view.llm.registry import register_provider


def test_parse_spec_forms(monkeypatch):
    monkeypatch.delenv("TASK2VIEW_LLM", raising=False)
    assert parse_spec("anthropic:claude-opus-5-5") == ("anthropic", "claude-opus-5-5")
    assert parse_spec("claude-opus-5-5") == ("anthropic", "claude-opus-5-5")
    assert parse_spec("gemini-2.5-flash") == ("gemini", "gemini-2.5-flash")
    assert parse_spec("ollama:qwen2.5-coder:14b") == ("ollama", "qwen2.5-coder:14b")
    assert parse_spec("anthropic")[0] == "anthropic"
    assert parse_spec(None)[0] == "gemini"


def test_parse_spec_default_from_env(monkeypatch):
    monkeypatch.setenv("TASK2VIEW_LLM", "vllm:my-model")
    assert parse_spec(None) == ("vllm", "my-model")


def test_parse_spec_errors():
    with pytest.raises(PipelineError, match="unknown LLM"):
        parse_spec("mystery-model")
    with pytest.raises(PipelineError, match="needs a model"):
        parse_spec("openai")


def test_all_providers_registered():
    assert {"anthropic", "gemini", "openai", "openrouter", "ollama", "vllm", "openai-compatible"} <= set(providers())


def test_spec_dispatches_to_registered_adapter():
    @register_provider("fake-test", default_model="m1")
    class FakeClient(LLMClient):
        provider = "fake-test"

        def complete_text(self, prompt, *, system=None, json_mode=False):
            return f'```json\n{{"model": "{self.model}", "json_mode": {str(json_mode).lower()}}}\n```'

    assert get_client("fake-test").complete_json("hi") == {"model": "m1", "json_mode": True}
    assert get_client("fake-test:m2").spec == "fake-test:m2"


def test_parse_json_rejects_non_objects():
    with pytest.raises(PipelineError):
        parse_json("no json here")
    with pytest.raises(PipelineError):
        parse_json("[1, 2]")


class _FakeMessages:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def _anthropic(monkeypatch, model, response):
    pytest.importorskip("anthropic")
    from task2view.llm.claude import AnthropicClient

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client = AnthropicClient(model)
    messages = _FakeMessages(response)
    client._client = SimpleNamespace(messages=messages, beta=SimpleNamespace(messages=messages))
    return client, messages


def _claude_reply(text, stop_reason="end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        stop_details=None,
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
    )


def test_anthropic_request_shape(monkeypatch):
    client, messages = _anthropic(monkeypatch, "claude-opus-5-5", _claude_reply('{"ok": 1}'))
    assert client.complete_json("prompt") == {"ok": 1}
    call = messages.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["fallbacks"] == "default"
    assert call["betas"] == ["server-side-fallback-2026-07-01"]
    assert call["output_config"] == {"effort": "high"}
    assert "JSON" in call["system"]
    assert "thinking" not in call


def test_anthropic_haiku_has_no_effort_or_fallbacks(monkeypatch):
    client, messages = _anthropic(monkeypatch, "claude-haiku-4-5", _claude_reply('{"ok": 1}'))
    client.complete_json("prompt")
    call = messages.calls[0]
    assert "output_config" not in call and "fallbacks" not in call


def test_anthropic_refusal_raises(monkeypatch):
    client, _ = _anthropic(monkeypatch, "claude-opus-5-5", _claude_reply("", stop_reason="refusal"))
    with pytest.raises(PipelineError, match="declined"):
        client.complete_json("prompt")


def test_openai_compatible_retries_without_response_format(monkeypatch):
    openai = pytest.importorskip("openai")
    from task2view.llm.openai_compat import OpenAICompatibleClient

    client = OpenAICompatibleClient("ollama", "qwen2.5-coder:14b")
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        if "response_format" in kwargs:
            request = SimpleNamespace(method="POST", url="http://localhost", headers={})
            raise openai.BadRequestError(
                "response_format unsupported",
                response=SimpleNamespace(status_code=400, request=request, headers={}),
                body=None,
            )
        choice = SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content='{"ok": true}'))
        return SimpleNamespace(choices=[choice])

    client._client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    assert client.complete_json("prompt") == {"ok": True}
    assert len(calls) == 2 and "response_format" not in calls[1]
    assert calls[0]["messages"][0]["role"] == "system"


def test_openai_compatible_requires_base_url(monkeypatch):
    pytest.importorskip("openai")
    from task2view.llm.openai_compat import OpenAICompatibleClient

    monkeypatch.delenv("OPENAI_COMPAT_BASE_URL", raising=False)
    with pytest.raises(PipelineError, match="OPENAI_COMPAT_BASE_URL"):
        OpenAICompatibleClient("openai-compatible", "m")


def test_usage_ledger_prices_known_models_and_flags_unknown():
    from task2view.llm.base import Usage
    from task2view.llm.usage import UsageLedger, cost_usd

    u = Usage(input_tokens=1_000_000, output_tokens=100_000, cache_read_tokens=1_000_000)
    assert cost_usd("anthropic:claude-sonnet-4-5", u) == pytest.approx(3.0 + 1.5 + 0.30)
    assert cost_usd("unknown:model", u) is None
    ledger = UsageLedger()
    ledger.record("phase5:IT1", "anthropic:claude-sonnet-4-5", u, 2.0)
    ledger.record("phase1", "unknown:model", Usage(input_tokens=10), 1.0)
    summary = ledger.summary()
    assert summary["by_phase"]["phase5"]["cost_usd"] == pytest.approx(4.8)
    assert summary["total"]["cost_complete"] is False


def test_runtime_records_reported_usage_per_purpose():
    from task2view.agents.runtime import AgentRuntime
    from task2view.llm.base import Usage

    @register_provider("usage-fixture", default_model="m")
    class Reporting(LLMClient):
        provider = "usage-fixture"

        def complete_text(self, prompt, *, system=None, json_mode=False):
            self.last_usage = Usage(input_tokens=120, output_tokens=30)
            return '{"ok": true}'

    runtime = AgentRuntime(model="usage-fixture")
    runtime.complete_json("hello", purpose="phase4:V1:task1")
    call = runtime.ledger.calls[0]
    assert (call.purpose, call.model, call.input_tokens, call.output_tokens, call.reported) == \
        ("phase4:V1:task1", "usage-fixture:m", 120, 30, True)
    assert call.cost_usd is None  # no price for this model
