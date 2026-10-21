"""ADR-008: UML 2.5.1 conformance by rules (phase8/uml_check.py), and every view Task2View draws passes it."""

import pytest

from task2view.phase7.notations import MODEL_KINDS, get_renderer
from task2view.phase8.uml_check import check_uml, infer_diagram

from .view_samples import SAMPLES


@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_task2view_drawings_are_uml(model_kind):
    findings, metrics = check_uml(get_renderer("plantuml").render(SAMPLES[model_kind]()).source, model_kind)
    assert not [f for f in findings if f["severity"] == "error"], findings
    assert metrics["uml_diagram"] and metrics["non_uml_symbols"] == 0


def test_non_uml_shapes_and_c4_are_errors():
    src = "@startuml\ncomponent A\ndatabase DB\nA --> DB\n@enduml"
    findings, m = check_uml(src)
    assert m["uml_diagram"] == "component" and any(f["severity"] == "error" and "database" in f["message"] for f in findings)
    assert not any("association" in f["message"] for f in findings)  # components are classifiers: associations are UML
    seq = "@startuml\nparticipant A\nparticipant B\nA ..|> B\n@enduml"
    assert any(f["check"] == "uml: paths" for f in check_uml(seq)[0])  # a realization is not a message
    c4 = "@startuml\n!include <C4/C4_Component>\nComponent(a, \"A\", \"Java\")\n@enduml"
    assert infer_diagram(c4) is None and check_uml(c4)[0][0]["severity"] == "error"


def test_mixing_diagram_types_is_a_warning_and_unknown_stereotypes_are_reported():
    src = "@startuml\nmainframe cmp X\nactor User\ncomponent A <<controller>>\nUser ..> A\n@enduml"
    findings, _ = check_uml(src)
    assert {f["severity"] for f in findings} == {"warning"}
    assert any("«controller»" in f["message"] for f in findings)


@pytest.mark.parametrize("src,diagram", [
    ("@startuml\nparticipant A\nA -> B : call\n@enduml", "sequence"),
    ("@startuml\n[*] --> Open\nOpen --> Closed\n@enduml", "state-machine"),
    ("@startuml\nnode Server\nartifact app.jar\n@enduml", "deployment"),
    ("@startuml\nactor U\nusecase (Book)\nU -- (Book)\n@enduml", "use-case"),
    ("@startuml\nmainframe pkg P\npackage A {\nclass X\n}\n@enduml", "package"),
])
def test_diagram_type_is_inferred(src, diagram):
    assert infer_diagram(src) == diagram
