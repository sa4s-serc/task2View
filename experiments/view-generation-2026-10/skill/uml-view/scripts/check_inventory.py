#!/usr/bin/env python3
"""check_inventory: check a view's inventory.json against the repository and the view's PlantUML source.

    python3 -I .claude/skills/uml-view/scripts/check_inventory.py view-out/<case>/inventory.json [--repo .]
        [--level overview|balanced|detailed] [--graph .claude/repo-graph.json]

The view source is view.puml next to the inventory. Checks:
  evidence      every "path:line" or "path:start-end" exists in the repository
  unbacked      every element and relation has evidence, or is marked "unknown" (reported, not an error)
  two-way       every element declared in view.puml is in the inventory, and every inventory element is drawn
  relations     every inventory relation is drawn, and every drawn relation is in the inventory
  concern       every concern detail says which elements answer it, or why it is not answered
  budget        element count against the uml-view budget for the model kind and the detail level (--level, the
                level given in the inputs, overrides the inventory's own detail_level)
  graph         with --graph: every element's "members" resolve to symbols; every drawn relation between two
                elements with members has at least one code dependency between them; dependencies between drawn
                elements that are not drawn are listed as "undrawn" (reported, not an error: draw them or say in
                the README why they are left out). Relations with an element that has no members are not checked.

Exit codes: 0 clean, 1 issues found, 2 the inventory or view could not be read.
Stdlib only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

BUDGET = {  # uml-view SKILL.md §1.3: (overview, balanced, detailed); None = no fixed cap
    "component": (7, 12, 20), "deployment": (7, 12, 20), "use case": (8, 8, None),
    "class": (7, 10, 15), "sequence": (5, 7, 7),
}
DECL = re.compile(r'^\s*(?:component|node|artifact|participant|actor|usecase|class|interface|enum|entity|'
                  r'boundary|control|database|collections|queue|package|frame|rectangle|abstract(?:\s+class)?)'
                  r'\s+("[^"]*"|[\w.:]+)(?:\s+<<[^>]*>>)?(?:\s+as\s+([\w.]+))?', re.I)
BRACKET = re.compile(r'^\s*\[([^\]]+)\]\s+as\s+([\w.]+)')
PAREN = re.compile(r'^\s*\(([^)]+)\)\s+as\s+([\w.]+)')
ARROW = re.compile(r'^\s*"?([\w.]+)"?\s*(?:"[^"]*"\s*)?([<o*|x}]*[-.]+(?:\[[^\]]*\])?(?:up|down|left|right)?[-.]*[>o*|x{]*)'
                   r'\s*(?:"[^"]*"\s*)?"?([\w.]+)"?')
EVIDENCE = re.compile(r'^(?P<path>[^:]+):(?P<a>\d+)(?:-(?P<b>\d+))?$')


def drawn(puml: str) -> tuple[set[str], set[tuple[str, str]]]:
    elements, relations = set(), set()
    for line in puml.splitlines():
        if line.strip().startswith("'"):
            continue
        m = DECL.match(line) or BRACKET.match(line) or PAREN.match(line)
        if m:
            name, alias = m.group(1), m.group(2)
            elements.add(alias or name.strip('"'))
            continue
        a = ARROW.match(line)
        if a and "hidden" not in a.group(2) and a.group(1) != a.group(3):
            relations.add((a.group(1), a.group(3)))
    return elements, relations


def check_evidence(ev, repo: Path, where: str, issues: list) -> bool:
    if ev in (None, [], ""):
        issues.append(("unbacked", f"{where}: no evidence; give path:line or \"unknown\""))
        return False
    if ev == "unknown":
        issues.append(("unbacked", f"{where}: marked unknown"))
        return False
    for e in ev if isinstance(ev, list) else [ev]:
        m = EVIDENCE.match(str(e).strip())
        if not m:
            issues.append(("evidence", f"{where}: '{e}' is not path:line"))
            continue
        f = repo / m["path"]
        if not f.is_file():
            issues.append(("evidence", f"{where}: {m['path']} does not exist"))
            continue
        n = sum(1 for _ in f.open(errors="replace"))
        last = int(m["b"] or m["a"])
        if int(m["a"]) < 1 or last > n:
            issues.append(("evidence", f"{where}: {e} is past the end of the file ({n} lines)"))
    return True


def graph_issues(inv: dict, graph_path: Path, issues: list) -> None:
    spec = importlib.util.spec_from_file_location("graph_query", Path(__file__).with_name("graph_query.py"))
    gq = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gq)
    try:
        graph = gq.load(str(graph_path))
    except (OSError, ValueError) as e:
        issues.append(("graph", f"cannot read {graph_path}: {e}"))
        return
    symbols = graph.get("symbols", {})
    members: dict[str, set[str]] = {}
    for e in inv.get("elements", []):
        specs = e.get("members") or []
        if not specs:
            continue
        ids = set()
        for s in specs:
            got = gq.resolve(s, symbols)
            if not got:
                issues.append(("graph", f"element {e['alias']}: member '{s}' matches no symbol"))
            ids |= got
        if ids:
            members[e["alias"]] = ids
    pairs = gq.edges_by_pair(graph)

    def between(a: str, b: str) -> list[dict]:
        found = []
        for x in members[a] - members[b]:
            for y in members[b] - members[a]:
                found += pairs.get((x, y), []) + pairs.get((y, x), [])
        return found

    drawn_pairs = set()
    for r in inv.get("relations", []):
        a, b = r.get("from"), r.get("to")
        if a in members and b in members and a != b:
            drawn_pairs.add(frozenset((a, b)))
            if not between(a, b):
                issues.append(("graph", f"{a}->{b} is drawn but the code has no dependency between their members"))
    aliases = sorted(members)
    for i, a in enumerate(aliases):
        for b in aliases[i + 1:]:
            if frozenset((a, b)) in drawn_pairs or members[a] >= members[b] or members[b] >= members[a]:
                continue  # drawn, or one element contains the other
            found = between(a, b)
            if found:
                issues.append(("undrawn", f"{a}--{b}: {len(found)} code dependencies, not drawn "
                                          f"(e.g. {found[0]['source']} -> {found[0]['target']} "
                                          f"at {found[0]['file']}:{found[0]['line']})"))
    unchecked = [e["alias"] for e in inv.get("elements", []) if e["alias"] not in members
                 and e.get("kind") != "message"]
    if unchecked:
        issues.append(("unchecked", f"no members, relations not checked against the graph: {', '.join(unchecked)}"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inventory")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--level", choices=["overview", "balanced", "detailed"],
                    help="the detail level given in the inputs; overrides the inventory's detail_level")
    ap.add_argument("--graph", help="the static dependency graph (.claude/repo-graph.json)")
    args = ap.parse_args()
    inv_path, repo = Path(args.inventory), Path(args.repo)
    try:
        inv = json.loads(inv_path.read_text())
        puml = (inv_path.parent / "view.puml").read_text()
    except (OSError, ValueError) as e:
        print(f"cannot read: {e}")
        return 2
    issues: list[tuple[str, str]] = []
    elements = {e["alias"]: e for e in inv.get("elements", [])}
    for alias, e in elements.items():
        check_evidence(e.get("evidence"), repo, f"element {alias}", issues)
    for r in inv.get("relations", []):
        check_evidence(r.get("evidence"), repo, f"relation {r.get('from')}->{r.get('to')}", issues)

    drawn_el, drawn_rel = drawn(puml)
    for a in sorted(drawn_el - set(elements)):
        issues.append(("two-way", f"{a} is drawn but not in the inventory"))
    for a in sorted({a for a, e in elements.items() if e.get("kind") != "message"} - drawn_el):
        issues.append(("two-way", f"{a} is in the inventory but not drawn"))
    inv_rel = {(r.get("from"), r.get("to")) for r in inv.get("relations", [])}
    undirected = lambda s: {frozenset(p) for p in s}
    for p in sorted(inv_rel):
        if frozenset(p) not in undirected(drawn_rel):
            issues.append(("relations", f"{p[0]}->{p[1]} is in the inventory but not drawn"))
    for p in sorted(drawn_rel):
        if frozenset(p) not in undirected(inv_rel) and p[0] in elements and p[1] in elements:
            issues.append(("relations", f"{p[0]}->{p[1]} is drawn but not in the inventory"))

    for d in inv.get("concern_details", []):
        if not d.get("answered_by") and not d.get("not_answered"):
            issues.append(("concern", f"'{d.get('detail')}': give answered_by or not_answered"))
        for a in d.get("answered_by") or []:
            if a not in elements:
                issues.append(("concern", f"'{d.get('detail')}': {a} is not an inventory element"))

    kind = str(inv.get("model_kind", "")).lower()
    level = str(inv.get("detail_level", "")).lower()
    if args.level:
        if level and level != args.level:
            issues.append(("budget", f"inventory says detail_level {level}, but the given level is {args.level}"))
        level = args.level
    caps = next((v for k, v in BUDGET.items() if k in kind), None)
    levels = ["overview", "balanced", "detailed"]
    if caps and level in levels:
        cap = caps[levels.index(level)]
        count = len(elements) if "sequence" not in kind else len({a for a, e in elements.items()
                                                                    if e.get("kind") != "message"})
        if cap is not None and count > cap:
            issues.append(("budget", f"{count} elements for a {level} {kind} view; budget is {cap}"))
    else:
        issues.append(("budget", "set model_kind and detail_level (overview, balanced or detailed)"))

    if args.graph:
        graph_issues(inv, Path(args.graph), issues)

    notes = {"unbacked", "undrawn", "unchecked"}
    errors = [i for i in issues if i[0] not in notes]
    for kind_, msg in issues:
        print(f"{kind_}: {msg}")
    print(f"{len(errors)} issues, {len(issues) - len(errors)} notes (unbacked, undrawn, unchecked), {len(elements)} elements, "
          f"{len(inv.get('relations', []))} relations")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
