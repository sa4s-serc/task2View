"""PDF Phase 5 — Evidence Extraction agents, one per analysis task."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import (
    AnalysisTask,
    GroundedClaim,
    RepositoryAnalysisPlan,
    StakeholderTaskProfile,
)
from task2view.agents.tools import RepoTools

PROMPT = """You are an Evidence Extraction and Grounding Agent.

Execute ONE analysis task. Inspect candidate locations, follow references
(imports, calls, config, tests). Candidate locations are starting points.
You may open more files. Do not invent types or files.

PROFILE TARGET: {target}
TASK: {task}

ANALYSIS TASK:
{task_json}

CONSTRAINTS:
{constraints}

Start by reading candidate locations (read/search/graph_query). Then return final JSON:
{{
  "claims": [
    {{
      "claim": "A invokes B",
      "source_element": "A",
      "target_element": "B",
      "relationship": "calls",
      "order": 1,
      "evidence": [{{"file":"relative/path","symbol":"TypeOrMethod","excerpt":"code"}}],
      "support_type": "directly_observed",
      "question_ids": ["AQ1"]
    }}
  ]
}}

support_type is directly_observed or inferred.
Every non-inferred claim needs file + excerpt from the repository.
"""


def _extract_one(
    task: AnalysisTask,
    profile: StakeholderTaskProfile,
    plan: RepositoryAnalysisPlan,
    tools: RepoTools,
    runtime: AgentRuntime,
) -> list[GroundedClaim]:
    instruction = PROMPT.format(
        target=profile.target or profile.task,
        task=profile.task,
        task_json=task.model_dump_json(indent=2),
        constraints="\n".join(plan.constraints) or "(none)",
    )
    raw = runtime.tool_loop(instruction, tools, max_steps=10)
    claims: list[GroundedClaim] = []
    for item in raw.get("claims") or []:
        source = str(item.get("source_element") or item.get("source") or "").strip()
        if not source:
            continue
        claims.append(
            GroundedClaim(
                claim=str(item.get("claim") or f"{source} {item.get('relationship') or ''} {item.get('target_element') or ''}").strip(),
                source_element=source,
                target_element=(str(item.get("target_element") or item.get("target") or "").strip() or None),
                relationship=item.get("relationship"),
                order=item.get("order"),
                evidence=list(item.get("evidence") or []),
                support_type=str(item.get("support_type") or "directly_observed"),
                question_ids=[str(x) for x in item.get("question_ids") or task.addresses],
                analysis_task=task.id,
            )
        )
    return claims


def extract_evidence(
    profile: StakeholderTaskProfile,
    plan: RepositoryAnalysisPlan,
    tools: RepoTools,
    runtime: AgentRuntime,
    *,
    workers: int = 2,
) -> list[GroundedClaim]:
    tasks = plan.analysis_tasks
    if not tasks:
        return []
    workers = max(1, min(workers, len(tasks)))
    if workers == 1:
        out: list[GroundedClaim] = []
        for task in tasks:
            out.extend(_extract_one(task, profile, plan, tools, runtime))
        return out
    collected: list[GroundedClaim] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_extract_one, task, profile, plan, tools, runtime) for task in tasks
        ]
        for fut in as_completed(futures):
            collected.extend(fut.result())
    return collected
