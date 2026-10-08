"""PDF Phase 3 — Knowledge-Grounded Viewpoint Planning Agent."""

from __future__ import annotations

from task2view.agents.knowledge_context import stakeholder_view_hints
from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import PlannedView, QuestionSet, StakeholderTaskProfile, ViewpointPlan
from task2view.contracts.models import ALLOWED_VIEW_TYPES, PipelineError
from task2view.knowledge.loader import KnowledgeBase, load_knowledge
from task2view.knowledge.selector import _NOTATION_LABEL, _granularity, match_task_cues

PROMPT = """You are the Knowledge-Grounded Viewpoint Planning Agent.

GOAL
Choose the one viewpoint whose diagram can answer the architectural questions already written.
The viewpoint is accepted only when its nodes are the facts those questions ask for.
Also choose the diagram language that will draw that viewpoint.
Granularity is not chosen in this step. It is looked up from the catalog for the id you return, so the same id always has the same grain.

INPUTS
1. PROFILE — who is asking, the task, the target, the goal, and any scope or constraints.
2. QUESTIONS — the questions from Phase 2, each with an id and a concern. These are the facts the diagram must supply.
3. ALLOWED — the only legal viewpoint ids. Each line states the nodes the diagram will contain, the relations, what it must not contain, which concerns it frames, and the catalog's default language for that id.
   Reason for the closed list: these ids frame the concerns Phase 2 chose. An id outside the list is not a result of this run.
4. LANGUAGES — the only legal diagram languages. Each line is an id this pipeline can render.
5. STAKEHOLDER — the role, and a reminder not to pick the diagram that role usually receives.

PROFILE
{profile}

QUESTIONS
{questions}

ALLOWED
{catalog}

LANGUAGES
{languages}

STAKEHOLDER
{hints}

DECISION
1. Read the questions first. The profile says who needs the answers. The questions say what the answers are.
2. Keep an allowed id only when its nodes and relations can show what the questions ask, and its do-not line does not forbid that.
   Reason: the diagram will contain those nodes and will omit what the do-not line names.
3. If several ids fit, choose the one whose nodes cover the questions at the top of the list. Do not pick an id because it is listed first in ALLOWED.
   Reason: the question list is already ordered, most needed first. The order of ALLOWED is not that ranking.
4. addresses lists the question ids this view answers, such as AQ1. Leave out a question these nodes cannot answer.
   Reason: an unanswered question is recorded as a gap. It is not drawn as an extra box.
5. required_evidence is what the repository must contain for the questions in addresses, using the vocabulary of the chosen nodes.
   Reason: the extraction step searches for this evidence and for nothing else this view does not owe.
6. purpose is one sentence: the target, the nodes, and why this id answers the questions rather than the other allowed ids.
   Reason: the sentence is the rationale stored with the run. It must be checkable against the questions.
7. notes says why the other allowed ids were rejected, in one sentence.
8. diagram_language is one id from LANGUAGES. Choose the language that can draw this viewpoint's nodes for these questions.
   Keep the default language on the chosen ALLOWED line when that picture fits.
   Name another language from LANGUAGES when the questions need a different picture, such as an ordered flow rather than a structure of boxes.
   language_reason is one sentence: which questions that language can show.
   Reason: the language is decided with the viewpoint, after the questions exist. A word in the goal is not a notation instruction. An id outside LANGUAGES is dropped and the catalog default is kept.

OUTPUT
Return only this JSON. Exactly one view. viewpoint_id must be copied from ALLOWED. diagram_language must be copied from LANGUAGES.
{{
  "views": [
    {{
      "id": "V1",
      "viewpoint_id": "one id from ALLOWED",
      "diagram_language": "one id from LANGUAGES",
      "language_reason": "why this language can draw these questions",
      "addresses": ["AQ1"],
      "required_evidence": ["what the repository must show"],
      "purpose": "why this viewpoint answers the questions"
    }}
  ],
  "notes": ["why this viewpoint and not the others in ALLOWED"]
}}
"""


def _make_planned_view(
    vid: str,
    item: dict,
    index: int,
    knowledge: KnowledgeBase,
    preferred_language: str | None,
) -> PlannedView | None:
    if vid not in knowledge.viewpoints:
        return None
    viewpoint = knowledge.viewpoint(vid)
    view_type = viewpoint["view_type"]
    if view_type not in ALLOWED_VIEW_TYPES:
        return None
    language, rule = _language_for(knowledge, view_type, viewpoint, item, preferred_language)
    return PlannedView(
        id=str(item.get("id") or f"V{index}"),
        viewpoint_id=vid,
        view_type=view_type,
        notation=_NOTATION_LABEL.get(view_type, viewpoint["name"]),
        diagram_language=language,
        diagram_language_rule=rule,
        granularity=_granularity(viewpoint, {}),
        purpose=str(item.get("purpose") or viewpoint.get("name") or ""),
        addresses=[str(x) for x in item.get("addresses") or []],
        required_evidence=[str(x) for x in item.get("required_evidence") or []],
        deferred=False,
    )


def _language_for(
    knowledge: KnowledgeBase,
    view_type: str,
    viewpoint: dict,
    item: dict,
    preferred_language: str | None,
) -> tuple[str, str]:
    """Request setting, else the viewpoint agent's language, else the catalog default."""
    formality = viewpoint.get("default_notation") or "semi-formal"
    default = viewpoint.get("default_diagram_language")
    if preferred_language:
        decision = knowledge.explain_language(
            view_type,
            preferred=preferred_language,
            preferred_source="request",
            formality=formality,
            viewpoint_default=default,
        )
        return decision["language"], decision["rule"]
    named = str(item.get("diagram_language") or "").strip().lower()
    reason = " ".join(str(item.get("language_reason") or "").split())
    registered = named in knowledge.notations.get("languages", {}) and knowledge.notation_supports(
        named, view_type
    )
    if registered:
        rule = f"viewpoint agent chose {named}"
        if reason:
            rule = f"{rule}: {reason}"
        return named, rule
    decision = knowledge.explain_language(
        view_type,
        preferred=None,
        preferred_source=None,
        formality=formality,
        viewpoint_default=default,
    )
    rule = decision["rule"]
    if named:
        rule = f"{rule} (agent named {named}, which is not a registered language)"
    return decision["language"], rule


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
    """Keyword override kept for tests. plan_viewpoints does not call it."""
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
        preferred_language,
    )
    if replacement is None:
        return []
    replacement.diagram_language = active.diagram_language
    replacement.diagram_language_rule = active.diagram_language_rule
    replacement.deferred = active.deferred
    for i, view in enumerate(planned):
        if view is active:
            planned[i] = replacement
            break
    return [
        f"retargeted {active.viewpoint_id} -> {replacement.viewpoint_id} "
        f"(structural tokens {structural} > behavioural {behavioural})"
    ]


def _allowed_catalog(knowledge: KnowledgeBase, viewpoint_ids: list[str], *, concerns_are_framed: bool) -> str:
    if concerns_are_framed:
        lines = ["These viewpoints frame the chosen concerns. Choose one id:"]
    else:
        lines = [
            "No viewpoint frames the chosen concerns. Choose one id from the catalog. "
            "Concerns it does not frame stay uncovered by this view:"
        ]
    for viewpoint_id in viewpoint_ids:
        if viewpoint_id not in knowledge.viewpoints:
            continue
        viewpoint = knowledge.viewpoints[viewpoint_id]
        grain = knowledge.published_grain(viewpoint_id, viewpoint.get("view_type"))
        framed = ", ".join(viewpoint.get("frames_concerns") or [])
        lines.append(
            f"- {viewpoint_id} ({viewpoint.get('name')}): "
            f"unit={grain.get('unit')}; nodes: {grain.get('nodes')}; "
            f"relations: {grain.get('relations')}; do not: {grain.get('forbid')}; "
            f"frames: {framed}; default language: {viewpoint.get('default_diagram_language')}"
        )
    return "\n".join(lines)


def _language_catalog(knowledge: KnowledgeBase) -> str:
    formality = knowledge.notations.get("formality") or {}
    lines = ["Registered diagram languages. diagram_language must be one of these ids."]
    for name in knowledge.notations.get("languages", {}):
        kind = formality.get(name)
        lines.append(f"- {name}" + (f" ({kind})" if kind else ""))
    return "\n".join(lines)


def plan_viewpoints(
    profile: StakeholderTaskProfile,
    questions: QuestionSet | None,
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
    max_views: int = 1,
    preferred_language: str | None = None,
    allowed_ids: list[str] | None = None,
    concerns_are_framed: bool = True,
) -> ViewpointPlan:
    knowledge = knowledge or load_knowledge()
    allowed = [vid for vid in (allowed_ids or list(knowledge.viewpoints)) if vid in knowledge.viewpoints]
    if not allowed:
        allowed = list(knowledge.viewpoints)
    qtext = "(none)"
    if questions is not None and questions.questions:
        qtext = "\n".join(
            f"- {q.id}: {q.text} (concern: {q.concern or 'unspecified'})" for q in questions.questions
        )
    raw = runtime.complete_json(
        PROMPT.format(
            profile=profile.model_dump_json(indent=2),
            questions=qtext,
            catalog=_allowed_catalog(knowledge, allowed, concerns_are_framed=concerns_are_framed),
            languages=_language_catalog(knowledge),
            hints=stakeholder_view_hints(
                knowledge,
                profile.canonical_role,
                chosen=list(profile.concerns),
                allowed=allowed,
            ),
        )
    )
    allowed_set = set(allowed)
    planned: list[PlannedView] = []
    for i, item in enumerate(raw.get("views") or [], start=1):
        vid = str(item.get("viewpoint_id") or "")
        if vid not in allowed_set:
            continue
        view = _make_planned_view(vid, item, i, knowledge, preferred_language)
        if view is not None:
            planned.append(view)
    notes = [str(x) for x in raw.get("notes") or []]
    if concerns_are_framed:
        notes.insert(0, "Eligible because they frame the chosen concerns: " + ", ".join(allowed))
    else:
        notes.insert(0, "No viewpoint frames the chosen concerns. Full catalog was offered.")
    if not planned:
        fallback = _make_planned_view(
            allowed[0],
            {"id": "V1", "purpose": knowledge.viewpoint(allowed[0]).get("name") or allowed[0]},
            1,
            knowledge,
            preferred_language,
        )
        if fallback is None:
            raise PipelineError("viewpoint planning agent selected no known viewpoint")
        planned = [fallback]
        notes.append(f"viewpoint agent returned no allowed id; using {allowed[0]}")
    for view in planned:
        if view.diagram_language_rule:
            notes.append(f"diagram language {view.diagram_language}: {view.diagram_language_rule}")
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
