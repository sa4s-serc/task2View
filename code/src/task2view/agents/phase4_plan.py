"""PDF Phase 4 — Repository Analysis Agents (plan only)."""

from __future__ import annotations

from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import (
    AnalysisTask,
    QuestionSet,
    RepositoryAnalysisPlan,
    StakeholderTaskProfile,
    ViewpointPlan,
)
from task2view.agents.tools import RepoTools

PROMPT = """You are a Repository Analysis Agent.

You PLAN the investigation. Do not claim what the architecture contains yet.
Candidate locations are starting points, not a closed file list.

PROFILE:
{profile}

QUESTIONS:
{questions}

VIEWPOINT PLAN (generate now, ignore deferred):
{views}

REPOSITORY TREE:
{tree}

GRAPH HUBS (optional, queryable via graph_query):
{hubs}

Inspect with tools if the tree is not enough, then return final JSON:
{{
  "analysis_goal": "...",
  "target_view": "V1",
  "target_granularity": "component_or_service_level",
  "analysis_tasks": [
    {{
      "id": "AT1",
      "goal": "identify entry points for the target",
      "candidate_locations": ["src/..."],
      "expected_evidence": ["endpoint", "initial component"],
      "addresses": ["AQ1"],
      "target_view": "V1"
    }}
  ],
  "constraints": [
    "Maintain the planned granularity",
    "Ground every relationship",
    "Distinguish observed and inferred"
  ]
}}

Create 2 to 4 analysis tasks that split the questions. Prefer real paths from the tree.
"""


def plan_repository_analysis(
    profile: StakeholderTaskProfile,
    questions: QuestionSet,
    viewpoint_plan: ViewpointPlan,
    tools: RepoTools,
    runtime: AgentRuntime,
) -> RepositoryAnalysisPlan:
    active = [v for v in viewpoint_plan.views if not v.deferred]
    qtext = "\n".join(f"{q.id}: {q.text}" for q in questions.questions)
    vtext = "\n".join(
        f"{v.id}: {v.viewpoint_id} / {v.view_type} addresses={v.addresses} evidence={v.required_evidence}"
        for v in active
    )
    tree = tools.list_tree(".", 3)
    hubs = tools.graph_query("")
    instruction = PROMPT.format(
        profile=profile.model_dump_json(indent=2),
        questions=qtext,
        views=vtext,
        tree=tree,
        hubs=hubs,
    )
    raw = runtime.tool_loop(instruction, tools)
    tasks: list[AnalysisTask] = []
    for i, item in enumerate(raw.get("analysis_tasks") or [], start=1):
        tasks.append(
            AnalysisTask(
                id=str(item.get("id") or f"AT{i}"),
                goal=str(item.get("goal") or "").strip(),
                candidate_locations=[str(x) for x in item.get("candidate_locations") or []],
                expected_evidence=[str(x) for x in item.get("expected_evidence") or []],
                addresses=[str(x) for x in item.get("addresses") or []],
                target_view=item.get("target_view"),
            )
        )
    tasks = [t for t in tasks if t.goal]
    if not tasks:
        loc = ["."]
        tasks = [
            AnalysisTask(
                id="AT1",
                goal="Recover components and interactions for the target",
                candidate_locations=loc,
                addresses=[q.id for q in questions.questions],
                target_view=active[0].id if active else None,
            )
        ]
    return RepositoryAnalysisPlan(
        analysis_goal=str(raw.get("analysis_goal") or profile.goal),
        target_view=raw.get("target_view") or (active[0].id if active else None),
        target_granularity=raw.get("target_granularity") or (active[0].granularity if active else None),
        analysis_tasks=tasks,
        constraints=[str(x) for x in raw.get("constraints") or []],
    )
