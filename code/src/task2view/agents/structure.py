"""Fill evidence on names the extractor already published.

Does not add components, connectors, or rename boxes. Ungrounded names are
dropped later by validate_view.
"""

from __future__ import annotations

from pathlib import Path

from task2view.contracts.models import (
    Evidence,
    RepositoryScope,
    ViewElement,
    ViewModel,
    ViewSpecification,
)
from task2view.knowledge.loader import KnowledgeBase, load_knowledge
from task2view.phase4.graph import RepositoryGraph

_DEFAULT_KEEP = frozenset(
    {"actor", "datastore", "external_system", "deployment_node", "system", "module"}
)


def _alias_map(knowledge: KnowledgeBase) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for layer in (knowledge.architectural_styles or {}).get("layers") or []:
        name = str(layer.get("name") or layer.get("id") or "").strip()
        if not name:
            continue
        mapping[str(layer.get("id") or name).casefold()] = name
        mapping[name.casefold()] = name
        for alias in layer.get("aliases") or []:
            mapping[str(alias).casefold()] = name
    return mapping


def canonical_layer(raw: str, knowledge: KnowledgeBase | None = None) -> str:
    knowledge = knowledge or load_knowledge()
    return _alias_map(knowledge).get(raw.casefold().strip(), raw.strip() or "root")


def resolve_type(name: str, graph: RepositoryGraph) -> str | None:
    return graph.resolve(name)


def _keep_kinds(knowledge: KnowledgeBase | None) -> frozenset[str]:
    if knowledge is None:
        return _DEFAULT_KEEP
    return knowledge.keep_without_graph() or _DEFAULT_KEEP


def _layered_viewpoint(spec: ViewSpecification | None) -> bool:
    if spec is None:
        return False
    vid = (spec.selected_view.viewpoint_id or "").casefold()
    vtype = (spec.selected_view.view_type or "").casefold()
    return "layer" in vid or "layer" in vtype


def _view_type(vm: ViewModel, spec: ViewSpecification | None) -> str:
    if spec is not None and spec.selected_view.view_type:
        return spec.selected_view.view_type
    return vm.view_type


def _dir_for(
    el: ViewElement,
    graph: RepositoryGraph,
    keep: frozenset[str],
) -> str | None:
    if el.kind in {"actor", "system", "module"}:
        return None
    if el.external or el.kind in keep:
        return "External"
    match = resolve_type(el.name, graph)
    if match is None and el.evidence and el.evidence.symbol:
        match = resolve_type(el.evidence.symbol, graph)
    if match is None and el.evidence and el.evidence.file:
        match = resolve_type(el.evidence.file, graph)
    if match is None:
        if el.evidence and el.evidence.file:
            parent = Path(el.evidence.file).parent.name
            return parent or "root"
        return "External"
    return graph.nodes[match].layer


def diagnose_structure(
    vm: ViewModel,
    graph: RepositoryGraph,
    knowledge: KnowledgeBase | None = None,
    spec: ViewSpecification | None = None,
) -> dict:
    knowledge = knowledge or load_knowledge()
    keep = _keep_kinds(knowledge)
    selected = {e.name for e in vm.elements if not e.external}
    resolved = {name: resolve_type(name, graph) for name in selected}
    known = {name: match for name, match in resolved.items() if match}
    by_id = {e.id: e for e in vm.elements}
    group_of: dict[str, str] = {}
    for group in vm.groups:
        for eid in group.contains:
            if eid in by_id:
                group_of[by_id[eid].name] = group.name

    misplaced: list[dict] = []
    style = _layered_viewpoint(spec)
    for el in vm.elements:
        if el.external or el.kind in keep:
            continue
        expected = _dir_for(el, graph, keep)
        if expected is None:
            continue
        if style:
            expected = canonical_layer(expected, knowledge)
        actual = group_of.get(el.name)
        if actual and actual != expected and (
            not style or canonical_layer(actual, knowledge) != expected
        ):
            misplaced.append({"element": el.name, "group": actual, "package": expected})

    have_pairs: set[tuple[str, str]] = set()
    for rel in vm.relations:
        src = by_id.get(rel.frm)
        dst = by_id.get(rel.to)
        if src and dst:
            have_pairs.add((src.name, dst.name))

    missing_edges: list[dict] = []
    for src_name, src_t in known.items():
        for dst_t in sorted(graph.uses.get(src_t, ())):
            dst_name = next((n for n, t in known.items() if t == dst_t), None)
            if dst_name and (src_name, dst_name) not in have_pairs:
                kind = "calls" if graph.has_call(src_t, dst_t) else "uses"
                missing_edges.append({"from": src_name, "to": dst_name, "kind": kind})

    missing_neighbors: list[dict] = []
    selected_types = set(known.values())
    seen: set[str] = set()
    for src_t in selected_types:
        for nb in graph.neighbors(src_t):
            if nb in selected_types or nb in seen or nb not in graph.nodes:
                continue
            seen.add(nb)
            node = graph.nodes[nb]
            missing_neighbors.append(
                {
                    "name": nb,
                    "layer": node.layer,
                    "path": node.path,
                    "degree": graph.degree(nb),
                    "via": src_t,
                }
            )
    missing_neighbors.sort(key=lambda row: -int(row["degree"]))
    return {
        "misplaced_groups": misplaced,
        "missing_edges": missing_edges[:40],
        "missing_neighbors": missing_neighbors[:20],
        "selected": sorted(known),
    }


def os_commonpath(paths: list[str]) -> str:
    from os.path import commonpath

    return commonpath(paths)


def system_label_from_paths(paths: list[str], knowledge: KnowledgeBase) -> str:
    """Name the software system from the common source root, not a project constant."""
    skip = {
        str(x).casefold()
        for x in (knowledge.view_projection.get("source_root_segments") or [])
    }
    skip.update({".", "/", "\\"})
    if not paths:
        return "System"
    try:
        prefix = Path(os_commonpath(paths))
    except ValueError:
        prefix = Path(paths[0]).parent
    meaningful = [part for part in prefix.parts if part.casefold() not in skip]
    if meaningful:
        return meaningful[-1]
    for path in paths:
        parts = [p for p in Path(path).parts if p.casefold() not in skip]
        if len(parts) >= 2:
            return parts[-2]
        if parts:
            return parts[0]
    return "System"



def owner_type(el: ViewElement, graph: RepositoryGraph) -> str | None:
    if el.evidence and el.evidence.symbol:
        match = resolve_type(el.evidence.symbol, graph)
        if match:
            return match
    if el.evidence and el.evidence.file:
        match = resolve_type(el.evidence.file, graph)
        if match:
            return match
    return resolve_type(el.name, graph)


def apply_facts(
    vm: ViewModel,
    graph: RepositoryGraph,
    spec: ViewSpecification | None = None,
    *,
    knowledge: KnowledgeBase | None = None,
    scope: RepositoryScope | None = None,
) -> tuple[ViewModel, dict]:
    """Attach file evidence to published names. Leave elements and relations unchanged."""
    del scope
    knowledge = knowledge or load_knowledge()
    before = diagnose_structure(vm, graph, knowledge, spec)
    for el in vm.elements:
        if el.external or el.kind in _keep_kinds(knowledge):
            continue
        match = owner_type(el, graph)
        if match is None or match not in graph.nodes:
            continue
        node = graph.nodes[match]
        if el.evidence is None:
            el.evidence = Evidence(file=node.path, symbol=match)
        else:
            el.evidence.file = el.evidence.file or node.path
            el.evidence.symbol = el.evidence.symbol or match

    vid = spec.selected_view.viewpoint_id if spec is not None else None
    unit = knowledge.view_unit(_view_type(vm, spec), vid)
    grounded = ViewModel(
        request_id=vm.request_id,
        view_type=vm.view_type,
        granularity=vm.granularity,
        groups=list(vm.groups),
        elements=list(vm.elements),
        relations=list(vm.relations),
        unanswered=list(vm.unanswered),
        notes=list(vm.notes),
    )
    after = diagnose_structure(grounded, graph, knowledge, spec)
    report = {
        "before": before,
        "after": after,
        "relations_added": 0,
        "edge_insertion": "none",
        "view_unit": unit,
        "groups": [g.name for g in grounded.groups],
    }
    if spec is not None:
        report["view_type"] = spec.selected_view.view_type
        report["viewpoint_id"] = spec.selected_view.viewpoint_id
    return grounded, report


ground_view_model = apply_facts
