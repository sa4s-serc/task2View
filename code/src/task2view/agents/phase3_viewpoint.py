"""PDF Phase 3 — Knowledge-Grounded Viewpoint Planning Agent."""

from __future__ import annotations

from task2view.agents.knowledge_context import stakeholder_view_hints, task_cue_block, viewpoint_catalog
from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import PlannedView, QuestionSet, StakeholderTaskProfile, ViewpointPlan
from task2view.contracts.models import ALLOWED_VIEW_TYPES, PipelineError
from task2view.knowledge.correspondence import Correspondence
from task2view.knowledge.loader import KnowledgeBase, load_knowledge
from task2view.phase2.selector import _NOTATION_LABEL, _granularity, match_task_cues

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

TASK CUES (from task_cues.yaml, matched against the profile text):
{cues}

RANKED CANDIDATES (catalog correspondence; you may only pick viewpoint_id from this list):
{candidates}

DEFAULT GRAIN:
{grain}

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
task-cue prefer_viewpoints (if any), then stakeholder required viewpoints,
then task-fit (scenario for interaction order, module-decomposition for
modify/locate change, control-flow for processing, context for overview,
allocation-deployment for runtime, data-model for persistence).

purpose must match the catalog grain of viewpoint_id (see CATALOG unit/nodes).
A module viewpoint must not mention classes. A scenario viewpoint describes
participants and order, not a class list. A data-model viewpoint may mention
entities. Do not force every stakeholder onto a component diagram.
"""


def _make_planned_view(
    vid: str,
    item: dict,
    index: int,
    knowledge: KnowledgeBase,
    profile: StakeholderTaskProfile,
    preferred_language: str | None,
) -> PlannedView | None:
    if vid not in knowledge.viewpoints:
        return None
    viewpoint = knowledge.viewpoint(vid)
    view_type = viewpoint["view_type"]
    if view_type not in ALLOWED_VIEW_TYPES:
        return None
    formality = viewpoint.get("default_notation") or "semi-formal"
    from_goal = knowledge.detect_language(profile.source_goal or profile.task)
    language = knowledge.choose_language(
        view_type,
        preferred=preferred_language or from_goal,
        formality=formality,
        viewpoint_default=viewpoint.get("default_diagram_language"),
    )
    return PlannedView(
        id=str(item.get("id") or f"V{index}"),
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


def _token_hits(blob: str, tokens: list[str]) -> int:
    low = blob.casefold()
    return sum(1 for token in tokens if token.casefold() in low)


def retarget_if_structural(
    planned: list[PlannedView],
    questions: QuestionSet,
    knowledge: KnowledgeBase,
    profile: StakeholderTaskProfile,
    preferred_language: str | None,
) -> list[str]:
    """Prefer a module/context viewpoint when questions ask for structure, not order."""
    cfg = knowledge.view_projection.get("viewpoint_tiebreak") or {}
    if not planned:
        return []
    active = next((view for view in planned if not view.deferred), None)
    if active is None:
        return []
    behavioural_ids = {str(x) for x in cfg.get("behavioural_ids") or []}
    if active.viewpoint_id not in behavioural_ids:
        return []
    cue_blob = " ".join(
        p for p in (profile.source_goal, profile.task, profile.target, profile.goal) if p
    )
    _, preferred, _ = match_task_cues(cue_blob, knowledge)
    if any(vid in behavioural_ids for vid in preferred):
        return []
    blob = " ".join(
        [
            " ".join(active.required_evidence),
            " ".join(q.text for q in questions.questions),
            profile.task or "",
            profile.goal or "",
            profile.source_goal or "",
        ]
    )
    structural = _token_hits(blob, [str(x) for x in cfg.get("structural_tokens") or []])
    behavioural = _token_hits(blob, [str(x) for x in cfg.get("behavioural_tokens") or []])
    if structural < behavioural or structural == 0:
        return []
    fallback = str(cfg.get("fallback_viewpoint") or "module-decomposition")
    replacement = _make_planned_view(
        fallback,
        {
            "id": active.id,
            "purpose": active.purpose,
            "addresses": active.addresses,
            "required_evidence": active.required_evidence,
        },
        1,
        knowledge,
        profile,
        preferred_language,
    )
    if replacement is None:
        return []
    replacement.deferred = active.deferred
    for i, view in enumerate(planned):
        if view is active:
            planned[i] = replacement
            break
    return [
        f"retargeted {active.viewpoint_id} -> {replacement.viewpoint_id} "
        f"(structural tokens {structural} > behavioural {behavioural})"
    ]


def plan_viewpoints(
    profile: StakeholderTaskProfile,
    questions: QuestionSet,
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
    max_views: int = 1,
    preferred_language: str | None = None,
    correspondence: Correspondence | None = None,
) -> ViewpointPlan:
    knowledge = knowledge or load_knowledge()
    cue_blob = " ".join(
        p for p in (profile.source_goal, profile.task, profile.target, profile.goal) if p
    )
    concerns, preferred, phrases = match_task_cues(cue_blob, knowledge)
    allowed = set(correspondence.candidate_ids()) if correspondence is not None else set()
    candidate_block = "No pre-ranked list; pick a catalog id."
    grain_block = "See CATALOG unit/nodes."
    if correspondence is not None:
        lines = [
            f"- {row.viewpoint_id} (score={row.score:.1f}, {row.view_type}) "
            f"{'; '.join(row.reasons[:2])}"
            for row in correspondence.ranked[:8]
        ]
        candidate_block = "\n".join(lines) or candidate_block
        grain_block = correspondence.grain.prompt()
    qtext = "\n".join(f"{q.id}: {q.text}" for q in questions.questions)
    raw = runtime.complete_json(
        PROMPT.format(
            profile=profile.model_dump_json(indent=2),
            questions=qtext,
            catalog=viewpoint_catalog(knowledge),
            hints=stakeholder_view_hints(knowledge, profile.canonical_role),
            cues=task_cue_block(concerns, preferred, phrases),
            candidates=candidate_block,
            grain=grain_block,
        )
    )
    planned: list[PlannedView] = []
    for i, item in enumerate(raw.get("views") or [], start=1):
        vid = str(item.get("viewpoint_id") or item.get("id") or "")
        if allowed and vid not in allowed:
            continue
        view = _make_planned_view(vid, item, i, knowledge, profile, preferred_language)
        if view is not None:
            planned.append(view)
    if not planned and correspondence is not None:
        view = _make_planned_view(
            correspondence.viewpoint_id,
            {
                "id": "V1",
                "purpose": correspondence.purpose,
                "required_evidence": [correspondence.grain.nodes, correspondence.grain.relations],
            },
            1,
            knowledge,
            profile,
            preferred_language,
        )
        if view is not None:
            view.purpose = correspondence.purpose
            planned.append(view)
    if not planned:
        raise PipelineError("viewpoint planning agent selected no known viewpoint")
    notes = [str(x) for x in raw.get("notes") or []]
    notes.extend(
        retarget_if_structural(planned, questions, knowledge, profile, preferred_language)
    )
    if allowed:
        active = next((view for view in planned if not view.deferred), None)
        if active is not None and active.viewpoint_id not in allowed:
            replacement = _make_planned_view(
                correspondence.viewpoint_id,
                {
                    "id": active.id,
                    "purpose": correspondence.purpose,
                    "addresses": active.addresses,
                    "required_evidence": active.required_evidence,
                },
                1,
                knowledge,
                profile,
                preferred_language,
            )
            if replacement is not None:
                for i, view in enumerate(planned):
                    if view is active:
                        planned[i] = replacement
                        break
                notes.append(
                    f"snapped {active.viewpoint_id} -> {correspondence.viewpoint_id} "
                    "(outside ranked candidates)"
                )
    for view in planned:
        note = _sanitize_purpose(view, knowledge, profile)
        if note:
            notes.append(note)
    for extra in planned[max_views:]:
        extra.deferred = True
    return ViewpointPlan(views=planned, notes=notes)


_PURPOSE_TYPE_MARKERS = (
    "specific class",
    "specific classes",
    "classes owning",
    "class names",
    "call chain",
    "type names",
    "classes",
)


def _sanitize_purpose(
    view: PlannedView,
    knowledge: KnowledgeBase,
    profile: StakeholderTaskProfile,
) -> str | None:
    if knowledge.published_grain(view.viewpoint_id).get("unit") == "type":
        return None
    low = (view.purpose or "").casefold()
    if not any(marker in low for marker in _PURPOSE_TYPE_MARKERS):
        return None
    grain = knowledge.published_grain(view.viewpoint_id)
    viewpoint = knowledge.viewpoint(view.viewpoint_id)
    name = str(viewpoint.get("name") or view.viewpoint_id)
    focus = profile.target or profile.task or "the task"
    view.purpose = (
        f"{name} for {focus}: {grain.get('nodes')}. "
        f"Relations: {grain.get('relations')}. Do not: {grain.get('forbid')}."
    )
    return f"sanitized purpose for {view.viewpoint_id} to catalog grain"
