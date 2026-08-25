"""Deterministic structure facts: directory groups, graph edges, evidence paths.

Style names (BCED, hexagonal) are optional and only applied when the selected
viewpoint is layered. Default groups are real parent directories.

The published view is a projection of the repository graph: extractor relations
are kept, extra graph edges are inserted only when the view type asks for them,
and element counts follow stakeholder / viewpoint caps in view_projection.yaml.
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
    {"actor", "datastore", "external_system", "deployment_node", "system"}
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
    if el.kind == "actor" or el.kind == "system":
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
    scope: RepositoryScope | None,
    knowledge: KnowledgeBase,
    keep: frozenset[str],
) -> ViewModel:
    cfg = knowledge.view_projection.get("context") or {}
    if _view_type(vm, spec) != "context_view" or not cfg.get("ensure_system", True):
        return vm
    internals = [
        e
        for e in vm.elements
        if e.kind not in {"actor", "system"}
        and not (e.external and e.kind in keep)
    ]
    min_internal = int(cfg.get("min_internal_elements") or 1)
    elements = list(vm.elements)
    relations = list(vm.relations)
    notes = list(vm.notes)
    existing = {e.name.casefold() for e in elements}

    if not any(e.kind == "system" for e in elements) and len(internals) < min_internal:
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
            existing.add(label.casefold())
            notes.append("added system boundary from source-root path")

    per_dir = int(cfg.get("representatives_per_directory") or 1)
    max_add = int(cfg.get("max_representatives") or 8)
    internals_now = [e for e in elements if e.kind not in {"actor", "system"}]
    if len(internals_now) < min_internal and per_dir > 0 and graph.nodes:
        scoped_paths = {c.path for c in (scope.candidate_areas if scope else [])}
        by_layer: dict[str, list] = defaultdict(list)
        for node in graph.nodes.values():
            if scoped_paths and node.path not in scoped_paths:
                continue
            by_layer[node.layer].append(node)
        if not by_layer:
            for node in graph.nodes.values():
                by_layer[node.layer].append(node)
        added = 0
        for _layer, nodes in sorted(by_layer.items()):
            ranked = sorted(nodes, key=lambda n: -graph.degree(n.name))
            for node in ranked[:per_dir]:
                if added >= max_add:
                    break
                if node.name.casefold() in existing:
                    continue
                elements.append(
                    ViewElement(
                        id=_next_element_id(elements),
                        name=node.name,
                        kind="component",
                        role=node.layer,
                        evidence=Evidence(
                            file=node.path,
                            symbol=node.name,
                            excerpt=f"{node.name} [{node.layer}]",
                        ),
                        support="observed",
                    )
                )
                existing.add(node.name.casefold())
                added += 1
            if added >= max_add:
                break
        if added:
            notes.append(f"added {added} directory representatives for context structure")

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


def _degree(el: ViewElement, graph: RepositoryGraph) -> int:
    match = resolve_type(el.name, graph)
    if match is None:
        return 0
    return graph.degree(match)


def _cap_elements(
    vm: ViewModel,
    graph: RepositoryGraph,
    spec: ViewSpecification | None,
    knowledge: KnowledgeBase,
    keep: frozenset[str],
    original_endpoints: set[str],
) -> ViewModel:
    view_type = _view_type(vm, spec)
    granularity = (
        spec.selected_view.granularity if spec is not None else vm.granularity
    )
    role = spec.stakeholder if spec is not None else None
    cap = knowledge.max_elements_for(role, view_type, granularity)
    if cap is None or len(vm.elements) <= cap:
        return vm
    caps_cfg = knowledge.view_projection.get("max_elements") or {}
    strict = bool(caps_cfg.get("context_one_per_group")) and view_type == "context_view"
    keep_one = bool(caps_cfg.get("keep_one_per_group", True))

    group_of: dict[str, str] = {}
    for group in vm.groups:
        for eid in group.contains:
            group_of[eid] = group.name

    must: list[ViewElement] = []
    rest: list[ViewElement] = []
    for el in vm.elements:
        if el.kind in keep or el.external or el.kind == "actor":
            must.append(el)
        else:
            rest.append(el)

    chosen: dict[str, ViewElement] = {e.id: e for e in must}
    if keep_one or strict:
        by_group: dict[str, list[ViewElement]] = defaultdict(list)
        for el in rest:
            by_group[group_of.get(el.id, "_")].append(el)
        for members in by_group.values():
            members.sort(key=lambda e: (-_degree(e, graph), e.name))
            pick = members[0]
            chosen[pick.id] = pick

    if not strict:
        leftover = [e for e in rest if e.id not in chosen]
        leftover.sort(
            key=lambda e: (
                0 if e.id in original_endpoints else 1,
                -_degree(e, graph),
                e.name,
            )
        )
        for el in leftover:
            if len(chosen) >= cap:
                break
            chosen[el.id] = el

    if len(chosen) > cap:
        droppable = [e for e in list(chosen.values()) if e.id not in {m.id for m in must}]
        droppable.sort(key=lambda e: (_degree(e, graph), e.name))
        for el in droppable:
            if len(chosen) <= cap:
                break
            del chosen[el.id]

    kept_ids = set(chosen)
    dropped = len(vm.elements) - len(kept_ids)
    vm.elements = [e for e in vm.elements if e.id in kept_ids]
    vm.relations = [r for r in vm.relations if r.frm in kept_ids and r.to in kept_ids]
    vm.groups = [
        ViewGroup(
            id=g.id,
            name=g.name,
            kind=g.kind,
            contains=[eid for eid in g.contains if eid in kept_ids],
        )
        for g in vm.groups
        if any(eid in kept_ids for eid in g.contains)
    ]
    if dropped:
        vm.notes = list(dict.fromkeys(vm.notes + [f"capped view to {len(vm.elements)} elements"]))
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
        match = resolve_type(el.name, graph)
        if match is None and el.evidence and el.evidence.symbol:
            match = resolve_type(el.evidence.symbol, graph)
        if match is None and el.evidence and el.evidence.file:
            match = resolve_type(el.evidence.file, graph)
        if match is None:
            continue
        el.name = match
        node = graph.nodes[match]
        if el.evidence is None:
            el.evidence = Evidence(file=node.path, symbol=match)
        else:
            el.evidence.file = node.path
            el.evidence.symbol = el.evidence.symbol or match

    original_endpoints = {rel.frm for rel in vm.relations} | {rel.to for rel in vm.relations}
    vm = _complete_context(vm, graph, spec, scope, knowledge, keep)

    groups = _rebuild_groups(vm, graph, spec, knowledge, keep)
    vm.groups = groups

    vm = _cap_elements(vm, graph, spec, knowledge, keep, original_endpoints)
    groups = _rebuild_groups(vm, graph, spec, knowledge, keep)
    vm.groups = groups

    by_id = {e.id: e for e in vm.elements}
    name_to_id = {e.name: e.id for e in vm.elements}
    group_of: dict[str, str] = {}
    for group in vm.groups:
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

    mode = knowledge.edge_insertion_mode(_view_type(vm, spec))
    added_rels = 0
    if mode != "none":
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
                added_rels += 1

    notes = list(vm.notes)
    if before["misplaced_groups"]:
        notes.append(f"regrouped {len(before['misplaced_groups'])} elements by directory")
    if added_rels:
        if mode == "inter_group":
            notes.append(f"inserted {added_rels} inter-package graph edges")
        else:
            notes.append(f"inserted {added_rels} graph edges among selected files")

    grounded = ViewModel(
        request_id=vm.request_id,
        view_type=vm.view_type,
        granularity=vm.granularity,
        groups=groups,
        elements=vm.elements,
        relations=relations,
        unanswered=vm.unanswered,
        notes=list(dict.fromkeys(notes)),
    )
    after = diagnose_structure(grounded, graph, knowledge, spec)
    report = {
        "before": before,
        "after": after,
        "relations_added": added_rels,
        "edge_insertion": mode,
        "groups": [g.name for g in groups],
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
