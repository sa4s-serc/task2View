"""Minimal agent runtime: JSON completion, or JSON tool loop (ADR-001)."""

from __future__ import annotations

import time
from collections.abc import Callable

from task2view.agents.tools import RepoTools
from task2view.contracts.models import PipelineError
from task2view.llm import get_client
from task2view.llm.usage import UsageLedger

GenerateFn = Callable[..., dict]


class AgentRuntime:
    """Sends prompts to one model and records every call (purpose, tokens, seconds, cost) in ``ledger``.

    ``generate`` injects a scripted function (tests); then usage is recorded as not reported.
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
            raise PipelineError("agent did not return a JSON object")
        return {k: v for k, v in raw.items() if not str(k).startswith("_")}

    def tool_loop(
        self,
        instruction: str,
        tools: RepoTools,
        *,
        max_steps: int = 8,
    ) -> dict:
        history = (
            instruction
            + "\n\nYou may inspect the repository with tools. Reply with JSON only, one of:\n"
            '{"tool":"list_tree","args":{"path":".","depth":3}}\n'
            '{"tool":"search","args":{"pattern":"Reservation","glob":".java"}}\n'
            '{"tool":"read","args":{"path":"relative/file.java","max_chars":8000}}\n'
            '{"tool":"graph_query","args":{"name":"TypeName"}}\n'
            '{"tool":"traverse_graph","args":{"name":"TypeName","hops":1}}\n'
            '{"tool":"edges_among","args":{"names":["A","B"]}}\n'
            '{"tool":"missing_neighbors","args":{"names":["A","B"]}}\n'
            '{"tool":"package_of","args":{"name":"TypeName"}}\n'
            '{"final": { ... the output object required above ... }}\n'
            "When you have enough evidence, return final. Do not invent files or types.\n"
        )
        for _ in range(max_steps):
            raw = self.complete_json(history)
            if "final" in raw:
                final = raw["final"]
                return final if isinstance(final, dict) else raw
            tool = raw.get("tool")
            if tool:
                observation = tools.dispatch(str(tool), raw.get("args") if isinstance(raw.get("args"), dict) else {})
                if len(observation) > 12_000:
                    observation = observation[:12_000] + "\n… truncated"
                history += f"\n\nTOOL {tool} RESULT:\n{observation}\n\nContinue. JSON only.\n"
                continue
            return raw
        raise PipelineError("agent exceeded tool-loop steps without a final answer")
