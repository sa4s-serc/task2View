"""Phase 4. Repository analysis plan.

The scoper proposes files. This agent assigns those files to the questions
already written, and records the grain and the constraints. Phase 5 reads
the files named here.
"""

from __future__ import annotations

import re

from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import (
    AnalysisTask,
    RepositoryAnalysisPlan,
    StakeholderTaskProfile,
)
from task2view.contracts.models import RepositoryScope, ScopeCandidate, ViewSpecification
from task2view.knowledge.loader import KnowledgeBase, load_knowledge

_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]{2,}")
_STOP = {
    "the", "and", "for", "how", "what", "which", "with", "from", "that", "this",
    "are", "does", "into", "their", "them", "component", "components", "module",
    "modules", "system", "question",
}
_START = {"task_seed", "ri_forced", "lexical", "grep"}
_NEAR = {"expansion_1hop", "expansion_2hop", "call_1hop"}

PROMPT = """You are the Repository Analysis Agent.

GOAL
Write the repository analysis plan for the questions already chosen.
Do not draw the architecture and do not read source code. Decide where Phase 5 must look, what it must find, and which constraints it must keep.
The same questions and the same file list must produce the same plan.

INPUTS
1. PROFILE — the stakeholder, the target, the goal, the scope, and the constraints.
2. QUESTIONS — one fact each. Every question becomes one analysis task, in this order.
3. GRAIN — the boxes Phase 5 may draw, and what it must not draw. Copy this. Do not invent a finer grain.
4. OFFERED FILES — the only paths you may name. Each line says whether it is a starting point (the name matched the task) or a neighbor (one step from a starting point in the file graph).
   Files that are present only because they have many connections are not in this list.

PROFILE
{profile}

QUESTIONS
{questions}

GRAIN
{grain}

OFFERED FILES
{files}

DECISION
1. Write one task per question, in the same order. addresses is that question id.
   Reason: Phase 5 checks the view one question at a time. A task that mixes two questions cannot be checked.
2. starting_points are offered files marked starting point whose path relates to that question.
   Reason: a starting point is where the search begins, not the most connected file in the repository.
3. candidate_locations are those starting points plus offered neighbors that belong to the same question.
   Reason: a neighbor is in scope only because a starting point points at it.
4. expected_evidence is the fact that question asks for, in the vocabulary of the grain.
   Reason: Phase 5 looks for this evidence and does not draw a box the grain forbids.
5. constraints are the profile constraints, the profile scope when it is non-empty, and the grain's do-not line.
   Reason: a limit the stakeholder stated, and a box the viewpoint forbids, both bind the extraction.
6. If no offered file relates to a question, leave that task's paths empty.
   Reason: an empty task is a recorded gap. Filling it with an unrelated file makes the diagram about the wrong code.

OUTPUT
Return only this JSON. target_view is the viewpoint id. target_granularity is the grain unit.
{{
  "analysis_goal": "what this analysis is for",
  "target_view": "viewpoint id",
  "target_granularity": "grain unit",
  "constraints": ["limit"],
  "analysis_tasks": [
    {{
      "id": "AT1",
      "addresses": ["AQ1"],
      "goal": "the fact AQ1 asks for",
      "starting_points": ["path from OFFERED FILES"],
      "candidate_locations": ["path from OFFERED FILES"],
      "expected_evidence": ["what the file must show"]
    }}
  ]
}}
"""


def _tokens(text: str) -> list[str]:
    found: list[str] = []
    for token in _TOKEN.findall(text.lower()):
        if token in _STOP or token in found or len(token) < 4:
            continue
        found.append(token)
    return found


def _offered(scope: RepositoryScope) -> list[ScopeCandidate]:
    return [cand for cand in scope.candidate_areas if cand.origin in _START or cand.origin in _NEAR]


def _matches(path: str, tokens: list[str]) -> bool:
    hay = path.lower()
    return any(token in hay for token in tokens)


def _fallback_task(
    index: int,
    question_id: str,
    question_text: str,
    offered: list[ScopeCandidate],
    viewpoint_id: str,
) -> AnalysisTask:
    tokens = _tokens(question_text)
    starts = [c.path for c in offered if c.origin in _START and _matches(c.path, tokens)]
    neighbors = [c.path for c in offered if c.origin in _NEAR and _matches(c.path, tokens)]
    locations = list(dict.fromkeys(starts + neighbors))
    return AnalysisTask(
        id=f"AT{index}",
        goal=question_text,
        addresses=[question_id],
        starting_points=starts,
        candidate_locations=locations,
        expected_evidence=[question_text],
        target_view=viewpoint_id,
    )


def _keep(paths: list[str], allowed: set[str]) -> list[str]:
    kept: list[str] = []
    for path in paths:
        if path in allowed and path not in kept:
            kept.append(path)
    return kept


def plan_repository_analysis(
    profile: StakeholderTaskProfile,
    spec: ViewSpecification,
    scope: RepositoryScope,
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
) -> RepositoryAnalysisPlan:
    knowledge = knowledge or load_knowledge()
    viewpoint_id = spec.selected_view.viewpoint_id or ""
    grain = knowledge.published_grain(viewpoint_id, spec.selected_view.view_type)
    offered = _offered(scope)
    allowed = {cand.path for cand in offered}
    questions = spec.architectural_questions or []
    qtext = "\n".join(f"- {q.id}: {q.text}" for q in questions) or "(none)"
    if offered:
        file_text = "\n".join(
            f"- {cand.path} ({'starting point' if cand.origin in _START else 'neighbor'}): {cand.reason}"
            for cand in offered
        )
    else:
        file_text = "(none)"
    profile_text = "\n".join(
        [
            f"stakeholder: {profile.stakeholder}",
            f"task: {profile.task}",
            f"target: {profile.target}",
            f"goal: {profile.goal}",
            f"scope: {profile.scope or '(none)'}",
            f"constraints: {', '.join(profile.constraints) or '(none)'}",
        ]
    )
    raw = runtime.complete_json(
        PROMPT.format(
            profile=profile_text,
            questions=qtext,
            grain=knowledge.grain_prompt(viewpoint_id, spec.selected_view.view_type),
            files=file_text,
        )
    )
    by_question = {q.id: q.text for q in questions}
    tasks: list[AnalysisTask] = []
    seen_questions: set[str] = set()
    for i, item in enumerate(raw.get("analysis_tasks") or [], start=1):
        addresses = [str(x) for x in item.get("addresses") or []]
        question_id = addresses[0] if addresses else ""
        if question_id and question_id not in by_question:
            continue
        if question_id:
            seen_questions.add(question_id)
        starts = _keep([str(p) for p in item.get("starting_points") or []], allowed)
        locations = _keep(
            starts + [str(p) for p in item.get("candidate_locations") or []],
            allowed,
        )
        tasks.append(
            AnalysisTask(
                id=str(item.get("id") or f"AT{i}"),
                goal=str(item.get("goal") or by_question.get(question_id) or ""),
                addresses=addresses or ([question_id] if question_id else []),
                starting_points=starts,
                candidate_locations=locations,
                expected_evidence=[
                    str(x) for x in (item.get("expected_evidence") or []) if str(x).strip()
                ],
                target_view=viewpoint_id,
            )
        )
    for index, question in enumerate(questions, start=1):
        if question.id in seen_questions:
            continue
        tasks.append(_fallback_task(index, question.id, question.text, offered, viewpoint_id))
    if not tasks and questions:
        tasks = [
            _fallback_task(i, q.id, q.text, offered, viewpoint_id)
            for i, q in enumerate(questions, start=1)
        ]
    constraints = [str(x) for x in raw.get("constraints") or [] if str(x).strip()]
    for item in profile.constraints:
        if item not in constraints:
            constraints.append(item)
    if profile.scope and profile.scope not in constraints:
        constraints.append(profile.scope)
    forbid = str(grain.get("forbid") or "").strip()
    if forbid and forbid not in constraints:
        constraints.append(forbid)
    return RepositoryAnalysisPlan(
        analysis_goal=str(raw.get("analysis_goal") or profile.goal or profile.task),
        target_view=viewpoint_id,
        target_granularity=str(grain.get("unit") or spec.selected_view.granularity),
        analysis_tasks=tasks,
        constraints=constraints,
    )


def scope_for_plan(scope: RepositoryScope, plan: RepositoryAnalysisPlan) -> RepositoryScope:
    """Phase 5 reads the files the plan named. An empty plan keeps the scoper list."""
    wanted: list[str] = []
    for task in plan.analysis_tasks:
        for path in list(task.starting_points) + list(task.candidate_locations):
            if path not in wanted:
                wanted.append(path)
    if not wanted:
        note = "No offered file matched the questions, so extraction kept the scoper list."
        if note not in plan.constraints:
            plan.constraints.append(note)
        return scope
    kept = [cand for cand in scope.candidate_areas if cand.path in set(wanted)]
    if not kept:
        return scope
    return scope.model_copy(update={"candidate_areas": kept})
