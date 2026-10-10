"""Token usage and cost per model call (research plan RQ4: time, tokens, cost).

The runtime records one entry per call: which phase and task it served, which
model answered, the tokens the provider reported, and the time it took. Cost
uses knowledge/data/vb/pricing.yaml; a model without a price is reported with
cost None (unknown), never guessed.
"""

from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from importlib import resources

import yaml
from pydantic import BaseModel, Field

from task2view.llm.base import Usage


@lru_cache(maxsize=1)
def pricing() -> dict:
    path = resources.files("task2view.knowledge.data").joinpath("vb", "pricing.yaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def cost_usd(spec: str, usage: Usage) -> float | None:
    models = pricing().get("models") or {}
    # a Claude subscription (claude-code:) is not billed per token: report the API-equivalent cost
    price = models.get(spec) or models.get(spec.replace("claude-code:", "anthropic:", 1))
    if price is None:
        return None
    return (usage.input_tokens * price["input"] + usage.output_tokens * price["output"]
            + usage.cache_read_tokens * price["cache_read"] + usage.cache_write_tokens * price["cache_write"]) / 1e6


class CallRecord(BaseModel):
    purpose: str  # phase1 | phase4:<task> | phase5:<task> | phase8-judge:<view> | ...
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    seconds: float = 0.0
    cost_usd: float | None = None
    reported: bool = True  # False when the provider returned no usage (e.g. scripted runs)


class UsageLedger(BaseModel):
    calls: list[CallRecord] = Field(default_factory=list)

    def record(self, purpose: str, model: str, usage: Usage | None, seconds: float) -> None:
        if usage is None:
            self.calls.append(CallRecord(purpose=purpose, model=model, seconds=seconds, reported=False))
            return
        self.calls.append(CallRecord(purpose=purpose, model=model, seconds=seconds, cost_usd=cost_usd(model, usage),
                                     input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                                     cache_read_tokens=usage.cache_read_tokens, cache_write_tokens=usage.cache_write_tokens))

    def extend(self, other: "UsageLedger") -> None:
        self.calls.extend(other.calls)

    def summary(self) -> dict:
        def block(records: list[CallRecord]) -> dict:
            costs = [r.cost_usd for r in records]
            known = all(c is not None for c in costs) and all(r.reported for r in records)
            return {
                "calls": len(records),
                "input_tokens": sum(r.input_tokens for r in records),
                "output_tokens": sum(r.output_tokens for r in records),
                "cache_read_tokens": sum(r.cache_read_tokens for r in records),
                "cache_write_tokens": sum(r.cache_write_tokens for r in records),
                "seconds": round(sum(r.seconds for r in records), 1),
                "cost_usd": round(sum(c for c in costs if c is not None), 4),
                "cost_complete": known,  # False: some calls had no usage or no price
            }

        by_phase: dict[str, list[CallRecord]] = defaultdict(list)
        by_model: dict[str, list[CallRecord]] = defaultdict(list)
        for r in self.calls:
            by_phase[r.purpose.split(":", 1)[0]].append(r)
            by_model[r.model].append(r)
        return {
            "total": block(self.calls),
            "by_phase": {k: block(v) for k, v in sorted(by_phase.items())},
            "by_model": {k: block(v) for k, v in sorted(by_model.items())},
            "pricing_source": f"{pricing().get('source')} (read {pricing().get('read_on')})",
        }
