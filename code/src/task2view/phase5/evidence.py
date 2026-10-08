"""Phase 5. One evidence extraction per analysis task, then one merged model.

Each task sees only the files the plan named. A claim that does not cite one
of those files is dropped. The view model is the boxes and edges those claims
support. Phase 7 draws that model. It does not read the repository again.
"""

from __future__ import annotations

from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import (
    AnalysisTask,
    ArchitectureEvidenceModel,
    GroundedClaim,
    RepositoryAnalysisPlan,
)
from task2view.contracts.models import (
    Evidence,
    RepositoryScope,
    ScopeCandidate,
    ViewElement,
    ViewModel,
    ViewRelation,
    ViewSpecification,
    canonical_relation_kind,
)
from task2view.knowledge.loader import KnowledgeBase, load_knowledge
from task2view.phase4.graph import RepositoryGraph
from task2view.phase5.extract import _pack_files

PROMPT = """You are the Evidence Extraction Agent.

GOAL
Execute this one analysis task. Return the claims the source code shows for it.
Do not draw the diagram. Do not answer any other question.

INPUTS
1. TASK — the question, the evidence to find, the grain, and the constraints.
2. SOURCE FILES — the only code you may use. These are the files the analysis plan named for this task.
3. GRAPH — links among those files. A parent directory is not a box.

TASK
{task}

GRAIN
{grain}

CONSTRAINTS
{constraints}

GRAPH
{graph}

SOURCE FILES
{files}

DECISION
1. A claim is one fact this task asks for.
   Reason: Phase 6 checks claims against questions. A claim that restates a different question cannot be checked.
2. evidence.file must be copied from the SOURCE FILES paths. excerpt is the line that shows the fact.
   Reason: a claim with no file in this task is not evidence.
3. source_element is the architectural name at the grain. A folder, a package, or a file name is not that name unless the grain unit is type.
   Reason: the published view names responsibilities, not directories.
4. When the fact is a connection, set target_element and relationship. Otherwise leave them empty.
5. support_type is directly_observed when the excerpt shows the fact, otherwise inferred.
6. If these files do not show the fact, return an empty claims list.
   Reason: an empty list is a gap. Inventing a box fills the gap with something the code does not show.

OUTPUT
Return only this JSON.
{{
  "claims": [
    {{
      "claim": "one fact",
      "source_element": "architectural name",
      "target_element": "",
      "relationship": "",
      "evidence": [{{"file": "path from SOURCE FILES", "symbol": "Name", "excerpt": "the line"}}],
      "support_type": "directly_observed"
    }}
  ]
}}
"""


def _task_paths(task: AnalysisTask) -> list[str]:
    paths: list[str] = []
    for path in list(task.starting_points) + list(task.candidate_locations):
        if path and path not in paths:
            paths.append(path)
    return paths


def _scope_for(scope: RepositoryScope, paths: list[str]) -> RepositoryScope:
    wanted = set(paths)
    kept = [cand for cand in scope.candidate_areas if cand.path in wanted]
    have = {cand.path for cand in kept}
    for path in paths:
        if path not in have:
            kept.append(
                ScopeCandidate(path=path, origin="analysis_task", reason="named by the analysis plan")
            )
    return scope.model_copy(update={"candidate_areas": kept})


def _first_evidence(raw: dict, allowed: set[str]) -> dict | None:
    items = raw.get("evidence") or []
    if isinstance(items, dict):
        items = [items]
    for item in items:
        if not isinstance(item, dict):
            continue
        path = str(item.get("file") or "").strip()
        if path in allowed:
            return item
    return None


def _claims_from_raw(raw: dict, task: AnalysisTask, allowed: set[str]) -> list[GroundedClaim]:
    claims: list[GroundedClaim] = []
    for item in raw.get("claims") or []:
        if not isinstance(item, dict):
            continue
        evidence = _first_evidence(item, allowed)
        source = str(item.get("source_element") or "").strip()
        if evidence is None or not source:
            continue
        target = str(item.get("target_element") or "").strip() or None
        relationship = str(item.get("relationship") or "").strip() or None
        support = str(item.get("support_type") or "directly_observed")
        if support not in {"directly_observed", "inferred"}:
            support = "inferred"
        claims.append(
            GroundedClaim(
                claim=str(item.get("claim") or "").strip() or source,
                source_element=source,
                target_element=target,
                relationship=relationship,
                evidence=[
                    {
                        "file": evidence.get("file"),
                        "symbol": evidence.get("symbol"),
                        "excerpt": evidence.get("excerpt"),
                    }
                ],
                support_type=support,
                question_ids=list(task.addresses),
                analysis_task=task.id,
            )
        )
    return claims


def _extract_task(
    task: AnalysisTask,
    spec: ViewSpecification,
    scope: RepositoryScope,
    graph: RepositoryGraph,
    repo_root: str,
    runtime: AgentRuntime,
    knowledge: KnowledgeBase,
    constraints: list[str],
) -> list[GroundedClaim]:
    paths = _task_paths(task)
    allowed = set(paths)
    if not paths:
        return []
    task_scope = _scope_for(scope, paths)
    grain = knowledge.grain_prompt(spec.selected_view.viewpoint_id, spec.selected_view.view_type)
    task_text = "\n".join(
        [
            f"id: {task.id}",
            f"questions: {', '.join(task.addresses) or '(none)'}",
            f"goal: {task.goal}",
            "evidence to find: " + "; ".join(task.expected_evidence) or "(the question)",
            "files: " + ", ".join(paths),
        ]
    )
    raw = runtime.complete_json(
        PROMPT.format(
            task=task_text,
            grain=grain,
            constraints="; ".join(constraints) or "(none)",
            graph=graph.summary(only_paths=set(paths)),
            files=_pack_files(repo_root, task_scope),
        )
    )
    return _claims_from_raw(raw, task, allowed)


def _merge(claims: list[GroundedClaim], tasks: list[AnalysisTask]) -> ArchitectureEvidenceModel:
    kept: list[GroundedClaim] = []
    seen: set[tuple] = set()
    for claim in claims:
        key = (
            claim.source_element.casefold(),
            (claim.target_element or "").casefold(),
            (claim.relationship or "").casefold(),
            claim.claim.casefold(),
        )
        if key in seen:
            continue
        seen.add(key)
        kept.append(claim)
    names: list[str] = []
    for claim in kept:
        for name in (claim.source_element, claim.target_element):
            if name and name not in names:
                names.append(name)
    answered_tasks = {claim.analysis_task for claim in kept}
    notes: list[str] = []
    for task in tasks:
        ids = ", ".join(task.addresses) or task.id
        hit = task.id in answered_tasks or any(
            set(task.addresses) & set(claim.question_ids) for claim in kept
        )
        if not _task_paths(task):
            notes.append(f"{task.id} unanswered: the plan named no file for {ids}")
        elif not hit:
            notes.append(f"{task.id} unanswered: the files did not show {ids}")
    return ArchitectureEvidenceModel(claims=kept, elements=names, notes=notes)


def _view_from_claims(
    model: ArchitectureEvidenceModel,
    spec: ViewSpecification,
) -> ViewModel:
    unit = spec.selected_view.grain_unit or "component"
    kind = "class" if unit == "type" else "component"
    ids: dict[str, str] = {}
    elements: list[ViewElement] = []
    for name in model.elements:
        key = name.casefold()
        if key in ids:
            continue
        claim = next(c for c in model.claims if c.source_element == name or c.target_element == name)
        ev = (claim.evidence or [{}])[0]
        eid = f"E{len(elements) + 1}"
        ids[key] = eid
        elements.append(
            ViewElement(
                id=eid,
                name=name,
                kind=kind,
                role=claim.claim if claim.source_element == name else None,
                evidence=Evidence(
                    file=ev.get("file"),
                    symbol=ev.get("symbol"),
                    excerpt=ev.get("excerpt"),
                ),
                support="observed" if claim.support_type == "directly_observed" else "inferred",
            )
        )
    relations: list[ViewRelation] = []
    for claim in model.claims:
        if not claim.target_element or not claim.relationship:
            continue
        frm = ids.get(claim.source_element.casefold())
        to = ids.get(claim.target_element.casefold())
        if not frm or not to:
            continue
        ev = (claim.evidence or [{}])[0]
        relations.append(
            ViewRelation(
                id=f"R{len(relations) + 1}",
                frm=frm,
                to=to,
                kind=canonical_relation_kind(claim.relationship),
                evidence=Evidence(file=ev.get("file"), symbol=ev.get("symbol"), excerpt=ev.get("excerpt")),
                support="observed" if claim.support_type == "directly_observed" else "inferred",
            )
        )
    unanswered = []
    for note in model.notes:
        if "unanswered" in note:
            unanswered.append(note)
    return ViewModel(
        request_id=spec.request_id,
        view_type=spec.selected_view.view_type,
        granularity=spec.selected_view.granularity,
        elements=elements,
        relations=relations,
        unanswered=unanswered,
        notes=list(model.notes),
    )


def tasks_name_files(plan: RepositoryAnalysisPlan) -> bool:
    return any(_task_paths(task) for task in plan.analysis_tasks)


def extract_from_plan(
    plan: RepositoryAnalysisPlan,
    spec: ViewSpecification,
    scope: RepositoryScope,
    graph: RepositoryGraph,
    repo_root: str,
    runtime: AgentRuntime,
    *,
    knowledge: KnowledgeBase | None = None,
) -> tuple[ArchitectureEvidenceModel, ViewModel]:
    """Run one extraction per task that names files, then merge the claims."""
    knowledge = knowledge or load_knowledge()
    claims: list[GroundedClaim] = []
    for task in plan.analysis_tasks:
        claims.extend(
            _extract_task(task, spec, scope, graph, repo_root, runtime, knowledge, plan.constraints)
        )
    model = _merge(claims, plan.analysis_tasks)
    return model, _view_from_claims(model, spec)
