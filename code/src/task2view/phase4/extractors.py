"""Phase 5 extractor protocol. Plug-ins share graph + scoped files → ViewModel."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from typing import Any, Protocol, runtime_checkable

from task2view.contracts.models import PipelineError, RepositoryScope, ViewModel, ViewSpecification
from task2view.phase3.graph import RepositoryGraph
from task2view.phase4.extract import EXTRACT_PROMPT, extract_view
from task2view.phase4.gemini import generate_json


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


ARCHAGENT_PROMPT = """You extract an architecture view from source code. Output JSON only.

This is the ArchAgent *shape*, not the ArchAgent system: Task2View already
built a filesystem graph (files, directories, import-like uses) and attached
that summary plus source chunks. There is no separate ArchAgent analysis loop.
Synthesize the view only from those two attachments. Do not invent types
that are absent from the graph listing and the files.

Follow this catalog grain. Do not invent a different diagram kind.
{grain}

Shared grounding:
- evidence.file must exist in SOURCE FILES. evidence.symbol is optional.
  Keep the published name unless grain unit is type.
- Never dump every class unless grain unit is type. Never draw parent-directory
  boxes as the model unless the grain is layers.
- Actors, datastores, and external systems may be external.
- support is "observed" if a file excerpt shows it, otherwise "inferred".
- Answer each required_information id or list it in unanswered.

Return this shape:
{{
  "elements": [{{"id":"E1","name":"...","kind":"component|module|actor|datastore|external_system|class","role":"...","external":false,
    "evidence":{{"file":"relative/path","symbol":"Name","excerpt":"..."}},
    "support":"observed"}}],
  "relations": [{{"id":"R1","from":"E1","to":"E2","kind":"uses|calls|dataflow|contains|deploys|transition",
    "label":"methodName","order":1,
    "evidence":{{"file":"...","symbol":"...","excerpt":"..."}},
    "support":"observed"}}],
  "groups": [],
  "unanswered": ["RI-6"],
  "notes": []
}}

view_type: {view_type}
viewpoint_id: {viewpoint_id}
granularity: {granularity}
purpose: {purpose}
required_information:
{required}

FILE/DIRECTORY GRAPH (kept files; parent directory in [dir]; import-like uses):
{graph}

SOURCE FILES:
{files}
"""


CIAO_PROMPT_JSON = "ciao_prompt.json"

CIAO_PROMPT_PREFIX = """You extract an architecture view from source code. Output JSON only.

OVERRIDE — these instructions beat anything in the JSON block below:
- The JSON is CIAO's documentation prompt, included verbatim so you have its
  grounding_policy and mapping_rules. It was written for a full-repo flatten
  that emits markdown + PlantUML. That is NOT this pipeline.
- Ignore markdown, ISO section templates, "no JSON", "examine every line of
  the repository", and "do not skip any part of the code".
- The scoped files below ARE the entire corpus for this call. Do not try to
  open CIAO-system/prompt.json or any other path.
- Apply only the grounding / do-not-invent / mapping_rules that match the
  requested view_type. Then return the ViewModel JSON schema after the JSON
  block. Do not write markdown.

----- BEGIN CIAO prompt.json -----
"""

CIAO_PROMPT_SUFFIX = """
----- END CIAO prompt.json -----

Pipeline output (JSON only, not CIAO markdown). Ignore the JSON's markdown
and PlantUML templates:
{{
  "elements": [{{"id":"E1","name":"...","kind":"component|module|actor|datastore|external_system","role":"...","external":false,
    "evidence":{{"file":"relative/path","symbol":"Name","excerpt":"..."}},
    "support":"observed"}}],
  "relations": [{{"id":"R1","from":"E1","to":"E2","kind":"uses|calls|dataflow|contains|deploys|transition",
    "label":"methodName","order":1,
    "evidence":{{"file":"...","symbol":"...","excerpt":"..."}},
    "support":"observed"}}],
  "groups": [],
  "unanswered": ["RI-6"],
  "notes": []
}}

Additional Task2View rules:
Follow this catalog grain. Do not invent a different diagram kind.
{grain}
- evidence.file must exist in SOURCE FILES. evidence.symbol is optional.
  Keep the published name unless grain unit is type.
- Never dump every class unless grain unit is type.
- support is "observed" if a file excerpt shows it, otherwise "inferred".
- Answer each required_information id or list it in unanswered.

view_type: {view_type}
viewpoint_id: {viewpoint_id}
granularity: {granularity}
purpose: {purpose}
required_information:
{required}

FILE/DIRECTORY GRAPH (kept files; parent directory in [dir]; scoped files first):
{graph}

SOURCE FILES:
{files}
"""


@lru_cache(maxsize=1)
def load_ciao_prompt_json() -> str:
    """Return the vendored CIAO-system/prompt.json text."""
    path = files("task2view.knowledge.data").joinpath(CIAO_PROMPT_JSON)
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as exc:
        raise PipelineError(f"CIAO prompt file missing: {CIAO_PROMPT_JSON}") from exc


def ciao_prompt_template() -> str:
    """Prompt sent to Gemini: verbatim CIAO prompt.json plus ViewModel schema."""
    body = load_ciao_prompt_json().replace("{", "{{").replace("}", "}}")
    return CIAO_PROMPT_PREFIX + body + CIAO_PROMPT_SUFFIX


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
    )


@register_extractor
class GeminiExtractor:
    """Graph summary + packed scoped files (pipeline spec v2 Phase 4a)."""

    name = "gemini"

    def extract(self, view_spec, scope, graph, repo_root, *, model=None, samples=1, generate=generate_json):
        return _run(
            view_spec,
            scope,
            graph,
            repo_root,
            model=model,
            samples=samples,
            generate=generate,
            prompt_template=EXTRACT_PROMPT,
        )


@register_extractor
class ArchAgentExtractor:
    """ArchAgent-shaped prompt over Task2View's filesystem graph + scoped files."""

    name = "archagent"

    def extract(self, view_spec, scope, graph, repo_root, *, model=None, samples=1, generate=generate_json):
        return _run(
            view_spec,
            scope,
            graph,
            repo_root,
            model=model,
            samples=samples,
            generate=generate,
            prompt_template=ARCHAGENT_PROMPT,
        )


@register_extractor
class CiaoExtractor:
    """Inject the vendored CIAO prompt.json into the extract call (scoped files only)."""

    name = "ciao"

    def extract(self, view_spec, scope, graph, repo_root, *, model=None, samples=1, generate=generate_json):
        return _run(
            view_spec,
            scope,
            graph,
            repo_root,
            model=model,
            samples=samples,
            generate=generate,
            prompt_template=ciao_prompt_template(),
        )
