"""PDF Phase 2 — Concern and Architectural Question Agent."""

from __future__ import annotations

from task2view.agents.knowledge_context import question_templates, stakeholder_view_hints
from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import ArchitecturalQuestion, QuestionSet, StakeholderTaskProfile
from task2view.knowledge.loader import KnowledgeBase, load_knowledge

PROMPT = """You are the Concern and Architectural Question Agent.

The user does not supply architectural questions. You derive them.
They are the information the stakeholder needs in order to perform the task.

PROFILE:
{profile}

STAKEHOLDER HINTS:
{hints}

SEED TEMPLATES (you may rewrite, drop, or add questions):
{seeds}

Return JSON:
{{
  "concerns": ["maintainability"],
  "questions": [
    {{"id":"AQ1","text":"...","concern":"maintainability","priority":1}}
  ]
}}

Rules:
- 3 to 8 questions.
- Each question must be answerable from a software repository in principle.
- Prefer the stakeholder's task and target over generic architecture dumps.
"""


def derive_questions(
    profile: StakeholderTaskProfile,
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
) -> QuestionSet:
    knowledge = knowledge or load_knowledge()
    role = profile.canonical_role
    viewpoint_ids: list[str] = []
    if role and role in knowledge.stakeholders:
        vp = knowledge.stakeholders[role].get("viewpoints") or {}
        viewpoint_ids = list(vp.get("required") or []) + list(vp.get("optional") or [])
    if not viewpoint_ids:
        viewpoint_ids = ["module-decomposition", "scenario", "control-flow"]
    focus = profile.target or profile.task
    raw = runtime.complete_json(
        PROMPT.format(
            profile=profile.model_dump_json(indent=2),
            hints=stakeholder_view_hints(knowledge, role),
            seeds=question_templates(knowledge, viewpoint_ids[:6], focus),
        )
    )
    questions = []
    for i, item in enumerate(raw.get("questions") or [], start=1):
        if isinstance(item, str):
            questions.append(ArchitecturalQuestion(id=f"AQ{i}", text=item, priority=i))
            continue
        questions.append(
            ArchitecturalQuestion(
                id=str(item.get("id") or f"AQ{i}"),
                text=str(item.get("text") or item.get("question") or "").strip(),
                concern=item.get("concern"),
                priority=int(item.get("priority") or i),
            )
        )
    questions = [q for q in questions if q.text]
    if not questions:
        questions = [
            ArchitecturalQuestion(
                id="AQ1",
                text=f"Which components participate in {focus} and how do they interact?",
                priority=1,
            )
        ]
    concerns = [str(c) for c in raw.get("concerns") or []]
    return QuestionSet(concerns=concerns, questions=questions)
