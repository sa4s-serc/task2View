from task2view.agents.runtime import AgentRuntime
from task2view.agents.schemas import StakeholderTaskProfile
from task2view.contracts.models import (
    RepositoryScope,
    ScopeCandidate,
    SelectedView,
    SpecQuestion,
    ViewSpecification,
)
from task2view.phase4.plan import plan_repository_analysis, scope_for_plan


def _spec() -> ViewSpecification:
    return ViewSpecification(
        request_id="REQ-PLAN",
        stakeholder="member-of-development-team",
        task_summary="modify seat booking",
        architectural_concerns=["maintainability"],
        selected_view=SelectedView(
            view_type="component_view",
            notation="Component Diagram",
            diagram_language="plantuml",
            granularity="component_or_service_level",
            purpose="modules that own booking",
            viewpoint_id="module-decomposition",
        ),
        required_information=[],
        architectural_questions=[
            SpecQuestion(id="AQ1", text="Which modules own seat booking?", concern="maintainability"),
        ],
    )


def _scope() -> RepositoryScope:
    return RepositoryScope(
        request_id="REQ-PLAN",
        target_view="component_view",
        scope_strategy="composite",
        candidate_areas=[
            ScopeCandidate(
                path="src/booking/SeatBooking.java",
                origin="task_seed",
                score=0.94,
                reason="name match for booking",
            ),
            ScopeCandidate(
                path="src/booking/SeatStore.java",
                origin="expansion_1hop",
                score=0.75,
                reason="1-hop from SeatBooking",
            ),
            ScopeCandidate(
                path="src/common/Application.java",
                origin="centrality_seed",
                score=0.88,
                reason="degree centrality 40",
            ),
        ],
    )


def test_plan_drops_files_that_are_only_highly_connected():
    def generate(prompt: str, *, model=None):
        assert "Repository Analysis Agent" in prompt
        assert "SeatBooking.java" in prompt
        assert "Application.java" not in prompt
        return {
            "analysis_goal": "modules for booking",
            "analysis_tasks": [
                {
                    "id": "AT1",
                    "addresses": ["AQ1"],
                    "goal": "Which modules own seat booking?",
                    "starting_points": ["src/booking/SeatBooking.java", "src/common/Application.java"],
                    "candidate_locations": [
                        "src/booking/SeatBooking.java",
                        "src/booking/SeatStore.java",
                        "src/invented/NotInTheGraph.java",
                    ],
                    "expected_evidence": ["the module that owns booking"],
                }
            ],
        }

    profile = StakeholderTaskProfile(
        stakeholder="developer",
        task="modify seat booking",
        target="seat booking",
        goal="see the modules",
        scope="booking-related code",
        constraints=["do not include the payment area"],
    )
    plan = plan_repository_analysis(profile, _spec(), _scope(), AgentRuntime(generate=generate))
    task = plan.analysis_tasks[0]
    assert task.starting_points == ["src/booking/SeatBooking.java"]
    assert task.candidate_locations == ["src/booking/SeatBooking.java", "src/booking/SeatStore.java"]
    assert plan.target_granularity == "component"
    assert "booking-related code" in plan.constraints
    assert "do not include the payment area" in plan.constraints
    narrowed = scope_for_plan(_scope(), plan)
    assert [c.path for c in narrowed.candidate_areas] == [
        "src/booking/SeatBooking.java",
        "src/booking/SeatStore.java",
    ]


def test_empty_plan_keeps_the_scoper_list_and_says_so():
    def generate(prompt: str, *, model=None):
        return {"analysis_tasks": []}

    spec = _spec()
    spec.architectural_questions = [
        SpecQuestion(id="AQ1", text="Which actors sit outside the boundary?", concern="general"),
    ]
    profile = StakeholderTaskProfile(stakeholder="developer", task="look", target="boundary")
    scope = _scope()
    plan = plan_repository_analysis(profile, spec, scope, AgentRuntime(generate=generate))
    assert plan.analysis_tasks[0].addresses == ["AQ1"]
    assert plan.analysis_tasks[0].candidate_locations == []
    kept = scope_for_plan(scope, plan)
    assert [c.path for c in kept.candidate_areas] == [c.path for c in scope.candidate_areas]
    assert any("scoper list" in item for item in plan.constraints)
