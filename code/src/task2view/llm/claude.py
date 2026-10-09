"""Anthropic (Claude) adapter, using the official ``anthropic`` SDK.

Install with ``pip install -e ".[anthropic]"``. Credentials resolve the SDK's
usual way: ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or an ``ant auth login``
profile.

Thinking is left at the model default (adaptive on current models). Depth is
set with ``output_config.effort`` (TASK2VIEW_LLM_EFFORT, default ``high``).
On models that support it, a safety-classifier refusal is re-run server-side on
Anthropic's recommended fallback model (``fallbacks: "default"``).
"""

from __future__ import annotations

import os

from task2view.contracts.models import PipelineError
from task2view.llm.base import JSON_INSTRUCTION, LLMClient, Prompt, Usage
from task2view.llm.registry import register_provider

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5-5")
MAX_TOKENS = 16000
FALLBACK_BETA = "server-side-fallback-2026-07-01"
# Models that accept fallbacks: "default" on the Claude API.
_FALLBACK_MODELS = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}
# Models that reject output_config.effort.
_NO_EFFORT_PREFIXES = ("claude-haiku-4-5", "claude-sonnet-4-5")


@register_provider("anthropic", default_model=DEFAULT_MODEL)
class AnthropicClient(LLMClient):
    provider = "anthropic"
    caches_blocks = True

    def __init__(self, model: str):
        super().__init__(model)
        try:
            import anthropic
        except ImportError as exc:
            raise PipelineError(
                'The anthropic provider needs the SDK: pip install -e ".[anthropic]"'
            ) from exc
        self._sdk = anthropic
        self._client = anthropic.Anthropic()
        self.effort = os.environ.get("TASK2VIEW_LLM_EFFORT", "high")

    def complete_text(self, prompt: Prompt, *, system: str | None = None, json_mode: bool = False) -> str:
        sdk = self._sdk
        system_text = "\n\n".join(p for p in (system, JSON_INSTRUCTION if json_mode else None) if p)
        params: dict = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": _content(prompt)}],
        }
        if system_text:
            params["system"] = system_text
        if not self.model.startswith(_NO_EFFORT_PREFIXES):
            params["output_config"] = {"effort": self.effort}
        try:
            if self.model in _FALLBACK_MODELS:
                response = self._client.beta.messages.create(
                    betas=[FALLBACK_BETA], fallbacks="default", **params
                )
            else:
                response = self._client.messages.create(**params)
        except sdk.RateLimitError as exc:
            raise PipelineError(f"Anthropic rate limit ({self.model}); retry later") from exc
        except sdk.APIStatusError as exc:
            raise PipelineError(f"Anthropic request failed ({self.model}: HTTP {exc.status_code}) {exc.message}") from exc
        except sdk.APIConnectionError as exc:
            raise PipelineError(f"Anthropic connection failed: {exc}") from exc

        u = getattr(response, "usage", None)
        self.last_usage = None if u is None else Usage(
            input_tokens=getattr(u, "input_tokens", 0) or 0,
            output_tokens=getattr(u, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
        )
        if response.stop_reason == "refusal":
            details = getattr(response, "stop_details", None)
            category = getattr(details, "category", None) if details else None
            raise PipelineError(f"Anthropic declined the request ({self.model}, category={category})")
        if response.stop_reason == "max_tokens":
            raise PipelineError(f"Anthropic reply hit max_tokens={MAX_TOKENS} ({self.model})")
        return "".join(block.text for block in response.content if block.type == "text")


def _content(prompt: Prompt) -> str | list[dict]:
    """Blocks get cache breakpoints on the first (prompt and card) and the last block, so each
    tool-loop step reads the earlier steps from the cache instead of paying for them again."""
    if isinstance(prompt, str):
        return prompt
    blocks = [{"type": "text", "text": text} for text in prompt]
    for i in {0, len(blocks) - 1}:
        blocks[i]["cache_control"] = {"type": "ephemeral"}
    return blocks
