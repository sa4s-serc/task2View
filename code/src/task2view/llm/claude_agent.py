"""Claude through the Claude Agent SDK, signed in with your own Claude subscription (no API key).

Spec: ``claude-code:<model>``, e.g. ``claude-code:claude-sonnet-5-5``. Install with
``pip install -e ".[claude-code]"`` and sign in once by running ``claude`` and ``/login``.

Each call is one turn with no tools, no filesystem settings (no CLAUDE.md, hooks or MCP
servers) and no saved session, so it behaves like a plain completion. Usage counts against
the subscription's 5-hour and weekly limits. When a limit is hit, the call raises
``UsageLimitReached`` with the reset time; it is deliberately not a PipelineError, so no
phase swallows it, and a resumable runner (scripts/run_goal_set.py) can stop or wait.
Token counts are recorded; their cost is the API-equivalent, not a charge.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime

from task2view.contracts.models import PipelineError
from task2view.llm.base import JSON_INSTRUCTION, LLMClient, Prompt, Usage, joined
from task2view.llm.registry import register_provider

DEFAULT_MODEL = os.environ.get("CLAUDE_CODE_MODEL", "claude-sonnet-5-5")


class UsageLimitReached(RuntimeError):
    """The subscription's usage limit is reached; ``resets_at`` is a Unix time (or None if unknown)."""

    def __init__(self, resets_at: int | None, kind: str | None):
        self.resets_at, self.kind = resets_at, kind
        when = datetime.fromtimestamp(resets_at).strftime("%Y-%m-%d %H:%M") if resets_at else "unknown"
        super().__init__(f"Claude usage limit reached ({kind or 'unknown window'}); resets at {when}")


@register_provider("claude-code", default_model=DEFAULT_MODEL)
class ClaudeCodeClient(LLMClient):
    provider = "claude-code"

    def __init__(self, model: str):
        super().__init__(model)
        try:
            import claude_agent_sdk
        except ImportError as exc:
            raise PipelineError('the claude-code provider needs the Agent SDK: pip install -e ".[claude-code]"') from exc
        if os.environ.get("ANTHROPIC_API_KEY"):  # the CLI would bill the key instead of the subscription
            raise PipelineError("ANTHROPIC_API_KEY is set: unset it to use your subscription, or use anthropic:<model>")
        self._sdk = claude_agent_sdk

    def complete_text(self, prompt: Prompt, *, system: str | None = None, json_mode: bool = False) -> str:
        return asyncio.run(self._ask(joined(prompt), "\n\n".join(p for p in (system, JSON_INSTRUCTION if json_mode else None) if p)))

    async def _ask(self, prompt: str, system: str) -> str:
        sdk = self._sdk
        options = sdk.ClaudeAgentOptions(model=self.model, system_prompt=system, tools=[], max_turns=1,
                                         setting_sources=[], extra_args={"no-session-persistence": None})
        text, result, limit = [], None, None
        try:
            async for message in sdk.query(prompt=prompt, options=options):
                if isinstance(message, sdk.RateLimitEvent) and message.rate_limit_info.status == "rejected":
                    limit = message.rate_limit_info
                elif isinstance(message, sdk.AssistantMessage):
                    text += [b.text for b in message.content if isinstance(b, sdk.TextBlock)]
                elif isinstance(message, sdk.ResultMessage):
                    result = message
        except sdk.ClaudeSDKError as exc:
            if limit is not None:
                raise UsageLimitReached(limit.resets_at, limit.rate_limit_type) from exc
            raise PipelineError(f"Claude Code call failed ({self.model}): {exc}") from exc
        if result is not None and result.usage:
            u = result.usage
            self.last_usage = Usage(input_tokens=u.get("input_tokens", 0) or 0, output_tokens=u.get("output_tokens", 0) or 0,
                                    cache_read_tokens=u.get("cache_read_input_tokens", 0) or 0,
                                    cache_write_tokens=u.get("cache_creation_input_tokens", 0) or 0)
        if limit is not None and (result is None or result.is_error):
            raise UsageLimitReached(limit.resets_at, limit.rate_limit_type)
        if result is None or result.is_error:
            detail = (result.errors or [result.result]) if result else ["no result"]
            raise PipelineError(f"Claude Code call failed ({self.model}): {'; '.join(map(str, detail))[:300]}")
        return result.result or "".join(text)
