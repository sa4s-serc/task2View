"""Provider-neutral LLM interface.

Each provider is an adapter (``LLMClient`` subclass) around its own SDK or REST
API. Which adapter a run uses is a strategy chosen from a ``provider:model``
spec (see ``registry.py``). Phases only ever call ``complete_json``.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from task2view.contracts.models import PipelineError

JSON_INSTRUCTION = "Reply with exactly one JSON object and nothing else."


def load_dotenv() -> None:
    """Copy KEY=value lines from the nearest .env into os.environ (unset keys only)."""
    here = Path(__file__).resolve()
    for path in (Path.cwd() / ".env", here.parents[3] / ".env", here.parents[4] / ".env"):
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            name = name.strip()
            if name and name not in os.environ:
                os.environ[name] = value.strip().strip("'").strip('"')
        return


@dataclass
class Usage:
    """Tokens one call consumed, as reported by the provider's API."""

    input_tokens: int = 0  # uncached input
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


class LLMClient(ABC):
    """One model behind one provider. ``complete_text`` sets ``last_usage``."""

    provider: str = ""

    def __init__(self, model: str):
        self.model = model
        self.last_usage: Usage | None = None

    @property
    def spec(self) -> str:
        return f"{self.provider}:{self.model}"

    @abstractmethod
    def complete_text(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        """Return the model's text reply to a single user prompt."""

    def complete_json(self, prompt: str, *, system: str | None = None) -> dict:
        return parse_json(self.complete_text(prompt, system=system, json_mode=True), self.spec)


def parse_json(text: str, source: str = "model") -> dict:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3]
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end < 0:
        raise PipelineError(f"{source} did not return JSON")
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise PipelineError(f"{source} returned invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise PipelineError(f"{source} did not return a JSON object")
    return parsed
