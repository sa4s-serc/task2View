"""Phase 1 — Stakeholder-Task Interpretation Agent."""

from __future__ import annotations

from task2view.agents.knowledge_context import role_catalog
from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import StakeholderTaskProfile
from task2view.knowledge.loader import KnowledgeBase, load_knowledge

PROMPT = """You are the Stakeholder-Task Interpretation Agent.

GOAL
Turn one free-text description into a stakeholder-task profile.
Later phases must use this profile and must not re-read the sentence to decide who is speaking or what the diagram is for.
The same description must produce the same fields, so two runs can be compared.

INPUTS
1. USER DESCRIPTION — the only text you may interpret.
2. ROLE CATALOG — the only legal values for canonical_role. The "also called" words are how a person might name that role.

ROLE CATALOG
{roles}

USER DESCRIPTION
{goal}

DECISION
Copy a field only from words that are in the description. Leave it empty when they are not.
Each split exists so a later phase can use one field without dragging the whole sentence along.

- stakeholder: the words they used for themselves.
  Reason: the original label is kept even after it is mapped to a catalog id.
- canonical_role: one id from the role catalog. null when no id fits.
  Reason: a closed id is what makes the role comparable across goals. Do not invent a role.
- task: the work they will do with the diagram, as a short phrase.
  Reason: the task is the job, not the wording of the request.
- target: the feature or subsystem, a noun phrase from their words.
  Reason: later questions and the file search use this noun, not the full sentence.
- goal: one sentence saying what the diagram must make clear.
  Reason: this is the success condition. It is not a second copy of the task.
- scope: a bound they stated, or an empty string.
  Reason: an invented bound would hide code the stakeholder did not exclude.
- constraints: limits they stated, or an empty list.
  Reason: same as scope. Do not add a limit they did not say.
- confidence: a number from 0 to 1 for how sure this mapping is.
  Reason: the run records uncertainty instead of hiding it.

Do not write concerns, questions, or a viewpoint. Those are the next two phases.

OUTPUT
Return only this JSON.
{{
  "stakeholder": "label as the user said it",
  "canonical_role": "one role id, or null",
  "task": "the work they will do",
  "target": "feature or subsystem",
  "goal": "what the diagram must show",
  "scope": "",
  "constraints": [],
  "confidence": 0.0
}}
"""


def interpret_stakeholder_task(
    goal: str,
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
) -> StakeholderTaskProfile:
    knowledge = knowledge or load_knowledge()
    raw = runtime.complete_json(
        PROMPT.format(roles=role_catalog(knowledge), goal=goal.strip())
    )
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
    # Concerns are identified in Phase 2, with the questions.
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
        concerns=[],
        environment=environment,
    )
