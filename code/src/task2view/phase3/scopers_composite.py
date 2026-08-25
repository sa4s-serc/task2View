"""SOTA default: task seeds ∪ degree centrality ∪ layer coverage ∪ 1-hop."""

from __future__ import annotations

from collections import defaultdict

from task2view.contracts.models import CleanedCorpus, RepositoryScope, ScopeCandidate, ViewSpecification
from task2view.phase3.graph import RepositoryGraph
from task2view.phase3.protocol import register_scoper
from task2view.phase3.select import budget_select
from task2view.phase3.seeds import forced_seed_candidates, task_seed_names as _task_seed_names


@register_scoper
class CompositeScoper:
    name = "composite"
    requires: set[str] = {"graph"}

    def scope(
        self,
        view_spec: ViewSpecification,
        repo_root: str,
        budget: int,
        corpus: CleanedCorpus | None = None,
        graph: RepositoryGraph | None = None,
    ) -> RepositoryScope:
        if corpus is None or graph is None:
            raise ValueError("composite scoper requires cleaned corpus and graph")

        by_path: dict[str, ScopeCandidate] = {}

        def add(path: str, origin: str, score: float, reason: str, serves: list[str]) -> None:
            prev = by_path.get(path)
            if prev is None or score > prev.score:
                by_path[path] = ScopeCandidate(
                    path=path, serves=serves, origin=origin, score=score, reason=reason
                )
            elif prev is not None:
                merged = sorted(set(prev.serves) | set(serves))
                prev.serves = merged

        task_hits = _task_seed_names(view_spec, graph)
        for name, serves in task_hits.items():
            node = graph.nodes[name]
            add(node.path, "task_seed", 0.94, f"name/path match for {name}", serves)

        for cand in forced_seed_candidates(view_spec, repo_root, corpus, graph):
            add(cand.path, cand.origin, cand.score, cand.reason, cand.serves)

        ranked = sorted(graph.nodes.values(), key=lambda n: -graph.degree(n.name))
        for node in ranked[:12]:
            add(
                node.path,
                "centrality_seed",
                0.88,
                f"degree centrality {graph.degree(node.name)} ({node.name})",
                [],
            )

        by_layer: dict[str, list] = defaultdict(list)
        for node in graph.nodes.values():
            by_layer[node.layer].append(node)
        for layer, nodes in by_layer.items():
            top = sorted(nodes, key=lambda n: -graph.degree(n.name))[:2]
            for node in top:
                add(
                    node.path,
                    "layer_seed",
                    0.82,
                    f"top-{min(2, len(nodes))} in layer {layer} ({node.name})",
                    [],
                )

        seed_names = {n for n, node in graph.nodes.items() if node.path in by_path}
        for name in list(seed_names):
            for nb in graph.neighbors(name):
                node = graph.nodes[nb]
                add(
                    node.path,
                    "expansion_1hop",
                    0.75,
                    f"1-hop from {name}",
                    [],
                )

        return budget_select(
            list(by_path.values()),
            view_spec=view_spec,
            repo_root=repo_root,
            budget=budget,
            strategy="composite",
            corpus=corpus,
            graph=graph,
            expansion_depth=1,
        )
