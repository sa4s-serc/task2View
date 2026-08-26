"""Default pipeline: agents 1–3, then SOTA scoper + extractor + adapter (ADR-002)."""

from __future__ import annotations

from task2view.agents.phase1_interpret import interpret_stakeholder_task
from task2view.agents.phase2_questions import derive_questions
from task2view.agents.phase3_viewpoint import plan_viewpoints
from task2view.agents.runtime import AgentRuntime
from task2view.contracts.models import (
    Preferences,
    NormalizedRequest,
    PipelineError,
    StakeholderRef,
    TaskRef,
    UserRequest,
)
from task2view.knowledge.correspondence import (
    select_correspondence,
    spec_from_correspondence,
    with_viewpoint,
)
from task2view.knowledge.loader import load_knowledge
from task2view.phase0.clean import clean_repository
from task2view.phase1.intake import new_request_id, resolve_repository
from task2view.phase3 import get_scoper
from task2view.phase3.graph import build_graph
from task2view.phase4 import get_adapter, get_extractor
from task2view.phase4.validate import validate_view


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


def _merge_question_concerns(spec, questions, knowledge) -> None:
    catalog = knowledge.catalog_concerns()
    concerns = list(spec.architectural_concerns)
    for extra in questions.concerns:
        if extra in catalog and extra not in concerns:
            concerns.append(extra)
    framed = set(knowledge.viewpoint(spec.selected_view.viewpoint_id).get("frames_concerns") or [])
    unanswered = [c for c in concerns if c not in framed and c != "general"]
    spec.architectural_concerns = concerns
    spec.unanswered_concerns = unanswered
    spec.declared_gaps = list(unanswered)


def _profile_blob(profile) -> str:
    return " ".join(
        p
        for p in (profile.source_goal, profile.task, profile.target, profile.goal)
        if p
    )


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
    correspondence = select_correspondence(
        request.stakeholder.role,
        _profile_blob(profile) or request.task.description,
        knowledge,
        goal=profile.source_goal or profile.task,
        extra_concerns=list(profile.concerns),
        preferred_language=raw.diagram_language,
    )
    questions = derive_questions(
        profile, runtime, knowledge=knowledge, correspondence=correspondence
    )
    viewpoint_plan = plan_viewpoints(
        profile,
        questions,
        runtime,
        knowledge=knowledge,
        max_views=raw.max_views,
        preferred_language=raw.diagram_language,
        correspondence=correspondence,
    )
    active = next((v for v in viewpoint_plan.views if not v.deferred), None)
    if active is None:
        raise PipelineError("no active view in the viewpoint plan")
    if active.viewpoint_id != correspondence.viewpoint_id:
        correspondence = with_viewpoint(
            correspondence,
            active.viewpoint_id,
            knowledge,
            preferred_language=raw.diagram_language,
            goal=profile.source_goal or profile.task,
        )
    spec = spec_from_correspondence(request, correspondence, knowledge)
    spec.task_summary = " | ".join(
        p for p in (profile.source_goal, profile.task, profile.target, profile.goal) if p
    )
    if active.purpose:
        spec.selected_view.purpose = active.purpose
    spec.selected_view.diagram_language = active.diagram_language
    spec.selected_view.notation = active.notation or spec.selected_view.notation
    spec.selected_view.granularity = active.granularity or spec.selected_view.granularity
    _merge_question_concerns(spec, questions, knowledge)
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
    extras = {
        "stakeholder_task_profile.json": profile.model_dump(mode="json"),
        "architectural_questions.json": questions.model_dump(mode="json"),
        "viewpoint_plan.json": viewpoint_plan.model_dump(mode="json"),
        "correspondence.json": correspondence.as_dict(),
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
    extractor = get_extractor(raw.extract_backend or "gemini")
    extract_kw = dict(
        model=raw.gemini_model,
        samples=raw.samples,
    )
    if generate is not None:
        extract_kw["generate"] = generate
    view_model = extractor.extract(spec, scope, graph, repo, **extract_kw)
    from task2view.agents.phase6_critic import refine_extracted_view
    view_model, structure_report = refine_extracted_view(
        view_model, spec, scope, graph, runtime, skip_critic=raw.skip_critic
    )
    extras["structure_report.json"] = structure_report
    notation = spec.selected_view.diagram_language
    adapter = get_adapter(notation)
    source = adapter.emit(view_model)
    cleaned, report = validate_view(view_model, spec, scope, graph, source, notation)
    result.view_model = cleaned
    result.diagram_source = adapter.emit(cleaned)
    result.validation = report
    return result
