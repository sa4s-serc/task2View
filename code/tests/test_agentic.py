from pathlib import Path

from task2view.contracts.models import UserRequest
from task2view.pipeline import run_pipeline, write_result


def _gr10() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data_points" / "progetto_ing_software_gr10-main-English"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("GR10 data point not found")


GR10 = _gr10()
GOAL = (
    "I am a software developer. I need to modify the seat booking functionality "
    "and understand the main system components involved and how they interact."
)


def _scripted(prompt: str, *, model=None):
    if "Stakeholder-Task Interpretation Agent" in prompt:
        return {
            "stakeholder": "software developer",
            "canonical_role": "member-of-development-team",
            "task": "modify seat booking and understand main components",
            "target": "seat booking",
            "goal": "understand components and interactions",
            "scope": "booking-related code",
            "constraints": [],
            "confidence": 0.9,
        }
    if "Concern and Architectural Question Agent" in prompt:
        return {
            "concerns": ["maintainability", "control-flow"],
            "questions": [
                {"id": "AQ1", "text": "Which components participate in seat booking?"},
                {"id": "AQ2", "text": "How do those components interact?"},
            ],
        }
    if "Viewpoint Planning Agent" in prompt:
        assert "RANKED CANDIDATES" not in prompt
        assert "module-decomposition" in prompt
        assert "AQ1" in prompt
        return {
            "views": [
                {
                    "id": "V1",
                    "viewpoint_id": "module-decomposition",
                    "diagram_language": "plantuml",
                    "language_reason": "the questions ask for components and how they interact",
                    "addresses": ["AQ1", "AQ2"],
                    "required_evidence": ["modules", "dependencies"],
                    "purpose": "show booking components",
                }
            ]
        }
    if "You extract an architecture view from source code" in prompt or "TYPED USES/CALLS GRAPH" in prompt:
        return {
            "elements": [
                {
                    "id": "E1",
                    "name": "Registration UI",
                    "kind": "component",
                    "role": "Accepts registration requests",
                    "evidence": {
                        "file": "src/main/java/Boundary/UserRegistrationGUI.java",
                        "symbol": "UserRegistrationGUI",
                        "excerpt": "systemServicesController.registerUser",
                    },
                    "support": "observed",
                },
                {
                    "id": "E2",
                    "name": "Registration service",
                    "kind": "component",
                    "role": "Creates the user account",
                    "evidence": {
                        "file": "src/main/java/Control/SystemServicesController.java",
                        "symbol": "SystemServicesController",
                        "excerpt": "registerUser",
                    },
                    "support": "observed",
                },
            ],
            "relations": [
                {
                    "id": "R1",
                    "from": "E1",
                    "to": "E2",
                    "kind": "call",
                    "label": "registerUser",
                    "order": 1,
                    "evidence": {
                        "file": "src/main/java/Boundary/UserRegistrationGUI.java",
                        "symbol": "UserRegistrationGUI",
                    },
                    "support": "observed",
                }
            ],
            "groups": [],
            "unanswered": [],
        }
    if "Repository Analysis Agent" in prompt:
        return {
            "analysis_goal": "find the modules for seat booking",
            "target_view": "module-decomposition",
            "target_granularity": "component",
            "constraints": ["booking-related code"],
            "analysis_tasks": [
                {
                    "id": "AT1",
                    "goal": "Which components participate in seat booking?",
                    "addresses": ["AQ1"],
                    "starting_points": [],
                    "candidate_locations": [],
                    "expected_evidence": ["modules that own booking"],
                },
                {
                    "id": "AT2",
                    "goal": "How do those components interact?",
                    "addresses": ["AQ2"],
                    "starting_points": [],
                    "candidate_locations": [],
                    "expected_evidence": ["calls between those modules"],
                },
            ],
        }
    if "Need-Evidence Reconciliation Agent" in prompt:
        return {
            "questions": [
                {"id": "AQ1", "support": "partial", "rationale": "modules are named, calls are not shown"},
                {"id": "AQ2", "support": "unsupported", "rationale": "no claim shows a call"},
            ],
            "unanswered": ["AQ2"],
            "limitations": ["the plan named no file"],
            "rationale": "plantuml is the viewpoint default; the evidence does not show calls",
        }
    if "View Generation Agent" in prompt:
        return {
            "elements": [
                {"name": "Registration UI", "kind": "component", "role": "Accepts registration requests"},
                {"name": "Registration service", "kind": "component", "role": "Creates the user account"},
            ],
            "relations": [
                {"from": "Registration UI", "to": "Registration service", "kind": "calls", "label": "registerUser"}
            ],
            "notes": ["scripted view"],
        }
    if "Completeness Critic" in prompt or "Structure Completeness Critic" in prompt:
        return {"add": [], "notes": ["scripted"]}
    raise AssertionError("unexpected prompt:\n" + prompt[:400])


def test_agentic_pipeline_with_scripted_agents(tmp_path: Path):
    result = run_pipeline(
        UserRequest(
            code=str(GR10),
            goal=GOAL,
            request_id="REQ-AGENT-001",
            extract_workers=1,
        ),
        generate=_scripted,
    )
    assert result.spec.selected_view.viewpoint_id == "module-decomposition"
    assert result.spec.selection_trace.method == "model-viewpoint"
    assert result.extras["correspondence.json"]["decided_by"] == "model"
    assert result.spec.selected_view.grain_unit == "component"
    assert "seat booking" in result.spec.task_summary.lower()
    assert result.scope.scope_strategy == "composite"
    assert result.view_model is not None
    names = {e.name for e in result.view_model.elements}
    assert names == {"Registration UI", "Registration service"}
    assert {e.kind for e in result.view_model.elements} == {"component"}
    write_result(tmp_path, result)
    assert (tmp_path / "stakeholder_task_profile.json").exists()
    assert (tmp_path / "architectural_questions.json").exists()
    assert (tmp_path / "viewpoint_plan.json").exists()
    assert (tmp_path / "correspondence.json").exists()
    assert (tmp_path / "repository_scope.json").exists()
    assert (tmp_path / "view_model.json").exists()
    assert (tmp_path / "repository_analysis_plan.json").exists()
    assert (tmp_path / "architecture_view.puml").exists()
    assert (tmp_path / "structure_report.json").exists()
    assert (tmp_path / "evidence_aware_plan.json").exists()
    aware = result.extras["evidence_aware_plan.json"]
    assert aware["diagram_language"] == "plantuml"
    assert aware["diagram_language_rule"].startswith("viewpoint agent chose plantuml")
    assert {row["id"]: row["support"] for row in aware["questions"]} == {
        "AQ1": "partial",
        "AQ2": "unsupported",
    }


def test_agentic_stop_after_scope():
    result = run_pipeline(
        UserRequest(
            code=str(GR10),
            goal=GOAL,
            request_id="REQ-AGENT-002",
            skip_extract=True,
        ),
        generate=_scripted,
    )
    assert result.view_model is None
    assert result.scope.candidate_areas
    assert "viewpoint_plan.json" in result.extras
    assert result.extras["repository_analysis_plan.json"]["analysis_tasks"]
