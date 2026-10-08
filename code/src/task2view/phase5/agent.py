"""Phase 5 — evidence extraction agent (bounded tool loop; ADR-006 D2; design 02 §5).

One agent per investigation task. It reads the repository through CardTools,
starting from the task's seeds but free to follow references, and returns small,
cited claims. It does not decide what is true: phase5/verify.py checks every
citation against the files and the dependency graph before anything enters the
Architecture Evidence Model.
"""

from __future__ import annotations

import json

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.aem import InvestigationTask, Question
from task2view.contracts.card import RepositoryCard
from task2view.contracts.models import PipelineError
from task2view.phase5.card_tools import CardTools
from task2view.prompts import load_prompt


_FINAL_NUDGE = "Step budget reached. Return {\"final\": {\"claims\": [...]}} now with the claims you can cite."


def run_evidence_task(
    task: InvestigationTask,
    questions: list[Question],
    card: RepositoryCard,
    runtime: AgentRuntime,
    *,
    card_text: str,
    viewpoint_name: str,
    max_read_lines: int = 200,
    max_hits: int = 40,
) -> tuple[list[dict], list[str]]:
    """Run one task. Returns (raw claim dicts, files opened)."""
    tools = CardTools(card, task.seeds.classes, max_read_lines=max_read_lines, max_hits=max_hits)
    history = load_prompt("phase5_evidence").render(
        goal=task.goal,
        questions="\n".join(f"- {q.id}: {q.text}" for q in questions if q.id in task.question_ids),
        viewpoint=viewpoint_name,
        elements=", ".join(task.expect_elements),
        relations=", ".join(task.expect_relations),
        card=card_text,
        symbols=", ".join(task.seeds.symbols) or "none",
        paths=", ".join(task.seeds.paths) or "none",
    )
    for step in range(task.budget_steps + 1):
        if step == task.budget_steps:
            history += "\n\n" + _FINAL_NUDGE
        reply = runtime.complete_json(history)
        if "final" in reply:
            claims = (reply.get("final") or {}).get("claims") or []
            return [c for c in claims if isinstance(c, dict)], sorted(tools.opened)
        tool = reply.get("tool")
        if not tool:
            raise PipelineError(f"{task.id}: agent reply is neither a tool call nor final")
        observation = tools.dispatch(str(tool), reply.get("args") if isinstance(reply.get("args"), dict) else {})
        history += f"\n\nCALL {json.dumps(reply)}\nRESULT:\n{observation[:12000]}\n\nContinue. JSON only."
    return [], sorted(tools.opened)
