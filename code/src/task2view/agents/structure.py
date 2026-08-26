"""Deterministic grounding after extraction.

Component views keep published names and add uses among owner files.
Type views insert graph edges among selected types.
Context views keep actors and the system. No folder-lift.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from task2view.contracts.models import (
    Evidence,
    RepositoryScope,
    ViewElement,
    ViewGroup,
    ViewModel,
    ViewRelation,
    ViewSpecification,
)
from task2view.knowledge.loader import KnowledgeBase, load_knowledge
from task2view.phase3.graph import RepositoryGraph

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


def _next_element_id(elements: list[ViewElement]) -> str:
    nums = []
    for el in elements:
        raw = el.id[1:] if el.id[:1].isalpha() else el.id
        if raw.isdigit():
            nums.append(int(raw))
    return f"E{(max(nums) if nums else 0) + 1}"


def _next_relation_id(relations: list[ViewRelation], extra: int = 0) -> str:
    nums = []
    for rel in relations:
        raw = rel.id[1:] if rel.id[:1].isalpha() else rel.id
        if raw.isdigit():
            nums.append(int(raw))
    return f"R{(max(nums) if nums else 0) + 1 + extra}"


def _complete_context(
    vm: ViewModel,
    graph: RepositoryGraph,
    spec: ViewSpecification | None,
    _scope: RepositoryScope | None,
    knowledge: KnowledgeBase,
) -> ViewModel:
    cfg = knowledge.view_projection.get("context") or {}
    if _view_type(vm, spec) != "context_view" or not cfg.get("ensure_system", True):
        return vm
    elements = list(vm.elements)
    relations = list(vm.relations)
    notes = list(vm.notes)
    existing = {e.name.casefold() for e in elements}

    if not any(e.kind == "system" for e in elements):
        paths = [n.path for n in graph.nodes.values() if n.path]
        label = system_label_from_paths(paths, knowledge)
        if label.casefold() not in existing:
            evidence_file = None
            try:
                evidence_file = os_commonpath(paths) if paths else None
            except ValueError:
                evidence_file = paths[0] if paths else None
            elements.append(
                ViewElement(
                    id=_next_element_id(elements),
                    name=label,
                    kind="system",
                    role="software system under analysis",
                    evidence=Evidence(file=evidence_file, excerpt="repository source root"),
                    support="inferred",
                )
            )
            notes.append("added system boundary from source-root path")

    system = next((e for e in elements if e.kind == "system"), None)
    rel_kind = str(cfg.get("actor_to_system_kind") or "uses")
    if system:
        attached = {rel.frm for rel in relations} | {rel.to for rel in relations}
        extra = 0
        for actor in elements:
            if actor.kind != "actor":
                continue
            if actor.id in attached:
                continue
            relations.append(
                ViewRelation(
                    id=_next_relation_id(relations, extra),
                    frm=actor.id,
                    to=system.id,
                    kind=rel_kind,
                    label=None,
                    support="inferred",
                )
            )
            extra += 1
        if extra:
            notes.append(f"linked {extra} actors to the system boundary")

    vm.elements = elements
    vm.relations = relations
    vm.notes = notes
    return vm


def _rebuild_groups(
    vm: ViewModel,
    graph: RepositoryGraph,
    spec: ViewSpecification | None,
    knowledge: KnowledgeBase,
    keep: frozenset[str],
) -> list[ViewGroup]:
    style = _layered_viewpoint(spec)
    by_dir: dict[str, list[str]] = defaultdict(list)
    for el in vm.elements:
        name = _dir_for(el, graph, keep)
        if name is None:
            continue
        if style and name not in {"External"} and el.kind != "system":
            name = canonical_layer(name, knowledge)
        by_dir[name].append(el.id)
    gkind = "layer" if style else "package"
    groups: list[ViewGroup] = []
    i = 1
    for folder, ids in sorted(by_dir.items()):
        kind = "boundary" if any(e.kind == "system" for e in vm.elements if e.id in ids) else gkind
        groups.append(ViewGroup(id=f"G{i}", name=folder, kind=kind, contains=ids))
        i += 1
    return groups


def _project_context(vm: ViewModel) -> ViewModel:
    keep = {"actor", "system", "datastore", "external_system", "deployment_node"}
    kept = [e for e in vm.elements if e.kind in keep]
    ids = {e.id for e in kept}
    vm.elements = kept
    vm.relations = [r for r in vm.relations if r.frm in ids and r.to in ids]
    vm.groups = []
    vm.notes = list(dict.fromkeys(vm.notes + ["context view: actors and system only"]))
    return vm


def _insert_type_edges(
    vm: ViewModel,
    graph: RepositoryGraph,
    spec: ViewSpecification | None,
    knowledge: KnowledgeBase,
    keep: frozenset[str],
) -> int:
    mode = knowledge.edge_insertion_mode(_view_type(vm, spec))
    if mode == "none":
        return 0
    groups = _rebuild_groups(vm, graph, spec, knowledge, keep)
    vm.groups = groups
    by_id = {e.id: e for e in vm.elements}
    name_to_id = {e.name: e.id for e in vm.elements}
    group_of: dict[str, str] = {}
    for group in groups:
        for eid in group.contains:
            if eid in by_id:
                group_of[eid] = group.name
    have: set[tuple[str, str]] = set()
    relations = list(vm.relations)
    for rel in relations:
        src = by_id.get(rel.frm)
        dst = by_id.get(rel.to)
        if src and dst:
            have.add((src.name, dst.name))
    added = 0
    extra = 0
    for src_name, src_id in name_to_id.items():
        src_el = by_id[src_id]
        if src_el.external or src_el.kind in keep:
            continue
        src_t = resolve_type(src_name, graph)
        if src_t is None:
            continue
        for dst_t in sorted(graph.uses.get(src_t, ())):
            dst_id = name_to_id.get(dst_t)
            if not dst_id or (src_t, dst_t) in have:
                continue
            if mode == "inter_group":
                src_g = group_of.get(src_id)
                dst_g = group_of.get(dst_id)
                if src_g and dst_g and src_g == dst_g:
                    continue
            kind = "calls" if graph.has_call(src_t, dst_t) else "uses"
            label = None
            if kind == "calls":
                methods = [m for t, m in graph.calls.get(src_t, ()) if t == dst_t]
                label = methods[0] if methods else None
            node = graph.nodes[src_t]
            relations.append(
                ViewRelation(
                    id=_next_relation_id(relations, extra),
                    frm=src_id,
                    to=dst_id,
                    kind=kind,
                    label=label,
                    evidence=Evidence(
                        file=node.path,
                        symbol=src_t,
                        excerpt=f"{src_t} {kind} {dst_t} (repository graph)",
                    ),
                    support="observed",
                )
            )
            have.add((src_t, dst_t))
            extra += 1
            added += 1
    vm.relations = relations
    return added


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


def _insert_owner_uses(vm: ViewModel, graph: RepositoryGraph) -> int:
    """Add uses between extracted components when their owner files have a graph edge."""
    owners = {e.id: owner_type(e, graph) for e in vm.elements}
    have: set[tuple[str, str]] = {(rel.frm, rel.to) for rel in vm.relations}
    ids = [
        e.id
        for e in vm.elements
        if not e.external and e.kind not in {"actor", "system", "datastore"}
    ]
    added = 0
    extra = 0
    relations = list(vm.relations)
    for src_id in ids:
        src_t = owners.get(src_id)
        if not src_t:
            continue
        for dst_id in ids:
            if src_id == dst_id or (src_id, dst_id) in have:
                continue
            dst_t = owners.get(dst_id)
            if not dst_t or dst_t == src_t:
                continue
            if dst_t not in graph.uses.get(src_t, ()):
                continue
            have.add((src_id, dst_id))
            node = graph.nodes.get(src_t)
            relations.append(
                ViewRelation(
                    id=_next_relation_id(relations, extra),
                    frm=src_id,
                    to=dst_id,
                    kind="uses",
                    evidence=Evidence(
                        file=node.path if node else None,
                        symbol=src_t,
                        excerpt=f"{src_t} uses {dst_t}",
                    ),
                    support="observed",
                )
            )
            extra += 1
            added += 1
    vm.relations = relations
    return added


def apply_facts(
    vm: ViewModel,
    graph: RepositoryGraph,
    spec: ViewSpecification | None = None,
    *,
    knowledge: KnowledgeBase | None = None,
    scope: RepositoryScope | None = None,
) -> tuple[ViewModel, dict]:
    knowledge = knowledge or load_knowledge()
    keep = _keep_kinds(knowledge)
    before = diagnose_structure(vm, graph, knowledge, spec)

    for el in vm.elements:
        if el.external or el.kind in keep:
            continue
        match = owner_type(el, graph)
        if match is None:
            continue
        node = graph.nodes[match]
        if el.kind in {"component", "module"}:
            if el.evidence is None:
                el.evidence = Evidence(file=node.path, symbol=match)
            else:
                el.evidence.file = el.evidence.file or node.path
                el.evidence.symbol = el.evidence.symbol or match
            continue
        el.name = match
        if el.evidence is None:
            el.evidence = Evidence(file=node.path, symbol=match)
        else:
            el.evidence.file = node.path
            el.evidence.symbol = el.evidence.symbol or match

    vid = spec.selected_view.viewpoint_id if spec is not None else None
    unit = knowledge.view_unit(_view_type(vm, spec), vid)
    added_rels = 0
    if unit == "context":
        vm = _complete_context(vm, graph, spec, scope, knowledge)
        vm = _project_context(vm)
    elif unit == "type":
        added_rels = _insert_type_edges(vm, graph, spec, knowledge, keep)
    else:
        added_rels = _insert_owner_uses(vm, graph)
        vm.groups = []

    notes = list(vm.notes)
    if before["misplaced_groups"] and unit == "type":
        notes.append(f"regrouped {len(before['misplaced_groups'])} elements by directory")
    if added_rels:
        notes.append(f"inserted {added_rels} graph edges among selected files")
    vm.notes = list(dict.fromkeys(notes))

    grounded = ViewModel(
        request_id=vm.request_id,
        view_type=vm.view_type,
        granularity=vm.granularity,
        groups=vm.groups,
        elements=vm.elements,
        relations=vm.relations,
        unanswered=vm.unanswered,
        notes=vm.notes,
    )
    after = diagnose_structure(grounded, graph, knowledge, spec)
    report = {
        "before": before,
        "after": after,
        "relations_added": added_rels,
        "edge_insertion": knowledge.edge_insertion_mode(_view_type(vm, spec)),
        "view_unit": unit,
        "groups": [g.name for g in grounded.groups],
    }
    if spec is not None:
        report["view_type"] = spec.selected_view.view_type
        report["viewpoint_id"] = spec.selected_view.viewpoint_id
    return grounded, report


def add_types(
    vm: ViewModel,
    names: list[str],
    graph: RepositoryGraph,
    *,
    knowledge: KnowledgeBase | None = None,
    cap: int = 8,
) -> tuple[ViewModel, list[str]]:
    existing = {e.name.casefold() for e in vm.elements}
    added: list[str] = []
    next_i = len(vm.elements) + 1
    elements = list(vm.elements)
    for raw in names:
        if len(added) >= cap:
            break
        match = resolve_type(str(raw), graph)
        if match is None or match.casefold() in existing:
            continue
        node = graph.nodes[match]
        elements.append(
            ViewElement(
                id=f"E{next_i}",
                name=match,
                kind="component",
                role=node.layer,
                evidence=Evidence(file=node.path, symbol=match, excerpt=f"{match} [{node.layer}]"),
                support="observed",
            )
        )
        existing.add(match.casefold())
        added.append(match)
        next_i += 1
    vm.elements = elements
    return vm, added


ground_view_model = apply_facts

