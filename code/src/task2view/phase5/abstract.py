"""ADR-007 step 3 — abstraction: group the classes behind the evidence into named architectural parts.

Deterministic; no model call (an optional naming call can rename or split parts afterwards).
1. Scope: the classes the verified evidence is about, plus the entry points that call them
   (API, UI, jobs) when their names share the request's vocabulary, and the data access,
   domain and integration classes they reach (two hops). This completes the path from where a
   request enters to where its data is stored.
2. Roles: each class gets a role from framework and naming conventions (element_roles.yaml).
   Helpers (DTOs, factories, strategies, enums) join the one part that uses them; a helper
   used by several parts (a data type passed between them) is listed, not drawn.
3. Parts: one part per role; facts add the database (deployment config) and the web client
   (web pages that call the API). Every part lists its member classes or files.
4. Connectors: code dependencies between members of two parts, merged into one arrow labelled
   with the intent for that pair of roles. Dependencies the layering does not allow are kept
   and marked; weak or implied relations are left out and listed.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from functools import lru_cache
from importlib import resources
from pathlib import Path

import yaml

from task2view.contracts.aem import EvidenceModel
from task2view.contracts.architecture import ArchView, Connector, Part
from task2view.contracts.card import RepositoryCard, Symbol
from task2view.phase4.investigate import tokens

_GENERIC = {"manager", "registry", "controller", "service", "facade", "selection", "util", "impl", "base", "abstract",
            "handler", "dto", "factory", "strategy", "functionality", "feature", "system", "data", "user", "users"}
_DEP_KINDS = {"calls", "field", "param", "returns", "instantiates", "extends", "implements"}
MIN_WEIGHT = 3  # weaker relations are listed, not drawn (unless they go against the layering)


@lru_cache(maxsize=1)
def role_catalog() -> dict:
    path = resources.files("task2view.knowledge.data").joinpath("vb", "element_roles.yaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _simple(name: str) -> str:
    return name.split("(", 1)[0].split("<", 1)[0].rsplit(".", 1)[-1]


def role_of(sym: Symbol, card: RepositoryCard, entry_kinds: dict[str, set[str]], entity_ids: set[str]) -> str:
    """Strongest evidence wins across roles: framework facts (entry points, annotations, supertypes,
    persisted entity, kind), then the class name, then the package; within a level, catalogue order."""
    cat = role_catalog()
    annotations = {_simple(a) for a in sym.annotations}
    supertypes = {_simple(t) for t in sym.extends + sym.implements}
    segments = {s.lower() for s in sym.package.split(".")} | {s.lower() for s in sym.file.split("/")[:-1]}
    levels = (
        lambda r: bool(entry_kinds.get(sym.id, set()) & set(r.get("entry", []))
                       or annotations & set(r.get("annotations", [])) or supertypes & set(r.get("supertypes", []))
                       or (r.get("entity") and sym.id in entity_ids) or sym.kind in r.get("kinds", [])),
        lambda r: any(sym.name.endswith(x) for x in r.get("suffixes", []))
                  or any(sym.name.startswith(x) for x in r.get("prefixes", [])),
        lambda r: bool(segments & {p.lower() for p in r.get("packages", [])}),
    )
    roles = [r for r in cat["roles"] if r["id"] != "bootstrap"]
    for matches in levels:
        hit = next((r["id"] for r in roles if matches(r)), None)
        if hit:
            return hit
    # start-up/configuration only when nothing else identifies the class (screens may have main())
    boot = next(r for r in cat["roles"] if r["id"] == "bootstrap")
    if any(matches(boot) for matches in levels):
        return "bootstrap"
    return cat["layer_fallback"].get(sym.layer or "", "service")


def _links(card: RepositoryCard) -> tuple[dict, dict]:
    out, inc = defaultdict(Counter), defaultdict(Counter)
    for e in card.edges:
        if e.kind in _DEP_KINDS and e.source != e.target:
            out[e.source][e.target] += 1
            inc[e.target][e.source] += 1
    return out, inc


def abstract_view(card: RepositoryCard, aem: EvidenceModel, *, target: str = "", title: str = "",
                  granularity: str = "medium", arrows: bool = True, subjects: dict[str, set[str]] | None = None,
                  max_parts: int = 99) -> ArchView:
    """``granularity``: "medium" (one part per role) or "coarse" (one part per layer).
    ``arrows``: False for decomposition views, which show containment only.
    ``subjects``: the request's enumerated subjects with this view's question ids; with two or more,
    parts are split along them where different classes answer them, within ``max_parts``."""
    cat = role_catalog()
    entry_kinds: dict[str, set[str]] = defaultdict(set)
    for ep in card.entry_points:
        entry_kinds[ep.symbol].add(ep.kind)
    entity_ids = {e.symbol for e in card.entities if e.symbol}
    prod = {sid: s for sid, s in card.symbols.items() if not s.is_test and s.kind != "module"}
    role = {sid: role_of(s, card, entry_kinds, entity_ids) for sid, s in prod.items()}
    out, inc = _links(card)

    # 1. scope: evidence classes, entry points that call them, and what they reach downstream
    core = {m for el in aem.elements.values() if el.kind == "component" for m in el.realized_by if m in prod}
    # the request's vocabulary: its words, the core classes' names, and the domain classes they use
    used_domain = {t for s in core for t in out[s] if t in prod and role[t] == "domain"}
    focus = (tokens(target) | {t for sid in core | used_domain if role[sid] not in {"helper", "bootstrap"}
                               for t in tokens(prod[sid].name)}) - _GENERIC
    on_topic = lambda sid: bool(tokens(prod[sid].name) & focus)  # noqa: E731
    scope = set(core)
    for sid in core:
        for caller in inc[sid]:
            if caller in prod and role[caller] in {"ui", "api", "job"} and on_topic(caller):
                scope.add(caller)
    for _ in range(3):  # screens reached through other screens (wizards, navigation)
        scope |= {n for s in scope if role[s] == "ui" for n in list(out[s]) + list(inc[s])
                  if n in prod and role[n] == "ui" and on_topic(n)}
    frontier = set(scope)
    for _ in range(2):
        nxt = {t for s in frontier for t in out[s] if t in prod and role[t] in {"data_access", "domain", "integration"}}
        frontier = nxt - scope
        scope |= nxt
    helpers = {t for s in scope if role[s] not in {"domain", "data_access"}
               for t in list(out[s]) + list(inc[s]) if t in prod and role[t] == "helper"}

    # 2-3. parts by role; helpers join the part of the member that uses them most
    members: dict[str, list[str]] = defaultdict(list)
    for sid in sorted(scope):
        if role[sid] not in {"helper", "bootstrap"}:
            members[role[sid]].append(sid)
    shared = []
    for h in sorted(helpers | {s for s in scope if role[s] == "helper"}):
        users = {u for u in scope if role[u] not in {"helper", "bootstrap"} and out[u][h] + out[h][u]}
        roles_using = {role[u] for u in users}
        if len(roles_using) == 1:
            members[roles_using.pop()].append(h)
        elif roles_using:  # a data type passed between parts belongs to none of them: no arrows through it
            shared.append(prod[h].name)
    view = ArchView(title=title or f"Architecture view{' — ' + target if target else ''}")
    tech = _technologies(card)
    degree = lambda m: sum(out[m].values()) + sum(inc[m].values())  # noqa: E731
    for r in sorted(members, key=lambda r: cat["rank"].get(r, 9)):
        ms = sorted(members[r], key=lambda m: (m not in core, -degree(m), prod[m].name))  # most relevant first
        named = [prod[m].name for m in ms if role[m] != "helper"]
        view.parts.append(Part(id=r, name=cat["labels"].get(r, r), role=r, technology=tech.get(r, ""), members=ms,
                               examples=named[:3]))
    _fact_parts(view, card, tech)
    if granularity == "coarse":
        _coarsen(view)
    elif subjects and len(subjects) >= 2:
        _split_by_subjects(view, card, aem, subjects, role, max_parts)
    mark_answers(view, aem, subjects or {})
    if shared:
        view.notes.append(f"shared data types (not drawn, no arrows through them): {', '.join(shared)}")
    bootstrap = sorted(prod[s].name for s in core if role[s] == "bootstrap")
    if bootstrap:
        view.notes.append(f"not drawn (start-up and configuration): {', '.join(bootstrap)}")
    lift_connectors(view, card, arrows=arrows)
    return view


def _subject_counts(aem: EvidenceModel, subjects: dict[str, set[str]]) -> dict[str, Counter]:
    """For each class, how many verified claims about it answer each subject's questions."""
    counts: dict[str, Counter] = defaultdict(Counter)
    for c in aem.claims.values():
        hit = [s for s, ids in subjects.items() if set(c.question_ids) & ids]
        for sym in {c.symbol, c.source, c.target} - {None}:
            for s in hit:
                counts[sym][s] += 1
    return counts


def _split_by_subjects(view: ArchView, card: RepositoryCard, aem: EvidenceModel, subjects: dict[str, set[str]],
                       role: dict[str, str], max_parts: int) -> None:
    """A detailed request lists what it wants to understand; give each subject its own part where the
    evidence puts it in different classes (services first, then API, UI, integration, data access).
    To make room, client parts that answer no subject become one part; afterwards, application parts
    answering the same subject are combined. If the view still exceeds ``max_parts``, it is left as it
    was (each part keeps the subjects it answers as a label)."""
    before = view.model_copy(deep=True)
    mark_answers(view, aem, subjects)
    clients = [p for p in view.parts if p.role in {"web_client", "ui"} and not p.answers]
    if len(clients) >= 2:
        merged = Part(id="clients", name="Clients", role="ui",
                      technology=", ".join(dict.fromkeys(p.technology for p in clients if p.technology)),
                      members=[m for p in clients for m in p.members], files=[f for p in clients for f in p.files],
                      examples=[p.name for p in clients])
        at = view.parts.index(clients[0])
        view.parts = [p for p in view.parts if p not in clients]
        view.parts.insert(at, merged)
    counts = _subject_counts(aem, subjects)
    order = list(subjects)
    split_any = False
    for r in ("service", "api", "ui", "integration", "data_access"):
        part = next((p for p in view.parts if p.id == r), None)
        if part is None:
            continue
        groups: dict[str, list[str]] = defaultdict(list)
        rest = []
        for m in part.members:
            if role.get(m) != "helper" and counts.get(m):
                best = max(counts[m].items(), key=lambda kv: (kv[1], -order.index(kv[0])))[0]
                groups[best].append(m)
            else:
                rest.append(m)
        if len(groups) < 2:
            continue
        largest = max(groups, key=lambda s: len(groups[s]))
        groups[largest] += rest  # helpers and unclaimed classes stay with the largest group
        at = view.parts.index(part)
        view.parts[at:at + 1] = [
            Part(id=f"{r}-{k + 1}", name=_subject_name(s), role=r, technology=part.technology, members=groups[s],
                 examples=[card.symbols[m].name for m in groups[s] if role.get(m) != "helper"][:3])
            for k, s in enumerate(sorted(groups, key=order.index))]
        split_any = True
    if not split_any:
        view.parts, view.notes = before.parts, before.notes
        return
    mark_answers(view, aem, subjects)
    by_subject: dict[str, list[Part]] = defaultdict(list)
    for p in view.parts:
        if p.role in {"service", "integration", "job"} and p.answers:
            by_subject[p.answers[0]].append(p)
    for s, same in by_subject.items():
        if len(same) > 1:  # e.g. the notification manager, its scheduler and its e-mail adapter
            keep = same[0]
            keep.role = "service" if any(p.role == "service" for p in same) else keep.role
            keep.name = _subject_name(s)
            for p in same[1:]:
                keep.members += p.members
                keep.examples = (keep.examples + p.examples)[:3]
                keep.technology = ", ".join(dict.fromkeys(t for t in (keep.technology, p.technology) if t))
            view.parts = [p for p in view.parts if p not in same[1:]]
    if len(view.parts) > max_parts:
        view.parts, view.notes = before.parts, before.notes + [
            f"subjects shown as labels: one part per subject would exceed {max_parts} parts"]
        return
    view.notes.append("parts follow the request's subjects: " + ", ".join(order))


def _subject_name(subject: str) -> str:
    words = " ".join(subject.split()[:5])
    return words[:1].upper() + words[1:]


def mark_answers(view: ArchView, aem: EvidenceModel, subjects: dict[str, set[str]]) -> None:
    counts = _subject_counts(aem, subjects) if subjects else {}
    for p in view.parts:
        hits = Counter()
        for m in p.members:
            hits.update(counts.get(m, {}))
        p.answers = [s for s, _ in hits.most_common()]


def shape_for_viewpoint(view: ArchView, viewpoint_id: str, aem: EvidenceModel, focus_questions: set[str]) -> None:
    """Each viewpoint answers its own question from the same parts.
    client-server: the path requests take, from where they enter to the database (plus flagged arrows).
    uses: what is affected when the part being changed changes: that part, everything depending on it
    (transitively), and what it uses directly. decomposition has no arrows (set by the caller)."""
    roles = {p.id: p.role for p in view.parts}
    entries = {p for p, r in roles.items() if r in {"web_client", "ui", "api", "job", "presentation"}}
    if viewpoint_id in {"client-server", "multi-tier"} and entries:
        reach, frontier = set(entries), set(entries)
        while frontier:
            frontier = {c.target for c in view.connectors if c.source in frontier} - reach
            reach |= frontier
        kept = [c for c in view.connectors if c.source in reach or c.against_layering]
        view.omitted += [f"{view.part(c.source).name} -> {view.part(c.target).name}: not on a request path"
                         for c in view.connectors if c not in kept]
        view.connectors = kept
    elif viewpoint_id == "uses":
        claims = Counter()
        for p in view.parts:
            for m in p.members:
                for c in aem.claims.values():
                    if m in {c.symbol, c.source, c.target} and (not focus_questions or set(c.question_ids) & focus_questions):
                        claims[p.id] += 1
        # the part being changed is logic, not where requests enter: entry parts are what depends on it
        logic = [p for p, _ in claims.most_common() if roles[p] not in {"database", "web_client", "ui", "api", "job"}]
        focus = logic[:1] or [p for p, _ in claims.most_common(1) if roles[p] not in {"database", "web_client"}]
        if not focus:
            return
        view.focus = focus
        dependents, frontier = set(focus), set(focus)
        while frontier:
            frontier = {c.source for c in view.connectors if c.target in frontier} - dependents
            dependents |= frontier
        kept = [c for c in view.connectors
                if c.target in dependents or c.source in focus or c.against_layering]
        view.omitted += [f"{view.part(c.source).name} -> {view.part(c.target).name}: not affected by a change to "
                         f"{view.part(focus[0]).name}" for c in view.connectors if c not in kept]
        view.connectors = kept
        for c in view.connectors:
            if c.target in dependents and not c.against_layering:
                c.label = "depends on"


_WEB = (".html", ".htm", ".js", ".ts", ".jsx", ".tsx")
_LAYERS = {"web_client": "presentation", "ui": "presentation", "api": "presentation", "job": "application",
           "service": "application", "integration": "application", "domain": "domain", "data_access": "data_access"}


def _coarsen(view: ArchView) -> None:
    """Coarse grain: one part per layer (presentation, application, domain, data access) plus the database."""
    cat = role_catalog()
    merged: dict[str, Part] = {}
    for p in view.parts:
        layer = _LAYERS.get(p.role)
        if layer is None:
            merged[p.id] = p
            continue
        into = merged.setdefault(layer, Part(id=layer, name=cat["labels"][layer], role=layer))
        into.members += p.members
        into.files += p.files
        into.technology = ", ".join(t for t in dict.fromkeys([*into.technology.split(", "), p.technology]) if t)
        into.examples.append(p.name)
    view.parts = sorted(merged.values(), key=lambda p: cat["rank"].get(p.role, 9))


def lift_connectors(view: ArchView, card: RepositoryCard, *, arrows: bool = True) -> None:
    """(Re)compute the arrows from the parts' members: code dependencies merged per pair of parts,
    plus the facts that link the web client and the database. Weak or implied relations are listed."""
    cat = role_catalog()
    view.connectors, view.omitted = [], []
    if not arrows:  # decomposition: containment only
        return
    prod = card.symbols
    owner = {m: p.id for p in view.parts for m in p.members}
    lifted: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for e in card.edges:
        a, b = owner.get(e.source), owner.get(e.target)
        if e.kind in _DEP_KINDS and a and b and a != b:
            lifted[(a, b)][f"{prod[e.source].name} -> {prod[e.target].name}"] += 1
    by_role = {p.role: p.id for p in view.parts}
    store = by_role.get("data_access")
    if "database" in by_role and store:
        lifted[(store, "database")]["persistence unit (deployment config)"] += MIN_WEIGHT
    web = next((p.id for p in view.parts if any(f.endswith(_WEB) for f in p.files)), None)
    api = next((p.id for p in view.parts if p.role == "api"), None)
    if web and api and web != api:
        lifted[(web, api)]["web pages call /api routes"] += MIN_WEIGHT
    roles = {p.id: p.role for p in view.parts}
    for (a, b), ev in sorted(lifted.items(), key=lambda x: -sum(x[1].values())):
        ra, rb = roles[a], roles[b]
        weight = sum(ev.values())
        against = ra != rb and rb not in cat["allowed"].get(ra, [rb]) and ra != "web_client"
        implied = ra == "data_access" and rb == "domain"
        if weight < MIN_WEIGHT or (implied and not against):
            reason = "implied: storage returns domain objects" if implied else "weak" + (", against the layering" if against else "")
            view.omitted.append(f"{view.part(a).name} -> {view.part(b).name}: {weight} code dependencies ({reason})")
            continue
        view.connectors.append(Connector(
            source=a, target=b, weight=weight, against_layering=against,
            label=cat["connectors"].get(f"{ra}>{rb}", "uses" if ra == rb else "depends on"),
            protocol="HTTP/JSON" if (a, b) == (web, api) else _protocol(ra, rb, card),
            evidence=[f"{k} ({n})" for k, n in ev.most_common(5)]))


def _technologies(card: RepositoryCard) -> dict[str, str]:
    deps = {d.lower() for b in card.build for d in b.dependencies}
    spring = any("spring-boot" in d for d in deps)
    jpa = any(k in d for d in deps for k in ("hibernate", "jpa", "eclipselink"))
    lang = next(iter(sorted(card.languages, key=lambda k: -card.languages[k])), "")
    return {"api": "Spring Boot REST" if spring else "HTTP API", "ui": "Java Swing" if "gui-client" in card.signals else "UI",
            "service": lang.capitalize(), "domain": "JPA entities" if jpa else "domain classes",
            "data_access": "JPA / Hibernate" if jpa else "data access", "job": "scheduled", "integration": "adapters"}


def _fact_parts(view: ArchView, card: RepositoryCard, tech: dict) -> None:
    for unit in card.deploy:
        url = str(unit.details.get("jdbc_url") or unit.details.get("spring.datasource.url") or "")
        m = re.match(r"jdbc:(\w+):(?://[^/]+/|.*?:)(\w+)", url)
        if m and not any(p.role == "database" for p in view.parts):
            engine = {"mysql": "MySQL", "postgresql": "PostgreSQL", "mariadb": "MariaDB", "h2": "H2"}.get(m.group(1), m.group(1))
            view.parts.append(Part(id="database", name=f"{engine} database", role="database", technology=engine,
                                   examples=[m.group(2)], files=[unit.file]))
    if any(p.role == "api" for p in view.parts):
        root = Path(card.root)
        pages = []
        for f in card.files:
            if f.file_class == "web" and f.path.endswith((".html", ".js", ".ts", ".jsx", ".tsx")):
                try:
                    if re.search(r"""['"`]/api\b|fetch\(|axios""", (root / f.path).read_text(errors="replace")):
                        pages.append(f.path)
                except OSError:
                    continue
        if pages:
            view.parts.insert(0, Part(id="web_client", name="Web client", role="web_client", technology="HTML / JavaScript",
                                      examples=[Path(p).name for p in pages[:3]], files=pages))


def _protocol(a: str, b: str, card: RepositoryCard) -> str:
    if a == "web_client":
        return "HTTP/JSON"
    if b == "database":
        return "JPA / JDBC"
    if a in {"ui", "api", "job", "presentation"}:
        return "in-process"
    return ""


_NAME = re.compile(r"^[A-Za-z][\w&/' -]{1,39}$")


def roles_of(card: RepositoryCard) -> dict[str, str]:
    entry_kinds: dict[str, set[str]] = defaultdict(set)
    for ep in card.entry_points:
        entry_kinds[ep.symbol].add(ep.kind)
    entity_ids = {e.symbol for e in card.entities if e.symbol}
    return {sid: role_of(s, card, entry_kinds, entity_ids) for sid, s in card.symbols.items()
            if not s.is_test and s.kind != "module"}


def name_parts(view: ArchView, card: RepositoryCard, aem: EvidenceModel, runtime, *, goal: str,
               purpose: str = "phase5c", max_parts: int = 99, single_class_parts: bool = True) -> ArchView:
    """One model call: architectural names, one-line descriptions, optional splits. Every reply is
    checked; what fails keeps the code's default, and arrows are recomputed from the code. A split
    is kept only if each new part has a class that is not a helper (no parts made of data types
    only) and the view stays within ``max_parts``; with ``single_class_parts`` False (requests that are
    not detailed), each new part also needs two or more classes."""
    from task2view.contracts.models import PipelineError
    from task2view.prompts import load_prompt

    nameable = [p for p in view.parts if p.members]
    if not nameable:
        return view
    simple = {m: card.symbols[m].name for p in nameable for m in p.members if m in card.symbols}
    lines = []
    for p in nameable:
        resp = {r.text for m in p.members if m in aem.component_of for r in aem.elements[aem.component_of[m]].responsibilities}
        lines.append(f"- id: {p.id} | role: {p.role} | current name: {p.name} | technology: {p.technology}"
                     + (f" | answers the request's: {'; '.join(p.answers)}" if p.answers else "") + "\n"
                     f"  members: {', '.join(simple[m] for m in p.members if m in simple)}\n"
                     f"  responsibilities: {'; '.join(sorted(resp)[:6]) or 'none verified'}")
    try:
        reply = runtime.complete_json(load_prompt("phase5c_name").render(goal=goal, parts="\n".join(lines)), purpose=purpose)
    except PipelineError as exc:
        view.notes.append(f"naming kept the defaults: {str(exc)[:120]}")
        return view
    class_names = set(simple.values()) | {mt.name for s in card.symbols.values() for mt in s.methods}
    by_id = {p.id: p for p in nameable}

    def good_name(name, part_size):
        return isinstance(name, str) and _NAME.match(name.strip()) and (part_size == 1 or name.strip() not in class_names)

    for row in reply.get("parts") or []:
        p = by_id.get(str((row or {}).get("id")))
        if p is None:
            continue
        if good_name(row.get("name"), len(p.members)):
            p.name = row["name"].strip()
        desc = str(row.get("description") or "").strip()
        if desc and len(desc.split()) <= 12:
            p.description = desc
    role = roles_of(card)
    for split in reply.get("splits") or []:
        p = by_id.get(str((split or {}).get("id")))
        groups = split.get("into") if isinstance(split, dict) else None
        if p is None or not isinstance(groups, list) or not 2 <= len(groups) <= 3:
            continue
        if len(view.parts) - 1 + len(groups) > max_parts:
            view.notes.append(f"split of {p.name} not applied: the view would exceed {max_parts} parts")
            continue
        by_simple = {simple[m]: m for m in p.members if m in simple}
        assigned = [[by_simple.get(str(x)) for x in (g.get("members") or [])] for g in groups if isinstance(g, dict)]
        flat = [m for g in assigned for m in g]
        if None in flat or sorted(flat) != sorted(by_simple.values()) or len(assigned) != len(groups) \
                or not all(good_name(g.get("name"), len(a)) for g, a in zip(groups, assigned)) \
                or not all(any(role.get(m) != "helper" for m in a) for a in assigned) \
                or not (single_class_parts or all(sum(role.get(m) != "helper" for m in a) >= 2 for a in assigned)):
            view.notes.append(f"split of {p.name} rejected: members must be partitioned exactly, each part with a non-helper class")
            continue
        at = view.parts.index(p)
        new = [Part(id=f"{p.id}-{k + 1}", name=g["name"].strip(), role=p.role, technology=p.technology, members=a,
                    description=str(g.get("description") or "")[:100],
                    examples=[simple[m] for m in a][:3]) for k, (g, a) in enumerate(zip(groups, assigned))]
        view.parts[at:at + 1] = new
    lift_connectors(view, card, arrows=bool(view.connectors) or bool(view.omitted))
    return view
