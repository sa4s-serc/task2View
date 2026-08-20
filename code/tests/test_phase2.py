from pathlib import Path

import pytest

from task2view.contracts.models import PipelineError, UserRequest
from task2view.phase1.intake import normalize_request
from task2view.phase2.selector import identify_view

def _gr10() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data_points" / "progetto_ing_software_gr10-main-English"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("GR10 data point not found")


GR10 = _gr10()

RUNNING_TASK = (
    "I need to understand how a user registration request is processed "
    "so I can design integration tests for it."
)


def _spec(**kwargs):
    raw = UserRequest(
        repository=str(GR10),
        stakeholder=kwargs.get("stakeholder", "Tester"),
        task=kwargs.get("task", RUNNING_TASK),
        request_id="REQ-001",
        diagram_language=kwargs.get("diagram_language"),
    )
    return identify_view(normalize_request(raw))


def test_running_example_selects_sequence_view():
    spec = _spec()
    assert spec.selected_view.viewpoint_id == "scenario"
    assert spec.selected_view.view_type == "sequence_view"
    assert spec.selected_view.diagram_language == "plantuml"
    assert spec.selected_view.granularity == "component_or_service_level"
    assert spec.selected_view.notation == "UML Sequence Diagram"
    ids = [item.id for item in spec.required_information]
    assert ids == ["RI-1", "RI-2", "RI-3", "RI-4", "RI-5", "RI-6"]
    assert "user registration" in spec.required_information[0].need
    assert "control-flow" in spec.architectural_concerns
    assert spec.selection_trace is not None
    assert spec.selection_trace.preferred_viewpoints[0] in {"scenario", "control-flow"}


def test_new_contributor_overview_selects_context_or_onboarding():
    spec = _spec(
        stakeholder="new contributor",
        task="I am new to the codebase and need an overview to get started.",
    )
    assert spec.selected_view.viewpoint_id in {"onboarding-path", "context"}
    assert spec.selected_view.view_type in {"component_view", "context_view"}


def test_unknown_notation_is_rejected():
    with pytest.raises(PipelineError, match="Unknown diagram_language"):
        _spec(diagram_language="not-a-notation")
