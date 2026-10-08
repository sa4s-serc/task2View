from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import ArchitectureEvidenceModel, GroundedClaim
from task2view.contracts.models import SelectedView, SpecQuestion, ViewModel, ViewSpecification
from task2view.phase6.reconcile import reconcile_evidence


def _spec() -> ViewSpecification:
    return ViewSpecification(
        request_id="REQ-REC",
        stakeholder="developer",
        task_summary="seat booking",
        architectural_concerns=["maintainability"],
        selected_view=SelectedView(
            view_type="component_view",
            notation="Component Diagram",
            diagram_language="plantuml",
            diagram_language_rule="viewpoint default: plantuml",
            granularity="component_or_service_level",
            purpose="modules",
            viewpoint_id="module-decomposition",
            grain_unit="component",
        ),
        required_information=[],
        architectural_questions=[
            SpecQuestion(id="AQ1", text="Which module owns booking?"),
            SpecQuestion(id="AQ2", text="Which module sends the confirmation?"),
        ],
    )


def test_omitted_question_is_unsupported_and_invented_ids_are_dropped():
    def generate(prompt, *, model=None):
        assert "Need-Evidence Reconciliation Agent" in prompt
        assert "viewpoint default: plantuml" in prompt
        return {
            "questions": [
                {"id": "AQ1", "support": "supported", "rationale": "Booking.java owns it"},
                {"id": "AQ9", "support": "supported", "rationale": "not a real question"},
                {"id": "AQ2", "support": "invented", "rationale": "not a legal level"},
            ],
            "unanswered": [],
            "limitations": ["no confirmation sender"],
            "rationale": "one question is shown",
        }

    evidence = ArchitectureEvidenceModel(
        claims=[
            GroundedClaim(
                claim="Booking owns the request",
                source_element="Booking",
                evidence=[{"file": "Booking.java"}],
                question_ids=["AQ1"],
            )
        ]
    )
    plan = reconcile_evidence(
        _spec(),
        None,
        evidence,
        ViewModel(
            request_id="REQ-REC",
            view_type="component_view",
            granularity="component_or_service_level",
        ),
        AgentRuntime(generate),
    )
    assert [row["id"] for row in plan.questions] == ["AQ1", "AQ2"]
    assert plan.questions[0]["support"] == "supported"
    assert plan.questions[1]["support"] == "unsupported"
    assert plan.unanswered == ["AQ2"]
    assert plan.diagram_language_rule == "viewpoint default: plantuml"
    assert "no confirmation sender" in plan.limitations
