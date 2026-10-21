"""ADR-008: PlantUML is the only renderer; it draws every UML model kind with a frame heading and compiles."""

import shutil
import subprocess

import pytest

from task2view.phase7.notations import MODEL_KINDS, NATIVE, get_renderer, renderers

from .view_samples import SAMPLES

LANGUAGES = sorted(NATIVE)


def test_samples_cover_every_model_kind():
    assert set(SAMPLES) == set(MODEL_KINDS)


def test_every_matrix_language_is_registered():
    assert set(renderers()) == set(NATIVE)


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_renders_every_model_kind(language, model_kind):
    view = SAMPLES[model_kind]()
    result = get_renderer(language).render(view)
    assert result.source.strip()
    assert result.approximated == (model_kind not in NATIVE[language])
    for e in view.content_elements():
        assert e.name in result.source, f"{language}/{model_kind} lost element {e.name}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_responsibilities_inside_elements_and_fragments_kept(language):
    comp = get_renderer(language).render(SAMPLES["uml-component"]())
    assert "charges the gateway" in comp.source
    seq = get_renderer(language).render(SAMPLES["uml-sequence"]())
    assert "order not NEW" in seq.source


@pytest.mark.skipif(shutil.which("plantuml") is None, reason="plantuml not installed")
@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_plantuml_output_compiles(model_kind, tmp_path):
    src = tmp_path / "v.puml"
    src.write_text(get_renderer("plantuml").render(SAMPLES[model_kind]()).source)
    proc = subprocess.run(["plantuml", "-checkonly", str(src)], capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_every_view_has_a_uml_frame_and_no_non_uml_shapes(model_kind):
    source = get_renderer("plantuml").render(SAMPLES[model_kind]()).source
    assert source.splitlines()[1].startswith("mainframe ")
    assert not any(line.strip().startswith(("database ", "cloud ", "rectangle \"Legend", "title ")) for line in source.splitlines())
