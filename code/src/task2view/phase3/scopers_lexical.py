from __future__ import annotations

import re

from task2view.contracts.models import CleanedCorpus, RepositoryScope, ScopeCandidate, ViewSpecification
from task2view.phase3.protocol import register_scoper
from task2view.phase3.select import budget_select

_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]{2,}")
_STOP = {
    "the", "and", "for", "need", "show", "how", "entry", "point", "component",
    "domain", "service", "between", "participants", "observable", "paths",
}


def keywords(view_spec: ViewSpecification) -> list[str]:
    blob = view_spec.task_summary
    for item in view_spec.required_information:
        blob += " " + item.need
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
