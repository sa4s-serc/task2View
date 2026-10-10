"""Model runtime: one JSON completion per call, each call recorded with its purpose, tokens, time and cost.

With ``cache_dir``, every reply is stored under a hash of (model, prompt). The pipeline is deterministic
given the replies, so re-running an interrupted run sends the same prompts and replays the stored
replies for free: no progress is lost when a run stops on a usage limit, an error or a closed laptop.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path

from task2view.contracts.models import PipelineError
from task2view.llm import get_client
from task2view.llm.base import Prompt, joined
from task2view.llm.usage import UsageLedger

GenerateFn = Callable[..., dict]


class AgentRuntime:
    """Sends prompts to one model and records every call in ``ledger``.

    ``generate`` injects a scripted function (tests); its usage is recorded as not reported.
    """

    def __init__(self, generate: GenerateFn | None = None, *, model: str | None = None, cache_dir: str | Path | None = None):
        self.model = model
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.ledger = UsageLedger()
        self._client = None if generate is not None else get_client(model)
        self.generate = generate or (lambda prompt, model=None: self._client.complete_json(prompt))
        self.spec = self._client.spec if self._client is not None else (model or "scripted")

    def complete_json(self, prompt: Prompt, *, purpose: str = "") -> dict:
        cached = self._cache_path(prompt)
        if cached is not None and cached.exists():
            self.ledger.record(f"{purpose or 'unlabelled'} (replayed)", self.spec, None, 0.0)
            return json.loads(cached.read_text(encoding="utf-8"))
        start = time.monotonic()
        if self._client is not None:
            self._client.last_usage = None
        try:
            raw = self.generate(prompt if self._client is not None else joined(prompt), model=self.model)
        finally:
            usage = self._client.last_usage if self._client is not None else None
            self.ledger.record(purpose or "unlabelled", self.spec, usage, time.monotonic() - start)
        if not isinstance(raw, dict):
            raise PipelineError("model reply is not a JSON object")
        reply = {k: v for k, v in raw.items() if not str(k).startswith("_")}
        if cached is not None:
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_text(json.dumps(reply), encoding="utf-8")
        return reply

    def _cache_path(self, prompt: Prompt) -> Path | None:
        if self.cache_dir is None:
            return None
        key = hashlib.sha256(f"{self.spec}\n{joined(prompt)}".encode("utf-8")).hexdigest()
        return self.cache_dir / key[:2] / f"{key}.json"
