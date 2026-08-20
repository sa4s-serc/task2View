from __future__ import annotations

from task2view.contracts.models import CleanedCorpus, RepositoryScope, ScopeCandidate, ViewSpecification
from task2view.phase3.protocol import register_scoper
from task2view.phase3.select import budget_select


@register_scoper
class FullScoper:
    name = "full"
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
            raise ValueError("full scoper requires a cleaned corpus")
        ri = [item.id for item in view_spec.required_information]
        cands = [
            ScopeCandidate(
                path=item.path,
                serves=list(ri),
                origin="full",
                score=1.0,
                reason="whole cleaned corpus",
            )
            for item in corpus.kept
        ]
        return budget_select(
            cands,
            view_spec=view_spec,
            repo_root=repo_root,
            budget=budget,
            strategy="full",
            corpus=corpus,
            graph=graph,
        )
