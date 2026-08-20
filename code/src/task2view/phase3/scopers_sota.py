"""Single-strategy SOTA scopers used as ablation arms (LocAgent / Aider / layer)."""

from __future__ import annotations

from collections import defaultdict

from task2view.contracts.models import CleanedCorpus, RepositoryScope, ScopeCandidate, ViewSpecification
from task2view.phase3.graph import RepositoryGraph
from task2view.phase3.protocol import register_scoper
from task2view.phase3.select import budget_select
from task2view.phase3.scopers_composite import _task_seed_names


def _require(corpus: CleanedCorpus | None, graph: RepositoryGraph | None) -> tuple[CleanedCorpus, RepositoryGraph]:
    if corpus is None or graph is None:
        raise ValueError("this scoper requires cleaned corpus and graph")
    return corpus, graph


@register_scoper
class Graph1Scoper:
    """Task seeds plus 1-hop expansion (LocAgent / RepoGraph one-hop localization)."""

    name = "graph1"
    requires: set[str] = {"graph"}

    def scope(
        self,
        view_spec: ViewSpecification,
        repo_root: str,
        budget: int,
        corpus: CleanedCorpus | None = None,
        graph: RepositoryGraph | None = None,
    ) -> RepositoryScope:
        corpus, graph = _require(corpus, graph)
        cands: list[ScopeCandidate] = []
        seeds = _task_seed_names(view_spec, graph)
        seen: set[str] = set()
        for name, serves in seeds.items():
            node = graph.nodes[name]
            if node.path not in seen:
                cands.append(
                    ScopeCandidate(
                        path=node.path,
                        serves=serves,
                        origin="task_seed",
                        score=0.94,
                        reason=f"name/path match for {name}",
                    )
                )
                seen.add(node.path)
            for nb in graph.neighbors(name):
                nnode = graph.nodes[nb]
                if nnode.path in seen:
                    continue
                cands.append(
                    ScopeCandidate(
                        path=nnode.path,
                        serves=[],
                        origin="expansion_1hop",
                        score=0.75,
                        reason=f"1-hop from {name}",
                    )
                )
                seen.add(nnode.path)
        return budget_select(
            cands,
            view_spec=view_spec,
            repo_root=repo_root,
            budget=budget,
            strategy="graph1",
            corpus=corpus,
            graph=graph,
        )


@register_scoper
class CentralScoper:
    """Top-k degree centrality (Aider RepoMap ablation; PageRank is ``pagerank``)."""

    name = "central"
    requires: set[str] = {"graph"}

    def scope(
        self,
        view_spec: ViewSpecification,
        repo_root: str,
        budget: int,
        corpus: CleanedCorpus | None = None,
        graph: RepositoryGraph | None = None,
        top_k: int = 12,
    ) -> RepositoryScope:
        corpus, graph = _require(corpus, graph)
        ranked = sorted(graph.nodes.values(), key=lambda n: -graph.degree(n.name))
        cands = [
            ScopeCandidate(
                path=node.path,
                serves=[],
                origin="centrality_seed",
                score=0.88,
                reason=f"degree centrality {graph.degree(node.name)} ({node.name})",
            )
            for node in ranked[:top_k]
        ]
        return budget_select(
            cands,
            view_spec=view_spec,
            repo_root=repo_root,
            budget=budget,
            strategy="central",
            corpus=corpus,
            graph=graph,
        )


@register_scoper
class LayerScoper:
    """Top-n types per package/layer — recovers thin mandatory layers."""

    name = "layer"
    requires: set[str] = {"graph"}

    def scope(
        self,
        view_spec: ViewSpecification,
        repo_root: str,
        budget: int,
        corpus: CleanedCorpus | None = None,
        graph: RepositoryGraph | None = None,
        per_layer: int = 2,
    ) -> RepositoryScope:
        corpus, graph = _require(corpus, graph)
        by_layer: dict[str, list] = defaultdict(list)
        for node in graph.nodes.values():
            by_layer[node.layer].append(node)
        cands: list[ScopeCandidate] = []
        for layer, nodes in by_layer.items():
            top = sorted(nodes, key=lambda n: -graph.degree(n.name))[:per_layer]
            for node in top:
                cands.append(
                    ScopeCandidate(
                        path=node.path,
                        serves=[],
                        origin="layer_seed",
                        score=0.82,
                        reason=f"top-{min(per_layer, len(nodes))} in layer {layer} ({node.name})",
                    )
                )
        return budget_select(
            cands,
            view_spec=view_spec,
            repo_root=repo_root,
            budget=budget,
            strategy="layer",
            corpus=corpus,
            graph=graph,
        )
