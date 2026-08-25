from pathlib import Path

from task2view.contracts.models import CleanedFile, CleanedCorpus
from task2view.phase3.graph import build_graph


def test_python_fixture_uses_directories_not_bced(tmp_path: Path):
    (tmp_path / "web").mkdir()
    (tmp_path / "app").mkdir()
    (tmp_path / "db").mkdir()
    (tmp_path / "web" / "pages.py").write_text("from app.services import Services\nServices().run()\n")
    (tmp_path / "app" / "services.py").write_text("from db.store import Store\nclass Services:\n    def run(self):\n        Store().save()\n")
    (tmp_path / "db" / "store.py").write_text("class Store:\n    def save(self):\n        return 1\n")
    corpus = CleanedCorpus(
        request_id="py-1",
        repository=str(tmp_path),
        kept=[
            CleanedFile(path="web/pages.py", language="python", bytes=40),
            CleanedFile(path="app/services.py", language="python", bytes=80),
            CleanedFile(path="db/store.py", language="python", bytes=40),
        ],
    )
    graph = build_graph(tmp_path, corpus)
    assert "pages" in graph.nodes
    assert graph.nodes["pages"].layer == "web"
    assert graph.nodes["services"].layer == "app"
    assert graph.nodes["store"].layer == "db"
    assert "Boundary" not in {n.layer for n in graph.nodes.values()}
    assert "Entity" not in {n.layer for n in graph.nodes.values()}
    assert graph.has_edge("pages", "services")
    assert graph.has_edge("services", "store")
    assert "javalang" not in graph.summary().lower()
