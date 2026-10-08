"""Phase 5b — consolidate verified claims and card facts into the Architecture Evidence Model.

Deterministic (design 02 §6; ADR-006 D2: cluster deterministically, names from members):
- Components: every non-test code symbol a verified claim is about becomes the
  anchor of one component. Helper types (enums, records, exceptions, DTOs, and
  interfaces with a single implementer) are attached to the anchor that uses them
  most instead of becoming components. A component is named after its anchor
  symbol, so every name exists in the code.
- Relations between components are lifted from dependency-graph edges between
  their members; each keeps the member edges behind it.
- Entities and their attributes and associations come from persistence facts.
  Foreign-key fields stay attributes; associations follow object references.
- Deployment elements come from deploy and build units.
- Actors, use cases and states come from verified claims (and, for states, from
  status enums / state classes in the card).
- Scenarios are the verified interactions, ordered, with alternative fragments
  for claims that carry a condition.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from task2view.contracts.aem import (
    ArchElement, ArchRelation, Attribute, Claim, Correspondence, EvidenceModel, Fragment, Responsibility, Scenario, Step,
)
from task2view.contracts.card import RepositoryCard

_DEP_KINDS = {"calls", "field", "instantiates", "param", "returns"}
_ASSOC = {"many-to-one": ("*", "1"), "one-to-one": ("1", "1"), "one-to-many": ("1", "*"), "many-to-many": ("*", "*"),
          "collection": ("1", "*")}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "x"


def build_evidence_model(claims: list[Claim], card: RepositoryCard, cfg: dict) -> EvidenceModel:
    aem = EvidenceModel(claims={c.id: c for c in claims})
    _components(aem, claims, card, cfg)
    _component_relations(aem, card)
    _claim_elements(aem, claims)
    _claim_relations(aem, claims)
    _entities(aem, card, claims)
    _deployment(aem, card)
    _states(aem, card, claims)
    _scenarios(aem, claims)
    return aem


# ------------------------------------------------------------- components

def _claim_symbols(claims: list[Claim], card: RepositoryCard) -> list[str]:
    seen: list[str] = []
    for c in claims:
        for sid in (c.symbol, c.source, c.target):
            if sid in card.symbols and not card.symbols[sid].is_test and sid not in seen:
                seen.append(sid)
    return seen


def _is_helper(sid: str, card: RepositoryCard, cfg: dict) -> bool:
    s = card.symbols[sid]
    return s.kind in set(cfg["helper_kinds"]) or any(s.name.endswith(sfx) for sfx in cfg["helper_name_suffixes"])


def _components(aem: EvidenceModel, claims: list[Claim], card: RepositoryCard, cfg: dict) -> None:
    relevant = _claim_symbols(claims, card)
    implementers: dict[str, list[str]] = defaultdict(list)
    for e in card.edges:
        if e.kind == "implements":
            implementers[e.target].append(e.source)
    # an interface with one implementation in the view merges into that implementation
    merged_into: dict[str, str] = {}
    for sid in relevant:
        impls = implementers.get(sid, [])
        if card.symbols[sid].kind == "interface" and len(impls) == 1 and impls[0] in relevant:
            merged_into[sid] = impls[0]
    helpers = [s for s in relevant if s not in merged_into and _is_helper(s, card, cfg)]
    anchors = [s for s in relevant if s not in helpers and s not in merged_into]
    for sid in anchors:
        s = card.symbols[sid]
        eid = f"cmp:{sid}"
        aem.elements[eid] = ArchElement(id=eid, kind="component", name=s.name, realized_by=[sid], layer=s.layer,
                                        support="observed", named_by="symbol")
        aem.component_of[sid] = eid
    for iface, impl in merged_into.items():
        eid = aem.component_of[impl]
        aem.elements[eid].realized_by.append(iface)
        aem.component_of[iface] = eid
    links = Counter()
    for e in card.edges:
        if e.kind != "imports":
            links[(e.source, e.target)] += 1
            links[(e.target, e.source)] += 1
    for h in helpers:
        best = max(anchors, key=lambda a: (links[(a, h)], -anchors.index(a)), default=None)
        if best is not None and links[(best, h)]:
            eid = aem.component_of[best]
            aem.elements[eid].realized_by.append(h)
            aem.component_of[h] = eid
        else:  # used by no anchor: keep it visible as its own element
            s = card.symbols[h]
            eid = f"cmp:{h}"
            aem.elements[eid] = ArchElement(id=eid, kind="component", name=s.name, realized_by=[h], layer=s.layer,
                                            named_by="symbol")
            aem.component_of[h] = eid
    for c in claims:
        if c.kind == "element" and c.symbol in aem.component_of:
            el = aem.elements[aem.component_of[c.symbol]]
            el.claims.append(c.id)
            for text in c.responsibilities:
                if text.lower() not in {r.text.lower() for r in el.responsibilities}:
                    el.responsibilities.append(Responsibility(text=text, claims=[c.id]))


def _component_relations(aem: EvidenceModel, card: RepositoryCard) -> None:
    lifted: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    labels: dict[tuple[str, str, str], Counter] = defaultdict(Counter)
    for e in card.edges:
        src, tgt = aem.component_of.get(e.source), aem.component_of.get(e.target)
        if not src or not tgt or src == tgt:
            continue
        kind = "uses" if e.kind in _DEP_KINDS else "generalization" if e.kind in {"extends", "implements"} else None
        if kind is None:
            continue
        key = (src, tgt, kind)
        lifted[key].append(f"{e.source} -{e.kind}-> {e.target} ({e.file}:{e.line})")
        if e.kind == "calls" and e.detail:
            labels[key][e.detail] += 1
    for (src, tgt, kind), members in lifted.items():
        rid = f"rel:{slug(src)}:{kind}:{slug(tgt)}"
        label = ", ".join(m for m, _ in labels[(src, tgt, kind)].most_common(2)) or None
        aem.relations[rid] = ArchRelation(id=rid, kind=kind, source=src, target=tgt, label=label,
                                          member_edges=sorted(set(members))[:20], support="observed")


# ------------------------------------------------------- claim elements

def _element_id_for(aem: EvidenceModel, ref: str | None) -> str | None:
    if not ref:
        return None
    if ref in aem.component_of:
        return aem.component_of[ref]
    for el in aem.elements.values():
        if el.kind != "component" and el.name.lower() == ref.lower():
            return el.id
    return None


def _claim_elements(aem: EvidenceModel, claims: list[Claim]) -> None:
    for c in claims:
        if c.kind != "element" or c.symbol in aem.component_of or not c.name:
            continue
        kind = c.element_kind or "component"
        eid = f"{kind}:{slug(c.name)}"
        el = aem.elements.get(eid)
        if el is None:
            el = aem.elements[eid] = ArchElement(id=eid, kind=kind, name=c.name.strip(), support=c.support, named_by="model")
        el.claims.append(c.id)
        for text in c.responsibilities:
            if text.lower() not in {r.text.lower() for r in el.responsibilities}:
                el.responsibilities.append(Responsibility(text=text, claims=[c.id]))


def _claim_relations(aem: EvidenceModel, claims: list[Claim]) -> None:
    for c in claims:
        if c.kind != "relation":
            continue
        src, tgt = _element_id_for(aem, c.source), _element_id_for(aem, c.target)
        if not src or not tgt or src == tgt:
            continue
        kind = c.relation or "uses"
        existing = next((r for r in aem.relations.values() if r.source == src and r.target == tgt
                         and (r.kind == kind or r.kind == "uses")), None)
        if existing:
            existing.claims.append(c.id)
            if c.label and not existing.label:
                existing.label = c.label
            continue
        rid = f"rel:{slug(src)}:{slug(kind)}:{slug(tgt)}"
        aem.relations[rid] = ArchRelation(id=rid, kind=kind, source=src, target=tgt, label=c.label,
                                          claims=[c.id], support=c.support)


# ---------------------------------------------------------------- entities

def _entities(aem: EvidenceModel, card: RepositoryCard, claims: list[Claim]) -> None:
    by_symbol: dict[str, str] = {}
    for ent in card.entities:
        eid = f"ent:{ent.symbol or slug(ent.table or ent.name)}"
        attrs = []
        for f in ent.fields:
            if f.relation and f.target and f.relation != "embedded":
                continue  # an object reference is an association, not an attribute
            attrs.append(Attribute(name=f.name, type=f.type, key=f.key, foreign_key=bool(f.foreign_key)))
        aem.elements[eid] = ArchElement(id=eid, kind="entity", name=ent.name, realized_by=[ent.symbol] if ent.symbol else [],
                                        attributes=attrs, details={"source": ent.source, "file": ent.file,
                                                                   **({"table": ent.table} if ent.table else {})},
                                        named_by="fact")
        if ent.symbol:
            by_symbol[ent.symbol] = eid
            if ent.symbol in aem.component_of:
                aem.correspondences.append(Correspondence(rule="entity-realized-by-component",
                                                          elements=[eid, aem.component_of[ent.symbol]]))
    seen_pairs: set[frozenset] = set()
    for ent in card.entities:
        src = by_symbol.get(ent.symbol or "")
        for f in ent.fields:
            if not (f.relation and f.target in by_symbol and src):
                continue
            tgt = by_symbol[f.target]
            pair = frozenset((src, tgt, f.relation if f.relation == "embedded" else "assoc"))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            kind = "composition" if f.relation == "embedded" else "association"
            mult = _ASSOC.get(f.relation)
            rid = f"rel:{slug(src)}:{kind}:{slug(tgt)}:{slug(f.name)}"
            aem.relations[rid] = ArchRelation(id=rid, kind=kind, source=src, target=tgt, label=f.name,
                                              multiplicity=f"{mult[0]}..{mult[1]}" if mult else None,
                                              member_edges=[f"{ent.symbol}.{f.name} -{f.relation}-> {f.target}"],
                                              support="observed")
    for c in claims:  # attributes a claim adds to an entity
        if c.kind == "element" and c.symbol in by_symbol and c.attributes:
            el = aem.elements[by_symbol[c.symbol]]
            names = {a.name for a in el.attributes}
            el.attributes += [Attribute(name=a["name"], type=a.get("type"), key=bool(a.get("key")))
                              for a in c.attributes if a["name"] not in names]
            el.claims.append(c.id)


# -------------------------------------------------------------- deployment

def _deployment(aem: EvidenceModel, card: RepositoryCard) -> None:
    artifacts = []
    for b in card.build:
        if b.name:
            eid = f"artifact:{slug(b.name)}"
            aem.elements[eid] = ArchElement(id=eid, kind="artifact", name=f"{b.name}.{b.packaging or b.tool}",
                                            details={"tool": b.tool, "file": b.file}, named_by="fact")
            artifacts.append(eid)
    datastores: dict[str, str] = {}
    for u in card.deploy:
        if u.kind == "compose-service":
            image = str(u.details.get("image", ""))
            is_store = any(db in image for db in ("postgres", "mysql", "mariadb", "mongo", "redis", "oracle", "sqlserver", "cassandra"))
            eid = f"{'datastore' if is_store else 'node'}:{slug(u.name)}"
            aem.elements[eid] = ArchElement(id=eid, kind="datastore" if is_store else "node", name=u.name,
                                            details={k: str(v) for k, v in u.details.items()}, named_by="fact")
            if is_store:
                datastores[u.name] = eid
        elif u.kind == "dockerfile":
            base = (u.details.get("from") or [""])[0]
            eid = f"execution_env:{slug(u.file)}"
            aem.elements[eid] = ArchElement(id=eid, kind="execution_env", name=str(base) or u.file,
                                            details={"file": u.file}, named_by="fact")
        elif u.kind in {"persistence-unit", "app-config"}:
            url = str(u.details.get("jdbc_url") or u.details.get("spring.datasource.url") or "")
            m = re.match(r"jdbc:(\w+)://([^/:]+)(?::\d+)?/(\w+)", url)
            if not m:
                continue
            technology, host, database = m.groups()
            same = datastores.get(host) or datastores.get(database)  # the URL's host is a compose service
            if same:
                aem.elements[same].details.update({"technology": technology, "database": database, "url": url})
                continue
            eid = f"datastore:{slug(database)}"
            aem.elements.setdefault(eid, ArchElement(id=eid, kind="datastore", name=database,
                                                     details={"technology": technology, "host": host, "url": url},
                                                     named_by="fact"))
            datastores[database] = eid
    nodes = [e for e in aem.elements.values() if e.kind in {"node", "execution_env"}]
    stores = [e for e in aem.elements.values() if e.kind == "datastore"]
    for art in artifacts:
        for node in nodes[:1]:
            rid = f"rel:{slug(art)}:deploys:{slug(node.id)}"
            aem.relations[rid] = ArchRelation(id=rid, kind="deploys", source=art, target=node.id, support="inferred")
        for store in stores:
            tech = store.details.get("technology") or store.details.get("image", "")
            rid = f"rel:{slug(art)}:communicates:{slug(store.id)}"
            aem.relations[rid] = ArchRelation(id=rid, kind="communicates", source=art, target=store.id,
                                              label=tech or None, support="inferred")


# ------------------------------------------------------------------ states

def _states(aem: EvidenceModel, card: RepositoryCard, claims: list[Claim]) -> None:
    for s in card.symbols.values():
        if s.is_test:
            continue
        if s.kind == "enum" and re.search(r"(status|state)$", s.name, re.I):
            for const in s.enum_constants:
                eid = f"state:{slug(s.name)}:{slug(const)}"
                aem.elements[eid] = ArchElement(id=eid, kind="state", name=const, realized_by=[s.id],
                                                details={"machine": s.name}, named_by="symbol")
    implements = defaultdict(list)
    for e in card.edges:
        if e.kind in {"extends", "implements"} and re.search(r"(status|state)$", e.target.rsplit(".", 1)[-1], re.I):
            implements[e.target].append(e.source)
    for base, subs in implements.items():
        for sub in subs:
            name = card.symbols[sub].name
            eid = f"state:{slug(base.rsplit('.', 1)[-1])}:{slug(name)}"
            aem.elements.setdefault(eid, ArchElement(id=eid, kind="state", name=name, realized_by=[sub],
                                                     details={"machine": base.rsplit(".", 1)[-1]}, named_by="symbol"))
    for c in claims:
        if c.kind == "state" and c.name:
            eid = next((e.id for e in aem.elements.values() if e.kind == "state" and e.name.lower() == c.name.lower()),
                       f"state:claimed:{slug(c.name)}")
            el = aem.elements.setdefault(eid, ArchElement(id=eid, kind="state", name=c.name, named_by="model",
                                                          support=c.support))
            el.claims.append(c.id)
        elif c.kind == "transition" and c.source and c.target:
            src = next((e.id for e in aem.elements.values() if e.kind == "state" and e.name.lower() == str(c.source).lower()), None)
            tgt = next((e.id for e in aem.elements.values() if e.kind == "state" and e.name.lower() == str(c.target).lower()), None)
            if src and tgt:
                rid = f"rel:{slug(src)}:transition:{slug(tgt)}"
                aem.relations[rid] = ArchRelation(id=rid, kind="transition", source=src, target=tgt, label=c.label,
                                                  claims=[c.id], support=c.support)


# --------------------------------------------------------------- scenarios

def _scenarios(aem: EvidenceModel, claims: list[Claim]) -> None:
    grouped: dict[str, list[Claim]] = defaultdict(list)
    for c in claims:
        if c.kind == "interaction":
            grouped[c.scenario or c.task].append(c)
    for name, steps in grouped.items():
        sid = f"scn:{slug(name)}"
        scenario = Scenario(id=sid, name=name)
        fragments: dict[str, Fragment] = {}
        ordered = sorted(steps, key=lambda c: (c.order if c.order is not None else 10_000, c.id))
        merged: dict[tuple, Step] = {}  # the same step found by several agents keeps all its claims
        for c in ordered:
            src = _element_id_for(aem, c.source) or _actor(aem, c.source)
            tgt = _element_id_for(aem, c.target)
            if not src or not tgt:
                continue
            key = (c.order, src, tgt, c.label or c.relation or "call")
            if key in merged:
                merged[key].claims.append(c.id)
                continue
            frag = None
            if c.condition:
                guard = c.condition.strip()
                if guard not in fragments:
                    fragments[guard] = Fragment(id=f"{sid}:alt{len(fragments) + 1}", kind="alt", guard=guard)
                frag = fragments[guard].id
            merged[key] = Step(order=len(merged) + 1, source=src, target=tgt, message=c.label or c.relation or "call",
                               fragment=frag, claims=[c.id])
            scenario.steps.append(merged[key])
        scenario.fragments = list(fragments.values())
        if scenario.steps:
            aem.scenarios[sid] = scenario


def _actor(aem: EvidenceModel, name: str | None) -> str | None:
    if not name:
        return None
    eid = next((e.id for e in aem.elements.values() if e.kind == "actor" and e.name.lower() == name.lower()), None)
    return eid
