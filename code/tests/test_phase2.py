from pathlib import Path

import pytest

from task2view.contracts.models import PipelineError
from tests.support import catalog_spec


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
    _request, spec = catalog_spec(
        GR10,
        kwargs.get("task", RUNNING_TASK),
        stakeholder=kwargs.get("stakeholder", "Tester"),
        diagram_language=kwargs.get("diagram_language"),
    )
    return spec


def test_running_example_selects_cnc_runtime_view():
    spec = _spec()
    assert spec.selected_view.viewpoint_id == "cnc-runtime"
    assert spec.selected_view.view_type == "component_view"
    assert spec.selected_view.diagram_language == "plantuml"
    assert spec.selected_view.diagram_language_rule == "viewpoint default: plantuml"
    assert spec.selected_view.granularity == "component_or_service_level"
    assert spec.selected_view.notation == "Component Diagram"
    ids = [item.id for item in spec.required_information]
    assert ids == ["RI-1", "RI-2", "RI-3", "RI-4"]
    assert "user registration" in spec.required_information[2].need
    assert "control-flow" in spec.architectural_concerns
    assert "connectivity" not in spec.architectural_concerns
    assert spec.selection_trace is not None
    assert spec.selection_trace.preferred_viewpoints[0] == "cnc-runtime"


def test_new_contributor_overview_selects_context():
    spec = _spec(
        stakeholder="new contributor",
        task="I am new to the codebase and need an overview to get started.",
    )
    assert spec.selected_view.viewpoint_id == "context"
    assert spec.selected_view.view_type == "context_view"


def test_a_language_word_in_the_goal_does_not_select_the_language():
    spec = _spec(
        stakeholder="Tester",
        task="Show the registration flow as a mermaid sequence diagram so I can design tests.",
    )
    assert spec.selected_view.diagram_language == "plantuml"
    assert spec.selected_view.diagram_language_rule == "viewpoint default: plantuml"
    assert spec.selected_view.viewpoint_id == "cnc-runtime"


def test_request_language_wins_over_a_language_named_in_the_goal():
    spec = _spec(
        stakeholder="Tester",
        task="Show the registration flow as a mermaid sequence diagram so I can design tests.",
        diagram_language="plantuml",
    )
    assert spec.selected_view.diagram_language == "plantuml"
    assert spec.selected_view.diagram_language_rule == "request named plantuml"


def test_unknown_notation_is_rejected():
    with pytest.raises(PipelineError, match="Unknown diagram_language"):
        _spec(diagram_language="not-a-notation")
