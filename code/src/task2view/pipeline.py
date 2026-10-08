from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from task2view.contracts.models import (
    CleanedCorpus,
    NormalizedRequest,
    RepositoryScope,
    UserRequest,
    ValidationReport,
    ViewModel,
    ViewSpecification,
)
from task2view.phase4.graph import RepositoryGraph
from task2view.phase8.validate import write_diagram

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


def run_pipeline(raw: UserRequest, *, generate=None) -> PipelineResult:
    if raw.config:
        from task2view.config import apply_pipeline_config, load_pipeline_config

        raw = apply_pipeline_config(raw, load_pipeline_config(raw.config))
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
            from task2view.phase7.compile import compile_diagram

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
