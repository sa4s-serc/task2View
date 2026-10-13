"""The claude-code provider (Agent SDK on a Claude subscription) and resumable runs. No network: the SDK is faked."""

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.models import PipelineError
from task2view.llm import claude_agent
from task2view.llm.registry import parse_spec
from task2view.llm.usage import Usage, cost_usd

CODE = Path(__file__).resolve().parents[1]


def _fake_sdk(messages, seen=None):
    sdk = types.SimpleNamespace()
    for name in ("RateLimitEvent", "AssistantMessage", "TextBlock", "ResultMessage"):
        setattr(sdk, name, type(name, (), {"__init__": lambda self, **kw: self.__dict__.update(kw)}))
    sdk.ClaudeSDKError = type("ClaudeSDKError", (Exception,), {})
    sdk.ClaudeAgentOptions = lambda **kw: kw

    async def query(prompt, options):
        if seen is not None:
            seen.append((prompt, options))
        for m in messages(sdk):
            if isinstance(m, Exception):
                raise m
            yield m
    sdk.query = query
    return sdk


def _client(monkeypatch, messages, seen=None):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = claude_agent.ClaudeCodeClient.__new__(claude_agent.ClaudeCodeClient)
    claude_agent.LLMClient.__init__(client, "claude-sonnet-4-5")
    client._sdk = _fake_sdk(messages, seen)
    return client


def test_spec_and_api_equivalent_price():
    assert parse_spec("claude-code:claude-sonnet-4-5") == ("claude-code", "claude-sonnet-4-5")
    assert cost_usd("claude-code:claude-sonnet-4-5", Usage(input_tokens=10**6)) == 3.0


def test_one_turn_without_tools_or_settings(monkeypatch):
    seen = []

    def messages(sdk):
        return [sdk.AssistantMessage(content=[sdk.TextBlock(text='{"a": 1}')]),
                sdk.ResultMessage(is_error=False, result='{"a": 1}', errors=None,
                                  usage={"input_tokens": 7, "output_tokens": 3, "cache_read_input_tokens": 2})]

    client = _client(monkeypatch, messages, seen)
    assert client.complete_json(["prefix", "step"]) == {"a": 1}
    prompt, options = seen[0]
    assert prompt == "prefix\n\nstep" and options["tools"] == [] and options["setting_sources"] == []
    assert options["max_turns"] == 1 and "no-session-persistence" in options["extra_args"]
    assert client.last_usage.input_tokens == 7 and client.last_usage.cache_read_tokens == 2


def test_usage_limit_carries_reset_time_and_is_not_a_pipeline_error(monkeypatch):
    def messages(sdk):
        info = types.SimpleNamespace(status="rejected", resets_at=1_900_000_000, rate_limit_type="five_hour")
        return [sdk.RateLimitEvent(rate_limit_info=info),
                sdk.ResultMessage(is_error=True, result="limit", errors=["limit"], usage=None)]

    with pytest.raises(claude_agent.UsageLimitReached) as err:
        _client(monkeypatch, messages).complete_json("p")
    assert err.value.resets_at == 1_900_000_000 and not isinstance(err.value, PipelineError)


def test_api_key_would_bill_the_key_instead(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", types.ModuleType("claude_agent_sdk"))
    with pytest.raises(PipelineError, match="ANTHROPIC_API_KEY"):
        claude_agent.ClaudeCodeClient("claude-sonnet-4-5")


def test_cached_replies_are_replayed_without_a_call(tmp_path):
    calls = []

    def generate(prompt, model=None):
        calls.append(prompt)
        return {"ok": len(calls)}

    first = AgentRuntime(generate=generate, cache_dir=tmp_path)
    assert first.complete_json(["a", "b"], purpose="p") == {"ok": 1}
    again = AgentRuntime(generate=generate, cache_dir=tmp_path)
    assert again.complete_json(["a", "b"], purpose="p") == {"ok": 1} and len(calls) == 1
    assert again.ledger.calls[0].replayed and again.ledger.summary()["total"]["calls"] == 0


def test_goal_set_stops_on_a_limit_and_resumes_where_it_stopped(tmp_path, monkeypatch, capsys):
    from .test_run_v2 import GOAL, SHOP, scripted

    spec = importlib.util.spec_from_file_location("run_goal_set", CODE / "scripts" / "run_goal_set.py")
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    goals = tmp_path / "goals.yaml"
    goals.write_text(json.dumps({"cases": {"A": {"code": str(SHOP), "goal": GOAL}, "B": {"code": str(SHOP), "goal": GOAL}}}))
    real_run_v2, state = script.run_v2, {"calls": 0, "limit": True}

    def limited(goal, code, **kw):
        state["calls"] += 1
        if state["limit"] and state["calls"] == 2:  # case B hits the limit
            raise claude_agent.UsageLimitReached(None, "five_hour")
        return real_run_v2(goal, code, generate=scripted, cache_dir=kw["cache_dir"])

    monkeypatch.setattr(script, "run_v2", limited)
    out = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["run_goal_set.py", "--goals", str(goals), "--out", str(out)])
    assert script.main() == 3
    assert (out / "A" / "README.md").exists() and not (out / "B").exists()
    state["limit"] = False
    assert script.main() == 0
    assert "skip A: already complete" in capsys.readouterr().out and (out / "B" / "README.md").exists()
