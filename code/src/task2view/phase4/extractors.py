"""Phase 5 extractor protocol. Plug-ins share graph + scoped files → ViewModel."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from task2view.contracts.models import RepositoryScope, ViewModel, ViewSpecification
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

You follow ArchAgent: static analysis produces an AST-derived reference graph;
the language model only synthesizes a view from that graph plus the source
chunks. Do not invent types that are absent from the graph. Actors/users may
be external.

Rules:
- Use ONLY the provided files and the repository graph.
- Every non-external element must have evidence.file and evidence.symbol that exist in the files.
- support is "observed" if a file excerpt shows it, otherwise "inferred".
- Keep the view at the requested granularity.
- Answer each required_information id or list it in unanswered.

Return this shape:
{{
  "elements": [{{"id":"E1","name":"...","kind":"component|class|actor|service|datastore|external_system","role":"...","external":false,
    "evidence":{{"file":"relative/path.java","symbol":"TypeName","excerpt":"..."}},
    "support":"observed"}}],
  "relations": [{{"id":"R1","from":"E1","to":"E2","kind":"call|depends|inherits|implements|dataflow",
    "label":"methodName","order":1,
    "evidence":{{"file":"...","symbol":"...","excerpt":"..."}},
    "support":"observed"}}],
  "groups": [{{"id":"G1","name":"Boundary","kind":"layer|package|boundary","contains":["E1"]}}],
  "unanswered": ["RI-6"],
  "notes": []
}}

view_type: {view_type}
granularity: {granularity}
purpose: {purpose}
required_information:
{required}

AST REFERENCE GRAPH (ground truth structure; prefer these type names):
{graph}

SOURCE FILES:
{files}
"""


CIAO_PROMPT = """You extract an architecture view from source code. Output JSON only.

You follow CIAO grounding rules from CIAO-system/prompt.json:
- Examine the provided source to understand components, responsibilities, and
  dependencies. The documentation must reflect the real implementation.
- Reflect practical decisions and architectural choices evident in the files.
- Do not invent types, files, or calls that are not in the graph or excerpts.
- Prefer a complete list of the in-scope components rather than a partial sample.

Rules:
- Use ONLY the provided files and the repository graph.
- Every non-external element must have evidence.file and evidence.symbol that exist in the files.
- support is "observed" if a file excerpt shows it, otherwise "inferred".
- Keep the view at the requested granularity.
- Answer each required_information id or list it in unanswered.

Return this shape:
{{
  "elements": [{{"id":"E1","name":"...","kind":"component|class|actor|service|datastore|external_system","role":"...","external":false,
    "evidence":{{"file":"relative/path.java","symbol":"TypeName","excerpt":"..."}},
    "support":"observed"}}],
  "relations": [{{"id":"R1","from":"E1","to":"E2","kind":"call|depends|inherits|implements|dataflow",
    "label":"methodName","order":1,
    "evidence":{{"file":"...","symbol":"...","excerpt":"..."}},
    "support":"observed"}}],
  "groups": [{{"id":"G1","name":"Boundary","kind":"layer|package|boundary","contains":["E1"]}}],
  "unanswered": ["RI-6"],
  "notes": []
}}

view_type: {view_type}
granularity: {granularity}
purpose: {purpose}
required_information:
{required}

REPOSITORY GRAPH (ground truth structure):
{graph}

SOURCE FILES:
{files}
"""


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
    """ArchAgent shape: AST reference graph in the prompt; LLM synthesizes the view."""

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
    """CIAO prompt.json grounding rules on the scoped corpus (not a full-repo flatten)."""

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
            prompt_template=CIAO_PROMPT,
        )
