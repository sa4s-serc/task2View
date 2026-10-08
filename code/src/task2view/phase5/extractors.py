"""Phase 5 extractor protocol. Plug-ins share graph + scoped files → ViewModel."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from typing import Any, Protocol, runtime_checkable

from task2view.contracts.models import PipelineError, RepositoryScope, ViewModel, ViewSpecification
from task2view.phase4.graph import RepositoryGraph
from task2view.phase5.extract import EXTRACT_PROMPT, extract_view
from task2view.llm.gemini import generate_json


@runtime_checkable
class Extractor(Protocol):
    name: str

    def extract(
        self,
        view_spec: ViewSpecification,
        scope: RepositoryScope,
        graph: RepositoryGraph,
        repo_root: str,
        *,
        model: str | None = None,
        samples: int = 1,
        generate=generate_json,
    ) -> ViewModel: ...


EXTRACTORS: dict[str, type] = {}


def register_extractor(cls: type) -> type:
    EXTRACTORS[cls.name] = cls
    return cls


def get_extractor(name: str) -> Extractor:
    try:
        return EXTRACTORS[name]()
    except KeyError as exc:
        raise KeyError(f"Unknown extractor {name!r}. Registered: {sorted(EXTRACTORS)}") from exc


ARCHAGENT_PROMPT = (
    "This is the ArchAgent *shape*, not the ArchAgent system. Task2View already "
    "built a filesystem graph and attached scoped source chunks. There is no "
    "separate ArchAgent analysis loop. Invent nothing that is absent from SOURCE "
    "FILES or the scoped file graph.\n\n"
    + EXTRACT_PROMPT
)

CIAO_PROMPT_JSON = "ciao_prompt.json"


@lru_cache(maxsize=1)
def load_ciao_prompt_json() -> str:
    """Task-adapted CIAO rules. Used to pick one viewpoint block, not inlined whole."""
    path = files("task2view.knowledge.data").joinpath(CIAO_PROMPT_JSON)
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as exc:
        raise PipelineError(f"CIAO prompt file missing: {CIAO_PROMPT_JSON}") from exc


def ciao_prompt_template() -> str:
    """Same extract contract as Gemini, plus CIAO mapping_rules for the viewpoint."""
    return (
        "CIAO extractor: output ViewModel JSON only. Do not write markdown, ISO "
        "section templates, or PlantUML from CIAO. Apply only the mapping_rules "
        "for the selected viewpoint_id at the end of this prompt.\n\n"
        + EXTRACT_PROMPT
    )


def _run(
    view_spec: ViewSpecification,
    scope: RepositoryScope,
    graph: RepositoryGraph,
    repo_root: str,
    *,
    model: str | None,
    samples: int,
    generate: Any,
    prompt_template: str,
    analysis_plan=None,
) -> ViewModel:
    return extract_view(
        view_spec,
        scope,
        graph,
        repo_root,
        model=model,
        samples=samples,
        generate=generate,
        prompt_template=prompt_template,
        analysis_plan=analysis_plan,
    )


@register_extractor
class GeminiExtractor:
    """Graph summary plus the scoped source files."""

    name = "gemini"

    def extract(self, view_spec, scope, graph, repo_root, *, model=None, samples=1, generate=generate_json, analysis_plan=None):
        return _run(
            view_spec,
            scope,
            graph,
            repo_root,
            model=model,
            samples=samples,
            generate=generate,
            prompt_template=EXTRACT_PROMPT,
            analysis_plan=analysis_plan,
        )


@register_extractor
class ArchAgentExtractor:
    """ArchAgent-shaped prompt over Task2View's filesystem graph + scoped files."""

    name = "archagent"

    def extract(self, view_spec, scope, graph, repo_root, *, model=None, samples=1, generate=generate_json, analysis_plan=None):
        return _run(
            view_spec,
            scope,
            graph,
            repo_root,
            model=model,
            samples=samples,
            generate=generate,
            prompt_template=ARCHAGENT_PROMPT,
            analysis_plan=analysis_plan,
        )


@register_extractor
class CiaoExtractor:
    """Inject the vendored CIAO prompt.json into the extract call (scoped files only)."""

    name = "ciao"

    def extract(self, view_spec, scope, graph, repo_root, *, model=None, samples=1, generate=generate_json, analysis_plan=None):
        return _run(
            view_spec,
            scope,
            graph,
            repo_root,
            model=model,
            samples=samples,
            generate=generate,
            prompt_template=ciao_prompt_template(),
            analysis_plan=analysis_plan,
        )
