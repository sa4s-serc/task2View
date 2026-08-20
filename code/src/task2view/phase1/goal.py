"""Split a stakeholder goal statement into a role and a task."""

from __future__ import annotations

import re

from task2view.contracts.models import PipelineError
from task2view.knowledge.loader import KnowledgeBase, load_knowledge

_GOAL = re.compile(
    r"""
    ^\s*
    (?:as\s+(?:an?\s+)? | i(?:['’]m|\s+am)\s+(?:an?\s+)?)
    (?P<role>.+?)
    (?:
        \s*[.,:]\s*
        | \s+(?=i\s+(?:need|want|would|have|must|should))
    )
    (?P<rest>.+)
    $
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)


def parse_goal(
    goal: str,
    *,
    stakeholder: str | None = None,
    knowledge: KnowledgeBase | None = None,
) -> tuple[str, str, str]:
    """Return (role_label, task, original_goal)."""
    knowledge = knowledge or load_knowledge()
    statement = goal.strip()
    if not statement:
        raise PipelineError("goal statement is empty")

    match = _GOAL.match(statement)
    if stakeholder and stakeholder.strip():
        role_label = stakeholder.strip()
        task = match.group("rest").strip() if match else statement
        return role_label, task, statement

    if not match:
        raise PipelineError(
            "goal statement must name a stakeholder role "
            "(e.g. 'As a tester, I need ...') or pass --stakeholder"
        )
    role_label = match.group("role").strip().strip(".,;:")
    task = match.group("rest").strip()
    if not task:
        raise PipelineError("goal statement has a role but no task")
    knowledge.resolve_role(role_label)
    return role_label, task, statement
