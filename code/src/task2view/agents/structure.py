"""Deterministic grounding after extraction.

Component views keep responsibility names when they resolve to files, otherwise
rebuild from the file graph so boxes are types with uses arrows — not folders.
Type views insert graph edges among selected types.
Context views keep actors and the system. No folder-lift.
"""

from __future__ import annotations

import re
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
_DECORATION = re.compile(
    r"\b(modules?|subsystems?|packages?|layers?|components?)\b", re.I
)
_EXTRA_FOLDER_LABELS = frozenset(
    {"dto", "dtos", "swing", "factory", "factories", "util", "utils", "common"}
)
_COMPONENT_CAP = 8
_RUNTIME_VIEWS = frozenset({"deployment_view"})


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
    if system and folder_like_name(system.name, graph, knowledge):
        paths = [n.path for n in graph.nodes.values() if n.path]
        label = system_label_from_paths(paths, knowledge)
        if label and label.casefold() not in existing:
            existing.discard(system.name.casefold())
            system.name = label
            notes.append("renamed folder-shaped system box to the source-root label")
            existing.add(label.casefold())
        elif label:
            system.name = label

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


def _layer_labels(knowledge: KnowledgeBase) -> set[str]:
    labels = set(_EXTRA_FOLDER_LABELS)
    for layer in (knowledge.architectural_styles or {}).get("layers") or []:
        for raw in [layer.get("id"), layer.get("name"), *(layer.get("aliases") or [])]:
            if raw:
                labels.add(str(raw).casefold())
    return labels


def _bare_label(name: str) -> str:
    stripped = _DECORATION.sub(" ", name)
    return re.sub(r"[._/\-]+", " ", stripped).strip()


def folder_like_name(
    name: str,
    graph: RepositoryGraph,
    knowledge: KnowledgeBase | None = None,
) -> bool:
    """True when a box is a directory, layer, or package — not a component."""
    knowledge = knowledge or load_knowledge()
    if not name or not name.strip():
        return True
    if resolve_type(name, graph):
        return False
    bare = _bare_label(name)
    if not bare:
        return True
    labels = _layer_labels(knowledge)
    tokens = [t for t in bare.casefold().split() if t]
    if tokens and all(t in labels for t in tokens):
        return True
    last = name.replace("\\", "/").rstrip("/").split("/")[-1].split(".")[-1]
    if _DECORATION.sub("", last).strip().casefold() in labels:
        return True
    dirs = {Path(node.path).parent.name.casefold() for node in graph.nodes.values() if node.path}
    if bare.casefold() in dirs or last.casefold() in dirs:
        return True
    return False


def _scoped_names(graph: RepositoryGraph, scope: RepositoryScope | None) -> list[str]:
    if scope is None:
        return list(graph.nodes)
    paths = {c.path for c in scope.candidate_areas}
    names = [n for n, node in graph.nodes.items() if node.path in paths]
    return names or list(graph.nodes)


def _connected_types(
    graph: RepositoryGraph,
    *,
    prefer: list[str],
    scope: RepositoryScope | None,
    cap: int = _COMPONENT_CAP,
) -> list[str]:
    pool = _scoped_names(graph, scope)
    pool_set = set(pool)
    ranked = sorted(pool, key=lambda n: (-graph.degree(n), n))
    selected: list[str] = []
    seen: set[str] = set()
    for name in prefer:
        match = resolve_type(name, graph)
        if match and match in pool_set and match not in seen:
            selected.append(match)
            seen.add(match)
        if len(selected) >= cap:
            return selected
    if not selected and ranked:
        selected.append(ranked[0])
        seen.add(ranked[0])
    changed = True
    while len(selected) < cap and changed:
        changed = False
        for name in ranked:
            if name in seen:
                continue
            linked = any(
                name in graph.uses.get(s, ()) or s in graph.uses.get(name, ())
                for s in selected
            )
            if not linked and selected:
                continue
            selected.append(name)
            seen.add(name)
            changed = True
            if len(selected) >= cap:
                return selected
    for name in ranked:
        if len(selected) >= cap:
            break
        if name not in seen:
            selected.append(name)
            seen.add(name)
    return selected


def _replace_internals(
    vm: ViewModel,
    names: list[str],
    graph: RepositoryGraph,
) -> None:
    keep = [e for e in vm.elements if e.external or e.kind in {"actor", "system", "datastore", "external_system", "deployment_node"}]
    used = {e.name.casefold() for e in keep}
    next_i = 1
    internals: list[ViewElement] = []
    for name in names:
        if name.casefold() in used:
            continue
        node = graph.nodes.get(name)
        if node is None:
            continue
        internals.append(
            ViewElement(
                id=f"E{next_i}",
                name=name,
                kind="component",
                role=node.layer,
                evidence=Evidence(file=node.path, symbol=name, excerpt=f"{name} [{node.layer}]"),
                support="observed",
            )
        )
        used.add(name.casefold())
        next_i += 1
    for el in keep:
        el.id = f"E{next_i}"
        next_i += 1
    vm.elements = internals + keep
    vm.relations = []
    vm.groups = []
    vm.notes = list(dict.fromkeys(list(vm.notes) + ["rebuilt boxes from file-graph types, not directories"]))


def _insert_owner_calls(vm: ViewModel, graph: RepositoryGraph) -> int:
    owners = {e.id: owner_type(e, graph) for e in vm.elements}
    have: set[tuple[str, str]] = {(rel.frm, rel.to) for rel in vm.relations}
    ids = [e.id for e in vm.elements if not e.external and e.kind not in {"actor", "system", "datastore"}]
    added = 0
    extra = 0
    relations = list(vm.relations)
    order = max((r.order or 0 for r in relations), default=0)
    for src_id in ids:
        src_t = owners.get(src_id)
        if not src_t:
            continue
        for dst_t, method in sorted(graph.calls.get(src_t, ())):
            dst_id = next((i for i in ids if owners.get(i) == dst_t), None)
            if not dst_id or (src_id, dst_id) in have:
                continue
            order += 1
            have.add((src_id, dst_id))
            node = graph.nodes.get(src_t)
            relations.append(
                ViewRelation(
                    id=_next_relation_id(relations, extra),
                    frm=src_id,
                    to=dst_id,
                    kind="calls",
                    label=method or "calls",
                    order=order,
                    evidence=Evidence(
                        file=node.path if node else None,
                        symbol=src_t,
                        excerpt=f"{src_t} calls {dst_t}.{method}",
                    ),
                    support="observed",
                )
            )
            extra += 1
            added += 1
    vm.relations = relations
    return added


def _recover_architecture(
    vm: ViewModel,
    graph: RepositoryGraph,
    spec: ViewSpecification | None,
    scope: RepositoryScope | None,
    knowledge: KnowledgeBase,
) -> int:
    """Replace directory boxes with connected file-graph types and fill uses/calls."""
    vtype = _view_type(vm, spec)
    if vtype in _RUNTIME_VIEWS:
        return _insert_owner_uses(vm, graph)
    internals = [
        e
        for e in vm.elements
        if not e.external and e.kind not in {"actor", "system", "datastore", "external_system", "deployment_node"}
    ]
    prefer = [e.name for e in internals if not folder_like_name(e.name, graph, knowledge)]
    bad = [e for e in internals if folder_like_name(e.name, graph, knowledge)]
    need_rebuild = (not internals) or (len(bad) >= max(1, (len(internals) + 1) // 2))
    if need_rebuild:
        names = _connected_types(graph, prefer=prefer, scope=scope)
        _replace_internals(vm, names, graph)
    elif len(internals) > _COMPONENT_CAP:
        ranked = sorted(
            internals,
            key=lambda e: -(graph.degree(owner_type(e, graph) or e.name) if owner_type(e, graph) else 0),
        )
        keep_ids = {e.id for e in ranked[:_COMPONENT_CAP]}
        keep_ids |= {
            e.id
            for e in vm.elements
            if e.external or e.kind in {"actor", "system", "datastore", "external_system"}
        }
        vm.elements = [e for e in vm.elements if e.id in keep_ids]
        vm.relations = [r for r in vm.relations if r.frm in keep_ids and r.to in keep_ids]
        vm.notes = list(dict.fromkeys(list(vm.notes) + [f"kept {_COMPONENT_CAP} highest-degree components"]))
    added = _insert_owner_uses(vm, graph)
    if vtype == "sequence_view":
        added += _insert_owner_calls(vm, graph)
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
        added_rels = _recover_architecture(vm, graph, spec, scope, knowledge)
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

