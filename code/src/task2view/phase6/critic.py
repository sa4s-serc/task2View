"""Phase 6. Need–evidence reconciliation.

Writes notes on which questions the view answers. Does not change the view.
"""

from __future__ import annotations

from task2view.agents.runtime import AgentRuntime
from task2view.agents.structure import diagnose_structure, ground_view_model
from task2view.contracts.models import PipelineError, RepositoryScope, ViewModel, ViewSpecification
from task2view.knowledge.loader import load_knowledge
from task2view.phase4.graph import RepositoryGraph

PROMPT = """You are the Structure Completeness Critic.

You do not edit the diagram. Say whether the elements on the page answer the questions at this grain.
add must be []. Notes are the only output that is kept.

For each question, one note: answered, or not answered, and what is missing.
Missing means a responsibility, connector, actor, or host that this grain allows and the question asks for.
A missing class, a missing neighbour in the file graph, or a box that would cover a declared gap is not a note.

GRAIN:
{grain}

VIEWPOINT / TASK:
{spec}

QUESTIONS:
{questions}

REQUIRED INFORMATION:
{required}

CURRENT ELEMENTS:
{elements}

UNANSWERED:
{unanswered}

DECLARED GAPS (this view does not cover these; do not ask for boxes for them):
{gaps}

Return JSON:
{{
  "add": [],
  "notes": ["AQ1 answered: ...", "AQ2 not answered: the view has no ..."]
}}
"""


def critique_completeness(
    vm: ViewModel,
    spec: ViewSpecification,
    graph: RepositoryGraph,
    scope: RepositoryScope,
    runtime: AgentRuntime,
) -> tuple[ViewModel, dict]:
    diagnosis = diagnose_structure(vm, graph)
    elements = ", ".join(f"{e.name}[{e.kind}]" for e in vm.elements) or "(none)"
    unanswered = ", ".join(vm.unanswered) or "(none)"
    questions = "\n".join(
        f"- {q.id}: {q.text}" for q in (spec.architectural_questions or [])
    ) or "(none)"
    required = "\n".join(f"- {ri.id}: {ri.need}" for ri in spec.required_information)
    kb = load_knowledge()
    spec_text = (
        f"view_type={spec.selected_view.view_type} "
        f"viewpoint_id={spec.selected_view.viewpoint_id} "
        f"grain_unit={spec.selected_view.grain_unit}\n"
        f"purpose={spec.selected_view.purpose}\n"
        f"task={spec.task_summary}"
    )
    prompt = PROMPT.format(
        grain=kb.grain_prompt(spec.selected_view.viewpoint_id, spec.selected_view.view_type),
        spec=spec_text,
        questions=questions,
        required=required,
        elements=elements,
        unanswered=unanswered,
        gaps=", ".join(spec.unanswered_concerns or spec.declared_gaps or []) or "(none)",
    )
    try:
        raw = runtime.complete_json(prompt)
    except (PipelineError, AssertionError, ValueError, TypeError) as exc:
        return vm, {"skipped": True, "error": str(exc), "added": []}
    names = [str(x) for x in (raw.get("add") or raw.get("add_types") or [])]
    return vm, {
        "skipped": False,
        "proposed": names,
        "added": [],
        "notes": [str(x) for x in raw.get("notes") or []],
        "diagnosis": {
            "missing_neighbors": diagnosis.get("missing_neighbors"),
            "missing_edges": diagnosis.get("missing_edges"),
        },
    }


def refine_extracted_view(
    vm: ViewModel,
    spec: ViewSpecification,
    scope: RepositoryScope,
    graph: RepositoryGraph,
    runtime: AgentRuntime | None,
    *,
    skip_critic: bool = False,
) -> tuple[ViewModel, dict]:
    vm, report = ground_view_model(vm, graph, spec, scope=scope)
    if skip_critic or runtime is None:
        report["critic"] = {"skipped": True}
        return vm, report
    vm, critic = critique_completeness(vm, spec, graph, scope, runtime)
    vm, report = ground_view_model(vm, graph, spec, scope=scope)
    report["critic"] = critic
    return vm, report


refine_extracted_view = refine_extracted_view
