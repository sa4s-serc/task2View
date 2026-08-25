"""PDF Phase 1 — Stakeholder-Task Interpretation Agent."""

from __future__ import annotations

from task2view.agents.knowledge_context import role_catalog
from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import StakeholderTaskProfile
from task2view.knowledge.loader import KnowledgeBase, load_knowledge

PROMPT = """You are the Stakeholder-Task Interpretation Agent.

Transform the user's free-text description into a structured profile.
The user does not have to use the words "As a ... I need".
Extract: stakeholder role, task, target (the system part), goal, scope, constraints.

{roles}

Return JSON:
{{
  "stakeholder": "label as the user said it",
  "canonical_role": "one id from the catalog if you can map it, else null",
  "task": "what they must do",
  "target": "feature or subsystem of interest",
  "goal": "what they need to understand or produce",
  "scope": "optional bound on the investigation",
  "constraints": [],
  "confidence": 0.0
}}

USER DESCRIPTION:
{goal}
"""


def interpret_stakeholder_task(
    goal: str,
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
) -> StakeholderTaskProfile:
    knowledge = knowledge or load_knowledge()
    raw = runtime.complete_json(PROMPT.format(roles=role_catalog(knowledge), goal=goal.strip()))
    label = str(raw.get("stakeholder") or raw.get("role") or "unknown").strip()
    canonical = raw.get("canonical_role") or None
    if canonical:
        try:
            canonical = knowledge.resolve_role(str(canonical))
        except Exception:
            canonical = None
    if canonical is None:
        try:
            canonical = knowledge.resolve_role(label)
        except Exception:
            canonical = None
    task = str(raw.get("task") or goal).strip()
    environment = str(raw.get("environment") or "").strip()
    blob = " ".join(
        p for p in (goal, task, str(raw.get("target") or ""), str(raw.get("goal") or "")) if p
    )
    concerns = knowledge.bind_concerns(canonical, blob)
    return StakeholderTaskProfile(
        stakeholder=canonical or label,
        canonical_role=canonical,
        original_label=label,
        task=task,
        target=str(raw.get("target") or "").strip(),
        goal=str(raw.get("goal") or task).strip(),
        scope=str(raw.get("scope") or "").strip(),
        constraints=[str(x) for x in raw.get("constraints") or []],
        confidence=raw.get("confidence"),
        source_goal=goal.strip(),
        concerns=concerns,
        environment=environment,
    )
