"""Phase 7 — project the Architecture Evidence Model onto one view (ADR-006 D3; design 03 §4).

Deterministic. Projection selects AEM entries relevant to the view's questions and
subjects, maps them to the kinds the viewpoint allows, and adds structure the
viewpoint calls for (layer nesting for the layered overlay, the system boundary
for use cases, nodes around artifacts). It never invents, renames or merges an
element. When the selection exceeds the detail-level cap, the rest is listed in
`overflow` for Phase 6 to decide on.
"""

from __future__ import annotations

from collections import Counter

from task2view.contracts.aem import ArchElement, EvidenceModel, Question
from task2view.contracts.card import RepositoryCard
from task2view.contracts.views import (
    ArchitectureView, Interaction, TraceRow, ViewAttribute, ViewElement, ViewFragment, ViewRelation,
)
from task2view.knowledge.catalog import Catalog, Viewpoint
from task2view.phase0.corpus import corpus_rules
from task2view.phase3.selection import PlannedView
from task2view.phase4.investigate import overlap, tokens

ENTITY_KINDS = {"entity", "enum"}
SCENARIO_KINDS = {"uml-sequence", "uml-communication", "uml-activity"}


def project_view(
    view_id: str,
    planned: PlannedView,
    questions: list[Question],
    aem: EvidenceModel,
    card: RepositoryCard,
    catalog: Catalog,
    *,
    target: str = "",
    fold: bool = False,
    exclude: set[str] | None = None,
) -> ArchitectureView:
    """Project one view. ``fold`` (Phase 6 simplify) groups components by layer or package;
    ``exclude`` (Phase 8 repair) leaves out marks that failed validation."""
    vp = catalog.viewpoint(planned.viewpoint_id)
    qids = [q.id for q in questions if q.view_id == view_id]
    cap = int(planned.granularity.get("max_elements") or 10)
    focus = " ".join([target, *planned.subjects])
    view = ArchitectureView(
        id=view_id, viewpoint_id=vp.id, viewpoint_name=vp.name, vb_ref=vp.vb_ref, model_kind=vp.model_kind,
        title=f"{vp.name} view — {target or card.name}", detail_level=planned.detail_level, max_elements=cap,
        purpose=f"{vp.name} ({vp.vb_ref}) answering {', '.join(planned.needs)}" + (f" for {target}" if target else ""),
        addresses=qids, overlays=list(planned.overlays),
    )
    if planned.evidence_gap:
        view.gaps.append(planned.evidence_gap)
    if vp.model_kind in SCENARIO_KINDS:
        _scenario(view, vp, aem, qids, focus)
    elif vp.model_kind == "uml-state":
        _states(view, aem, focus)
    elif vp.model_kind == "uml-usecase":
        _use_cases(view, aem, card)
    elif vp.id == "context":
        _context(view, aem, card)
    elif vp.model_kind == "uml-deployment":
        _deployment(view, vp, aem)
    elif "entity" in vp.element_kinds:
        _data_model(view, aem, card, focus)
    elif vp.model_kind == "table":
        _table(view, vp, aem)
    else:
        _structure(view, vp, aem, qids, focus, fold=fold)
    if exclude:
        view.elements = [e for e in view.elements if e.id not in exclude]
        ids = {e.id for e in view.elements}
        view.relations = [r for r in view.relations if r.id not in exclude and r.source in ids and r.target in ids]
        view.interactions = [i for i in view.interactions if i.source in ids and i.target in ids]
        view.limitations.append(f"{len(exclude)} mark(s) removed after failing validation")
    _traceability(view, aem, card)
    return view


# ------------------------------------------------------------- helpers

def _relevance(aem: EvidenceModel, el: ArchElement, qids: list[str], focus_tokens: set[str]) -> tuple:
    claimed = sum(1 for c in el.claims if set(aem.claims[c].question_ids) & set(qids)) if qids else 0
    named = overlap(focus_tokens, tokens(el.name)) if focus_tokens else 0
    return (claimed, named, len(el.responsibilities), len(el.claims))


def _cap(view: ArchitectureView, ranked: list[ArchElement], reserve: int = 0) -> list[ArchElement]:
    room = max(view.max_elements - reserve, 0)
    kept, rest = ranked[:room], ranked[room:]
    view.overflow = [e.id for e in rest]
    if rest:
        view.limitations.append(f"{len(rest)} further element(s) exceed the {view.detail_level} cap of {view.max_elements}")
    return kept


def _view_kind(el: ArchElement, vp: Viewpoint) -> str:
    if el.kind in vp.element_kinds:
        return el.kind
    for alt in ("component", "module", "class", "service"):
        if alt in vp.element_kinds:
            return alt
    return vp.element_kinds[0]


def _layers(view: ArchitectureView, elements: list[ViewElement]) -> None:
    if "layered" not in view.overlays:
        return
    order = [layer["id"] for layer in corpus_rules()["layers"]]
    names = {layer["id"]: layer["name"] for layer in corpus_rules()["layers"]}
    used = [lid for lid in order if any(e.stereotype == lid for e in elements)]
    groups = [ViewElement(id=f"group:layer:{lid}", kind="layer", name=names[lid], group=True) for lid in used]
    for e in elements:
        if e.stereotype in used:
            e.parent = f"group:layer:{e.stereotype}"
    view.elements[:0] = groups


def _packages(view: ArchitectureView, elements: list[ViewElement]) -> None:
    """Nest components in the package (module) of their anchor symbol when there is more than one."""
    packages = {e.id: e.realized_by[0].rsplit(".", 1)[0] for e in elements if e.realized_by and "." in e.realized_by[0]}
    if len(set(packages.values())) < 2:
        return
    groups = []
    for pkg in sorted(set(packages.values())):
        groups.append(ViewElement(id=f"group:module:{pkg}", kind="module", name=pkg.rsplit(".", 1)[-1], group=True,
                                  realized_by=[pkg]))
    for e in elements:
        if e.id in packages:
            e.parent = f"group:module:{packages[e.id]}"
    view.elements[:0] = groups


def _relations(view: ArchitectureView, aem: EvidenceModel, kinds: set[str], rename: dict[str, str] | None = None) -> None:
    ids = {e.id for e in view.elements}
    for r in aem.relations.values():
        if r.kind in kinds and r.source in ids and r.target in ids:
            view.relations.append(ViewRelation(id=r.id, kind=(rename or {}).get(r.kind, r.kind), source=r.source,
                                               target=r.target, label=r.label, multiplicity=r.multiplicity,
                                               support=r.support))


def _element(el: ArchElement, kind: str, *, stereotype: str | None = None) -> ViewElement:
    return ViewElement(id=el.id, kind=kind, name=el.name, stereotype=stereotype,
                       responsibilities=[r.text for r in el.responsibilities],
                       attributes=[ViewAttribute(**a.model_dump()) for a in el.attributes],
                       realized_by=list(el.realized_by), support=el.support)


# --------------------------------------------------------- structural views

def _structure(view: ArchitectureView, vp: Viewpoint, aem: EvidenceModel, qids: list[str], focus: str,
               *, fold: bool = False) -> None:
    ftok = tokens(focus)
    comps = [e for e in aem.elements.values() if e.kind == "component"]
    if vp.id == "uses":
        comps = _uses_neighbourhood(aem, comps, qids, ftok)
    elif vp.id == "generalization":
        in_hierarchy = {r.source for r in aem.relations.values() if r.kind == "generalization"} | \
                       {r.target for r in aem.relations.values() if r.kind == "generalization"}
        comps = [c for c in comps if c.id in in_hierarchy]
    ranked = sorted(comps, key=lambda e: _relevance(aem, e, qids, ftok), reverse=True)
    if fold:
        _folded(view, vp, aem, ranked)
        return
    stores = [e for e in aem.elements.values() if e.kind == "datastore"] if "datastore" in vp.element_kinds else []
    stores = stores if any(e.layer == "persistence" for e in ranked) else []
    kept = _cap(view, ranked, reserve=len(stores))
    elements = [_element(el, _view_kind(el, vp), stereotype=el.layer) for el in kept]
    view.elements.extend(elements)
    writers = [e for e in elements if e.stereotype == "persistence"]
    store_kind = next((k for k in ("writes", "uses") if k in vp.relation_kinds), vp.relation_kinds[0])
    for store in stores if writers else []:
        view.elements.append(_element(store, "datastore"))
        view.relations.extend(ViewRelation(id=f"rel:{e.id}:{store_kind}:{store.id}", kind=store_kind, source=e.id,
                                           target=store.id, support="inferred") for e in writers)
    if vp.id == "generalization":
        _relations(view, aem, {"generalization"}, {"generalization": "is-a"})
    elif vp.id == "layered":
        _relations(view, aem, {"uses"}, {"uses": "allowed-to-use"})
    elif "uses" in vp.relation_kinds or vp.family == "cnc":
        _relations(view, aem, {"uses"}, {"uses": "uses" if "uses" in vp.relation_kinds else vp.relation_kinds[0]})
    if not elements:
        view.gaps.append(f"no components evidenced for the {vp.name.lower()} view")
    # decomposition draws is-part-of as nesting, not as edges
    _layers(view, elements)
    if vp.id == "decomposition" and "layered" not in view.overlays:
        _packages(view, elements)


def _folded(view: ArchitectureView, vp: Viewpoint, aem: EvidenceModel, ranked: list[ArchElement]) -> None:
    """Coarser grain: one element per layer (or package when there are no layers), listing its components."""
    names = {layer["id"]: layer["name"] for layer in corpus_rules()["layers"]}
    groups: dict[str, list[ArchElement]] = {}
    for el in ranked:
        key = el.layer or (el.realized_by[0].rsplit(".", 1)[0] if el.realized_by and "." in el.realized_by[0] else "other")
        groups.setdefault(key, []).append(el)
    member_of = {}
    kind = "module" if "module" in vp.element_kinds else _view_kind(ranked[0], vp) if ranked else "component"
    keys = list(groups)
    if len(keys) > view.max_elements:
        view.overflow = [m.id for k in keys[view.max_elements:] for m in groups[k]]
        view.limitations.append(f"{len(keys) - view.max_elements} further group(s) exceed the cap of {view.max_elements}")
    for key in keys[: view.max_elements]:
        members = groups[key]
        fid = f"fold:{key}"
        for m in members:
            member_of[m.id] = fid
        view.elements.append(ViewElement(id=fid, kind=kind, name=names.get(key, key.rsplit(".", 1)[-1]),
                                         stereotype=key if key in names else None,
                                         responsibilities=[f"{m.name}" + (f": {m.responsibilities[0].text}" if m.responsibilities else "")
                                                           for m in members[:6]] + ([f"… {len(members) - 6} more"] if len(members) > 6 else []),
                                         realized_by=[m.id for m in members]))
    lifted: dict[tuple[str, str], int] = {}
    for r in aem.relations.values():
        a, b = member_of.get(r.source), member_of.get(r.target)
        if r.kind == "uses" and a and b and a != b:
            lifted[(a, b)] = lifted.get((a, b), 0) + 1
    rel_kind = "allowed-to-use" if vp.id == "layered" else ("uses" if "uses" in vp.relation_kinds else vp.relation_kinds[0])
    for (a, b), n in lifted.items():
        view.relations.append(ViewRelation(id=f"rel:{a}:{rel_kind}:{b}", kind=rel_kind, source=a, target=b,
                                           label=f"{n} dependencies"))
    view.limitations.append("simplified to one element per layer or package (Phase 6)")


def _uses_neighbourhood(aem: EvidenceModel, comps: list[ArchElement], qids: list[str], ftok: set[str]) -> list[ArchElement]:
    """Focus components (claimed for this view or named in the focus) plus what uses them and what they use."""
    focus = [c for c in comps if _relevance(aem, c, qids, ftok)[:2] != (0, 0)]
    if not focus:
        return comps
    ids = {c.id for c in focus}
    near = Counter()
    for r in aem.relations.values():
        if r.kind != "uses":
            continue
        if r.target in ids and r.source not in ids:
            near[r.source] += 2  # dependents matter most for change impact
        elif r.source in ids and r.target not in ids:
            near[r.target] += 1
    by_id = {c.id: c for c in comps}
    return focus + [by_id[i] for i, _ in near.most_common() if i in by_id]


def _data_model(view: ArchitectureView, aem: EvidenceModel, card: RepositoryCard, focus: str) -> None:
    ftok = tokens(focus)
    entities = [e for e in aem.elements.values() if e.kind == "entity"]
    if ftok:
        scored = sorted(entities, key=lambda e: (overlap(ftok, tokens(e.name)), len(e.attributes)), reverse=True)
        if overlap(ftok, tokens(scored[0].name) if scored else set()):
            seeds = {e.id for e in scored if overlap(ftok, tokens(e.name))}
            linked = {r.target for r in aem.relations.values() if r.source in seeds and r.kind in {"association", "composition"}} | \
                     {r.source for r in aem.relations.values() if r.target in seeds and r.kind in {"association", "composition"}}
            entities = [e for e in scored if e.id in seeds] + [e for e in scored if e.id in linked - seeds]
    kept = _cap(view, entities)
    view.elements.extend(_element(e, "entity", stereotype="entity") for e in kept)
    _relations(view, aem, {"association", "composition"})
    sym_to_ent = {s: e.id for e in kept for s in e.realized_by}
    for edge in card.edges:
        if edge.kind == "extends" and edge.source in sym_to_ent and edge.target in sym_to_ent:
            view.relations.append(ViewRelation(id=f"rel:{edge.source}:generalization:{edge.target}", kind="generalization",
                                               source=sym_to_ent[edge.source], target=sym_to_ent[edge.target],
                                               support="inferred"))
    if not entities:
        view.gaps.append("no persisted entities found in the repository")


# ------------------------------------------------------- behavioural views

def _scenario(view: ArchitectureView, vp: Viewpoint, aem: EvidenceModel, qids: list[str], focus: str) -> None:
    scenarios = list(aem.scenarios.values())
    if not scenarios:
        view.gaps.append("no verified interactions: the order of calls could not be recovered")
        return
    ftok = tokens(focus)

    def score(s):
        claimed = sum(1 for st in s.steps for c in st.claims if set(aem.claims[c].question_ids) & set(qids))
        return (claimed, overlap(ftok, tokens(s.name)), len(s.steps))

    scenarios.sort(key=score, reverse=True)
    chosen = scenarios[0]
    view.scenario = chosen.name
    if len(scenarios) > 1:
        view.limitations.append(f"one scenario per view; also recovered: {', '.join(s.name for s in scenarios[1:])}")
    participants: list[str] = []
    for st in chosen.steps:
        for pid in (st.source, st.target):
            if pid not in participants:
                participants.append(pid)
    if len(participants) > view.max_elements:
        view.overflow = participants[view.max_elements:]
        view.limitations.append(f"{len(view.overflow)} participant(s) exceed the {view.detail_level} cap")
        participants = participants[: view.max_elements]
    kind = "lifeline" if "lifeline" in vp.element_kinds else "component" if "component" in vp.element_kinds else "action"
    for pid in participants:
        el = aem.elements[pid]
        view.elements.append(_element(el, "actor" if el.kind == "actor" else kind, stereotype=el.layer))
    allowed = set(vp.fragments) if vp.id == "sequence" else {"alt"}
    level_fragments = set(vp.granularity.get(view.detail_level, {}).get("fragments", list(allowed)))
    frag_ids = {f.id for f in chosen.fragments if f.kind in allowed and f.kind in level_fragments}
    view.fragments = [ViewFragment(id=f.id, kind=f.kind, guard=f.guard) for f in chosen.fragments if f.id in frag_ids]
    for st in chosen.steps:
        if st.source in participants and st.target in participants:
            view.interactions.append(Interaction(order=st.order, source=st.source, target=st.target, message=st.message,
                                                 kind=st.kind, fragment=st.fragment if st.fragment in frag_ids else None))
    if len(frag_ids) < len(chosen.fragments):
        view.limitations.append(f"alternative paths beyond the {view.detail_level} level are not drawn")


def _states(view: ArchitectureView, aem: EvidenceModel, focus: str) -> None:
    states = [e for e in aem.elements.values() if e.kind == "state"]
    machines = Counter(e.details.get("machine", "") for e in states)
    if not machines:
        view.gaps.append("no element with explicit states found")
        return
    ftok = tokens(focus)
    machine = max(machines, key=lambda m: (overlap(ftok, tokens(m)), machines[m]))
    chosen = [e for e in states if e.details.get("machine", "") == machine]
    view.scenario = machine
    view.elements.extend(_element(e, "state") for e in _cap(view, chosen))
    _relations(view, aem, {"transition"})
    if not view.relations:
        view.limitations.append("states are recovered from code; transitions were not evidenced")


def _use_cases(view: ArchitectureView, aem: EvidenceModel, card: RepositoryCard) -> None:
    actors = [e for e in aem.elements.values() if e.kind == "actor"]
    cases = [e for e in aem.elements.values() if e.kind == "use_case"]
    system = ViewElement(id="group:system", kind="system", name=card.name, group=True)
    view.elements.append(system)
    view.elements.extend(_element(a, "actor") for a in actors)
    for uc in _cap(view, cases):
        el = _element(uc, "use_case")
        el.parent = system.id
        view.elements.append(el)
    _relations(view, aem, {"association", "include", "extend", "generalization", "uses"}, {"uses": "association"})
    if not cases:
        view.gaps.append("no use cases were evidenced")


def _context(view: ArchitectureView, aem: EvidenceModel, card: RepositoryCard) -> None:
    """The system as one box; actors, external systems and datastores around it, linked where evidence links them."""
    outer = {"actor", "external_system", "datastore"}
    system = ViewElement(id="system", kind="system", name=card.name, realized_by=[card.name])
    kept = _cap(view, [e for e in aem.elements.values() if e.kind in outer], reserve=1)
    view.elements += [system, *(_element(e, e.kind) for e in kept)]
    ids = {e.id for e in kept}
    inside = {e.id for e in aem.elements.values() if e.kind not in outer}
    edges = {(system.id, e.id) for e in kept if e.kind == "datastore"}
    for r in aem.relations.values():
        if r.source in ids and r.target in inside:
            edges.add((r.source, system.id))
        elif r.target in ids and r.source in inside:
            edges.add((system.id, r.target))
    view.relations += [ViewRelation(id=f"rel:{a}:uses:{b}", kind="uses", source=a, target=b, support="inferred")
                       for a, b in sorted(edges)]
    if not kept:
        view.gaps.append("no actors, external systems or datastores were evidenced")


def _deployment(view: ArchitectureView, vp: Viewpoint, aem: EvidenceModel) -> None:
    kinds = set(vp.element_kinds)
    picked = [e for e in aem.elements.values() if e.kind in kinds]
    for e in _cap(view, picked):
        view.elements.append(_element(e, e.kind))
    ids = {e.id for e in view.elements}
    for r in aem.relations.values():
        if r.kind == "deploys" and r.source in ids and r.target in ids:
            view.element(r.source).parent = r.target  # node ⊃ artifact
    _relations(view, aem, {"communicates", "contains"})  # deploys is drawn as nesting
    if not picked:
        view.gaps.append("no deployment descriptors or build units found")


def _table(view: ArchitectureView, vp: Viewpoint, aem: EvidenceModel) -> None:
    if vp.id == "implementation":  # components, mapped to their files by the traceability table
        rows = [e for e in aem.elements.values() if e.kind == "component"]
    else:  # modules and components alone do not answer an interface, decision or requirement table
        rows = [e for e in aem.elements.values() if e.kind in set(vp.element_kinds) - {"module", "component"}]
    view.elements.extend(_element(e, _view_kind(e, vp)) for e in _cap(view, rows))
    if not rows:
        view.gaps.append(f"no evidence for {vp.name.lower()}")


# ------------------------------------------------------------ traceability

def _traceability(view: ArchitectureView, aem: EvidenceModel, card: RepositoryCard) -> None:
    for e in view.content_elements():
        members = [aem.elements[m] for m in e.realized_by if m in aem.elements]  # folded elements list AEM ids
        symbols = [s for s in e.realized_by if s in card.symbols] + [s for m in members for s in m.realized_by]
        files = sorted({card.symbols[s].file for s in symbols})
        el = aem.elements.get(e.id)
        if el is not None and not files:
            files = sorted({ref.file for c in el.claims if c in aem.claims for ref in aem.claims[c].evidence})
            if not files and el.details.get("file"):
                files = [el.details["file"]]
        view.traceability.append(TraceRow(element=e.id, name=e.name, files=files, symbols=symbols))
