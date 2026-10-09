"""Image rendering: local compilers first, Kroki only when its URL is given."""

import shutil
from pathlib import Path

import pytest

from task2view.phase7 import compile as compile_mod
from task2view.phase7.compile import compile_run_dir, notation_of, parse_formats


def test_parse_formats():
    assert parse_formats("svg, PNG") == ["svg", "png"]
    assert parse_formats("") == ["svg"]
    with pytest.raises(ValueError):
        parse_formats("gif")


def test_notation_from_run_writer_file_names():
    assert notation_of(Path("V1-x/view.puml")) == "plantuml"
    assert notation_of(Path("V1-x/view.mermaid.mmd")) == "mermaid"
    assert notation_of(Path("V1-x/view.c4plantuml.puml")) == "c4plantuml"


def test_no_remote_rendering_without_kroki_url(tmp_path, monkeypatch):
    (tmp_path / "V1-a").mkdir()
    (tmp_path / "V1-a" / "view.d2.d2").write_text("a -> b")
    called = []
    monkeypatch.setattr(compile_mod, "_kroki", lambda *a: called.append(a) or b"<svg/>")
    report = compile_run_dir(tmp_path, formats=["svg"])
    assert report["status"] == "fail" and not called and "kroki-url" in report["errors"][0]
    report = compile_run_dir(tmp_path, formats=["svg"], kroki_url="https://kroki.example")
    assert report["status"] == "ok" and report["files"] == [{"file": "V1-a/view.d2.svg", "backend": "kroki"}]


@pytest.mark.skipif(shutil.which("plantuml") is None, reason="plantuml not installed")
def test_local_plantuml(tmp_path):
    (tmp_path / "V1-a").mkdir()
    (tmp_path / "V1-a" / "view.puml").write_text("@startuml\ncomponent A\n@enduml\n")
    (tmp_path / "V1-a" / "view.json").write_text("{}")
    report = compile_run_dir(tmp_path, formats=["svg"])
    assert report == {"status": "ok", "files": [{"file": "V1-a/view.svg", "backend": "local"}], "errors": []}
