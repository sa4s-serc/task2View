#!/usr/bin/env python3
"""component_model: check a UML component model (model.json) and draw it, so a component view is valid by construction.

    python3 -I .claude/skills/uml-view/scripts/component_model.py check view-out/<case>/model.json [--graph .claude/repo-graph.json]
    python3 -I .claude/skills/uml-view/scripts/component_model.py build view-out/<case>/model.json [--graph .claude/repo-graph.json]

`build` checks the model and, if it has no errors, writes view.puml and inventory.json next to it (the inventory is
derived from the model, so check_inventory.py still applies). The PlantUML is generated here; do not edit it by hand.

model.json (UML 2.5.1 component diagram, Clause 11.6; Palladio-style: components meet through interfaces):
{"title": "Seat booking", "detail_level": "overview | balanced | detailed",
 "components": [{"id": "booking", "name": "Booking", "responsibility": "...", "members": ["it.app.booking.*"],
                 "evidence": ["src/...:12-40"], "parent": null, "stereotype": null,
                 "provides": ["IBooking"], "requires": ["IRepo"]}],
 "interfaces": [{"id": "IBooking", "name": "Booking API", "evidence": ["src/...:5"], "members": ["it.app.booking.BookingService"]}],
 "actors":     [{"id": "student", "name": "Student", "uses": ["IBooking"], "evidence": ["..."]}],
 "dependencies": [{"from": "booking", "to": "notify", "label": "notifies", "evidence": ["..."]}],
 "concern_details": [{"detail": "...", "answered_by": ["booking"]}, {"detail": "...", "not_answered": "why"}],
 "omitted": [{"name": "...", "reason": "..."}]}

Rules checked (errors unless marked "note"):
  ids           unique; every reference (parent, provides, requires, uses, dependency ends) exists
  interfaces    every interface is provided by a component, or marked "external": true
  connected     every component provides, requires or depends on something (an isolated box says nothing)
  stereotypes   only the UML standard profile ones that apply to components (Table 22.1): subsystem, service,
                process, entity, specification, realization, implement
  labels        dependency labels are 1-4 words and not method calls (no "(", no camelCase identifier)
  members       components (except ones marked "external": true) have members; with --graph every member spec
                matches symbols, and sibling components do not share symbols
  grain         note: a component whose members are one class (it may be a class drawn as a component)
  graph         with --graph: every required interface / dependency between components with members is backed by at
                least one code dependency between their members; dependencies between components that are not
                drawn are listed (note)
Stdlib only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

STEREOTYPES = {"subsystem", "service", "process", "entity", "specification", "realization", "implement"}
CAMEL = re.compile(r"^[a-z]+[A-Z]\w*$")


def graph_module():
    spec = importlib.util.spec_from_file_location("graph_query", Path(__file__).with_name("graph_query.py"))
    gq = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gq)
    return gq


def check(m: dict, graph_path: str | None) -> tuple[list[str], list[str]]:
    errors, notes = [], []
    comps = {c["id"]: c for c in m.get("components", [])}
    ifaces = {i["id"]: i for i in m.get("interfaces", [])}
    actors = {a["id"]: a for a in m.get("actors", [])}
    ids = [*comps, *ifaces, *actors]
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"ids: '{dup}' is used more than once")
    if not comps:
        errors.append("ids: no components")
    providers = {}
    for c in comps.values():
        if c.get("parent") and c["parent"] not in comps:
            errors.append(f"ids: {c['id']}: parent '{c['parent']}' is not a component")
        for i in c.get("provides", []) + c.get("requires", []):
            if i not in ifaces:
                errors.append(f"ids: {c['id']}: interface '{i}' is not declared")
        for i in c.get("provides", []):
            providers.setdefault(i, []).append(c["id"])
        if c.get("stereotype") and c["stereotype"].lower() not in STEREOTYPES:
            errors.append(f"stereotypes: {c['id']}: «{c['stereotype']}» is not a UML standard stereotype for "
                          f"components ({', '.join(sorted(STEREOTYPES))})")
        if not c.get("members") and not c.get("external"):
            errors.append(f"members: {c['id']}: no members (say which code it stands for, or mark it external)")
    for a in actors.values():
        for i in a.get("uses", []):
            if i not in ifaces:
                errors.append(f"ids: actor {a['id']}: interface '{i}' is not declared")
    for i, iface in ifaces.items():
        if i not in providers and not iface.get("external"):
            errors.append(f"interfaces: '{i}' is provided by no component (add the provider or mark it external)")
    deps = m.get("dependencies", [])
    for d in deps:
        for end in (d.get("from"), d.get("to")):
            if end not in comps:
                errors.append(f"ids: dependency {d.get('from')}->{d.get('to')}: '{end}' is not a component")
        label = str(d.get("label", "")).strip()
        if not label or len(label.split()) > 4 or "(" in label or CAMEL.match(label):
            errors.append(f"labels: dependency {d.get('from')}->{d.get('to')}: '{label}' should be 1-4 plain words, "
                          "not a method call")
    linked = {d.get("from") for d in deps} | {d.get("to") for d in deps}
    children = {c.get("parent") for c in comps.values()}
    for c in comps.values():
        if not (c.get("provides") or c.get("requires") or c["id"] in linked or c["id"] in children):
            errors.append(f"connected: {c['id']} provides, requires and depends on nothing")

    if graph_path:
        gq = graph_module()
        try:
            graph = gq.load(graph_path)
        except (OSError, ValueError) as e:
            errors.append(f"graph: cannot read {graph_path}: {e}")
            return errors, notes
        symbols, pairs = graph.get("symbols", {}), gq.edges_by_pair(graph)
        mem = {}
        for c in comps.values():
            ids_ = set()
            for spec in c.get("members", []):
                got = gq.resolve(spec, symbols)
                if not got:
                    errors.append(f"members: {c['id']}: '{spec}' matches no symbol")
                ids_ |= got
            if ids_:
                mem[c["id"]] = ids_
            if len(ids_) == 1 and not any(ch["parent"] == c["id"] for ch in comps.values() if ch.get("parent")):
                notes.append(f"grain: {c['id']} stands for one class ({next(iter(ids_))}); a component is usually a "
                             "group of classes behind an interface")
        siblings = {}
        for c in comps.values():
            siblings.setdefault(c.get("parent"), []).append(c["id"])
        for group in siblings.values():
            for i, a in enumerate(group):
                for b in group[i + 1:]:
                    shared = mem.get(a, set()) & mem.get(b, set())
                    if shared:
                        errors.append(f"members: {a} and {b} share {len(shared)} symbols (e.g. {sorted(shared)[0]})")

        def between(a: str, b: str) -> list:
            found = []
            for x in mem[a] - mem[b]:
                for y in mem[b] - mem[a]:
                    found += pairs.get((x, y), [])
            return found

        drawn = set()
        for c in comps.values():
            for i in c.get("requires", []):
                for p in providers.get(i, []):
                    if c["id"] in mem and p in mem and p != c["id"]:
                        drawn.add(frozenset((c["id"], p)))
                        if not between(c["id"], p):
                            errors.append(f"graph: {c['id']} requires {i} from {p}, but no code in {c['id']} depends "
                                          f"on code in {p}")
        for d in deps:
            a, b = d.get("from"), d.get("to")
            if a in mem and b in mem:
                drawn.add(frozenset((a, b)))
                if not between(a, b):
                    errors.append(f"graph: dependency {a}->{b} has no code dependency behind it")
        nested = lambda a, b: comps[a].get("parent") == b or comps[b].get("parent") == a
        keys = sorted(mem)
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                if frozenset((a, b)) in drawn or nested(a, b):
                    continue
                n = len(between(a, b)) + len(between(b, a))
                if n:
                    notes.append(f"undrawn: {a}--{b}: {n} code dependencies, not drawn")
    return errors, notes


def q(s: str) -> str:
    return str(s).replace('"', "'")


def render(m: dict) -> str:
    comps = {c["id"]: c for c in m.get("components", [])}
    lines = ["@startuml", "skinparam componentStyle uml2", "skinparam defaultFontName Helvetica",
             "skinparam linetype polyline", f"title cmp {q(m.get('title', 'Component view'))}", ""]
    for a in m.get("actors", []):
        lines.append(f'actor "{q(a["name"])}" as {a["id"]}')

    def emit(cid: str, indent: str) -> None:
        c = comps[cid]
        st = f" <<{c['stereotype'].lower()}>>" if c.get("stereotype") else ""
        kids = [k for k, v in comps.items() if v.get("parent") == cid]
        head = f'{indent}component "{q(c["name"])}" as {cid}{st}'
        if kids:
            lines.append(head + " {")
            for k in kids:
                emit(k, indent + "  ")
            lines.append(indent + "}")
        else:
            lines.append(head)

    for cid, c in comps.items():
        if not c.get("parent"):
            emit(cid, "")
    for i in m.get("interfaces", []):
        lines.append(f'interface "{q(i["name"])}" as {i["id"]}')
    lines.append("")
    for c in comps.values():
        for i in c.get("provides", []):
            lines.append(f"{c['id']} - {i}")
    for c in comps.values():
        for i in c.get("requires", []):
            lines.append(f"{c['id']} ..> {i} : <<use>>")
    for a in m.get("actors", []):
        for i in a.get("uses", []):
            lines.append(f"{a['id']} ..> {i} : <<use>>")
    for d in m.get("dependencies", []):
        lines.append(f"{d['from']} ..> {d['to']} : {q(d['label'])}")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def inventory(m: dict) -> dict:
    els = [{"alias": c["id"], "name": c["name"], "responsibility": c.get("responsibility", ""),
            "evidence": c.get("evidence", "unknown"), **({"members": c["members"]} if c.get("members") else {}),
             **({"parent": c["parent"]} if c.get("parent") else {})}
           for c in m.get("components", [])]
    provided_by = {}
    for c in m.get("components", []):
        for i in c.get("provides", []):
            provided_by.setdefault(i, []).extend(c.get("members", []))
    # an interface stands for the code of the components that provide it, unless the model names its own members
    els += [{"alias": i["id"], "name": i["name"], "kind": "interface", "evidence": i.get("evidence", "unknown"),
             **({"members": i.get("members") or provided_by[i["id"]]} if i.get("members") or provided_by.get(i["id"])
                else {})} for i in m.get("interfaces", [])]
    els += [{"alias": a["id"], "name": a["name"], "kind": "actor", "evidence": a.get("evidence", "unknown")}
            for a in m.get("actors", [])]
    rels = []
    for c in m.get("components", []):
        rels += [{"from": c["id"], "to": i, "label": "provides", "evidence": c.get("evidence", "unknown")}
                 for i in c.get("provides", [])]
        rels += [{"from": c["id"], "to": i, "label": "<<use>>", "evidence": c.get("evidence", "unknown")}
                 for i in c.get("requires", [])]
    for a in m.get("actors", []):
        rels += [{"from": a["id"], "to": i, "label": "<<use>>", "evidence": a.get("evidence", "unknown")}
                 for i in a.get("uses", [])]
    rels += [{"from": d["from"], "to": d["to"], "label": d["label"], "evidence": d.get("evidence", "unknown")}
             for d in m.get("dependencies", [])]
    return {"model_kind": "UML component diagram", "detail_level": m.get("detail_level", ""),
            "elements": els, "relations": rels, "concern_details": m.get("concern_details", []),
            "omitted": m.get("omitted", [])}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["check", "build"])
    ap.add_argument("model")
    ap.add_argument("--graph")
    args = ap.parse_args()
    path = Path(args.model)
    try:
        m = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        print(f"cannot read: {e}")
        return 2
    errors, notes = check(m, args.graph)
    for e in errors:
        print(f"error: {e}")
    for n in notes:
        print(f"note: {n}")
    print(f"{len(errors)} errors, {len(notes)} notes")
    if errors:
        return 1
    if args.cmd == "build":
        (path.parent / "view.puml").write_text(render(m), encoding="utf-8")
        (path.parent / "inventory.json").write_text(json.dumps(inventory(m), indent=1), encoding="utf-8")
        print(f"wrote {path.parent / 'view.puml'} and inventory.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
