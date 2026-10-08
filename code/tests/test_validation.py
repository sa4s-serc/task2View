from task2view.agents.schemas import ArchitectureEvidenceModel, EvidenceAwarePlan, GroundedClaim
from task2view.contracts.models import (
    RepositoryScope,
    SelectedView,
    SpecQuestion,
    ViewElement,
    ViewModel,
    ViewRelation,
    ViewSpecification,
)
from task2view.phase4.graph import RepoNode, RepositoryGraph
from task2view.phase8.validate import validate_view


def _spec() -> ViewSpecification:
    return ViewSpecification(
        request_id="REQ-VAL",
        stakeholder="developer",
        task_summary="seat booking",
        architectural_concerns=["maintainability"],
        selected_view=SelectedView(
            view_type="component_view",
            notation="Component Diagram",
            diagram_language="plantuml",
            diagram_language_rule="viewpoint agent chose plantuml",
            granularity="component_or_service_level",
            purpose="modules",
            viewpoint_id="module-decomposition",
            grain_unit="component",
        ),
        required_information=[],
        architectural_questions=[
            SpecQuestion(id="AQ1", text="Which module owns booking?"),
            SpecQuestion(id="AQ2", text="Which module sends mail?"),
        ],
    )


def test_validation_records_faithfulness_coverage_and_grain():
    graph = RepositoryGraph(
        nodes={
            "Booking": RepoNode(name="Booking", path="Booking.java", layer="src"),
            "Seat": RepoNode(name="Seat", path="Seat.java", layer="src"),
        }
    )
    vm = ViewModel(
        request_id="REQ-VAL",
        view_type="component_view",
        granularity="component_or_service_level",
        elements=[
            ViewElement(id="E1", name="Booking", kind="component"),
            ViewElement(id="E2", name="Seat", kind="class"),
            ViewElement(id="E3", name="Ghost", kind="component"),
        ],
        relations=[
            ViewRelation(id="R1", frm="E1", to="E2", kind="calls", label="reserve"),
        ],
    )
    evidence = ArchitectureEvidenceModel(
        claims=[
            GroundedClaim(
                claim="Booking calls Seat",
                source_element="Booking",
                target_element="Seat",
                relationship="calls",
                evidence=[{"file": "Booking.java"}],
                question_ids=["AQ1"],
            )
        ]
    )
    reconciliation = EvidenceAwarePlan(
        questions=[
            {"id": "AQ1", "support": "supported", "rationale": "Booking.java shows it"},
            {"id": "AQ2", "support": "unsupported", "rationale": "no mailer was found"},
        ]
    )
    cleaned, report = validate_view(
        vm,
        _spec(),
        RepositoryScope(request_id="REQ-VAL", target_view="module-decomposition", scope_strategy="composite"),
        graph,
        "@startuml\n@enduml\n",
        "plantuml",
        evidence=evidence,
        reconciliation=reconciliation,
    )
    names = {el.name for el in cleaned.elements}
    assert names == {"Booking", "Seat"}
    assert any(rel.label == "reserve" for rel in cleaned.relations)
    assert report.semantic["faithfulness"]["dropped_elements"] == ["Ghost"]
    coverage = {row["id"]: row["status"] for row in report.semantic["question_coverage"]}
    assert coverage == {"AQ1": "covered", "AQ2": "unanswered"}
    assert report.semantic["consistency"]["granularity_violations"] == ["Seat is a class in a component view"]
    assert report.semantic["consistency"]["diagram_language_rule"] == "viewpoint agent chose plantuml"
    assert report.verdict == "pass_with_corrections"
