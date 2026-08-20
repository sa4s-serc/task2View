from pathlib import Path

from task2view.contracts.models import UserRequest
from task2view.phase0.clean import clean_repository
from task2view.phase1.intake import normalize_request
from task2view.phase2.selector import identify_view
from task2view.phase3 import build_graph, get_scoper


def _gr10() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data_points" / "progetto_ing_software_gr10-main-English"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("GR10 data point not found")


GR10 = _gr10()
GOAL = (
    "As a Tester, I need to understand how a user registration request is processed "
    "so I can design integration tests for it."
)


def _scope(strategy: str):
    corpus = clean_repository(GR10, request_id="REQ-001")
    spec = identify_view(
        normalize_request(UserRequest(code=str(GR10), goal=GOAL, request_id="REQ-001"))
    )
    graph = build_graph(GR10, corpus)
    scope = get_scoper(strategy).scope(
        spec, str(GR10), 120_000, corpus=corpus, graph=graph
    )
    return corpus, graph, scope


def _paths(scope) -> set[str]:
    return {c.path for c in scope.candidate_areas}


def test_full_keeps_cleaned_corpus():
    corpus, graph, scope = _scope("full")
    assert len(scope.candidate_areas) == corpus.counts["kept"] == 44
    assert graph.nodes
    assert graph.parse_failures == []
    assert "UserRegistrationGUI" in graph.nodes
    assert "PersistenceService" in graph.nodes
    assert graph.has_edge("UserRegistrationGUI", "SystemServicesController")
    assert graph.has_edge("UserRegistrationController", "UserService")
    assert graph.has_edge("UserService", "PersistenceService")


def test_lexical_misses_persistence_and_facade():
    _, _, scope = _scope("lexical")
    paths = _paths(scope)
    assert any("UserRegistration" in p for p in paths)
    assert not any(p.endswith("PersistenceService.java") for p in paths)
    assert not any(p.endswith("SystemServicesController.java") for p in paths)


def test_composite_recovers_registration_facade_and_persistence():
    _, _, scope = _scope("composite")
    names = " ".join(_paths(scope))
    assert "UserRegistrationGUI.java" in names
    assert "UserRegistrationController.java" in names
    assert "SystemServicesController.java" in names
    assert "PersistenceService.java" in names
    origins = {c.origin for c in scope.candidate_areas}
    assert "task_seed" in origins
    assert "centrality_seed" in origins or "layer_seed" in origins
    assert "expansion_1hop" in origins


def test_layer_scoper_includes_database_boundary():
    _, _, scope = _scope("layer")
    assert any(p.endswith("PersistenceService.java") for p in _paths(scope))


def test_locagent_covers_graph1_and_may_expand_further():
    _, _, hop1 = _scope("graph1")
    _, _, hop2 = _scope("locagent")
    assert _paths(hop1) <= _paths(hop2)


def test_pagerank_scoper_includes_high_rank_types():
    _, graph, scope = _scope("pagerank")
    ranked = sorted(graph.pagerank().items(), key=lambda kv: -kv[1])
    top_files = {graph.nodes[name].path for name, _ in ranked[:8]}
    scoped = _paths(scope)
    assert scoped & top_files
    assert any("SystemServicesController.java" in p or "PersistenceService.java" in p for p in scoped)


def test_grep_scoper_hits_registration_sources():
    _, _, scope = _scope("grep")
    paths = _paths(scope)
    assert any("UserRegistration" in p for p in paths)
    assert paths


def test_registered_plugin_names():
    from task2view.cli import _plugin_names

    names = _plugin_names()
    for scoper in ("composite", "graph1", "locagent", "pagerank", "grep", "dataflow", "full"):
        assert scoper in names["scopers"]
    for extractor in ("gemini", "archagent", "ciao"):
        assert extractor in names["extractors"]
    for notation in (
        "plantuml",
        "mermaid",
        "d2",
        "c4plantuml",
        "structurizr",
        "graphviz",
        "nomnoml",
        "excalidraw",
        "bpmn",
    ):
        assert notation in names["notations"]
