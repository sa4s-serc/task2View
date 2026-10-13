"""Named viewpoint constraints (catalog `constraints`), one predicate each.

A predicate returns the violations it finds as (mark id, message). Mark ids are
element or relation ids, so a repair can remove exactly the offending marks.
Every predicate is general: it reads the view, the viewpoint record, the AEM and
the repository card, never a particular repository's names.
"""

from __future__ import annotations

from collections.abc import Callable

from task2view.contracts.aem import EvidenceModel
from task2view.contracts.card import RepositoryCard
from task2view.contracts.views import ArchitectureView
from task2view.knowledge.catalog import Viewpoint

Violation = tuple[str, str]
Predicate = Callable[[ArchitectureView, Viewpoint, EvidenceModel, RepositoryCard], list[Violation]]

_GROUP_KINDS = {"layer", "module", "tier", "system", "node", "execution_env"}
_CONTAINS = {"layer": {"component", "module", "class", "interface", "service", "lifeline"},
             "module": {"component", "module", "class", "interface", "service"},
             "tier": {"component", "datastore", "module"},
             "system": {"use_case"},
             "node": {"artifact", "execution_env", "component", "datastore"},
             "execution_env": {"artifact", "component"}}
_OVERLAY_RELATIONS = {"layered": {"allowed-to-use"}}
PREDICATES: dict[str, Predicate] = {}


def predicate(name: str):
    def wrap(fn: Predicate) -> Predicate:
        PREDICATES[name] = fn
        return fn
    return wrap


@predicate("element_kind_allowed")
def _element_kind_allowed(view, vp, aem, card):
    allowed = set(vp.element_kinds)
    return [(e.id, f"{e.name}: kind {e.kind!r} is not a {vp.name} element") for e in view.elements
            if e.kind not in allowed and not (e.group and e.kind in _GROUP_KINDS)]


@predicate("relation_kind_allowed")
def _relation_kind_allowed(view, vp, aem, card):
    allowed = set(vp.relation_kinds) | {k for o in view.overlays for k in _OVERLAY_RELATIONS.get(o, set())}
    return [(r.id, f"relation kind {r.kind!r} is not a {vp.name} relation") for r in view.relations if r.kind not in allowed]


@predicate("max_elements")
def _max_elements(view, vp, aem, card):
    n = len(view.content_elements())
    return [(view.id, f"{n} elements exceed the cap of {view.max_elements}")] if n > view.max_elements else []


@predicate("no_package_or_directory_element")
def _no_package_or_directory_element(view, vp, aem, card):
    containers = {seg.lower() for s in card.symbols.values() for seg in s.package.split(".") if seg} | \
                 {seg.lower() for f in card.files for seg in f.path.split("/")[:-1]}
    software = {"component", "module", "class", "interface", "service", "lifeline", "system"}
    return [(e.id, f"{e.name!r} is a package or directory name, not an architectural element")
            for e in view.content_elements()
            if e.kind in software and e.name.lower() in containers and not e.realized_by]


@predicate("component_has_responsibility")
def _component_has_responsibility(view, vp, aem, card):
    return [(e.id, f"{e.name} shows no responsibility") for e in view.content_elements()
            if e.kind in {"component", "module"} and not e.responsibilities]


@predicate("nesting_well_formed")
def _nesting_well_formed(view, vp, aem, card):
    by_id = {e.id: e for e in view.elements}
    out = []
    for e in view.elements:
        if e.parent is None:
            continue
        parent = by_id.get(e.parent)
        if parent is None:
            out.append((e.id, f"{e.name}: parent {e.parent!r} is not in the view"))
        elif e.kind not in _CONTAINS.get(parent.kind, set()):
            out.append((e.id, f"{e.name} ({e.kind}) cannot be nested in {parent.name} ({parent.kind})"))
    return out


@predicate("lifeline_is_component_or_actor")
def _lifeline_is_component_or_actor(view, vp, aem, card):
    out = []
    for e in view.content_elements():
        if e.kind not in {"lifeline", "actor"}:
            out.append((e.id, f"{e.name}: a sequence participant must be a lifeline or an actor"))
        elif e.kind == "lifeline":
            el = aem.elements.get(e.id)
            if el is None or el.kind not in {"component", "external_system", "datastore"}:
                out.append((e.id, f"{e.name}: lifeline is not a component of the evidence model"))
    return out


@predicate("messages_ordered")
def _messages_ordered(view, vp, aem, card):
    orders = [i.order for i in view.interactions]
    return [] if orders == sorted(set(orders)) else [(view.id, "interaction order is not a strict sequence")]


@predicate("message_backed_by_call_evidence")
def _message_backed(view, vp, aem, card):
    steps = {(st.source, st.target, st.message): st for s in aem.scenarios.values() for st in s.steps}
    return [(view.id, f"message {i.order} {i.message!r} has no claim") for i in view.interactions
            if not (steps.get((i.source, i.target, i.message)) and steps[(i.source, i.target, i.message)].claims)]


@predicate("association_not_fk_field")
def _association_not_fk_field(view, vp, aem, card):
    out = []
    by_id = {e.id: e for e in view.elements}
    for r in view.relations:
        if r.kind != "association" or not r.label:
            continue
        src = by_id.get(r.source)
        fks = {a.name.lower() for a in (src.attributes if src else []) if a.foreign_key}
        if r.label.lower() in fks or r.label.lower().endswith("_id") or (r.label.endswith("Id") and len(r.label) > 2):
            out.append((r.id, f"association {r.label!r} is a foreign-key field; it belongs inside {src.name if src else r.source}"))
    return out


@predicate("entity_has_attributes")
def _entity_has_attributes(view, vp, aem, card):
    return [(e.id, f"{e.name} shows no attributes") for e in view.content_elements() if e.kind == "entity" and not e.attributes]


@predicate("one_system_box")
def _one_system_box(view, vp, aem, card):
    n = sum(1 for e in view.elements if e.kind == "system")
    return [] if n == 1 else [(view.id, f"{n} system boxes; expected exactly one")]


@predicate("actor_outside_boundary")
def _actor_outside_boundary(view, vp, aem, card):
    systems = {e.id for e in view.elements if e.kind == "system"}
    return [(e.id, f"actor {e.name} is drawn inside the system") for e in view.elements if e.kind == "actor" and e.parent in systems]


@predicate("node_contains_artifact")
def _node_contains_artifact(view, vp, aem, card):
    hosts = {e.id for e in view.elements if e.kind in {"node", "execution_env"}}
    if not hosts:
        return []
    return [(e.id, f"artifact {e.name} is not allocated to a node") for e in view.elements
            if e.kind == "artifact" and e.parent not in hosts]


@predicate("relation_has_evidence")
def _relation_has_evidence(view, vp, aem, card):
    out = []
    for r in view.relations:
        rel = aem.relations.get(r.id)
        if r.id.startswith(("rel:fold:", "conn:")) or (rel is None and r.support == "inferred"):
            continue  # folded, projection-inferred, or lifted from code by the abstraction step (ADR-007)
        if rel is None or not (rel.member_edges or rel.claims):
            out.append((r.id, f"relation {r.source} -> {r.target} has no evidence"))
    return out


@predicate("no_isolated_element")
def _no_isolated_element(view, vp, aem, card):
    linked = {r.source for r in view.relations} | {r.target for r in view.relations} | \
             {i.source for i in view.interactions} | {i.target for i in view.interactions}
    return [(e.id, f"{e.name} takes part in no relation") for e in view.content_elements() if e.id not in linked]


def check_constraints(view: ArchitectureView, vp: Viewpoint, aem: EvidenceModel, card: RepositoryCard,
                      severities: dict[str, dict]) -> list[dict]:
    findings = []
    for name in vp.constraints:
        fn = PREDICATES.get(name)
        if fn is None:
            findings.append({"constraint": name, "severity": "error", "mark": view.id, "message": "no predicate implemented"})
            continue
        for mark, message in fn(view, vp, aem, card):
            findings.append({"constraint": name, "severity": severities.get(name, {}).get("severity", "error"),
                             "mark": mark, "message": message})
    return findings
