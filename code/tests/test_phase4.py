from pathlib import Path

from task2view.contracts.models import (
    Evidence,
    UserRequest,
    ViewElement,
    ViewModel,
    ViewRelation,
)
from task2view.phase4 import get_adapter
from task2view.phase4.extract import extract_view
from task2view.phase4.validate import validate_view
from task2view.pipeline import run_legacy_pipeline, write_result


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


def _fixture_vm() -> ViewModel:
    return ViewModel(
        request_id="REQ-001",
        view_type="sequence_view",
        granularity="component_or_service_level",
        elements=[
            ViewElement(id="E0", name="User", kind="actor", external=True),
            ViewElement(
                id="E1",
                name="UserRegistrationGUI",
                kind="component",
                evidence=Evidence(file="src/main/java/Boundary/UserRegistrationGUI.java", symbol="UserRegistrationGUI"),
            ),
            ViewElement(
                id="E2",
                name="SystemServicesController",
                kind="component",
                evidence=Evidence(
                    file="src/main/java/Control/SystemServicesController.java",
                    symbol="SystemServicesController",
                ),
            ),
            ViewElement(id="E99", name="MadeUpService", kind="component"),
        ],
        relations=[
            ViewRelation(id="R1", frm="E0", to="E1", kind="call", label="submit", order=1),
            ViewRelation(id="R2", frm="E1", to="E2", kind="call", label="registerUser", order=2),
            ViewRelation(id="R3", frm="E1", to="E99", kind="call", label="ghost", order=3),
        ],
    )


def test_plantuml_and_mermaid_emit_sequence():
    vm = _fixture_vm()
    puml = get_adapter("plantuml").emit(vm)
    assert "@startuml" in puml and "@enduml" in puml
    assert "UserRegistrationGUI" in puml
    assert "E1 -> E2: registerUser" in puml
    mmd = get_adapter("mermaid").emit(vm)
    assert mmd.startswith("sequenceDiagram")
    assert "E0->>E1: submit" in mmd


def test_every_registered_notation_emits_source():
    vm = _fixture_vm()
    from task2view.phase4 import ADAPTERS

    markers = {
        "plantuml": "@startuml",
        "c4plantuml": "C4_Component",
        "mermaid": "sequenceDiagram",
        "d2": "->",
        "graphviz": "digraph",
        "structurizr": "workspace",
        "nomnoml": "[",
        "excalidraw": "excalidraw",
        "bpmn": "definitions",
    }
    assert set(ADAPTERS) == set(markers)
    for name, marker in markers.items():
        src = get_adapter(name).emit(vm)
        assert marker in src, name


def test_semantic_gate_drops_unresolved_and_rewrites():
    result = run_legacy_pipeline(
        UserRequest(code=str(GR10), goal=GOAL, request_id="REQ-001", skip_extract=True, legacy=True)
    )
    cleaned, report = validate_view(
        _fixture_vm(),
        result.spec,
        result.scope,
        result.graph,
        get_adapter("plantuml").emit(_fixture_vm()),
        "plantuml",
    )
    names = {e.name for e in cleaned.elements}
    assert "UserRegistrationGUI" in names
    assert "SystemServicesController" in names
    assert "MadeUpService" not in names
    assert report.verdict == "pass_with_corrections"
    assert any(u == "MadeUpService" for u in report.semantic["unresolved_elements"])
    labels = {r.label for r in cleaned.relations}
    assert "ghost" not in labels
    assert "registerUser" in labels


def _fake_generate(prompt: str, *, model=None):
    assert "SOURCE FILES" in prompt
    assert "GRAPH" in prompt
    return {
        "elements": [
            {"id": "E0", "name": "User", "kind": "actor", "external": True},
            {
                "id": "E1",
                "name": "UserRegistrationGUI",
                "kind": "component",
                "evidence": {
                    "file": "src/main/java/Boundary/UserRegistrationGUI.java",
                    "symbol": "UserRegistrationGUI",
                },
            },
            {
                "id": "E2",
                "name": "SystemServicesController",
                "kind": "component",
                "evidence": {
                    "file": "src/main/java/Control/SystemServicesController.java",
                    "symbol": "SystemServicesController",
                },
            },
            {"id": "E3", "name": "HallucinatedMailer", "kind": "component"},
        ],
        "relations": [
            {"id": "R1", "from": "E0", "to": "E1", "kind": "call", "label": "submit", "order": 1},
            {"id": "R2", "from": "E1", "to": "E2", "kind": "call", "label": "registerUser", "order": 2},
            {"id": "R3", "from": "E1", "to": "E3", "kind": "call", "label": "sendWelcomeEmail", "order": 3},
        ],
        "groups": [{"id": "G1", "name": "Boundary", "kind": "layer", "contains": ["E1"]}],
        "unanswered": ["RI-6"],
        "notes": [],
    }


def test_extract_with_mocked_gemini_then_gate(tmp_path: Path):
    result = run_legacy_pipeline(
        UserRequest(
            code=str(GR10),
            goal=GOAL,
            request_id="REQ-001",
            scope_strategy="composite",
            samples=1,
            legacy=True,
        ),
        generate=_fake_generate,
    )
    assert result.view_model is not None
    names = {e.name for e in result.view_model.elements}
    assert "HallucinatedMailer" not in names
    assert "UserRegistrationGUI" in names
    assert result.diagram_source and "@startuml" in result.diagram_source
    assert result.validation is not None
    write_result(tmp_path, result)
    assert (tmp_path / "repository_scope.json").exists()
    assert (tmp_path / "view_model.json").exists()
    assert (tmp_path / "architecture_view.puml").exists()
    assert (tmp_path / "validation_report.json").exists()


def test_extract_archagent_and_ciao_backends(tmp_path: Path):
    for backend in ("archagent", "ciao"):
        result = run_legacy_pipeline(
            UserRequest(
                code=str(GR10),
                goal=GOAL,
                request_id=f"REQ-{backend}",
                extract_backend=backend,
                diagram_language="mermaid",
                legacy=True,
            ),
            generate=_fake_generate,
        )
        assert result.view_model is not None
        assert "UserRegistrationGUI" in {e.name for e in result.view_model.elements}
        assert result.diagram_source and result.diagram_source.startswith("sequenceDiagram")
        write_result(tmp_path / backend, result)
        assert (tmp_path / backend / "architecture_view.mmd").exists()


def test_extract_view_injectable_generate():
    result = run_legacy_pipeline(
        UserRequest(code=str(GR10), goal=GOAL, request_id="REQ-001", skip_extract=True, legacy=True)
    )
    vm = extract_view(
        result.spec,
        result.scope,
        result.graph,
        str(GR10),
        generate=_fake_generate,
    )
    assert any(e.name == "UserRegistrationGUI" for e in vm.elements)
    assert any(e.name == "HallucinatedMailer" for e in vm.elements)
