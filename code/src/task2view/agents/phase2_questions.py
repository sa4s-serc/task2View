"""PDF Phase 2 — Concern and Architectural Question Agent."""

from __future__ import annotations

from task2view.agents.knowledge_context import grain_summaries, question_templates, stakeholder_view_hints
from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import ArchitecturalQuestion, QuestionSet, StakeholderTaskProfile
from task2view.knowledge.correspondence import Correspondence
from task2view.knowledge.loader import KnowledgeBase, load_knowledge
from task2view.phase2.selector import match_task_cues

PROMPT = """You are the Concern and Architectural Question Agent.

The user does not supply architectural questions. You derive them.
They are the information the stakeholder needs in order to perform the task.

PROFILE:
{profile}

STAKEHOLDER HINTS:
{hints}

PUBLISHED GRAIN of the selected viewpoint (questions must stay at this grain):
{grains}

SEED TEMPLATES (rewrite to the task; stay at the grain of those viewpoints):
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
- Match question grain to the catalog viewpoints above. A tester's scenario
  viewpoint may ask how a request is processed; an architect's module viewpoint
  asks modules and uses; a data-model viewpoint may ask entities. Do not ask
  for a class inventory unless a seeded viewpoint's unit is type. Do not ask
  for an exact call chain unless a seeded viewpoint is scenario or control-flow.
- Do not assume every stakeholder needs a component diagram.
"""


def derive_questions(
    profile: StakeholderTaskProfile,
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
    correspondence: Correspondence | None = None,
) -> QuestionSet:
    knowledge = knowledge or load_knowledge()
    role = profile.canonical_role
    viewpoint_ids: list[str] = []
    if correspondence is not None:
        viewpoint_ids = [correspondence.viewpoint_id]
    elif role and role in knowledge.stakeholders:
        vp = knowledge.stakeholders[role].get("viewpoints") or {}
        viewpoint_ids = list(vp.get("required") or []) + list(vp.get("optional") or [])
    if not viewpoint_ids:
        viewpoint_ids = ["module-decomposition", "scenario", "control-flow"]
    blob = " ".join(
        p for p in (profile.task, profile.goal, profile.source_goal, profile.target) if p
    )
    _, preferred, _ = match_task_cues(blob, knowledge)
    if correspondence is not None:
        grain_ids = viewpoint_ids
    else:
        grain_ids = [vid for vid in preferred if vid in knowledge.viewpoints] or viewpoint_ids
    focus = profile.target or profile.task
    raw = runtime.complete_json(
        PROMPT.format(
            profile=profile.model_dump_json(indent=2),
            hints=stakeholder_view_hints(knowledge, role),
            grains=grain_summaries(knowledge, grain_ids[:8]),
            seeds=question_templates(knowledge, grain_ids[:6], focus),
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
    allow_behavioural = _goal_is_behavioural(profile, knowledge) or any(
        vid in {"scenario", "control-flow"} for vid in grain_ids
    )
    allow_types = any(
        knowledge.published_grain(vid).get("unit") == "type" for vid in grain_ids
    )
    questions = [
        q
        for q in questions
        if _keep_question(q.text, allow_behavioural=allow_behavioural, allow_types=allow_types)
    ]
    if not questions:
        questions = _fallback_questions(focus, grain_ids, knowledge)
    concerns = [str(c) for c in raw.get("concerns") or []]
    return QuestionSet(concerns=concerns, questions=questions)


_CLASS_LIST_MARKERS = (
    "specific class",
    "specific classes",
    "which classes",
    "list the class",
    "class names",
    "every class",
    "all classes",
)
_TYPE_MARKERS = (
    "persistent entities",
    "data entities stored",
    "entity relationship",
)
_CALL_CHAIN_MARKERS = (
    "exact call chain",
    "call chain",
    "execution order",
)


def _token_hits(blob: str, tokens: list[str]) -> int:
    low = blob.casefold()
    return sum(1 for token in tokens if token.casefold() in low)


def _goal_is_behavioural(profile: StakeholderTaskProfile, knowledge: KnowledgeBase) -> bool:
    cfg = knowledge.view_projection.get("viewpoint_tiebreak") or {}
    blob = " ".join(
        p for p in (profile.task, profile.goal, profile.source_goal, profile.target) if p
    )
    behavioural = _token_hits(blob, [str(x) for x in cfg.get("behavioural_tokens") or []])
    structural = _token_hits(blob, [str(x) for x in cfg.get("structural_tokens") or []])
    return behavioural > structural


def _fallback_questions(
    focus: str,
    viewpoint_ids: list[str],
    knowledge: KnowledgeBase,
) -> list[ArchitecturalQuestion]:
    vid = viewpoint_ids[0] if viewpoint_ids else "module-decomposition"
    grain = knowledge.published_grain(vid)
    unit = grain.get("unit")
    if unit == "context":
        text = f"Which actors and external systems interact with {focus}?"
    elif unit == "type":
        text = f"Which entities or types are involved in {focus} and how are they related?"
    else:
        text = f"What {grain.get('nodes')} are involved in {focus}?"
    return [ArchitecturalQuestion(id="AQ1", text=text, priority=1)]


def _keep_question(
    text: str,
    *,
    allow_behavioural: bool,
    allow_types: bool,
) -> bool:
    low = text.casefold()
    if any(marker in low for marker in _CLASS_LIST_MARKERS):
        return False
    if any(marker in low for marker in _TYPE_MARKERS):
        return allow_types
    if any(marker in low for marker in _CALL_CHAIN_MARKERS):
        return allow_behavioural
    return True
