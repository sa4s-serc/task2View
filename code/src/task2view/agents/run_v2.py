"""Task2View pipeline: request + repository -> one UML view, in one pass.

Phase 0  repository card (deterministic)
Phase 1  needs, subjects, target, detail level, view spec (LLM, verified against the request)
Phase 3  the one viewpoint that best covers the needs (deterministic)
Phase 2  the view's questions (deterministic)
Phase 4  investigation plan (deterministic suggestions, planning call)
Phase 5  evidence agent with tools -> verified claims -> Architecture Evidence Model
Phase 7  the view: parts and arrows for structural views (abstraction), projection otherwise; drawn in UML
Phase 8  checks: the diagram compiles and every mark is backed by verified code
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.aem import EvidenceModel, InvestigationTask, Question
from task2view.contracts.architecture import ArchView
from task2view.contracts.card import RepositoryCard
from task2view.contracts.views import RenderResult, ViewSet
from task2view.knowledge.catalog import load_catalog
from task2view.llm.usage import UsageLedger
from task2view.phase0.card import build_card, render_card, repo_facts
from task2view.phase1.needs import NeedProfile, apply_clarifications, extract_needs
from task2view.phase2.view_questions import derive_view_questions, view_id
from task2view.phase3.selection import ViewPlan, select_one_view
from task2view.phase4.investigate import pipeline_config, plan_investigation
from task2view.phase5.abstract import abstract_view, lift_connectors, mark_answers, name_parts, shape_for_viewpoint
from task2view.phase5.collect import collect_evidence
from task2view.phase7.abstracted import ABSTRACTED, render_abstracted, to_architecture_view, with_abstraction_coverage
from task2view.phase7.notations import get_renderer
from task2view.phase7.project import project_view
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
    viewset: ViewSet
    renders: dict[str, list[RenderResult]]
    validation: dict[str, ViewValidation]
    llm: str | None = None
    arch_views: dict[str, ArchView] = field(default_factory=dict)  # parts and connectors of a structural view
    usage: dict = field(default_factory=dict)  # UsageLedger.summary(); calls in usage["calls"]
    log: list[str] = field(default_factory=list)


def run_v2(
    goal: str,
    code: str,
    *,
    llm: str | None = None,
    compile_enabled: bool = True,
    evidence_mode: str = "agent",
    cache_dir: str | Path | None = None,
    generate=None,
    ask=None,
) -> RunV2Result:
    """``ask(question, options, default)``: put Phase 1 clarification questions to a person; without
    it the defaults are used (non-interactive runs and experiments)."""
    catalog = load_catalog()
    cfg = pipeline_config()
    runtime = AgentRuntime(generate=generate, model=llm, cache_dir=cache_dir)
    log: list[str] = [f"generator: {runtime.spec}", f"evidence: {evidence_mode}"]

    card = build_card(code)
    card_text = render_card(card)
    profile = extract_needs(goal, runtime, catalog=catalog)
    log += apply_clarifications(profile, catalog, ask)
    log.append(f"view spec: {profile.spec.scope} scope, {profile.spec.granularity} granularity, {profile.spec.behaviour}")
    plan = select_one_view(profile.selection_input(), catalog, repo_facts(card), behaviour=profile.spec.behaviour,
                           compact_catalog=with_abstraction_coverage(catalog, profile.spec.granularity))
    questions = derive_view_questions(profile, plan, catalog)
    tasks = plan_investigation(plan, questions, card, catalog, target=profile.target, runtime=runtime, card_text=card_text)
    # package boxes only for a whole-system overview; a request about a feature needs the classes involved in it
    grain = "package" if profile.detail_level == "overview" and not profile.target else "class"
    aem = collect_evidence(tasks, questions, card, runtime, catalog, card_text=card_text, grain=grain, mode=evidence_mode)
    log.append(f"evidence: {len(tasks)} task(s), {len(aem.claims)} claims, {len(aem.rejected_claims)} rejected; "
               f"{grain}-level components")

    views, renders, validation, arch_views = [], {}, {}, {}
    for i, planned in enumerate(plan.views):  # one view (Phase 3 selects one)
        vid = view_id(i, planned.viewpoint_id)
        view = project_view(vid, planned, questions, aem, card, catalog, target=profile.target)
        vp = catalog.viewpoint(view.viewpoint_id)
        arch = None
        if vp.id in ABSTRACTED and profile.spec.granularity != "fine":  # parts, not classes (ADR-007)
            view.max_elements = int(cfg["abstraction"]["max_parts"].get(view.detail_level, 9))
            arch = _request_parts(card, aem, runtime, profile, questions, goal, view.max_elements, log)
            arch.title = view.title
            if any(p.members for p in arch.parts):
                lift_connectors(arch, card, arrows=vp.id != "decomposition")
                shape_for_viewpoint(arch, vp.id, aem, {q.id for q in questions if q.view_id == vid
                                                       and q.need in {"change-impact", "dependencies"}})
                view = to_architecture_view(arch, view, vp, card)
                render = render_abstracted(arch, view, card.name)
                arch_views[vid] = arch
                log.append(f"{vid}: {len(arch.parts)} parts, {len(arch.connectors)} arrows (abstraction)")
            else:
                arch = None
        if arch is None:
            render = get_renderer("plantuml").render(view)
        validation[vid] = validate_view(view, render, aem, card, catalog, compile_enabled=compile_enabled)
        views.append(view)
        renders[vid] = [render]

    viewset = ViewSet(system=card.name, stakeholder=profile.role, goal=goal, views=views,
                      uncovered_needs=plan.uncovered_needs, secondary_not_shown=plan.secondary_not_shown)
    ledger = UsageLedger()
    ledger.extend(runtime.ledger)
    usage = ledger.summary() | {"calls": [c.model_dump() for c in ledger.calls]}
    total = usage["total"]
    replayed = usage["replayed"]["calls"]
    log.append(f"usage: {total['calls']} new calls" + (f" (+{replayed} replayed from cache)" if replayed else "") +
               f", {total['input_tokens']} input / {total['output_tokens']} output / "
               f"{total['cache_read_tokens']} cache-read tokens, ${total['cost_usd']:.4f}"
               + ("" if total["cost_complete"] else " (incomplete: some calls had no reported usage or no price)"))
    return RunV2Result(goal=goal, card=card, profile=profile, plan=plan, questions=questions, tasks=tasks, aem=aem,
                       viewset=viewset, renders=renders, validation=validation, llm=runtime.spec,
                       arch_views=arch_views, usage=usage, log=log)


def _request_parts(card, aem, runtime, profile, questions, goal: str, max_parts: int, log: list[str]) -> ArchView:
    """ADR-007 step 3: the parts (with names) of the structural view. A detailed request's enumerated
    subjects shape them."""
    subjects: dict[str, set[str]] = defaultdict(set)
    if profile.detail_level == "detailed":
        for q in questions:
            if q.subject:
                subjects[q.subject].add(q.id)
    arch = abstract_view(card, aem, target=profile.target, granularity=profile.spec.granularity,
                         subjects=subjects, max_parts=max_parts)
    if len(arch.parts) > max_parts and profile.spec.granularity != "coarse":
        arch = abstract_view(card, aem, target=profile.target, granularity="coarse")  # one level coarser
        log.append(f"parts exceed the cap of {max_parts}; drawn by layer instead")
    if any(p.members for p in arch.parts):
        arch = name_parts(arch, card, aem, runtime, goal=goal, purpose="phase5c", max_parts=max_parts,
                          single_class_parts=profile.detail_level == "detailed")
        mark_answers(arch, aem, subjects)
    return arch
