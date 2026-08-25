"""Phase 4c — deterministic semantic and light syntactic gates."""

from __future__ import annotations

from pathlib import Path

from task2view.contracts.models import (
    RepositoryScope,
    ValidationReport,
    ViewElement,
    ViewGroup,
    ViewModel,
    ViewSpecification,
)
from task2view.knowledge.loader import load_knowledge
from task2view.phase3.graph import RepositoryGraph


def _keep_without_graph() -> frozenset[str]:
    return load_knowledge().keep_without_graph()


def _names(vm: ViewModel) -> dict[str, ViewElement]:
    return {e.id: e for e in vm.elements}


def _resolve_type(name: str, graph: RepositoryGraph) -> str | None:
    return graph.resolve(name)


def _resolve_element(el: ViewElement, graph: RepositoryGraph) -> str | None:
    if el.external or el.kind in _keep_without_graph():
        return el.name
    match = _resolve_type(el.name, graph)
    if match:
        return match
    if el.evidence and el.evidence.symbol:
        match = _resolve_type(el.evidence.symbol, graph)
        if match:
            return match
    if el.evidence and el.evidence.file:
        return _resolve_type(el.evidence.file, graph)
    return None


def _misplaced_groups(vm: ViewModel, graph: RepositoryGraph) -> list[dict]:
    from task2view.agents.structure import diagnose_structure
    return diagnose_structure(vm, graph).get("misplaced_groups") or []


def validate_view(
    vm: ViewModel,
    view_spec: ViewSpecification,
    scope: RepositoryScope,
    graph: RepositoryGraph,
    diagram_source: str,
    notation: str,
) -> tuple[ViewModel, ValidationReport]:
    scoped = {c.path for c in scope.candidate_areas}
    elems = _names(vm)
    resolved_e = 0
    unresolved_e: list[str] = []
    kept_elements: list[ViewElement] = []
    id_map: dict[str, str] = {}
    for el in vm.elements:
        match = _resolve_element(el, graph)
        if match is None:
            unresolved_e.append(el.name)
            id_map[el.id] = ""
            continue
        if not (el.external or el.kind in _keep_without_graph()):
            el.name = match
            if el.evidence and el.evidence.file and el.evidence.file not in scoped and match in graph.nodes:
                el.evidence.file = graph.nodes[match].path
        kept_elements.append(el)
        resolved_e += 1

    kept_ids = {e.id for e in kept_elements}
    resolved_r = 0
    unsupported: list[dict] = []
    kept_rels = []
    for rel in vm.relations:
        if rel.frm not in kept_ids or rel.to not in kept_ids:
            unsupported.append(
                {"from": rel.frm, "to": rel.to, "label": rel.label, "reason": "endpoint dropped"}
            )
            continue
        src = elems[rel.frm]
        dst = elems[rel.to]
        if (
            src.external
            or dst.external
            or             src.kind in _keep_without_graph()
            or dst.kind in _keep_without_graph()
            or rel.kind == "return"
        ):
            kept_rels.append(rel)
            resolved_r += 1
            continue
        src_t = _resolve_type(src.name, graph)
        dst_t = _resolve_type(dst.name, graph)
        ok = False
        if src_t and dst_t:
            if rel.kind in {"calls", "call"}:
                ok = graph.has_call(src_t, dst_t) or graph.has_edge(src_t, dst_t)
            elif rel.kind in {"uses", "depends", "dataflow"}:
                ok = graph.has_edge(src_t, dst_t)
            elif rel.kind == "contains":
                ok = True
            else:
                ok = graph.has_edge(src_t, dst_t) or graph.has_call(src_t, dst_t)
        if ok:
            kept_rels.append(rel)
            resolved_r += 1
        else:
            unsupported.append(
                {
                    "from": src.name,
                    "to": dst.name,
                    "label": rel.label,
                    "reason": "no edge in repository graph",
                }
            )

    kept_groups: list[ViewGroup] = []
    for group in vm.groups:
        contains = [eid for eid in group.contains if eid in kept_ids]
        if contains:
            kept_groups.append(
                ViewGroup(id=group.id, name=group.name, kind=group.kind, contains=contains)
            )

    extra_notes = []
    if unresolved_e:
        extra_notes.append(f"removed {len(unresolved_e)} unresolved elements")
    if unsupported:
        extra_notes.append(f"removed {len(unsupported)} unsupported relations")

    cleaned = ViewModel(
        request_id=vm.request_id,
        view_type=vm.view_type,
        granularity=vm.granularity,
        groups=kept_groups,
        elements=kept_elements,
        relations=kept_rels,
        unanswered=vm.unanswered,
        notes=vm.notes + extra_notes,
    )

    syntax = {"status": "pass", "attempts": 1}
    if notation in {"plantuml", "c4plantuml"}:
        if "@startuml" not in diagram_source or "@enduml" not in diagram_source:
            syntax = {"status": "fail", "attempts": 1, "error": "missing @startuml/@enduml"}
    elif notation == "mermaid":
        if "sequenceDiagram" not in diagram_source and "flowchart" not in diagram_source:
            syntax = {"status": "fail", "attempts": 1, "error": "unrecognised mermaid header"}
    elif notation == "d2":
        if "->" not in diagram_source and ":" not in diagram_source:
            syntax = {"status": "fail", "attempts": 1, "error": "unrecognised d2"}
    elif notation == "graphviz":
        if "digraph" not in diagram_source and "graph " not in diagram_source:
            syntax = {"status": "fail", "attempts": 1, "error": "unrecognised graphviz"}
    elif notation == "structurizr":
        if "workspace" not in diagram_source:
            syntax = {"status": "fail", "attempts": 1, "error": "missing structurizr workspace"}
    elif notation == "nomnoml":
        if "[" not in diagram_source:
            syntax = {"status": "fail", "attempts": 1, "error": "unrecognised nomnoml"}
    elif notation == "excalidraw":
        if "excalidraw" not in diagram_source:
            syntax = {"status": "fail", "attempts": 1, "error": "missing excalidraw document"}
    elif notation == "bpmn":
        if "definitions" not in diagram_source:
            syntax = {"status": "fail", "attempts": 1, "error": "unrecognised bpmn"}

    n_el = max(1, len(vm.elements))
    n_rel = max(1, len(vm.relations))
    unanswered = [
        ri.id
        for ri in view_spec.required_information
        if ri.id in (vm.unanswered or [])
    ]
    uncovered = list(view_spec.unanswered_concerns or [])
    cleaned.unanswered = list(dict.fromkeys(list(cleaned.unanswered) + unanswered + uncovered))
    verdict = "pass"
    if unsupported or unresolved_e or unanswered or uncovered:
        verdict = "pass_with_corrections"
    if syntax.get("status") == "fail" or not cleaned.elements:
        verdict = "fail"

    report = ValidationReport(
        request_id=vm.request_id,
        notation=notation,
        syntax=syntax,
        semantic={
            "elements_resolved": f"{resolved_e}/{n_el}",
            "relations_resolved": f"{resolved_r}/{n_rel}",
            "unsupported": unsupported,
            "unresolved_elements": unresolved_e,
            "granularity_violations": [],
            "unanswered_information": unanswered,
            "unanswered_concerns": uncovered,
            "scope_files": len(scoped),
            "misplaced_groups": _misplaced_groups(cleaned, graph),
        },
        verdict=verdict,
    )
    return cleaned, report


def write_diagram(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
