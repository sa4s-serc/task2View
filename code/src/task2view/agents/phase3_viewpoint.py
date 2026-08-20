"""PDF Phase 3 — Knowledge-Grounded Viewpoint Planning Agent."""

from __future__ import annotations

from task2view.agents.knowledge_context import stakeholder_view_hints, viewpoint_catalog
from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import PlannedView, QuestionSet, StakeholderTaskProfile, ViewpointPlan
from task2view.contracts.models import ALLOWED_VIEW_TYPES, PipelineError
from task2view.knowledge.loader import KnowledgeBase, load_knowledge
from task2view.phase2.selector import _NOTATION_LABEL, _granularity

PROMPT = """You are the Knowledge-Grounded Viewpoint Planning Agent.

Map stakeholder, task, concerns, and architectural questions onto viewpoint ids
from the catalog. Do not invent viewpoint ids.

PROFILE:
{profile}

QUESTIONS:
{questions}

CATALOG:
{catalog}

STAKEHOLDER HINTS:
{hints}

Return JSON:
{{
  "views": [
    {{
      "id": "V1",
      "viewpoint_id": "module-decomposition",
      "addresses": ["AQ1","AQ3"],
      "required_evidence": ["modules", "responsibilities", "containment"],
      "purpose": "why this view helps the task"
    }}
  ],
  "notes": []
}}

Pick the smallest set of views that covers the questions. Preferred order is
stakeholder required viewpoints, then task-fit (scenario for interaction order,
module-decomposition for modify/locate change, control-flow for processing).
"""


def plan_viewpoints(
    profile: StakeholderTaskProfile,
    questions: QuestionSet,
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
    max_views: int = 1,
    preferred_language: str | None = None,
) -> ViewpointPlan:
    knowledge = knowledge or load_knowledge()
    qtext = "\n".join(f"{q.id}: {q.text}" for q in questions.questions)
    raw = runtime.complete_json(
        PROMPT.format(
            profile=profile.model_dump_json(indent=2),
            questions=qtext,
            catalog=viewpoint_catalog(knowledge),
            hints=stakeholder_view_hints(knowledge, profile.canonical_role),
        )
    )
    planned: list[PlannedView] = []
    for i, item in enumerate(raw.get("views") or [], start=1):
        vid = str(item.get("viewpoint_id") or item.get("id") or "")
        if vid not in knowledge.viewpoints:
            continue
        viewpoint = knowledge.viewpoint(vid)
        view_type = viewpoint["view_type"]
        if view_type not in ALLOWED_VIEW_TYPES:
            continue
        formality = viewpoint.get("default_notation") or "semi-formal"
        language = knowledge.choose_language(
            view_type,
            preferred=preferred_language or viewpoint.get("default_diagram_language"),
            formality=formality,
        )
        planned.append(
            PlannedView(
                id=str(item.get("id") or f"V{i}"),
                viewpoint_id=vid,
                view_type=view_type,
                notation=_NOTATION_LABEL.get(view_type, viewpoint["name"]),
                diagram_language=language,
                granularity=_granularity(viewpoint, {}),
                purpose=str(item.get("purpose") or viewpoint.get("name") or ""),
                addresses=[str(x) for x in item.get("addresses") or []],
                required_evidence=[str(x) for x in item.get("required_evidence") or []],
                deferred=False,
            )
        )
    if not planned:
        raise PipelineError("viewpoint planning agent selected no known viewpoint")
    for extra in planned[max_views:]:
        extra.deferred = True
    return ViewpointPlan(views=planned, notes=[str(x) for x in raw.get("notes") or []])
