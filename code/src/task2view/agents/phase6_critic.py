"""Completeness critic (ADR-003 D2).

One optional agent. It sees a graph diagnosis (missing neighbours, unused
edges) and may name extra types to add. The orchestrator accepts a name only
if the repository graph contains it, then re-runs structure grounding.
This is not ADR-001 Phase 6 (need-evidence reconciliation).
"""

from __future__ import annotations

from task2view.agents.runtime import AgentRuntime
from task2view.agents.structure import add_types, diagnose_structure, ground_view_model
from task2view.contracts.models import PipelineError, RepositoryScope, ViewModel, ViewSpecification
from task2view.phase3.graph import RepositoryGraph

PROMPT = """You are the Structure Completeness Critic.

The view below was extracted by a plug-in and then regrouped using the
repository graph (packages and uses/calls edges among selected types).
Your job is completeness against the stakeholder questions, not completeness
of the call graph. Add a neighbour only when it answers an unanswered
required-information item or restores a directory/layer the view omits.

Do not invent types. You may only pick names from MISSING_NEIGHBOURS.
Do not add types just to fill MISSING_EDGES. Cap: 4 types. Return [] if
the view already answers the questions.

VIEWPOINT / TASK:
{spec}

CURRENT ELEMENTS:
{elements}

UNANSWERED:
{unanswered}

GRAPH DIAGNOSIS (external evidence, not your memory):
{diagnosis}

Return JSON:
{{
  "add": ["TypeName", "..."],
  "notes": ["why"]
}}
"""


def _fmt_diagnosis(diag: dict) -> str:
    lines = ["misplaced_groups:"]
    rows = diag.get("misplaced_groups") or []
    if rows:
        for row in rows:
            lines.append(f"- {row}")
    else:
        lines.append("- (none; grouping already graph-grounded)")
    lines.append("missing_edges among selected types:")
    edges = diag.get("missing_edges") or []
    if edges:
        for row in edges[:15]:
            lines.append(f"- {row['from']} -{row['kind']}-> {row['to']}")
    else:
        lines.append("- (none)")
    lines.append("missing_neighbours (name, layer, degree, via):")
    nbs = diag.get("missing_neighbors") or []
    if nbs:
        for row in nbs[:15]:
            lines.append(
                f"- {row['name']} layer={row['layer']} deg={row['degree']} via={row.get('via') or row.get('via')} path={row['path']}"
            )
    else:
        lines.append("- (none)")
    return "\n".join(lines)


def critique_completeness(
    vm: ViewModel,
    spec: ViewSpecification,
    graph: RepositoryGraph,
    scope: RepositoryScope,
    runtime: AgentRuntime,
) -> tuple[ViewModel, dict]:
    diagnosis = diagnose_structure(vm, graph)
    allowed = {row["name"] for row in diagnosis.get("missing_neighbors") or []}
    elements = ", ".join(f"{e.name}[{e.kind}]" for e in vm.elements) or "(none)"
    unanswered = ", ".join(vm.unanswered) or "(none)"
    spec_text = (
        f"view_type={spec.selected_view.view_type} "
        f"granularity={spec.selected_view.granularity}\n"
        f"purpose={spec.selected_view.purpose}\n"
        f"task={spec.task_summary}\n"
        f"concerns={spec.architectural_concerns}\n"
        f"required_information={[ri.need for ri in spec.required_information]}"
    )
    prompt = PROMPT.format(
        spec=spec_text,
        elements=elements,
        unanswered=unanswered,
        diagnosis=_fmt_diagnosis(diagnosis),
    )
    try:
        raw = runtime.complete_json(prompt)
    except (PipelineError, AssertionError, ValueError, TypeError) as exc:
        return vm, {"skipped": True, "error": str(exc), "added": []}
    names = [str(x) for x in (raw.get("add") or raw.get("add_types") or [])]
    names = [n for n in names if n in allowed]
    vm, added = add_types(vm, names, graph, cap=4)
    return vm, {
        "skipped": False,
        "proposed": names,
        "added": added,
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
