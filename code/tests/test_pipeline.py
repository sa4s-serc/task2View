from pathlib import Path

from task2view.pipeline import write_result, write_run
from tests.support import catalog_scope


def _gr10() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data" / "progetto_ing_software_gr10-main-English"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("GR10 data point not found")


GR10 = _gr10()
GOAL = (
    "As a Tester, I need to understand how a user registration request is processed "
    "so I can design integration tests for it."
)


def test_pipeline_writes_three_artifacts(tmp_path: Path):
    result = catalog_scope(GR10, GOAL, stakeholder="Tester", request_id="REQ-001")
    write_run(tmp_path, result.corpus, result.request, result.spec)
    assert (tmp_path / "cleaned_corpus.json").exists()
    assert (tmp_path / "normalized_request.json").exists()
    assert (tmp_path / "view_specification.json").exists()
    assert result.corpus.counts["kept"] == 44
    assert result.spec.request_id == result.request.request_id == result.corpus.request_id == "REQ-001"


def test_pipeline_through_scope_without_gemini(tmp_path: Path):
    result = catalog_scope(
        GR10,
        GOAL,
        stakeholder="Tester",
        request_id="REQ-001",
        scope_strategy="composite",
    )
    write_result(tmp_path, result)
    assert (tmp_path / "repository_scope.json").exists()
    assert not (tmp_path / "view_model.json").exists()
    assert result.scope.scope_strategy == "composite"
    assert any("UserRegistration" in c.path for c in result.scope.candidate_areas)
