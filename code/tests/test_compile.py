from pathlib import Path

from task2view.phase4.compile import compile_diagram, infer_notation, parse_formats


FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"fake-png"
FAKE_SVG = b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'
FAKE_JPEG = b"\xff\xd8\xffjpeg"


def _fetch(diagram_type, fmt, source, *, url, timeout):
    assert diagram_type == "plantuml"
    assert "@startuml" in source
    assert url.startswith("https://kroki.io")
    if fmt == "svg":
        return FAKE_SVG
    if fmt == "png":
        return FAKE_PNG
    if fmt == "jpeg":
        return FAKE_JPEG
    raise AssertionError(fmt)


def test_parse_formats_aliases_jpg():
    assert parse_formats("svg, png, jpg") == ["svg", "png", "jpeg"]


def test_infer_c4_from_include(tmp_path: Path):
    path = tmp_path / "architecture_view.puml"
    path.write_text("@startuml\n!include <C4/C4_Component>\n@enduml\n")
    assert infer_notation(path) == "c4plantuml"


def test_compile_diagram_writes_svg_png_jpeg(tmp_path: Path):
    report = compile_diagram(
        "@startuml\nA -> B\n@enduml\n",
        "plantuml",
        tmp_path,
        formats=["svg", "png", "jpeg"],
        fetch=_fetch,
    )
    assert report["status"] == "ok"
    assert (tmp_path / "architecture_view.svg").read_bytes() == FAKE_SVG
    assert (tmp_path / "architecture_view.png").read_bytes() == FAKE_PNG
    assert (tmp_path / "architecture_view.jpeg").read_bytes() == FAKE_JPEG
    assert report["files"]["png"] == "architecture_view.png"


def test_compile_records_error_without_raising(tmp_path: Path):
    def boom(*_args, **_kwargs):
        raise RuntimeError("offline")

    report = compile_diagram("x", "plantuml", tmp_path, formats=["png"], fetch=boom)
    assert report["status"] == "fail"
    assert "png" in report["errors"]
    assert not list(tmp_path.glob("*.png"))
