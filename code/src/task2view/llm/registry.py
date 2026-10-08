"""Choose an LLM adapter from a ``provider:model`` spec.

Examples::

    gemini:gemini-2.5-flash
    anthropic:claude-opus-5-5
    openai:<model>
    ollama:qwen2.5-coder:14b        # model ids may contain ':'
    vllm:<served-model-name>
    openrouter:<vendor>/<model>

A bare model id is accepted when its provider is obvious (``claude-…``,
``gemini-…``). A bare provider name uses that provider's default model.
The default spec is ``TASK2VIEW_LLM``, else Gemini's default model.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from functools import lru_cache

from task2view.contracts.models import PipelineError
from task2view.llm.base import LLMClient, load_dotenv

load_dotenv()

Factory = Callable[[str], LLMClient]

_FACTORIES: dict[str, Factory] = {}
_DEFAULT_MODELS: dict[str, str | None] = {}
_BARE_PREFIXES = {"claude-": "anthropic", "gemini-": "gemini"}


def register_provider(name: str, *, default_model: str | None = None):
    """Register a factory (usually an ``LLMClient`` subclass) under ``name``."""

    def wrap(factory: Factory) -> Factory:
        _FACTORIES[name] = factory
        _DEFAULT_MODELS[name] = default_model
        return factory

    return wrap


def providers() -> dict[str, str | None]:
    """Registered provider names and their default models (None = must be named)."""
    return dict(sorted(_DEFAULT_MODELS.items()))


def default_spec() -> str:
    return os.environ.get("TASK2VIEW_LLM") or "gemini"


def parse_spec(spec: str | None) -> tuple[str, str]:
    text = (spec or default_spec()).strip()
    head, sep, tail = text.partition(":")
    if head in _FACTORIES:
        provider, model = head, tail if sep else ""
    else:
        provider = next((p for prefix, p in _BARE_PREFIXES.items() if text.startswith(prefix)), "")
        model = text
        if not provider:
            raise PipelineError(
                f"unknown LLM {text!r}: use provider:model with provider one of "
                f"{', '.join(sorted(_FACTORIES))}"
            )
    model = model or _DEFAULT_MODELS.get(provider) or ""
    if not model:
        raise PipelineError(f"LLM provider {provider!r} needs a model: use {provider}:<model>")
    return provider, model


@lru_cache(maxsize=None)
def _client(provider: str, model: str) -> LLMClient:
    return _FACTORIES[provider](model)


def get_client(spec: str | None = None) -> LLMClient:
    return _client(*parse_spec(spec))


def generate_json(prompt: str, *, model: str | None = None) -> dict:
    """Single JSON completion. ``model`` is a spec; None means the default spec."""
    return get_client(model).complete_json(prompt)
