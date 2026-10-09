"""Phase 5 — evidence extraction agent (bounded tool loop; ADR-006 D2; design 02 §5).

One agent per investigation task. It reads the repository through CardTools,
starting from the task's seeds but free to follow references, and returns small,
cited claims. It does not decide what is true: phase5/verify.py checks every
citation against the files and the dependency graph before anything enters the
Architecture Evidence Model.
"""

from __future__ import annotations

import json
from collections import Counter

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.aem import InvestigationTask, Question
from task2view.contracts.card import RepositoryCard
from task2view.phase5.card_tools import CardTools
from task2view.prompts import load_prompt


_MAX_OBSERVATION = 12000
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
    keep_results: int = 4,
) -> tuple[list[dict], list[str], Counter]:
    """Run one task. Returns (raw claim dicts, files opened, tool-call counts)."""
    tools = CardTools(card, task.seeds.classes, max_read_lines=max_read_lines, max_hits=max_hits)
    prompt = load_prompt("phase5_evidence").render(
        goal=task.goal,
        questions="\n".join(f"- {q.id}: {q.text}" for q in questions if q.id in task.question_ids),
        viewpoint=viewpoint_name,
        elements=", ".join(task.expect_elements),
        relations=", ".join(task.expect_relations),
        card=card_text,
        symbols=", ".join(task.seeds.symbols) or "none",
        paths=", ".join(task.seeds.paths) or "none",
    )
    blocks = [prompt]  # the prompt, then one block per step: older results are masked, the prefix stays cacheable
    results: list[int] = []  # indexes of blocks holding a full tool result
    seen_calls: set[str] = set()
    for step in range(task.budget_steps + 1):
        if step == task.budget_steps:
            blocks.append(_FINAL_NUDGE)
        reply = runtime.complete_json(blocks, purpose=f"phase5:{task.id}")
        if "final" in reply:
            final = reply["final"]
            claims = final.get("claims") if isinstance(final, dict) else final
            claims = [c for c in claims if isinstance(c, dict)] if isinstance(claims, list) else []
            return claims, sorted(tools.opened), tools.calls
        tool = reply.get("tool")
        if not tool:
            blocks.append(f"REPLY {json.dumps(reply)[:500]}\nRESULT: not a tool call. "
                          'Reply with {"tool": ...} or {"final": ...}.')
            continue
        call = json.dumps(reply, sort_keys=True)
        if call in seen_calls:
            observation = "repeated call: its result is above (or was elided); change the arguments or finish"
        else:
            seen_calls.add(call)
            observation = tools.dispatch(str(tool), reply.get("args") if isinstance(reply.get("args"), dict) else {})
        if len(observation) > _MAX_OBSERVATION:
            observation = observation[:_MAX_OBSERVATION] + "\n[truncated; narrow the call]"
        blocks.append(f"CALL {json.dumps(reply)}\nRESULT:\n{observation}\n\nContinue. JSON only.")
        results.append(len(blocks) - 1)
        for i in results[:-keep_results] if keep_results else results:
            if not blocks[i].startswith("CALL") or "[result elided" in blocks[i]:
                continue
            head = blocks[i].split("\nRESULT:", 1)[0]
            blocks[i] = f"{head}\nRESULT: [result elided to save context; repeat a read to see it again]"
    tools.calls["budget-exhausted"] += 1
    return [], sorted(tools.opened), tools.calls
