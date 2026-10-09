"""Model runtime: one JSON completion per call, each call recorded with its purpose, tokens, time and cost."""

from __future__ import annotations

import time
from collections.abc import Callable

from task2view.contracts.models import PipelineError
from task2view.llm import get_client
from task2view.llm.usage import UsageLedger

GenerateFn = Callable[..., dict]


class AgentRuntime:
    """Sends prompts to one model and records every call in ``ledger``.

    ``generate`` injects a scripted function (tests); its usage is recorded as not reported.
    """

    def __init__(self, generate: GenerateFn | None = None, *, model: str | None = None):
        self.model = model
        self.ledger = UsageLedger()
        self._client = None if generate is not None else get_client(model)
        self.generate = generate or (lambda prompt, model=None: self._client.complete_json(prompt))
        self.spec = self._client.spec if self._client is not None else (model or "scripted")

    def complete_json(self, prompt: str, *, purpose: str = "") -> dict:
        start = time.monotonic()
        if self._client is not None:
            self._client.last_usage = None
        try:
            raw = self.generate(prompt, model=self.model)
        finally:
            usage = self._client.last_usage if self._client is not None else None
            self.ledger.record(purpose or "unlabelled", self.spec, usage, time.monotonic() - start)
        if not isinstance(raw, dict):
            raise PipelineError("model reply is not a JSON object")
        return {k: v for k, v in raw.items() if not str(k).startswith("_")}
