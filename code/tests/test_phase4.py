from pathlib import Path

from task2view.contracts.models import (
    Evidence,
    ViewElement,
    ViewModel,
    ViewRelation,
)
from task2view.phase7 import get_adapter
from task2view.phase5.extract import extract_view
from task2view.phase8.validate import validate_view
from task2view.pipeline import write_result
from tests.support import catalog_scope, complete_extract


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
    from task2view.phase7 import ADAPTERS

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
    result = catalog_scope(GR10, GOAL, stakeholder="Tester", request_id="REQ-001")
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
    result = complete_extract(
        catalog_scope(GR10, GOAL, stakeholder="Tester", request_id="REQ-001", scope_strategy="composite"),
        _fake_generate,
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


def test_ciao_prompt_uses_mapping_rules_not_full_doc():
    from task2view.phase5.extract import ciao_grounding_rules
    from task2view.phase5.extractors import ciao_prompt_template, load_ciao_prompt_json

    body = load_ciao_prompt_json()
    assert "ISO/IEC/IEEE 42010" in body
    assert "Examine every line of source code" not in body
    assert "crucial NO JSON" not in body
    template = ciao_prompt_template()
    filled = template.format(
        view_type="component_view",
        viewpoint_id="module-decomposition",
        grain="VIEWPOINT GRAIN (module-decomposition), unit=component",
        granularity="component_or_service_level",
        purpose="test",
        questions="- AQ1: x",
        required="- RI-1: x",
        gaps="(none)",
        graph="GRAPH",
        files="SOURCE FILES",
        plan="(none)",
        allowed="HomePageGUI, ReportService",
        ciao_grounding=ciao_grounding_rules("module-decomposition"),
    )
    assert "----- BEGIN CIAO prompt.json -----" not in filled
    assert "Examine every line of source code" not in filled
    assert "crucial NO JSON" not in filled
    assert "mapping_rules for module-decomposition" in filled
    assert "Do not use folder or package names" in filled
    assert "Do not invent nodes, interfaces, or relationships" not in filled
    runtime = ciao_grounding_rules("cnc-runtime")
    assert "mapping_rules for cnc-runtime" in runtime
    assert "Do not invent nodes, interfaces, or relationships" in runtime
    assert "exactly one system box" in ciao_grounding_rules("context")
    assert "Do not invent architecture decision records" in ciao_grounding_rules("decision-record")
    assert ciao_grounding_rules("component_view") == ""
    assert ciao_grounding_rules(view_type="deployment_view").startswith(
        "CIAO mapping_rules for allocation-deployment"
    )
    assert "GROUNDABLE FILE STEMS" in filled
    assert "use these as box/lifeline labels" not in filled
    assert "catalog grain" in filled
    assert "VIEWPOINT GRAIN" in filled
    assert "QUESTIONS this view must answer" in filled


def test_extract_archagent_and_ciao_backends(tmp_path: Path):
    for backend in ("archagent", "ciao"):
        captured: dict[str, str] = {}

        def generate(prompt: str, *, model=None, _backend=backend, _cap=captured):
            if "SOURCE FILES" in prompt or "TYPED USES" in prompt:
                _cap["prompt"] = prompt
            return _fake_generate(prompt, model=model)

        result = complete_extract(
            catalog_scope(
                GR10,
                GOAL,
                stakeholder="Tester",
                request_id=f"REQ-{backend}",
                diagram_language="mermaid",
            ),
            generate,
            backend=backend,
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
            assert "BEGIN CIAO prompt.json" not in captured["prompt"]
            assert "Examine every line of source code" not in captured["prompt"]
            assert "CIAO extractor" in captured["prompt"]
            assert "mapping_rules for cnc-runtime" in captured["prompt"]
            assert "SOURCE FILES" in captured["prompt"]
            assert "omitted=0" in captured["prompt"]
            assert "GROUNDABLE FILE STEMS" in captured["prompt"]
        if backend == "archagent":
            assert "not the ArchAgent system" in captured["prompt"]
            assert "static analysis produces an AST-derived reference graph" not in captured["prompt"]
            assert "SCOPED FILE GRAPH" in captured["prompt"] or "filesystem graph" in captured["prompt"].lower()
        write_result(tmp_path / backend, result)
        assert (tmp_path / backend / "architecture_view.mmd").exists()


def test_extract_view_injectable_generate():
    result = catalog_scope(GR10, GOAL, stakeholder="Tester", request_id="REQ-001")
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
    from task2view.phase5.extract import _pack_files

    result = catalog_scope(GR10, GOAL, stakeholder="Tester", request_id="REQ-001")
    packed = _pack_files(str(GR10), result.scope)
    assert "omitted=0" in packed.split("\n", 1)[0]
    for cand in result.scope.candidate_areas:
        assert f"### FILE: {cand.path}" in packed


def test_graph_summary_includes_scoped_types():
    result = catalog_scope(GR10, GOAL, stakeholder="Tester", request_id="REQ-001")
    prefer = []
    for cand in result.scope.candidate_areas:
        prefer.extend(result.graph.path_to_types.get(cand.path, []))
    scoped = {c.path for c in result.scope.candidate_areas}
    text = result.graph.summary(limit=5, prefer=prefer, only_paths=scoped)
    assert "java_ast=" not in text
    assert "javalang" not in text.lower()
    assert "scoped_files=" in text or "parent directory" in text.lower()
    for name in prefer:
        assert name in text
    listed = {line.split()[0] for line in text.splitlines() if "[dir=" in line}
    scoped_names = {
        name for name, node in result.graph.nodes.items() if node.path in scoped
    }
    assert listed <= scoped_names


def test_gate_keeps_datastore_and_resolves_via_symbol():
    from task2view.contracts.models import Evidence, ViewElement, ViewRelation

    result = catalog_scope(GR10, GOAL, stakeholder="Tester", request_id="REQ-001")
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
    result = catalog_scope(GR10, GOAL, stakeholder="Tester", request_id="REQ-001")
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

