"""Shared helpers for turning candidate paths into RepositoryScope."""

from __future__ import annotations

from task2view.contracts.models import (
    CleanedCorpus,
    RepositoryScope,
    ScopeCandidate,
    ViewSpecification,
)
from task2view.phase3.graph import RepositoryGraph
from task2view.phase3.tokens import file_tokens


def budget_select(
    candidates: list[ScopeCandidate],
    *,
    view_spec: ViewSpecification,
    repo_root: str,
    budget: int,
    strategy: str,
    corpus: CleanedCorpus,
    graph: RepositoryGraph | None,
) -> RepositoryScope:
    best: dict[str, ScopeCandidate] = {}
    for cand in candidates:
        prev = best.get(cand.path)
        if prev is None or cand.score > prev.score:
            best[cand.path] = cand
    ordered = sorted(best.values(), key=lambda c: (-c.score, c.path))
    selected: list[ScopeCandidate] = []
    tokens = 0
    excluded = 0
    for cand in ordered:
        cost = file_tokens(repo_root, cand.path)
        if selected and tokens + cost > budget:
            excluded += 1
            continue
        selected.append(cand)
        tokens += cost
    served: set[str] = set()
    for cand in selected:
        served.update(cand.serves)
    all_ri = [item.id for item in view_spec.required_information]
    graph_meta = {"nodes": 0, "edges": 0, "parse_failures": []}
    if graph is not None:
        graph_meta = {
            "nodes": len(graph.nodes),
            "edges": sum(len(v) for v in graph.uses.values()),
            "parse_failures": list(graph.parse_failures),
        }
    return RepositoryScope(
        request_id=view_spec.request_id,
        target_view=view_spec.selected_view.view_type,
        scope_strategy=strategy,
        graph=graph_meta,
        candidate_areas=selected,
        scope_constraints={
            "expansion_depth": 1,
            "token_budget": budget,
            "tokens_selected": tokens,
            "budget_forced_exclusions": excluded,
            "corpus_kept": corpus.counts.get("kept", len(corpus.kept)),
        },
        coverage_report={
            "required_information_served": [i for i in all_ri if i in served],
            "required_information_unserved": [i for i in all_ri if i not in served],
        },
    )
