from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import (
    ArchitectureEvidenceModel,
    GroundedClaim,
    RepositoryAnalysisPlan,
    StakeholderTaskProfile,
)
from task2view.contracts.models import (
    Evidence,
    SelectedView,
    SpecQuestion,
    ViewElement,
    ViewModel,
    ViewRelation,
    ViewSpecification,
)
from task2view.phase7.generate import generate_view


def _spec() -> ViewSpecification:
    return ViewSpecification(
        request_id="REQ-VIEW",
        stakeholder="developer",
        task_summary="seat booking",
        architectural_concerns=["maintainability"],
        selected_view=SelectedView(
            view_type="component_view",
            notation="Component Diagram",
            diagram_language="plantuml",
            granularity="component_or_service_level",
            purpose="modules that own booking",
            viewpoint_id="module-decomposition",
            grain_unit="component",
        ),
        required_information=[],
        architectural_questions=[SpecQuestion(id="AQ1", text="Which module owns booking?")],
    )


def _current() -> ViewModel:
    return ViewModel(
        request_id="REQ-VIEW",
        view_type="component_view",
        granularity="component_or_service_level",
        elements=[
            ViewElement(
                id="E1",
                name="Seat booking",
                kind="component",
                evidence=Evidence(file="src/booking/SeatBooking.java", symbol="SeatBooking"),
            ),
            ViewElement(
                id="E2",
                name="Reservation store",
                kind="component",
                evidence=Evidence(file="src/booking/SeatStore.java", symbol="SeatStore"),
            ),
        ],
        relations=[
            ViewRelation(id="R1", frm="E1", to="E2", kind="uses"),
        ],
    )


def test_view_agent_keeps_only_recorded_names_and_connections():
    def generate(prompt: str, *, model=None):
        assert "View Generation Agent" in prompt
        assert "PROFILE" in prompt
        assert "QUESTIONS" in prompt
        assert "EVIDENCE" in prompt
        assert "Seat booking" in prompt
        return {
            "elements": [
                {"name": "Seat booking", "kind": "component", "role": "accepts a reservation"},
                {"name": "Reservation store", "kind": "component", "role": "stores it"},
                {"name": "Mailer", "kind": "component", "role": "sends mail"},
            ],
            "relations": [
                {"from": "Seat booking", "to": "Reservation store", "kind": "uses"},
                {"from": "Seat booking", "to": "Mailer", "kind": "calls"},
            ],
            "notes": ["Mailer was not in the evidence"],
        }

    evidence = ArchitectureEvidenceModel(
        elements=["Seat booking", "Reservation store"],
        claims=[
            GroundedClaim(
                claim="Seat booking stores a reservation",
                source_element="Seat booking",
                target_element="Reservation store",
                relationship="uses",
                evidence=[{"file": "src/booking/SeatBooking.java", "symbol": "SeatBooking", "excerpt": "save"}],
                question_ids=["AQ1"],
                analysis_task="AT1",
            )
        ],
    )
    profile = StakeholderTaskProfile(
        stakeholder="developer",
        task="modify booking",
        target="seat booking",
        goal="see the modules",
    )
    view = generate_view(
        profile,
        _spec(),
        RepositoryAnalysisPlan(analysis_tasks=[]),
        evidence,
        _current(),
        ["AQ1 answered"],
        AgentRuntime(generate=generate),
    )
    assert {el.name for el in view.elements} == {"Seat booking", "Reservation store"}
    assert len(view.relations) == 1
    assert view.relations[0].kind == "uses"
    assert view.elements[0].evidence is not None
    assert view.elements[0].evidence.file == "src/booking/SeatBooking.java"
