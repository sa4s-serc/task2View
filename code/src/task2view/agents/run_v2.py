"""ADR-006 pipeline: goal + repository -> validated view set.

Phase 0  repository card (deterministic)
Phase 1  needs, subjects, target, detail level (LLM, verified against the goal)
Phase 3  covering viewpoint selection (deterministic)
Phase 2  questions per selected view (deterministic)
Phase 4  investigation plan (deterministic suggestions, optional planning agent)
Phase 5  evidence agents with tools -> verified claims -> Architecture Evidence Model
Phase 6  per-view decisions; request_evidence loops back to 4-5 (bounded)
Phase 7  deterministic projection + rendering in the requested notations
Phase 8  five-layer validation; failed marks are removed and the view re-projected (bounded)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.aem import EvidenceModel, InvestigationTask, Question
from task2view.contracts.card import RepositoryCard
from task2view.contracts.views import ArchitectureView, RenderResult, ViewCorrespondence, ViewSet
from task2view.knowledge.catalog import load_catalog
from task2view.llm import get_client
from task2view.phase0.card import build_card, render_card, repo_facts
from task2view.phase1.needs import NeedProfile, extract_needs
from task2view.phase2.view_questions import derive_view_questions, view_id
from task2view.phase3.selection import ViewPlan, select_views
from task2view.phase4.investigate import pipeline_config, plan_investigation
from task2view.phase5.collect import collect_evidence
from task2view.phase6.decide import ViewDecision, coverage, decide
from task2view.phase7.notations import get_renderer
from task2view.phase7.project import project_view
from task2view.phase8.judge import JudgeReport, judge_view
from task2view.phase8.validate_view import ViewValidation, validate_view


@dataclass
class RunV2Result:
    goal: str
    card: RepositoryCard
    profile: NeedProfile
    plan: ViewPlan
    questions: list[Question]
    tasks: list[InvestigationTask]
    aem: EvidenceModel
    decisions: dict[str, ViewDecision]
    viewset: ViewSet
    renders: dict[str, list[RenderResult]]
    validation: dict[str, ViewValidation]
    llm: str | None = None
    judge_llm: str | None = None
    log: list[str] = field(default_factory=list)


def run_v2(
    goal: str,
    code: str,
    *,
    llm: str | None = None,
    judge_llm: str | None = None,
    max_views: int = 3,
    languages: list[str] | None = None,
    compile_enabled: bool = True,
    generate=None,
    judge_generate=None,
) -> RunV2Result:
    catalog = load_catalog()
    cfg = pipeline_config()
    languages = languages or ["plantuml"]
    runtime = AgentRuntime(generate=generate, model=llm)
    llm_spec = (llm or "scripted") if generate is not None else get_client(llm).spec
    judge_runtime = None
    if judge_llm or judge_generate is not None:
        judge_runtime = AgentRuntime(generate=judge_generate, model=judge_llm)
    log: list[str] = [f"generator: {llm_spec}", f"judge: {judge_llm or ('scripted' if judge_generate else 'none')}"]

    card = build_card(code)
    card_text = render_card(card)
    profile = extract_needs(goal, runtime, catalog=catalog)
    plan = select_views(profile.selection_input(), catalog, repo_facts(card), max_views=max_views)
    questions = derive_view_questions(profile, plan, catalog)
    tasks = plan_investigation(plan, questions, card, catalog, target=profile.target, runtime=runtime, card_text=card_text)
    aem = collect_evidence(tasks, questions, card, runtime, catalog, card_text=card_text)
    log.append(f"round 1: {len(tasks)} tasks, {len(aem.claims)} claims, {len(aem.rejected_claims)} rejected")

    planned = {view_id(i, v.viewpoint_id): v for i, v in enumerate(plan.views)}
    folded: set[str] = set()
    rounds_left = int(cfg["repair"]["evidence_rounds"])
    round_no = 1
    while True:
        views = {vid: project_view(vid, pv, questions, aem, card, catalog, target=profile.target, fold=vid in folded)
                 for vid, pv in planned.items()}
        decisions = {vid: decide(views[vid], planned[vid], questions, aem, evidence_rounds_left=rounds_left,
                                 already_simplified=vid in folded) for vid in views}
        needing = [q for d in decisions.values() if d.decision == "request_evidence" for q in d.unsupported_questions]
        to_fold = {vid for vid, d in decisions.items() if d.decision == "simplify"}
        if needing and rounds_left > 0:
            round_no += 1
            rounds_left -= 1
            wanted = [q for q in questions if q.id in set(needing)]
            extra = plan_investigation(plan, wanted, card, catalog, target=profile.target, runtime=runtime, card_text=card_text)
            for t in extra:
                t.id = f"R{round_no}-{t.id}"
            tasks += extra
            aem = collect_evidence(extra, questions, card, runtime, catalog, card_text=card_text,
                                   previous=list(aem.claims.values()))
            log.append(f"round {round_no}: {len(extra)} tasks for {len(wanted)} unsupported question(s)")
            continue
        if to_fold - folded:
            folded |= to_fold
            log.append(f"simplified: {', '.join(sorted(to_fold))}")
            continue
        break

    final_views: dict[str, ArchitectureView] = {}
    renders: dict[str, list[RenderResult]] = {}
    validation: dict[str, ViewValidation] = {}
    retries = int(cfg["repair"]["projection_retries"])
    for vid, view in views.items():
        if decisions[vid].decision == "drop":
            log.append(f"{vid} dropped: {decisions[vid].reason}")
            continue
        excluded: set[str] = set()
        for attempt in range(retries + 1):
            render = get_renderer(languages[0]).render(view)
            result = validate_view(view, render, aem, card, catalog, decisions[vid].coverage, compile_enabled=compile_enabled)
            if result.verdict != "fail" or not result.repair_marks or attempt == retries:
                break
            excluded |= set(result.repair_marks)
            log.append(f"{vid} repair {attempt + 1}: removing {len(result.repair_marks)} mark(s)")
            view = project_view(vid, planned[vid], questions, aem, card, catalog, target=profile.target,
                                fold=vid in folded, exclude=excluded)
        judge = judge_view(view, questions, goal, render.source, render.language, judge_runtime,
                           judge_spec=judge_llm, generator_spec=llm_spec) if judge_runtime else JudgeReport(
            status="not-run", summary="no judge model configured (--judge-llm)")
        result.task_fit = judge.model_dump()
        final_views[vid] = view
        validation[vid] = result
        renders[vid] = [render] + [get_renderer(lang).render(view) for lang in languages[1:]]

    viewset = ViewSet(
        system=card.name, stakeholder=profile.role, goal=goal, views=list(final_views.values()),
        correspondences=_correspondences(final_views),
        declared_gaps=[f"{vid}: {d.reason}" for vid, d in decisions.items() if d.decision in {"gap", "drop"}],
        uncovered_needs=plan.uncovered_needs, secondary_not_shown=plan.secondary_not_shown,
    )
    return RunV2Result(goal=goal, card=card, profile=profile, plan=plan, questions=questions, tasks=tasks, aem=aem,
                       decisions=decisions, viewset=viewset, renders=renders, validation=validation,
                       llm=llm_spec, judge_llm=judge_llm, log=log)


def _correspondences(views: dict[str, ArchitectureView]) -> list[ViewCorrespondence]:
    """The same AEM element drawn in several views (ISO 42010 correspondence, rule: same element)."""
    where: dict[str, list[str]] = defaultdict(list)
    for vid, view in views.items():
        for e in view.content_elements():
            where[e.id].append(f"{vid}:{e.id}")
    return [ViewCorrespondence(rule="same-element", elements=refs) for refs in where.values() if len(refs) > 1]
