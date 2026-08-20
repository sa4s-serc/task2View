from pathlib import Path

import pytest

from task2view.contracts.models import PipelineError, UserRequest
from task2view.phase1.intake import normalize_request

def _gr10() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data_points" / "progetto_ing_software_gr10-main-English"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("GR10 data point not found")


GR10 = _gr10()


def test_phase1_parses_goal_statement():
    request = normalize_request(
        UserRequest(
            code=str(GR10),
            goal="As a Tester, I need to understand how a user registration request is processed so I can design integration tests for it.",
            request_id="REQ-001",
        )
    )
    assert request.request_id == "REQ-001"
    assert request.stakeholder.role == "tester-and-integrator"
    assert request.stakeholder.original_label == "Tester"
    assert request.task.description.startswith("I need to understand")
    assert "As a Tester" in request.goal
    assert Path(request.repository.location).is_dir()


def test_phase1_parses_i_am_a_role_with_period():
    request = normalize_request(
        UserRequest(
            code=str(GR10),
            goal="I am a software developer. I need to modify the seat booking functionality and understand the main system components involved and how they interact.",
            request_id="REQ-IS-001",
        )
    )
    assert request.stakeholder.role == "member-of-development-team"
    assert request.stakeholder.original_label == "software developer"
    assert request.task.description.startswith("I need to modify")


def test_phase1_split_form_still_works():
    request = normalize_request(
        UserRequest(
            repository=str(GR10),
            stakeholder="Tester",
            task="I need to understand how a user registration request is processed so I can design integration tests for it.",
            request_id="REQ-001",
        )
    )
    assert request.stakeholder.role == "tester-and-integrator"
    assert request.task.description.startswith("I need to understand")


def test_phase1_rejects_missing_repo():
    with pytest.raises(PipelineError, match="does not exist"):
        normalize_request(
            UserRequest(
                repository="/tmp/no-such-task2view-repo",
                stakeholder="tester",
                task="anything non empty",
            )
        )


def test_phase1_rejects_goal_without_role():
    with pytest.raises(PipelineError, match="must name a stakeholder role"):
        normalize_request(
            UserRequest(
                code=str(GR10),
                goal="Understand how registration works",
            )
        )


def test_phase1_rejects_unknown_role():
    with pytest.raises(PipelineError, match="Unknown stakeholder"):
        normalize_request(
            UserRequest(
                repository=str(GR10),
                stakeholder="wizard",
                task="anything non empty",
            )
        )
