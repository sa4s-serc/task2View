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
    if "Completeness Critic" in prompt:
        return {"add": [], "notes": []}
    assert "SOURCE FILES" in prompt
    assert "GRAPH" in prompt
    return {
        "elements": [
            {"id": "E0", "name": "User", "kind": "actor", "external": True},
            {
                "id": "E1",
                "name": "Registration UI",
                "kind": "component",
                "role": "Accepts registration requests",
                "evidence": {
                    "file": "src/main/java/Boundary/UserRegistrationGUI.java",
                    "symbol": "UserRegistrationGUI",
                },
            },
            {
                "id": "E2",
                "name": "Registration service",
                "kind": "component",
                "role": "Creates the user account",
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
    assert "Registration UI" in names
    assert "Registration service" in names
    assert "UserRegistrationGUI" not in names
    assert result.diagram_source and "@startuml" in result.diagram_source
    assert result.validation is not None
    write_result(tmp_path, result)
    assert (tmp_path / "repository_scope.json").exists()
    assert (tmp_path / "view_model.json").exists()
    assert (tmp_path / "architecture_view.puml").exists()
    assert (tmp_path / "validation_report.json").exists()


def test_ciao_prompt_inlines_verbatim_prompt_json():
    from task2view.phase4.extractors import ciao_prompt_template, load_ciao_prompt_json

    body = load_ciao_prompt_json()
    assert "ISO/IEC/IEEE 42010" in body
    assert "Do not invent actors, use cases, or relations not present in the repository." in body
    template = ciao_prompt_template()
    filled = template.format(
        view_type="component_view",
        viewpoint_id="module-decomposition",
        grain="VIEWPOINT GRAIN (module-decomposition), unit=component",
        granularity="component_or_service_level",
        purpose="test",
        required="- AQ1: x",
        graph="GRAPH",
        files="SOURCE FILES",
        allowed="HomePageGUI, ReportService",
    )
    assert "----- BEGIN CIAO prompt.json -----" in filled
    assert "ISO/IEC/IEEE 42010" in filled
    assert "grounding_policy" in filled
    assert "OVERRIDE" in filled
    assert "Ignore markdown" in filled
    assert "You follow CIAO grounding rules from CIAO-system/prompt.json" not in filled
    assert "static analysis produces an AST-derived reference graph" not in filled
    assert "evidence.symbol is optional" in filled
    assert "catalog grain" in filled
    assert "VIEWPOINT GRAIN" in filled
    assert "Every non-external element must have evidence.file and evidence.symbol" not in filled
    assert "Emit a relation for every uses/calls edge" not in filled


def test_extract_archagent_and_ciao_backends(tmp_path: Path):
    for backend in ("archagent", "ciao"):
        captured: dict[str, str] = {}

        def generate(prompt: str, *, model=None, _backend=backend, _cap=captured):
            if "SOURCE FILES" in prompt or "TYPED USES" in prompt:
                _cap["prompt"] = prompt
            return _fake_generate(prompt, model=model)

        result = run_legacy_pipeline(
            UserRequest(
                code=str(GR10),
                goal=GOAL,
                request_id=f"REQ-{backend}",
                extract_backend=backend,
                diagram_language="mermaid",
                legacy=True,
            ),
            generate=generate,
        )
        assert result.view_model is not None
        names = {e.name for e in result.view_model.elements}
        assert "UserRegistrationGUI" not in names
        assert "Registration UI" in names
        assert "Registration service" in names
        assert result.diagram_source and (
            result.diagram_source.startswith("flowchart")
            or "Registration UI" in result.diagram_source
            or "sequenceDiagram" in result.diagram_source
        )
        if backend == "ciao":
            assert "BEGIN CIAO prompt.json" in captured["prompt"]
            assert "OVERRIDE" in captured["prompt"]
            assert "ISO/IEC/IEEE 42010" in captured["prompt"]
            assert "SOURCE FILES" in captured["prompt"]
            assert "omitted=0" in captured["prompt"]
        if backend == "archagent":
            assert "not the ArchAgent system" in captured["prompt"]
            assert "static analysis produces an AST-derived reference graph" not in captured["prompt"]
            assert "FILE/DIRECTORY GRAPH" in captured["prompt"] or "filesystem graph" in captured["prompt"].lower()
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
    assert any(e.name == "Registration UI" for e in vm.elements)
    assert any(e.name == "HallucinatedMailer" for e in vm.elements)


def test_pack_files_never_omits_scoped_paths(tmp_path: Path):
    from task2view.phase4.extract import _pack_files

    result = run_legacy_pipeline(
        UserRequest(code=str(GR10), goal=GOAL, request_id="REQ-001", skip_extract=True, legacy=True)
    )
    packed = _pack_files(str(GR10), result.scope)
    assert "omitted=0" in packed.split("\n", 1)[0]
    for cand in result.scope.candidate_areas:
        assert f"### FILE: {cand.path}" in packed


def test_graph_summary_includes_scoped_types():
    result = run_legacy_pipeline(
        UserRequest(code=str(GR10), goal=GOAL, request_id="REQ-001", skip_extract=True, legacy=True)
    )
    prefer = []
    for cand in result.scope.candidate_areas:
        prefer.extend(result.graph.path_to_types.get(cand.path, []))
    text = result.graph.summary(limit=5, prefer=prefer)
    assert "java_ast=" not in text
    assert "javalang" not in text.lower()
    assert "files=" in text or "parent directory" in text.lower()
    for name in prefer:
        assert name in text


def test_gate_keeps_datastore_and_resolves_via_symbol():
    from task2view.contracts.models import Evidence, ViewElement, ViewRelation

    result = run_legacy_pipeline(
        UserRequest(code=str(GR10), goal=GOAL, request_id="REQ-001", skip_extract=True, legacy=True)
    )
    vm = ViewModel(
        request_id="REQ-001",
        view_type="deployment_view",
        granularity="component_or_service_level",
        elements=[
            ViewElement(id="E1", name="App", kind="component", evidence=Evidence(symbol="UserRegistrationGUI")),
            ViewElement(id="E2", name="Relational Database Engine", kind="datastore"),
            ViewElement(id="E3", name="MadeUpService", kind="component"),
        ],
        relations=[
            ViewRelation(id="R1", frm="E1", to="E2", kind="depends", label="JDBC"),
            ViewRelation(id="R2", frm="E1", to="E3", kind="call", label="ghost"),
        ],
    )
    cleaned, report = validate_view(
        vm, result.spec, result.scope, result.graph, "@startuml\n@enduml\n", "plantuml"
    )
    names = {e.name for e in cleaned.elements}
    assert "App" in names
    assert "UserRegistrationGUI" not in names
    assert "Relational Database Engine" in names
    assert "MadeUpService" not in names
    assert any(r.label == "JDBC" for r in cleaned.relations)
    assert not any(r.label == "ghost" for r in cleaned.relations)
    assert report.verdict == "pass_with_corrections"


def test_gate_keeps_system_boundary():
    result = run_legacy_pipeline(
        UserRequest(code=str(GR10), goal=GOAL, request_id="REQ-001", skip_extract=True, legacy=True)
    )
    vm = ViewModel(
        request_id="REQ-001",
        view_type="context_view",
        granularity="system_or_context_level",
        elements=[
            ViewElement(id="E1", name="Citizen", kind="actor", external=True),
            ViewElement(id="E2", name="MunicipalReports", kind="system", support="inferred"),
            ViewElement(id="E3", name="MadeUpService", kind="component"),
        ],
        relations=[
            ViewRelation(id="R1", frm="E1", to="E2", kind="uses"),
        ],
    )
    cleaned, _report = validate_view(
        vm, result.spec, result.scope, result.graph, "@startuml\n@enduml\n", "plantuml"
    )
    names = {e.name for e in cleaned.elements}
    kinds = {e.kind for e in cleaned.elements}
    assert "Citizen" in names
    assert "MunicipalReports" in names
    assert "system" in kinds
    assert "MadeUpService" not in names
    assert any(r.frm == "E1" and r.to == "E2" for r in cleaned.relations)

