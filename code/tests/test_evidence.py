from pathlib import Path

from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import AnalysisTask, RepositoryAnalysisPlan
from task2view.contracts.models import (
    RepositoryScope,
    ScopeCandidate,
    SelectedView,
    ViewSpecification,
)
from task2view.phase4.graph import RepositoryGraph
from task2view.phase5.evidence import extract_from_plan


def _spec() -> ViewSpecification:
    return ViewSpecification(
        request_id="REQ-EV",
        stakeholder="developer",
        task_summary="seat booking",
        architectural_concerns=["maintainability"],
        selected_view=SelectedView(
            view_type="component_view",
            notation="Component Diagram",
            diagram_language="plantuml",
            granularity="component_or_service_level",
            purpose="modules",
            viewpoint_id="module-decomposition",
            grain_unit="component",
        ),
        required_information=[],
    )


def test_each_task_is_extracted_alone_and_claims_merge(tmp_path: Path):
    booking = tmp_path / "SeatBooking.java"
    booking.write_text("class SeatBooking { void reserve() {} }\n", encoding="utf-8")
    store = tmp_path / "SeatStore.java"
    store.write_text("class SeatStore { void save() {} }\n", encoding="utf-8")
    seen: list[str] = []

    def generate(prompt: str, *, model=None):
        assert "Evidence Extraction Agent" in prompt
        seen.append(prompt)
        if "SeatBooking.java" in prompt and "SeatStore.java" not in prompt:
            return {
                "claims": [
                    {
                        "claim": "Seat booking accepts a reservation",
                        "source_element": "Seat booking",
                        "evidence": [{"file": str(booking), "symbol": "SeatBooking", "excerpt": "reserve"}],
                        "support_type": "directly_observed",
                    },
                    {
                        "claim": "invented",
                        "source_element": "Mailer",
                        "evidence": [{"file": "src/not/in/task.java", "symbol": "Mailer", "excerpt": "send"}],
                        "support_type": "directly_observed",
                    },
                ]
            }
        return {
            "claims": [
                {
                    "claim": "Seat booking stores a reservation",
                    "source_element": "Seat booking",
                    "target_element": "Reservation store",
                    "relationship": "uses",
                    "evidence": [{"file": str(store), "symbol": "SeatStore", "excerpt": "save"}],
                    "support_type": "directly_observed",
                }
            ]
        }

    plan = RepositoryAnalysisPlan(
        analysis_goal="booking",
        target_view="module-decomposition",
        target_granularity="component",
        constraints=["booking-related code"],
        analysis_tasks=[
            AnalysisTask(
                id="AT1",
                goal="Which module owns booking?",
                addresses=["AQ1"],
                starting_points=[str(booking)],
                candidate_locations=[str(booking)],
                expected_evidence=["the module that owns booking"],
            ),
            AnalysisTask(
                id="AT2",
                goal="Where is the reservation stored?",
                addresses=["AQ2"],
                starting_points=[str(store)],
                candidate_locations=[str(store)],
                expected_evidence=["the store"],
            ),
            AnalysisTask(
                id="AT3",
                goal="Who is notified?",
                addresses=["AQ3"],
                starting_points=[],
                candidate_locations=[],
                expected_evidence=["a notifier"],
            ),
        ],
    )
    scope = RepositoryScope(
        request_id="REQ-EV",
        target_view="component_view",
        scope_strategy="composite",
        candidate_areas=[
            ScopeCandidate(path=str(booking), origin="task_seed", reason="booking"),
            ScopeCandidate(path=str(store), origin="task_seed", reason="store"),
        ],
    )
    evidence, view = extract_from_plan(
        plan,
        _spec(),
        scope,
        RepositoryGraph(),
        str(tmp_path),
        AgentRuntime(generate=generate),
    )
    assert len(seen) == 2
    assert "SeatStore.java" not in seen[0]
    assert "SeatBooking.java" not in seen[1]
    assert [c.source_element for c in evidence.claims] == ["Seat booking", "Seat booking"]
    assert "Mailer" not in evidence.elements
    names = {el.name for el in view.elements}
    assert names == {"Seat booking", "Reservation store"}
    assert view.relations[0].kind == "uses"
    assert any("AT3 unanswered" in note for note in evidence.notes)
