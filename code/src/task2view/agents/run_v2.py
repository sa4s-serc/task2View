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
from pathlib import Path

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.aem import EvidenceModel, InvestigationTask, Question
from task2view.contracts.card import RepositoryCard
from task2view.contracts.views import ArchitectureView, RenderResult, ViewCorrespondence, ViewSet
from task2view.knowledge.catalog import load_catalog
from task2view.llm.usage import UsageLedger
from task2view.phase0.card import build_card, render_card, repo_facts
from task2view.phase1.needs import NeedProfile, extract_needs
from task2view.phase2.view_questions import derive_view_questions, view_id
from task2view.phase3.selection import ViewPlan, select_views
from task2view.phase4.investigate import pipeline_config, plan_investigation
from task2view.phase5.collect import collect_evidence
from task2view.phase6.decide import ViewDecision, coverage, decide
from task2view.phase7.notations import get_renderer
from task2view.phase7.project import SCENARIO_KINDS, project_view
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
    usage: dict = field(default_factory=dict)  # UsageLedger.summary(); calls in usage["calls"]
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
    evidence_mode: str = "agent",
    cache_dir: str | Path | None = None,
    generate=None,
    judge_generate=None,
) -> RunV2Result:
    catalog = load_catalog()
    cfg = pipeline_config()
    languages = languages or ["plantuml"]
    runtime = AgentRuntime(generate=generate, model=llm, cache_dir=cache_dir)
    llm_spec = runtime.spec
    judge_runtime = None
    if judge_llm or judge_generate is not None:
        judge_runtime = AgentRuntime(generate=judge_generate, model=judge_llm)
    log: list[str] = [f"generator: {llm_spec}", f"evidence: {evidence_mode}", f"judge: {judge_llm or ('scripted' if judge_generate else 'none')}"]

    card = build_card(code)
    card_text = render_card(card)
    profile = extract_needs(goal, runtime, catalog=catalog)
    plan = select_views(profile.selection_input(), catalog, repo_facts(card), max_views=max_views)
    questions = derive_view_questions(profile, plan, catalog)
    tasks = plan_investigation(plan, questions, card, catalog, target=profile.target, runtime=runtime, card_text=card_text)
    grain = "package" if profile.detail_level == "overview" else "class"
    aem = collect_evidence(tasks, questions, card, runtime, catalog, card_text=card_text, grain=grain,
                           mode=evidence_mode)
    log.append(f"round 1: {len(tasks)} tasks, {len(aem.claims)} claims, {len(aem.rejected_claims)} rejected; "
               f"{grain}-level components")

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
                                   previous=aem, grain=grain, mode=evidence_mode)
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
                           judge_spec=judge_runtime.spec, generator_spec=llm_spec) if judge_runtime else JudgeReport(
            status="not-run", summary="no judge model configured (--judge-llm)")
        result.task_fit = judge.model_dump()
        final_views[vid] = view
        validation[vid] = result
        renders[vid] = [render] + [get_renderer(lang).render(view) for lang in languages[1:]]

    viewset = ViewSet(
        system=card.name, stakeholder=profile.role, goal=goal, views=list(final_views.values()),
        correspondences=_correspondences(final_views), correspondence_gaps=_correspondence_gaps(final_views),
        declared_gaps=[f"{vid}: {d.reason}" for vid, d in decisions.items() if d.decision in {"gap", "drop"}],
        uncovered_needs=plan.uncovered_needs, secondary_not_shown=plan.secondary_not_shown,
    )
    ledger = UsageLedger()
    ledger.extend(runtime.ledger)
    if judge_runtime is not None:
        ledger.extend(judge_runtime.ledger)
    usage = ledger.summary() | {"calls": [c.model_dump() for c in ledger.calls]}
    total = usage["total"]
    log.append(f"usage: {total['calls']} calls, {total['input_tokens']} input / {total['output_tokens']} output / "
               f"{total['cache_read_tokens']} cache-read tokens, ${total['cost_usd']:.4f}"
               + ("" if total["cost_complete"] else " (incomplete: some calls had no reported usage or no price)"))
    return RunV2Result(goal=goal, card=card, profile=profile, plan=plan, questions=questions, tasks=tasks, aem=aem,
                       decisions=decisions, viewset=viewset, renders=renders, validation=validation,
                       llm=llm_spec, judge_llm=judge_runtime.spec if judge_runtime else None, usage=usage, log=log)


def _correspondence_gaps(views: dict[str, ArchitectureView]) -> list[str]:
    """A behavioural view's components should be elements of a structural view in the same set."""
    structural = [v for v in views.values() if v.model_kind not in SCENARIO_KINDS | {"uml-state", "table"}]
    if not structural:
        return []
    drawn = {e.id for v in structural for e in v.content_elements()} | \
            {m for v in structural for e in v.content_elements() for m in e.realized_by}
    return [f"{vid}: {e.name} is in no structural view of this set"
            for vid, v in views.items() if v.model_kind in SCENARIO_KINDS
            for e in v.content_elements() if e.id.startswith("cmp:") and e.id not in drawn]


def _correspondences(views: dict[str, ArchitectureView]) -> list[ViewCorrespondence]:
    """The same AEM element drawn in several views (ISO 42010 correspondence, rule: same element)."""
    where: dict[str, list[str]] = defaultdict(list)
    for vid, view in views.items():
        for e in view.content_elements():
            where[e.id].append(f"{vid}:{e.id}")
    return [ViewCorrespondence(rule="same-element", elements=refs) for refs in where.values() if len(refs) > 1]
