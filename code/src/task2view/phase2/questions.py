"""PDF Phase 2 — Concern and Architectural Question Agent."""

from __future__ import annotations

from task2view.agents.knowledge_context import (
    concern_meanings,
    grain_summaries,
    question_templates,
)
from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import ArchitecturalQuestion, QuestionSet, StakeholderTaskProfile
from task2view.knowledge.correspondence import Correspondence
from task2view.knowledge.loader import KnowledgeBase, load_knowledge

PROMPT = """You are the Concern and Architectural Question Agent.

GOAL
Decide which architectural concerns this goal raises, and write the questions those concerns create.
This step runs before any viewpoint is chosen. The next step may pick a diagram only if that diagram can answer these questions.
The record must be comparable across runs: a closed set of concern ids, and a short list of questions, each tied to one concern and to the target.

INPUTS
1. PROFILE — the stakeholder-task profile from Phase 1. Use its task, target, goal, scope, and constraints. Do not re-interpret the original sentence.
2. CONCERN CATALOG — the only legal concern ids. Each line is the fact that concern asks the repository to reveal.
   Viewpoint names are omitted on purpose. Naming a diagram here would decide Phase 3 before the questions exist.

PROFILE
{profile}

CONCERN CATALOG
{concerns}

DECISION
Follow this order.

1. Read the target and the goal. The questions are about that target.
   Reason: the target is the noun a later phase will search for in the repository. The stakeholder's job title is not the target.
2. Choose the concern ids this goal needs, using the meanings above. One goal may need several. Do not copy every concern a role might have.
   Reason: copying a role's whole list made every goal for that role look the same, so the viewpoint step could not tell them apart.
3. For each chosen concern, write the facts someone must learn from the source code. One question is one fact. It names the target. Its concern is one of the ids you listed.
   Reason: a later phase checks the diagram against these questions one by one. A question that restates the whole goal cannot be checked.
4. Put the questions in the order the stakeholder needs them. The first question is the fact they need first. Write 3 to 6 questions, and fewer when the task is narrow.
   Reason: this list is the information budget for the rest of the run. Later phases read it from top to bottom. A long list makes every file look relevant.
5. Do not name a diagram type. Do not copy one template per viewpoint.
   Reason: no viewpoint has been chosen. A template per viewpoint would make every goal produce the same questions.
6. Stay inside the profile's scope and constraints when those fields are non-empty. Every question must be answerable by reading the repository.
   Reason: a question that cannot be answered from code cannot be grounded later.

OUTPUT
Return only this JSON.
- concerns: the ids you chose, most needed first.
- questions: one object per fact, in the same order.
- id: AQ1, AQ2, and so on, in the same order as the list.
- text: one sentence that names the target.
- concern: one id from concerns.

{{
  "concerns": ["concern-id"],
  "questions": [
    {{"id":"AQ1","text":"one fact about the target","concern":"concern-id"}}
  ]
}}
{appendix}
"""

_APPENDIX_SELECTED = """
ALREADY SELECTED VIEWPOINT
A viewpoint was supplied to this call. Keep every question at its grain, and tag each question with a concern that viewpoint frames.
Do not ask for something its grain forbids.

{grain_heading}
{grains}

{seed_heading}
{seeds}
"""


def derive_questions(
    profile: StakeholderTaskProfile,
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
    correspondence: Correspondence | None = None,
) -> QuestionSet:
    knowledge = knowledge or load_knowledge()
    focus = profile.target or profile.task
    if correspondence is not None:
        grain_ids = [correspondence.viewpoint_id]
        appendix = _APPENDIX_SELECTED.format(
            grain_heading="PUBLISHED GRAIN. Questions must stay at this grain:",
            grains=grain_summaries(knowledge, grain_ids[:8]),
            seed_heading="CHECKLIST for that viewpoint. Rewrite a line only when it names this target:",
            seeds=question_templates(knowledge, grain_ids[:6], focus),
        )
    else:
        grain_ids = []
        appendix = ""
    raw = runtime.complete_json(
        PROMPT.format(
            profile=profile.model_dump_json(indent=2),
            concerns=concern_meanings(knowledge),
            appendix=appendix,
        )
    )
    catalog = knowledge.catalog_concerns()
    questions = []
    for i, item in enumerate(raw.get("questions") or [], start=1):
        if isinstance(item, str):
            questions.append(ArchitecturalQuestion(id=f"AQ{i}", text=item.strip()))
            continue
        concern = str(item.get("concern") or "").strip()
        questions.append(
            ArchitecturalQuestion(
                id=str(item.get("id") or f"AQ{i}"),
                text=str(item.get("text") or item.get("question") or "").strip(),
                concern=concern if concern in catalog else None,
            )
        )
    questions = [q for q in questions if q.text]
    concerns: list[str] = []
    for item in list(profile.concerns) + [str(c) for c in raw.get("concerns") or []]:
        concern_id = str(item).strip()
        if concern_id in catalog and concern_id not in concerns:
            concerns.append(concern_id)
    if correspondence is not None:
        framed = set(knowledge.viewpoint(correspondence.viewpoint_id).get("frames_concerns") or [])
        framed.add("general")
        questions = [q for q in questions if not q.concern or q.concern in framed]
        concerns = [concern_id for concern_id in concerns if concern_id in framed]
    if not questions:
        questions = _fallback_questions(focus, grain_ids, knowledge)
    return QuestionSet(concerns=concerns, questions=questions)


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
    return [ArchitecturalQuestion(id="AQ1", text=text)]
