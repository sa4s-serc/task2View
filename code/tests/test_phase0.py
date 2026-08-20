from pathlib import Path

from task2view.phase0.clean import clean_repository

def _gr10() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data_points" / "progetto_ing_software_gr10-main-English"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("GR10 data point not found")


GR10 = _gr10()


def test_phase0_keeps_only_java_source():
    corpus = clean_repository(GR10, request_id="REQ-001")
    assert corpus.counts["kept"] == 44
    assert corpus.counts["languages"] == {"java": 44}
    assert all(item.path.endswith(".java") for item in corpus.kept)
    dropped_paths = {item.path for item in corpus.dropped}
    assert any(p.endswith(".vpp") for p in dropped_paths)
    assert any(p.endswith(".png") for p in dropped_paths)
    assert any(p.endswith(".md") for p in dropped_paths)
    assert "pom.xml" in dropped_paths or any(p.endswith("pom.xml") for p in dropped_paths)
    assert not any(item.path.endswith(".java") for item in corpus.dropped)
