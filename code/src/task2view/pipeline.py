from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from task2view.contracts.models import (
    CleanedCorpus,
    NormalizedRequest,
    PipelineError,
    RepositoryScope,
    UserRequest,
    ValidationReport,
    ViewModel,
    ViewSpecification,
)
from task2view.phase0.clean import clean_repository
from task2view.phase1.intake import new_request_id, normalize_request
from task2view.phase2.selector import identify_view
from task2view.phase3 import build_graph, get_scoper
from task2view.phase3.graph import RepositoryGraph
from task2view.phase4 import get_adapter, get_extractor
from task2view.phase4.gemini import generate_json
from task2view.phase4.validate import validate_view, write_diagram

DIAGRAM_EXT = {
    "plantuml": "puml",
    "c4plantuml": "puml",
    "mermaid": "mmd",
    "d2": "d2",
    "graphviz": "dot",
    "structurizr": "dsl",
    "nomnoml": "nomnoml",
    "excalidraw": "excalidraw.json",
    "bpmn": "bpmn",
}


@dataclass
class PipelineResult:
    corpus: CleanedCorpus
    request: NormalizedRequest
    spec: ViewSpecification
    graph: RepositoryGraph
    scope: RepositoryScope
    view_model: ViewModel | None = None
    diagram_source: str | None = None
    validation: ValidationReport | None = None
    extras: dict[str, Any] = field(default_factory=dict)


def run_through_phase2(
    raw: UserRequest,
) -> tuple[CleanedCorpus, NormalizedRequest, ViewSpecification]:
    raw.request_id = raw.request_id or new_request_id()
    corpus = clean_repository(raw.code or raw.repository or "", request_id=raw.request_id)
    request = normalize_request(raw)
    request.corpus = {
        "kept": corpus.counts["kept"],
        "dropped": corpus.counts["dropped"],
        "languages": corpus.counts.get("languages", {}),
    }
    spec = identify_view(request)
    return corpus, request, spec


def run_through_phase3(raw: UserRequest) -> PipelineResult:
    corpus, request, spec = run_through_phase2(raw)
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
    return PipelineResult(corpus=corpus, request=request, spec=spec, graph=graph, scope=scope)


def run_legacy_pipeline(raw: UserRequest, *, generate=None) -> PipelineResult:
    result = run_through_phase3(raw)
    if raw.skip_extract:
        return result
    generate = generate or generate_json
    extractor = get_extractor(raw.extract_backend or "gemini")
    result.view_model = extractor.extract(
        result.spec,
        result.scope,
        result.graph,
        result.request.repository.location,
        model=raw.gemini_model,
        samples=raw.samples,
        generate=generate,
    )
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


def run_pipeline(raw: UserRequest, *, generate=None) -> PipelineResult:
    if raw.legacy:
        return run_legacy_pipeline(raw, generate=generate)
    from task2view.agents.orchestrate import run_agentic

    return run_agentic(raw, generate=generate)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _dump(model) -> dict:
    return model.model_dump(mode="json", by_alias=True)


def write_run(
    out_dir: Path,
    corpus: CleanedCorpus,
    request: NormalizedRequest,
    spec: ViewSpecification,
    *,
    scope: RepositoryScope | None = None,
    view_model: ViewModel | None = None,
    diagram_source: str | None = None,
    validation: ValidationReport | None = None,
    notation: str | None = None,
    render_formats: list[str] | None = None,
    kroki_url: str | None = None,
) -> None:
    write_json(out_dir / "cleaned_corpus.json", _dump(corpus))
    write_json(out_dir / "normalized_request.json", _dump(request))
    write_json(out_dir / "view_specification.json", _dump(spec))
    if scope is not None:
        write_json(out_dir / "repository_scope.json", _dump(scope))
    if view_model is not None:
        write_json(out_dir / "view_model.json", _dump(view_model))
    lang = notation or spec.selected_view.diagram_language
    if diagram_source is not None:
        ext = DIAGRAM_EXT.get(lang, "txt")
        write_diagram(out_dir / f"architecture_view.{ext}", diagram_source)
        if render_formats:
            from task2view.phase4.compile import compile_diagram

            report = compile_diagram(
                diagram_source,
                lang,
                out_dir,
                stem="architecture_view",
                formats=render_formats,
                kroki_url=kroki_url,
            )
            write_json(out_dir / "render_report.json", report)
    if validation is not None:
        write_json(out_dir / "validation_report.json", _dump(validation))


def write_result(
    out_dir: Path,
    result: PipelineResult,
    *,
    render_formats: list[str] | None = None,
    kroki_url: str | None = None,
) -> None:
    write_run(
        out_dir,
        result.corpus,
        result.request,
        result.spec,
        scope=result.scope,
        view_model=result.view_model,
        diagram_source=result.diagram_source,
        validation=result.validation,
        notation=result.spec.selected_view.diagram_language,
        render_formats=render_formats,
        kroki_url=kroki_url,
    )
    for name, payload in (result.extras or {}).items():
        write_json(out_dir / name, payload)
