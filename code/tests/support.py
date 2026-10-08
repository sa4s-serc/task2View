"""Catalog-backed fixtures for tests that need a spec and a scope without agents."""

from __future__ import annotations

from pathlib import Path

from task2view.contracts.models import (
    NormalizedRequest,
    Preferences,
    StakeholderRef,
    TaskRef,
    ViewSpecification,
)
from task2view.knowledge.correspondence import select_correspondence, spec_from_correspondence
from task2view.knowledge.loader import load_knowledge
from task2view.phase0.clean import clean_repository
from task2view.inputs.repository import resolve_repository
from task2view.phase4 import build_graph, get_scoper
from task2view.pipeline import PipelineResult


def catalog_spec(
    repo: str | Path,
    text: str,
    *,
    stakeholder: str = "Tester",
    goal: str | None = None,
    request_id: str = "REQ-001",
    diagram_language: str | None = None,
    scope_token_budget: int = 120_000,
) -> tuple[NormalizedRequest, ViewSpecification]:
    knowledge = load_knowledge()
    role_id = knowledge.resolve_role(stakeholder)
    profile = knowledge.stakeholder(role_id)
    concerns = knowledge.bind_concerns(role_id, text)
    correspondence = select_correspondence(
        role_id,
        text,
        knowledge,
        goal=goal or text,
        extra_concerns=concerns,
        preferred_language=diagram_language,
    )
    request = NormalizedRequest(
        request_id=request_id,
        repository=resolve_repository(str(repo)),
        stakeholder=StakeholderRef(
            role=role_id,
            original_label=stakeholder,
            iso_42010_class=profile.get("iso_42010_class"),
            vb_row=profile.get("vb_row") or role_id,
        ),
        task=TaskRef(description=text),
        goal=goal or text,
        concerns=list(concerns),
        preferences=Preferences(
            diagram_language=diagram_language,
            scope_token_budget=scope_token_budget,
        ),
    )
    return request, spec_from_correspondence(request, correspondence, knowledge)


def catalog_scope(
    repo: str | Path,
    text: str,
    *,
    stakeholder: str = "Tester",
    goal: str | None = None,
    request_id: str = "REQ-001",
    diagram_language: str | None = None,
    scope_strategy: str = "composite",
    scope_token_budget: int = 120_000,
) -> PipelineResult:
    request, spec = catalog_spec(
        repo,
        text,
        stakeholder=stakeholder,
        goal=goal,
        request_id=request_id,
        diagram_language=diagram_language,
        scope_token_budget=scope_token_budget,
    )
    corpus = clean_repository(repo, request_id=request_id)
    request.corpus = {
        "kept": corpus.counts["kept"],
        "dropped": corpus.counts["dropped"],
        "languages": corpus.counts.get("languages", {}),
    }
    graph = build_graph(request.repository.location, corpus)
    scope = get_scoper(scope_strategy).scope(
        spec,
        request.repository.location,
        scope_token_budget,
        corpus=corpus,
        graph=graph,
    )
    return PipelineResult(corpus=corpus, request=request, spec=spec, graph=graph, scope=scope)


def complete_extract(result: PipelineResult, generate, *, backend: str = "gemini", samples: int = 1) -> PipelineResult:
    from task2view.phase6.critic import refine_extracted_view
    from task2view.agents.runtime import AgentRuntime
    from task2view.phase5 import get_extractor
    from task2view.phase7 import get_adapter
    from task2view.phase8.validate import validate_view

    extractor = get_extractor(backend)
    result.view_model = extractor.extract(
        result.spec,
        result.scope,
        result.graph,
        result.request.repository.location,
        samples=samples,
        generate=generate,
    )
    runtime = AgentRuntime(generate=generate)
    result.view_model, structure_report = refine_extracted_view(
        result.view_model,
        result.spec,
        result.scope,
        result.graph,
        runtime,
    )
    result.extras["structure_report.json"] = structure_report
    notation = result.spec.selected_view.diagram_language
    adapter = get_adapter(notation)
    source = adapter.emit(result.view_model)
    cleaned, report = validate_view(
        result.view_model,
        result.spec,
        result.scope,
        result.graph,
        source,
        notation,
    )
    result.view_model = cleaned
    result.diagram_source = adapter.emit(cleaned)
    result.validation = report
    return result
