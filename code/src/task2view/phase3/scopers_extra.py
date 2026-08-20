"""Published-mechanism scopers that are not the original three ablation arms."""

from __future__ import annotations

from pathlib import Path

from task2view.contracts.models import CleanedCorpus, RepositoryScope, ScopeCandidate, ViewSpecification
from task2view.phase3.graph import RepositoryGraph
from task2view.phase3.protocol import register_scoper
from task2view.phase3.select import budget_select
from task2view.phase3.scopers_composite import _task_seed_names
from task2view.phase3.scopers_lexical import keywords
from task2view.phase3.scopers_sota import _require


@register_scoper
class LocAgentScoper:
    """Task seeds plus 2-hop BFS on the typed uses graph.

    LocAgent (Chen et al.) localizes with a multi-hop code graph and LLM tools.
    This plug-in is the graph walk only — not their SWE-bench agent harness.
    """

    name = "locagent"
    requires: set[str] = {"graph"}

    def scope(
        self,
        view_spec: ViewSpecification,
        repo_root: str,
        budget: int,
        corpus: CleanedCorpus | None = None,
        graph: RepositoryGraph | None = None,
        hops: int = 2,
    ) -> RepositoryScope:
        corpus, graph = _require(corpus, graph)
        seeds = _task_seed_names(view_spec, graph)
        reached = graph.hop_from(set(seeds), hops)
        cands: list[ScopeCandidate] = []
        seen: set[str] = set()
        for name, serves in seeds.items():
            node = graph.nodes[name]
            if node.path in seen:
                continue
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
        for name in reached - set(seeds):
            node = graph.nodes[name]
            if node.path in seen:
                continue
            cands.append(
                ScopeCandidate(
                    path=node.path,
                    serves=[],
                    origin="expansion_2hop",
                    score=0.72,
                    reason=f"{hops}-hop from task seeds ({name})",
                )
            )
            seen.add(node.path)
        return budget_select(
            cands,
            view_spec=view_spec,
            repo_root=repo_root,
            budget=budget,
            strategy="locagent",
            corpus=corpus,
            graph=graph,
        )


@register_scoper
class PageRankScoper:
    """Top-k PageRank on the typed uses/calls graph (Aider RepoMap)."""

    name = "pagerank"
    requires: set[str] = {"graph"}

    def scope(
        self,
        view_spec: ViewSpecification,
        repo_root: str,
        budget: int,
        corpus: CleanedCorpus | None = None,
        graph: RepositoryGraph | None = None,
        top_k: int = 16,
    ) -> RepositoryScope:
        corpus, graph = _require(corpus, graph)
        seeds = _task_seed_names(view_spec, graph)
        pers = {name: 10.0 for name in seeds} or None
        ranked = graph.pagerank(personalization=pers)
        ordered = sorted(ranked.items(), key=lambda kv: -kv[1])
        cands: list[ScopeCandidate] = []
        seen: set[str] = set()
        for name, score in ordered[:top_k]:
            node = graph.nodes[name]
            if node.path in seen:
                continue
            cands.append(
                ScopeCandidate(
                    path=node.path,
                    serves=seeds.get(name, []),
                    origin="pagerank_seed",
                    score=min(0.99, 0.5 + score),
                    reason=f"PageRank {score:.4f} ({name})",
                )
            )
            seen.add(node.path)
        return budget_select(
            cands,
            view_spec=view_spec,
            repo_root=repo_root,
            budget=budget,
            strategy="pagerank",
            corpus=corpus,
            graph=graph,
        )


@register_scoper
class GrepScoper:
    """Full-text keyword hits in path or file body (SWE-bench / LocAgent grep baseline)."""

    name = "grep"
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
            raise ValueError("grep scoper requires a cleaned corpus")
        cues = keywords(view_spec)
        root = Path(repo_root)
        cands: list[ScopeCandidate] = []
        for item in corpus.kept:
            hay_path = item.path.lower()
            try:
                body = (root / item.path).read_text(encoding="utf-8", errors="replace")[:80_000].lower()
            except OSError:
                body = ""
            hits = [c for c in cues if c in hay_path or c in body]
            if not hits:
                continue
            serves = [
                ri.id
                for ri in view_spec.required_information
                if any(c in ri.need.lower() or c in hay_path for c in hits)
            ]
            cands.append(
                ScopeCandidate(
                    path=item.path,
                    serves=serves,
                    origin="grep",
                    score=min(1.0, 0.45 + 0.1 * len(hits)),
                    reason="grep keywords: " + ", ".join(hits[:6]),
                )
            )
        return budget_select(
            cands,
            view_spec=view_spec,
            repo_root=repo_root,
            budget=budget,
            strategy="grep",
            corpus=corpus,
            graph=graph,
        )


@register_scoper
class DataflowScoper:
    """Task seeds plus 1-hop on the call graph (sequence / dataflow localization)."""

    name = "dataflow"
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
        seeds = _task_seed_names(view_spec, graph)
        names = set(seeds)
        for seed in list(seeds):
            names |= graph.call_neighbors(seed)
        cands: list[ScopeCandidate] = []
        seen: set[str] = set()
        for name, serves in seeds.items():
            node = graph.nodes[name]
            if node.path in seen:
                continue
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
        for name in names - set(seeds):
            node = graph.nodes.get(name)
            if node is None or node.path in seen:
                continue
            cands.append(
                ScopeCandidate(
                    path=node.path,
                    serves=[],
                    origin="call_1hop",
                    score=0.78,
                    reason=f"call-graph neighbor of a task seed ({name})",
                )
            )
            seen.add(node.path)
        return budget_select(
            cands,
            view_spec=view_spec,
            repo_root=repo_root,
            budget=budget,
            strategy="dataflow",
            corpus=corpus,
            graph=graph,
        )
