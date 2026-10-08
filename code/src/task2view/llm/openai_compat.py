"""OpenAI and OpenAI-compatible adapters (open-source models), using the ``openai`` SDK.

Install with ``pip install -e ".[openai]"``. One adapter class, several presets:

| provider            | endpoint                                   | key env var            |
|---------------------|--------------------------------------------|------------------------|
| `openai`            | OpenAI                                     | OPENAI_API_KEY         |
| `openrouter`        | https://openrouter.ai/api/v1               | OPENROUTER_API_KEY     |
| `ollama`            | OLLAMA_BASE_URL or http://localhost:11434/v1 | (none)               |
| `vllm`              | VLLM_BASE_URL or http://localhost:8000/v1  | VLLM_API_KEY (optional) |
| `openai-compatible` | OPENAI_COMPAT_BASE_URL (required)          | OPENAI_COMPAT_API_KEY  |

No preset has a default model: name it, e.g. ``ollama:qwen2.5-coder:14b``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from task2view.contracts.models import PipelineError
from task2view.llm.base import JSON_INSTRUCTION, LLMClient
from task2view.llm.registry import register_provider


@dataclass(frozen=True)
class Endpoint:
    base_url_env: str | None
    base_url_default: str | None
    key_env: str | None
    key_default: str | None = None


PRESETS: dict[str, Endpoint] = {
    "openai": Endpoint(None, None, "OPENAI_API_KEY"),
    "openrouter": Endpoint(None, "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "ollama": Endpoint("OLLAMA_BASE_URL", "http://localhost:11434/v1", None, "ollama"),
    "vllm": Endpoint("VLLM_BASE_URL", "http://localhost:8000/v1", "VLLM_API_KEY", "EMPTY"),
    "openai-compatible": Endpoint("OPENAI_COMPAT_BASE_URL", None, "OPENAI_COMPAT_API_KEY", "EMPTY"),
}


class OpenAICompatibleClient(LLMClient):
    def __init__(self, provider: str, model: str):
        super().__init__(model)
        self.provider = provider
        try:
            import openai
        except ImportError as exc:
            raise PipelineError(f'The {provider} provider needs the SDK: pip install -e ".[openai]"') from exc
        self._sdk = openai
        endpoint = PRESETS[provider]
        base_url = (os.environ.get(endpoint.base_url_env) if endpoint.base_url_env else None) or endpoint.base_url_default
        if endpoint.base_url_env and not base_url:
            raise PipelineError(f"{provider}: set {endpoint.base_url_env}")
        key = (os.environ.get(endpoint.key_env) if endpoint.key_env else None) or endpoint.key_default
        if not key:
            raise PipelineError(f"{provider}: set {endpoint.key_env}")
        self._client = openai.OpenAI(api_key=key, base_url=base_url)

    def complete_text(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        sdk = self._sdk
        system_text = "\n\n".join(p for p in (system, JSON_INSTRUCTION if json_mode else None) if p)
        messages = ([{"role": "system", "content": system_text}] if system_text else []) + [
            {"role": "user", "content": prompt}
        ]
        try:
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **({"response_format": {"type": "json_object"}} if json_mode else {}),
                )
            except sdk.BadRequestError:
                if not json_mode:
                    raise
                # Some open-source servers reject response_format; the instruction still asks for JSON.
                response = self._client.chat.completions.create(model=self.model, messages=messages)
        except sdk.RateLimitError as exc:
            raise PipelineError(f"{self.spec} rate limit; retry later") from exc
        except sdk.APIStatusError as exc:
            raise PipelineError(f"{self.spec} request failed (HTTP {exc.status_code})") from exc
        except sdk.APIConnectionError as exc:
            raise PipelineError(f"{self.spec} connection failed: {exc}") from exc
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise PipelineError(f"{self.spec} reply was cut off (finish_reason=length)")
        return choice.message.content or ""


def _preset(name: str):
    return lambda model: OpenAICompatibleClient(name, model)


for _name in PRESETS:
    register_provider(_name)(_preset(_name))
