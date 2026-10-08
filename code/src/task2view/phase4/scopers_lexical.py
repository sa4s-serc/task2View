from __future__ import annotations

import re

from task2view.contracts.models import CleanedCorpus, RepositoryScope, ScopeCandidate, ViewSpecification
from task2view.phase4.protocol import register_scoper
from task2view.phase4.select import budget_select

_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]{2,}")
_STOP = {
    "the", "and", "for", "need", "show", "how", "entry", "point", "component",
    "components", "module", "modules", "class", "classes", "type", "types",
    "domain", "service", "between", "participants", "observable", "paths",
    "question", "questions", "concern", "viewpoint", "diagram", "system",
    "responsibility", "responsibilities", "hierarchy", "containment",
    "connector", "connectors", "owner", "owns", "handles",
}


def keywords(view_spec: ViewSpecification) -> list[str]:
    """Tokens that pull files out of the graph.

    The task sentence and required-information lines are included, and so are
    the Phase 1–3 decisions: question text, viewpoint purpose, and concerns.
    """
    parts = [view_spec.task_summary or ""]
    for item in view_spec.required_information:
        parts.append(item.need)
    for question in view_spec.architectural_questions or []:
        parts.append(question.text)
    view = view_spec.selected_view
    parts.append(view.purpose or "")
    parts.extend(view_spec.architectural_concerns or [])
    blob = " ".join(parts)
    found = []
    for tok in _TOKEN.findall(blob.lower()):
        if tok in _STOP or tok in found:
            continue
        found.append(tok)
    return found


@register_scoper
class LexicalScoper:
    name = "lexical"
    requires: set[str] = set()

    def scope(
        self,
        view_spec: ViewSpecification,
        repo_root: str,
        budget: int,
        corpus: CleanedCorpus | None = None,
        graph=None,
    ) -> RepositoryScope:
        if corpus is None:
            raise ValueError("lexical scoper requires a cleaned corpus")
        cues = keywords(view_spec)
        cands: list[ScopeCandidate] = []
        for item in corpus.kept:
            hay = item.path.lower()
            hits = [c for c in cues if c in hay]
            if not hits:
                continue
            serves = [
                ri.id
                for ri in view_spec.required_information
                if any(c in ri.need.lower() or c in hay for c in hits)
            ]
            cands.append(
                ScopeCandidate(
                    path=item.path,
                    serves=serves,
                    origin="lexical",
                    score=min(1.0, 0.4 + 0.15 * len(hits)),
                    reason="filename/path keywords: " + ", ".join(hits[:6]),
                )
            )
        return budget_select(
            cands,
            view_spec=view_spec,
            repo_root=repo_root,
            budget=budget,
            strategy="lexical",
            corpus=corpus,
            graph=graph,
        )
