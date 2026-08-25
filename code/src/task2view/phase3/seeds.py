"""Required-information forced seeds for every scoper.

Cues come from the goal and required_information text. Files match by type
name, path, or (for rare cues) file body. Tokens that hit too many files are
skipped so a shared package segment cannot force the whole corpus. No
repository or type names are hard-coded.
"""

from __future__ import annotations

from pathlib import Path

from task2view.contracts.models import CleanedCorpus, ScopeCandidate, ViewSpecification
from task2view.knowledge.loader import KnowledgeBase, load_knowledge
from task2view.phase3.graph import RepositoryGraph
from task2view.phase3.scopers_lexical import keywords

_DEFAULTS = {
    "max_files": 8,
    "max_document_fraction": 0.25,
    "min_token_length": 4,
    "body_chars": 80_000,
    "max_body_hits_per_cue": 3,
}


def _cfg(knowledge: KnowledgeBase | None = None) -> dict:
    knowledge = knowledge or load_knowledge()
    raw = knowledge.view_projection.get("forced_seeds") or {}
    cfg = dict(_DEFAULTS)
    cfg.update({k: v for k, v in raw.items() if k != "extra_stopwords"})
    return cfg


def cue_forms(token: str) -> list[str]:
    """Light inflection so 'notifications' matches NotificationManager."""
    tok = token.casefold()
    forms = [tok]
    if tok.endswith("ies") and len(tok) > 5:
        forms.append(tok[:-3] + "y")
    elif tok.endswith("es") and len(tok) > 5 and not tok.endswith("sses"):
        forms.append(tok[:-2])
    elif tok.endswith("s") and not tok.endswith("ss") and len(tok) > 4:
        forms.append(tok[:-1])
    return list(dict.fromkeys(forms))


def _hay_path(name: str, path: str) -> str:
    return f"{name} {path}".replace("\\", "/").casefold()


def _matches(hay: str, token: str) -> bool:
    return any(form in hay for form in cue_forms(token))


def _ri_ids_for(view_spec: ViewSpecification, hits: list[str], hay: str) -> list[str]:
    serves: list[str] = []
    for ri in view_spec.required_information:
        need = ri.need.casefold()
        if any(_matches(need, h) or _matches(hay, h) for h in hits):
            serves.append(ri.id)
    if serves:
        return serves
    if view_spec.required_information:
        return [view_spec.required_information[0].id]
    return []


def _task_cues(view_spec: ViewSpecification, knowledge: KnowledgeBase) -> list[str]:
    stops = {
        str(x).casefold()
        for x in (knowledge.view_projection.get("forced_seeds") or {}).get("extra_stopwords") or []
    }
    min_len = int(_cfg(knowledge)["min_token_length"])
    return [c for c in keywords(view_spec) if c not in stops and len(c) >= min_len]


def _document_frequency(cue: str, hays: list[str]) -> int:
    return sum(1 for hay in hays if _matches(hay, cue))


def _rare_cues(cues: list[str], hays: list[str], max_fraction: float) -> list[str]:
    n = len(hays) or 1
    rare: list[str] = []
    for cue in cues:
        df = _document_frequency(cue, hays)
        if 0 < df <= max(1, int(n * max_fraction)):
            rare.append(cue)
    return rare


def task_seed_names(
    view_spec: ViewSpecification,
    graph: RepositoryGraph,
    *,
    knowledge: KnowledgeBase | None = None,
) -> dict[str, list[str]]:
    knowledge = knowledge or load_knowledge()
    cues = _task_cues(view_spec, knowledge)
    hits: dict[str, list[str]] = {}
    for name, node in graph.nodes.items():
        hay = _hay_path(name, node.path)
        matched = [c for c in cues if _matches(hay, c)]
        if matched:
            hits[name] = _ri_ids_for(view_spec, matched, hay)
    return hits


def forced_seed_candidates(
    view_spec: ViewSpecification,
    repo_root: str,
    corpus: CleanedCorpus,
    graph: RepositoryGraph | None,
    *,
    knowledge: KnowledgeBase | None = None,
) -> list[ScopeCandidate]:
    """Must-include files for rare goal / required-information cues."""
    knowledge = knowledge or load_knowledge()
    cfg = _cfg(knowledge)
    cues = _task_cues(view_spec, knowledge)
    if not cues:
        return []

    nodes = list(graph.nodes.values()) if graph is not None else []
    path_hays = [_hay_path(n.name, n.path) for n in nodes] or [item.path.casefold() for item in corpus.kept]
    rare = _rare_cues(cues, path_hays, float(cfg["max_document_fraction"]))
    if not rare:
        return []

    by_path: dict[str, ScopeCandidate] = {}
    max_files = int(cfg["max_files"])
    body_limit = int(cfg["body_chars"])
    max_body = int(cfg["max_body_hits_per_cue"])
    root = Path(repo_root)

    def add(path: str, hits: list[str], origin: str, score: float, reason: str, hay: str) -> None:
        prev = by_path.get(path)
        cand = ScopeCandidate(
            path=path,
            serves=_ri_ids_for(view_spec, hits, hay),
            origin=origin,
            score=score,
            reason=reason,
        )
        if prev is None or cand.score > prev.score:
            by_path[path] = cand
        else:
            prev.serves = sorted(set(prev.serves) | set(cand.serves))

    if graph is not None:
        for node in nodes:
            hay = _hay_path(node.name, node.path)
            matched = [c for c in rare if _matches(hay, c)]
            if not matched:
                continue
            add(
                node.path,
                matched,
                "ri_forced",
                0.99,
                "required-information name/path: " + ", ".join(matched[:6]),
                hay,
            )
    else:
        for item in corpus.kept:
            hay = item.path.casefold()
            matched = [c for c in rare if _matches(hay, c)]
            if not matched:
                continue
            add(item.path, matched, "ri_forced", 0.99, "required-information path: " + ", ".join(matched[:6]), hay)

    path_covered = {c.path for c in by_path.values()}
    uncovered = [c for c in rare if _document_frequency(c, path_hays) == 0]
    if uncovered:
        scored: dict[str, list[tuple[int, str, str]]] = {cue: [] for cue in uncovered}
        for item in corpus.kept:
            if item.path in path_covered:
                continue
            try:
                body = (root / item.path).read_text(encoding="utf-8", errors="replace")[:body_limit].casefold()
            except OSError:
                continue
            hay = item.path.casefold() + " " + body
            for cue in uncovered:
                if not _matches(hay, cue):
                    continue
                scored[cue].append((body.count(cue_forms(cue)[0]), item.path, hay))
        for cue, rows in scored.items():
            rows.sort(key=lambda row: (-row[0], row[1]))
            for _count, path, hay in rows[:max_body]:
                add(
                    path,
                    [cue],
                    "ri_forced",
                    0.96,
                    f"required-information body: {cue}",
                    hay,
                )

    ordered = sorted(by_path.values(), key=lambda c: (-c.score, -len(c.serves), c.path))
    return ordered[:max_files]


# Back-compat alias used by existing scopers.
_task_seed_names = task_seed_names
