from pathlib import Path

import pytest

from task2view.phase1.interpret import interpret_stakeholder_task
from task2view.agents.runtime import AgentRuntime
from task2view.contracts.models import PipelineError
from task2view.knowledge.loader import load_knowledge
from task2view.inputs.repository import resolve_repository


def _gr10() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data_points" / "progetto_ing_software_gr10-main-English"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("GR10 data point not found")


GR10 = _gr10()
DEVELOPER_GOAL = (
    "I need to modify the seat booking functionality and understand the main "
    "system components involved and how they interact."
)
TESTER_GOAL = (
    "I need to understand how a user registration request is processed "
    "so I can design integration tests for it."
)


def test_bind_concerns_follows_the_goal_not_the_role_list():
    knowledge = load_knowledge()
    role = knowledge.resolve_role("software developer")
    concerns = knowledge.bind_concerns(role, DEVELOPER_GOAL)
    assert concerns == ["maintainability"]
    assert "control-flow" not in concerns
    assert "connectivity" not in concerns


def test_tester_registration_does_not_inherit_connectivity():
    knowledge = load_knowledge()
    role = knowledge.resolve_role("Tester")
    concerns = knowledge.bind_concerns(role, TESTER_GOAL)
    assert "control-flow" in concerns
    assert "functional-suitability" in concerns
    assert "connectivity" not in concerns


def test_quiet_goal_keeps_only_the_top_priority_concern():
    knowledge = load_knowledge()
    role = knowledge.resolve_role("Tester")
    assert knowledge.bind_concerns(role, "hello there") == ["functional-suitability"]


def test_interpret_fills_the_profile_and_leaves_concerns_for_phase_2():
    def generate(prompt: str, *, model=None):
        assert "Stakeholder-Task Interpretation Agent" in prompt
        assert "canonical_role" in prompt
        assert "modify" in prompt
        return {
            "stakeholder": "software developer",
            "canonical_role": "member-of-development-team",
            "task": "change seat booking",
            "target": "seat booking",
            "goal": "see the modules that own booking",
            "scope": "booking-related code",
            "constraints": [],
            "concerns": ["deployment"],
            "confidence": 0.8,
        }

    profile = interpret_stakeholder_task(
        DEVELOPER_GOAL,
        AgentRuntime(generate=generate),
    )
    assert profile.canonical_role == "member-of-development-team"
    assert profile.target == "seat booking"
    assert profile.scope == "booking-related code"
    assert profile.concerns == []


def test_resolve_repository_rejects_missing_path():
    with pytest.raises(PipelineError, match="does not exist"):
        resolve_repository("/tmp/no-such-task2view-repo")


def test_resolve_repository_accepts_the_evaluation_repo():
    ref = resolve_repository(str(GR10))
    assert Path(ref.location).is_dir()
    assert ref.name
