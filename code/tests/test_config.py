from pathlib import Path

from task2view.config import apply_pipeline_config, load_pipeline_config
from task2view.contracts.models import UserRequest
from task2view.phase3 import SCOPERS
from task2view.phase4 import EXTRACTORS


def test_yaml_config_selects_plugins(tmp_path: Path):
    path = tmp_path / "pipeline.yaml"
    path.write_text(
        "scoper: pagerank\nextractor: ciao\ndiagram_language: mermaid\nskip_critic: true\n"
    )
    raw = UserRequest(code=str(tmp_path), goal="As a developer I need an overview")
    raw = apply_pipeline_config(raw, load_pipeline_config(path))
    assert raw.scope_strategy == "pagerank"
    assert raw.extract_backend == "ciao"
    assert raw.diagram_language == "mermaid"
    assert raw.skip_critic is True
    assert "pagerank" in SCOPERS
    assert "ciao" in EXTRACTORS


def test_cli_values_override_yaml_defaults(tmp_path: Path):
    path = tmp_path / "pipeline.yaml"
    path.write_text("scoper: pagerank\nextractor: ciao\n")
    raw = UserRequest(
        code=str(tmp_path),
        goal="As a developer I need an overview",
        scope_strategy="full",
        extract_backend="gemini",
    )
    raw = apply_pipeline_config(raw, load_pipeline_config(path))
    assert raw.scope_strategy == "full"
    assert raw.extract_backend == "gemini"
