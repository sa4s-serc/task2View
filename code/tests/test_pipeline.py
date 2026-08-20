from pathlib import Path

from task2view.contracts.models import UserRequest
from task2view.pipeline import run_pipeline, run_through_phase2, write_result, write_run


def _gr10() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data_points" / "progetto_ing_software_gr10-main-English"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("GR10 data point not found")


GR10 = _gr10()


def test_pipeline_writes_three_artifacts(tmp_path: Path):
    corpus, request, spec = run_through_phase2(
        UserRequest(
            code=str(GR10),
            goal="As a Tester, I need to understand how a user registration request is processed so I can design integration tests for it.",
            request_id="REQ-001",
        )
    )
    write_run(tmp_path, corpus, request, spec)
    assert (tmp_path / "cleaned_corpus.json").exists()
    assert (tmp_path / "normalized_request.json").exists()
    assert (tmp_path / "view_specification.json").exists()
    assert corpus.counts["kept"] == 44
    assert spec.request_id == request.request_id == corpus.request_id == "REQ-001"


def test_pipeline_through_scope_without_gemini(tmp_path: Path):
    result = run_pipeline(
        UserRequest(
            code=str(GR10),
            goal="As a Tester, I need to understand how a user registration request is processed so I can design integration tests for it.",
            request_id="REQ-001",
            skip_extract=True,
            scope_strategy="composite",
            legacy=True,
        )
    )
    write_result(tmp_path, result)
    assert (tmp_path / "repository_scope.json").exists()
    assert not (tmp_path / "view_model.json").exists()
    assert result.scope.scope_strategy == "composite"
    assert any("UserRegistration" in c.path for c in result.scope.candidate_areas)
