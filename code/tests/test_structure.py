from task2view.agents.structure import diagnose_structure, ground_view_model, system_label_from_paths
from task2view.contracts.models import (
    Evidence,
    RepositoryScope,
    ScopeCandidate,
    SelectedView,
    ViewElement,
    ViewGroup,
    ViewModel,
    ViewRelation,
    ViewSpecification,
)
from task2view.knowledge.loader import load_knowledge
from task2view.phase3.graph import RepoNode, RepositoryGraph


def _graph() -> RepositoryGraph:
    g = RepositoryGraph()
    g.nodes["Report"] = RepoNode("Report", "src/main/java/Entity/Report.java", "Entity")
    g.nodes["HomePageGUI"] = RepoNode("HomePageGUI", "src/main/java/Boundary/HomePageGUI.java", "Boundary")
    g.nodes["ReportService"] = RepoNode("ReportService", "src/main/java/Control/ReportService.java", "Control")
    g.nodes["InternalNote"] = RepoNode("InternalNote", "src/main/java/Entity/InternalNote.java", "Entity")
    g.uses["HomePageGUI"].add("ReportService")
    g.uses["ReportService"].add("Report")
    g.uses["InternalNote"].add("Report")
    g.calls["HomePageGUI"].add(("ReportService", "loadReports"))
    return g


def _misplaced_view() -> ViewModel:
    return ViewModel(
        request_id="REQ-STRUCT",
        view_type="component_view",
        granularity="component_or_service_level",
        groups=[
            ViewGroup(id="G1", name="Presentation Layer", kind="layer", contains=["E1", "E2"]),
            ViewGroup(id="G2", name="Persistence Layer", kind="layer", contains=["E3"]),
        ],
        elements=[
            ViewElement(
                id="E1", name="Report", kind="class",
                evidence=Evidence(file="src/main/java/Entity/Report.java", symbol="Report"),
            ),
            ViewElement(
                id="E2", name="HomePageGUI", kind="component",
                evidence=Evidence(file="src/main/java/Boundary/HomePageGUI.java", symbol="HomePageGUI"),
            ),
            ViewElement(
                id="E3", name="ReportService", kind="component",
                evidence=Evidence(file="src/main/java/Control/ReportService.java", symbol="ReportService"),
            ),
        ],
        relations=[],
    )


def _spec(view_type: str, viewpoint_id: str = "module-decomposition") -> ViewSpecification:
    return ViewSpecification(
        request_id="REQ-STRUCT",
        stakeholder="current-and-future-architect",
        task_summary="review organization",
        architectural_concerns=["maintainability"],
        selected_view=SelectedView(
            view_type=view_type,
            notation="Component Diagram",
            diagram_language="plantuml",
            granularity="component_or_service_level",
            purpose="structure",
            viewpoint_id=viewpoint_id,
        ),
        required_information=[],
    )


def test_diagnose_flags_wrong_packages():
    diag = diagnose_structure(_misplaced_view(), _graph())
    misplaced = {row["element"] for row in diag["misplaced_groups"]}
    assert "Report" in misplaced
    assert "ReportService" in misplaced


def test_grounding_keeps_component_names_and_fills_owner_uses():
    grounded, report = ground_view_model(_misplaced_view(), _graph(), _spec("component_view"))
    names = {e.name for e in grounded.elements}
    assert names == {"Report", "HomePageGUI", "ReportService"}
    assert report["view_unit"] == "component"
    by_id = {e.id: e.name for e in grounded.elements}
    pairs = {(by_id[r.frm], by_id[r.to]) for r in grounded.relations}
    assert ("HomePageGUI", "ReportService") in pairs
    assert ("ReportService", "Report") in pairs


def test_component_view_does_not_collapse_to_packages():
    vm = _misplaced_view()
    vm.elements.append(
        ViewElement(
            id="E4",
            name="InternalNote",
            kind="class",
            evidence=Evidence(file="src/main/java/Entity/InternalNote.java", symbol="InternalNote"),
        )
    )
    grounded, report = ground_view_model(vm, _graph(), _spec("component_view"))
    names = {e.name for e in grounded.elements}
    assert "InternalNote" in names
    assert "HomePageGUI" in names
    assert "Boundary" not in names
    assert report["view_unit"] == "component"


def test_component_view_keeps_responsibility_names():
    g = _graph()
    vm = ViewModel(
        request_id="REQ-MESH",
        view_type="component_view",
        granularity="component_or_service_level",
        elements=[
            ViewElement(
                id="E1", name="Report intake", kind="component",
                evidence=Evidence(file="src/main/java/Boundary/HomePageGUI.java", symbol="HomePageGUI"),
            ),
            ViewElement(
                id="E2", name="Report application", kind="component",
                evidence=Evidence(file="src/main/java/Control/ReportService.java", symbol="ReportService"),
            ),
            ViewElement(
                id="E3", name="Report store", kind="component",
                evidence=Evidence(file="src/main/java/Entity/Report.java", symbol="Report"),
            ),
        ],
        relations=[],
    )
    grounded, report = ground_view_model(vm, g, _spec("component_view"))
    names = {e.name for e in grounded.elements}
    assert names == {"Report intake", "Report application", "Report store"}
    by_id = {e.id: e.name for e in grounded.elements}
    pairs = {(by_id[r.frm], by_id[r.to]) for r in grounded.relations}
    assert ("Report intake", "Report application") in pairs
    assert ("Report application", "Report store") in pairs
    assert report["view_unit"] == "component"


def test_sequence_view_keeps_component_participants():
    vm = _misplaced_view()
    vm.view_type = "sequence_view"
    vm.relations = [
        ViewRelation(id="R1", frm="E2", to="E3", kind="call", label="loadReports", order=1),
    ]
    grounded, report = ground_view_model(vm, _graph(), _spec("sequence_view", "scenario"))
    assert report["view_unit"] == "component"
    names = {e.name for e in grounded.elements}
    assert "HomePageGUI" in names
    assert "ReportService" in names
    by_id = {e.id: e.name for e in grounded.elements}
    pairs = {(by_id[r.frm], by_id[r.to]) for r in grounded.relations}
    assert ("HomePageGUI", "ReportService") in pairs


def test_class_view_inserts_type_edges():
    vm = _misplaced_view()
    vm.view_type = "class_view"
    vm.elements.append(
        ViewElement(
            id="E4",
            name="InternalNote",
            kind="class",
            evidence=Evidence(file="src/main/java/Entity/InternalNote.java", symbol="InternalNote"),
        )
    )
    grounded, report = ground_view_model(vm, _graph(), _spec("class_view", "data-model"))
    by_id = {e.id: e.name for e in grounded.elements}
    pairs = {(by_id[r.frm], by_id[r.to]) for r in grounded.relations}
    assert ("InternalNote", "Report") in pairs
    assert report["view_unit"] == "type"
    assert report["edge_insertion"] == "all_selected"


def test_context_view_adds_system_and_directory_structure():
    vm = ViewModel(
        request_id="REQ-CTX",
        view_type="context_view",
        granularity="system_or_context_level",
        elements=[
            ViewElement(id="E1", name="Citizen", kind="actor", external=True),
            ViewElement(id="E2", name="Operator", kind="actor", external=True),
        ],
        relations=[],
    )
    spec = _spec("context_view", "context")
    spec.task_summary = "identify users and system structure"
    scope = RepositoryScope(
        request_id="REQ-CTX",
        target_view="context_view",
        scope_strategy="pagerank",
        candidate_areas=[
            ScopeCandidate(path="src/main/java/Boundary/HomePageGUI.java", serves=[], origin="seed", score=1.0),
            ScopeCandidate(path="src/main/java/Control/ReportService.java", serves=[], origin="seed", score=1.0),
            ScopeCandidate(path="src/main/java/Entity/Report.java", serves=[], origin="seed", score=1.0),
        ],
    )
    grounded, _report = ground_view_model(vm, _graph(), spec, scope=scope)
    kinds = {e.kind for e in grounded.elements}
    names = {e.name for e in grounded.elements}
    assert kinds <= {"actor", "system"}
    assert "Citizen" in names and "Operator" in names
    assert any(e.kind == "system" for e in grounded.elements)
    assert "HomePageGUI" not in names
    by_id = {e.id: e for e in grounded.elements}
    system = next(e for e in grounded.elements if e.kind == "system")
    actor_links = {
        (by_id[r.frm].name, by_id[r.to].name)
        for r in grounded.relations
        if by_id[r.frm].kind == "actor"
    }
    assert ("Citizen", system.name) in actor_links
    assert ("Operator", system.name) in actor_links


def test_system_label_uses_source_root_not_layout_noise():
    kb = load_knowledge()
    label = system_label_from_paths(
        [
            "src/main/java/com/acme/ledger/Foo.java",
            "src/main/java/com/acme/ledger/Bar.java",
        ],
        kb,
    )
    assert label == "ledger"
    assert label.casefold() not in {"src", "main", "java"}


def test_retarget_behavioural_view_when_questions_are_structural():
    from task2view.agents.phase3_viewpoint import retarget_if_structural
    from task2view.agents.schemas import ArchitecturalQuestion, PlannedView, QuestionSet, StakeholderTaskProfile

    kb = load_knowledge()
    planned = [
        PlannedView(
            id="V1",
            viewpoint_id="scenario",
            view_type="sequence_view",
            required_evidence=["containment", "responsibilities"],
        )
    ]
    questions = QuestionSet(
        questions=[
            ArchitecturalQuestion(id="AQ1", text="What is the package hierarchy for this feature?"),
        ]
    )
    profile = StakeholderTaskProfile(
        stakeholder="developer",
        canonical_role="member-of-development-team",
        task="understand module responsibilities and structure",
        source_goal="I need to understand the organization of the modules",
    )
    notes = retarget_if_structural(planned, questions, kb, profile, None)
    assert planned[0].viewpoint_id == "module-decomposition"
    assert planned[0].view_type == "component_view"
    assert notes


def test_module_kind_with_file_evidence_keeps_published_name():
    g = RepositoryGraph()
    g.nodes["Login"] = RepoNode(
        "Login", "src/main/java/it/acme/app/boundary/Swing/Login.java", "Swing"
    )
    g.nodes["Facade"] = RepoNode(
        "Facade", "src/main/java/it/acme/app/controller/Facade.java", "controller"
    )
    g.uses["Login"].add("Facade")
    vm = ViewModel(
        request_id="REQ-NS",
        view_type="component_view",
        granularity="component_or_service_level",
        elements=[
            ViewElement(
                id="E1", name="Booking UI", kind="module",
                evidence=Evidence(file="src/main/java/it/acme/app/boundary/Swing/Login.java", symbol="Login"),
            ),
            ViewElement(
                id="E2", name="Booking application", kind="module",
                evidence=Evidence(file="src/main/java/it/acme/app/controller/Facade.java", symbol="Facade"),
            ),
        ],
        relations=[],
    )
    grounded, report = ground_view_model(vm, g, _spec("component_view"))
    names = {e.name for e in grounded.elements}
    assert names == {"Booking UI", "Booking application"}
    by_id = {e.id: e.name for e in grounded.elements}
    pairs = {(by_id[r.frm], by_id[r.to]) for r in grounded.relations}
    assert ("Booking UI", "Booking application") in pairs
    assert report["view_unit"] == "component"


def test_keep_sequence_when_questions_are_behavioural():
    from task2view.agents.phase3_viewpoint import retarget_if_structural
    from task2view.agents.schemas import ArchitecturalQuestion, PlannedView, QuestionSet, StakeholderTaskProfile

    kb = load_knowledge()
    planned = [
        PlannedView(
            id="V1",
            viewpoint_id="scenario",
            view_type="sequence_view",
            required_evidence=["call chain"],
        )
    ]
    questions = QuestionSet(
        questions=[
            ArchitecturalQuestion(id="AQ1", text="What is the execution order when a request is processed?"),
        ]
    )
    profile = StakeholderTaskProfile(
        stakeholder="tester",
        canonical_role="tester-and-integrator",
        task="how a request is processed",
        source_goal="I need to understand how a user registration request is processed",
    )
    notes = retarget_if_structural(planned, questions, kb, profile, None)
    assert planned[0].viewpoint_id == "scenario"
    assert notes == []


def test_keep_scenario_when_task_cues_prefer_behaviour():
    from task2view.agents.phase3_viewpoint import retarget_if_structural
    from task2view.agents.schemas import ArchitecturalQuestion, PlannedView, QuestionSet, StakeholderTaskProfile

    kb = load_knowledge()
    planned = [
        PlannedView(id="V1", viewpoint_id="scenario", view_type="sequence_view")
    ]
    questions = QuestionSet(
        questions=[
            ArchitecturalQuestion(
                id="AQ1",
                text="Which components participate in registration and how do they interact?",
            )
        ]
    )
    profile = StakeholderTaskProfile(
        stakeholder="tester",
        canonical_role="tester-and-integrator",
        task="test user registration",
        source_goal=(
            "I am an integration tester. I need to test the user registration "
            "functionality and understand which system components are involved "
            "and how they interact."
        ),
    )
    notes = retarget_if_structural(planned, questions, kb, profile, None)
    assert planned[0].viewpoint_id == "scenario"
    assert notes == []


def test_retarget_on_structural_behavioural_tie():
    from task2view.agents.phase3_viewpoint import retarget_if_structural
    from task2view.agents.schemas import ArchitecturalQuestion, PlannedView, QuestionSet, StakeholderTaskProfile

    kb = load_knowledge()
    planned = [
        PlannedView(id="V1", viewpoint_id="scenario", view_type="sequence_view")
    ]
    questions = QuestionSet(questions=[ArchitecturalQuestion(id="AQ1", text="Which components participate?")])
    profile = StakeholderTaskProfile(
        stakeholder="tester",
        canonical_role="tester-and-integrator",
        task="understand component responsibilities",
        source_goal="understand the main components involved, their responsibilities, and how they interact when a new user creates an account",
    )
    notes = retarget_if_structural(planned, questions, kb, profile, None)
    assert planned[0].viewpoint_id == "module-decomposition"
    assert notes


def test_questions_match_viewpoint_grain():
    from task2view.agents.phase2_questions import _keep_question

    assert not _keep_question(
        "Which specific classes own booking?",
        allow_behavioural=False,
        allow_types=False,
    )
    assert not _keep_question(
        "What is the exact call chain from the API?",
        allow_behavioural=False,
        allow_types=False,
    )
    assert _keep_question(
        "What is the exact call chain from the API?",
        allow_behavioural=True,
        allow_types=False,
    )
    assert _keep_question(
        "Which persistent entities store a report?",
        allow_behavioural=False,
        allow_types=True,
    )
    assert not _keep_question(
        "Which persistent entities store a report?",
        allow_behavioural=False,
        allow_types=False,
    )
    assert _keep_question(
        "Which components participate in booking?",
        allow_behavioural=False,
        allow_types=False,
    )


def test_viewpoint_purpose_drops_classes():
    from task2view.agents.phase3_viewpoint import _sanitize_purpose
    from task2view.agents.schemas import PlannedView, StakeholderTaskProfile

    kb = load_knowledge()
    view = PlannedView(
        id="V1",
        viewpoint_id="module-decomposition",
        view_type="component_view",
        purpose="Identify the top-level module and specific classes owning seat booking",
    )
    profile = StakeholderTaskProfile(
        stakeholder="developer",
        canonical_role="member-of-development-team",
        task="modify seat booking",
        target="seat booking",
    )
    note = _sanitize_purpose(view, kb, profile)
    assert note
    assert "specific classes" not in view.purpose.casefold()
    assert "seat booking" in view.purpose.casefold()


def test_data_model_purpose_may_mention_entities():
    from task2view.agents.phase3_viewpoint import _sanitize_purpose
    from task2view.agents.schemas import PlannedView, StakeholderTaskProfile

    kb = load_knowledge()
    view = PlannedView(
        id="V1",
        viewpoint_id="data-model",
        view_type="class_view",
        purpose="Show persistent entities that store a municipal report",
    )
    profile = StakeholderTaskProfile(
        stakeholder="analyst",
        canonical_role="analyst",
        task="inspect the report schema",
        target="report schema",
    )
    assert _sanitize_purpose(view, kb, profile) is None
    assert "entities" in view.purpose.casefold()



