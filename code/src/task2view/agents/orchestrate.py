"""Runs phases 1–8 in diagram order. Phases 4–8 keep their current methods."""

from __future__ import annotations

from task2view.phase1.interpret import interpret_stakeholder_task
from task2view.phase2.questions import derive_questions
from task2view.phase3.viewpoint import plan_viewpoints
from task2view.agents.runtime import AgentRuntime
from task2view.contracts.models import (
    Preferences,
    NormalizedRequest,
    PipelineError,
    SpecQuestion,
    StakeholderRef,
    TaskRef,
    UserRequest,
)
from task2view.knowledge.selector import _instantiate_required_information
from task2view.knowledge.correspondence import (
    select_correspondence,
    spec_from_correspondence,
    viewpoints_for_concerns,
)
from task2view.knowledge.loader import load_knowledge
from task2view.phase0.clean import clean_repository
from task2view.inputs.repository import new_request_id, resolve_repository
from task2view.phase4 import get_scoper
from task2view.phase4.graph import build_graph
from task2view.phase4.plan import plan_repository_analysis, scope_for_plan
from task2view.phase5 import get_extractor
from task2view.phase5.evidence import extract_from_plan, tasks_name_files
from task2view.phase7 import get_adapter
from task2view.phase7.generate import generate_view
from task2view.agents.structure import ground_view_model
from task2view.phase6.reconcile import reconcile_evidence
from task2view.phase8.validate import validate_view


def _normalized(raw: UserRequest, profile, knowledge, corpus) -> NormalizedRequest:
    role_id = profile.canonical_role
    if not role_id or role_id not in knowledge.stakeholders:
        role_id = "member-of-development-team"
    row = knowledge.stakeholder(role_id)
    repo = resolve_repository(raw.code or raw.repository or "")
    return NormalizedRequest(
        request_id=raw.request_id or new_request_id(),
        repository=repo,
        stakeholder=StakeholderRef(
            role=role_id,
            original_label=profile.original_label or profile.stakeholder,
            iso_42010_class=row.get("iso_42010_class"),
            vb_row=row.get("vb_row") or role_id,
        ),
        task=TaskRef(description=profile.task),
        goal=profile.source_goal or profile.task,
        preferences=Preferences(
            diagram_language=raw.diagram_language,
            max_views=raw.max_views,
            scope_token_budget=raw.scope_token_budget,
        ),
        environment=profile.environment or None,
        concerns=list(profile.concerns),
        corpus={
            "kept": corpus.counts["kept"],
            "dropped": corpus.counts["dropped"],
            "languages": corpus.counts.get("languages", {}),
        },
    )


def _record_uncovered(spec, knowledge) -> None:
    """Concerns the model chose that this viewpoint does not frame stay uncovered.

    They are not added from phrase cues, and they are not drawn as extra boxes.
    """
    framed = set(knowledge.viewpoint(spec.selected_view.viewpoint_id).get("frames_concerns") or [])
    uncovered = [c for c in spec.architectural_concerns if c not in framed and c != "general"]
    spec.unanswered_concerns = uncovered
    spec.declared_gaps = list(uncovered)


def run_agentic(raw: UserRequest, *, generate=None):
    from task2view.pipeline import PipelineResult

    knowledge = load_knowledge()
    if raw.config:
        from task2view.config import apply_pipeline_config, load_pipeline_config

        raw = apply_pipeline_config(raw, load_pipeline_config(raw.config))
    raw.request_id = raw.request_id or new_request_id()
    runtime = AgentRuntime(generate=generate, model=raw.gemini_model)
    corpus = clean_repository(raw.code or raw.repository or "", request_id=raw.request_id)
    profile = interpret_stakeholder_task(raw.goal or "", runtime, knowledge=knowledge)
    request = _normalized(raw, profile, knowledge, corpus)
    questions = derive_questions(profile, runtime, knowledge=knowledge)
    if questions.concerns:
        profile.concerns = list(questions.concerns)
        request.concerns = list(questions.concerns)
    allowed, concerns_are_framed = viewpoints_for_concerns(knowledge, list(profile.concerns))
    viewpoint_plan = plan_viewpoints(
        profile,
        questions,
        runtime,
        knowledge=knowledge,
        max_views=raw.max_views,
        preferred_language=raw.diagram_language,
        allowed_ids=allowed,
        concerns_are_framed=concerns_are_framed,
    )
    active = next((v for v in viewpoint_plan.views if not v.deferred), None)
    if active is None:
        raise PipelineError("no active view in the viewpoint plan")
    cue_text = profile.source_goal or request.goal or request.task.description
    correspondence = select_correspondence(
        request.stakeholder.role,
        cue_text,
        knowledge,
        goal=profile.source_goal or profile.task,
        extra_concerns=list(profile.concerns),
        preferred_language=raw.diagram_language,
        viewpoint_id=active.viewpoint_id,
    )
    spec = spec_from_correspondence(request, correspondence, knowledge)
    spec.task_summary = " | ".join(
        p for p in (profile.source_goal, profile.task, profile.target, profile.goal) if p
    )
    focus = (profile.target or "").strip()
    if focus and focus.casefold() != correspondence.task_focus.casefold():
        spec.required_information = _instantiate_required_information(
            correspondence.viewpoint_id, focus, knowledge
        )
    spec.architectural_questions = [
        SpecQuestion(id=q.id, text=q.text, concern=q.concern) for q in questions.questions
    ]
    spec.selected_view.diagram_language = active.diagram_language
    spec.selected_view.diagram_language_rule = active.diagram_language_rule
    spec.selected_view.notation = active.notation or spec.selected_view.notation
    spec.selected_view.granularity = active.granularity or spec.selected_view.granularity
    _record_uncovered(spec, knowledge)
    repo = request.repository.location
    graph = build_graph(repo, corpus)
    strategy = raw.scope_strategy or "composite"
    scoper = get_scoper(strategy)
    scope = scoper.scope(
        spec,
        repo,
        request.preferences.scope_token_budget,
        corpus=corpus,
        graph=graph,
    )
    if not scope.candidate_areas:
        raise PipelineError(f"scope strategy {strategy!r} selected no files")
    analysis_plan = plan_repository_analysis(profile, spec, scope, runtime, knowledge=knowledge)
    scope = scope_for_plan(scope, analysis_plan)
    extras = {
        "stakeholder_task_profile.json": profile.model_dump(mode="json"),
        "architectural_questions.json": questions.model_dump(mode="json"),
        "viewpoint_plan.json": viewpoint_plan.model_dump(mode="json"),
        "correspondence.json": correspondence.as_dict(),
        "repository_analysis_plan.json": analysis_plan.model_dump(mode="json"),
    }
    result = PipelineResult(
        corpus=corpus,
        request=request,
        spec=spec,
        graph=graph,
        scope=scope,
        extras=extras,
    )
    if raw.skip_extract:
        return result
    evidence = None
    if tasks_name_files(analysis_plan):
        evidence, view_model = extract_from_plan(
            analysis_plan, spec, scope, graph, repo, runtime, knowledge=knowledge
        )
        extras["architecture_evidence_model.json"] = evidence.model_dump(mode="json")
    else:
        extractor = get_extractor(raw.extract_backend or "gemini")
        extract_kw = dict(
            model=raw.gemini_model,
            samples=raw.samples,
        )
        if generate is not None:
            extract_kw["generate"] = generate
        view_model = extractor.extract(
            spec, scope, graph, repo, analysis_plan=analysis_plan, **extract_kw
        )
    view_model, structure_report = ground_view_model(view_model, graph, spec, scope=scope)
    aware = None
    if not raw.skip_critic:
        aware = reconcile_evidence(spec, analysis_plan, evidence, view_model, runtime)
        extras["evidence_aware_plan.json"] = aware.model_dump(mode="json")
        structure_report["reconciliation"] = aware.model_dump(mode="json")
    extras["structure_report.json"] = structure_report
    critic_notes = []
    if aware is not None:
        critic_notes = [
            f"{row['id']} {row['support']}: {row['rationale']}" for row in aware.questions
        ]
    view_model = generate_view(
        profile,
        spec,
        analysis_plan,
        evidence,
        view_model,
        critic_notes,
        runtime,
        knowledge=knowledge,
    )
    notation = spec.selected_view.diagram_language
    adapter = get_adapter(notation)
    source = adapter.emit(view_model)
    cleaned, report = validate_view(
        view_model,
        spec,
        scope,
        graph,
        source,
        notation,
        evidence=evidence,
        reconciliation=aware,
    )
    result.view_model = cleaned
    result.diagram_source = adapter.emit(cleaned)
    result.validation = report
    return result
