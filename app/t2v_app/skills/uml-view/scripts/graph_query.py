#!/usr/bin/env python3
"""graph_query: query the repository's static dependency graph (.claude/repo-graph.json).

    python3 -I .claude/skills/uml-view/scripts/graph_query.py summary
    python3 -I .claude/skills/uml-view/scripts/graph_query.py search TERM [TERM ...]
    python3 -I .claude/skills/uml-view/scripts/graph_query.py around NAME [--depth 2] [--tests]
    python3 -I .claude/skills/uml-view/scripts/graph_query.py members SPEC [SPEC ...]

The graph is built from the code only, before the session (tree-sitter): symbols (classes, interfaces, ...),
dependencies between them (imports, extends, implements, fields, parameters, returns, instantiates, calls,
annotations) with file:line, entry points, persisted entities, deployment and build files. It does not contain
framework wiring done at run time, databases, external systems or users.

  summary   languages, layers, packages, entry points, entities, deployment, build, most depended-on symbols
  search    symbols, methods, routes and entities whose names contain the terms (case-insensitive), most matches
            first: where the concern lives in the code
  around    what NAME depends on and what depends on it, up to --depth hops; NAME is a symbol id, a simple class
            name or a member spec
  members   which symbols a member spec stands for (see below)

Member specs, as used in inventory.json "members":
  pkg.sub.Class   one symbol (tests included only when named like this)
  pkg.sub.*       every non-test symbol in that package and its subpackages
  path/to/dir/    every non-test symbol in files under that path (a path to one file also works)

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT = ".claude/repo-graph.json"


def load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def resolve(spec: str, symbols: dict) -> set[str]:
    """Symbol ids a member spec stands for."""
    spec = spec.strip()
    if spec.endswith(".*"):
        pkg = spec[:-2]
        return {i for i, s in symbols.items() if not s.get("is_test")
                and (s.get("package") == pkg or s.get("package", "").startswith(pkg + ".") or i.startswith(pkg + "."))}
    if "/" in spec:
        return {i for i, s in symbols.items() if not s.get("is_test")
                and (s["file"] == spec or s["file"].startswith(spec.rstrip("/") + "/"))}
    if spec in symbols:
        return {spec}
    return {i for i, s in symbols.items() if s["name"] == spec}


def edges_by_pair(graph: dict) -> dict[tuple[str, str], list[dict]]:
    pairs = defaultdict(list)
    for e in graph.get("edges", []):
        if e["source"] != e["target"]:
            pairs[(e["source"], e["target"])].append(e)
    return pairs


def summary(g: dict) -> None:
    sym = g.get("symbols", {})
    print(f"REPOSITORY {g.get('name')}")
    print("languages: " + ", ".join(f"{k} ({v} files)" for k, v in sorted(g.get("languages", {}).items())))
    if g.get("layers"):
        print("layers (top to bottom):")
        for layer, pkgs in g["layers"].items():
            print(f"  {layer}: {', '.join(pkgs)}")
    pkgs = Counter(s.get("package", "") for s in sym.values() if not s.get("is_test"))
    print(f"packages ({len(pkgs)}), non-test symbols per package:")
    for p, n in sorted(pkgs.items()):
        print(f"  {p or '(default)'}: {n}")
    eps = g.get("entry_points", [])
    print(f"entry points ({len(eps)}):")
    for e in eps:
        print(f"  {e['kind']} {e['symbol']} {e.get('detail', '')} ({e['file']}:{e['line']})")
    if g.get("entities"):
        print(f"persisted entities ({len(g['entities'])}):")
        for ent in g["entities"]:
            rel = [f"{f['name']}->{(f.get('target') or '').rsplit('.', 1)[-1]}" for f in ent.get("fields", [])
                   if f.get("relation")]
            print(f"  {ent['name']} [{ent['source']}] {ent['file']}" + (f" relations: {', '.join(rel)}" if rel else ""))
    for d in g.get("deploy", []):
        print(f"deploy/config: {d['kind']} {d['name']} ({d['file']}) {d.get('details', {})}")
    for b in g.get("build", []):
        print(f"build: {b['tool']} {b.get('name') or b['file']} {b.get('packaging', '')} "
              f"deps: {', '.join(b.get('dependencies', []))}")
    fan = Counter(e["target"] for e in g.get("edges", []) if not sym.get(e["source"], {}).get("is_test"))
    print("most depended-on symbols:")
    for sid, n in fan.most_common(12):
        print(f"  {sid} ({n} incoming)")
    for n in g.get("notes", [])[:5]:
        print(f"note: {n}")


def search(g: dict, terms: list[str]) -> None:
    terms = [t.lower() for t in terms]
    hits: dict[str, set[str]] = defaultdict(set)
    where: dict[str, set[str]] = defaultdict(set)
    for sid, s in g.get("symbols", {}).items():
        for t in terms:
            if t in sid.lower():
                hits[sid].add(t)
            for m in s.get("methods", []):
                if t in m["name"].lower():
                    hits[sid].add(t)
                    where[sid].add(f"{m['name']}():{m['start_line']}")
    for e in g.get("entry_points", []):
        for t in terms:
            if t in e.get("detail", "").lower():
                hits[e["symbol"]].add(t)
                where[e["symbol"]].add(f"{e['kind']} {e['detail']}")
    for ent in g.get("entities", []):
        for t in terms:
            if t in ent["name"].lower() and ent.get("symbol"):
                hits[ent["symbol"]].add(t)
                where[ent["symbol"]].add("persisted entity")
    sym = g.get("symbols", {})
    ranked = sorted(hits, key=lambda i: (-len(hits[i]), sym.get(i, {}).get("is_test", False), i))
    for sid in ranked[:40]:
        s = sym.get(sid, {})
        tag = " [test]" if s.get("is_test") else ""
        print(f"{len(hits[sid])} {sid} ({s.get('kind', '?')}, layer {s.get('layer')}){tag} "
              f"{s.get('file')}:{s.get('start_line')}  {'; '.join(sorted(where[sid])[:4])}")
    if len(ranked) > 40:
        print(f"... {len(ranked) - 40} more; add terms to narrow")
    if not ranked:
        print("no matches")


def around(g: dict, name: str, depth: int, tests: bool) -> None:
    sym = g.get("symbols", {})
    start = resolve(name, sym)
    if not start:
        print(f"no symbol matches {name}")
        return
    pairs = edges_by_pair(g)
    out, inc = defaultdict(set), defaultdict(set)
    for a, b in pairs:
        out[a].add(b)
        inc[b].add(a)
    keep = lambda i: tests or not sym.get(i, {}).get("is_test")
    frontier, seen = set(start), set(start)
    for hop in range(1, depth + 1):
        nxt = set()
        for direction, nbrs, arrow in (("depends on", out, "->"), ("used by", inc, "<-")):
            rows = []
            for a in sorted(frontier):
                for b in sorted(nbrs[a]):
                    if not keep(b) or b in seen:
                        continue
                    es = pairs[(a, b)] if arrow == "->" else pairs[(b, a)]
                    kinds = ",".join(sorted({e["kind"] for e in es}))
                    rows.append(f"  {a} {arrow} {b}  [{kinds}] {es[0]['file']}:{es[0]['line']}")
                    nxt.add(b)
            if rows:
                print(f"hop {hop}, {direction}:")
                print("\n".join(rows))
        seen |= nxt
        frontier = nxt
        if not frontier:
            break


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--graph", default=DEFAULT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    s = sub.add_parser("search")
    s.add_argument("terms", nargs="+")
    a = sub.add_parser("around")
    a.add_argument("name")
    a.add_argument("--depth", type=int, default=1)
    a.add_argument("--tests", action="store_true", help="include test classes")
    m = sub.add_parser("members")
    m.add_argument("specs", nargs="+")
    args = ap.parse_args()
    try:
        g = load(args.graph)
    except (OSError, ValueError) as e:
        print(f"cannot read the graph: {e}")
        return 2
    if args.cmd == "summary":
        summary(g)
    elif args.cmd == "search":
        search(g, args.terms)
    elif args.cmd == "around":
        around(g, args.name, args.depth, args.tests)
    else:
        for spec in args.specs:
            ids = sorted(resolve(spec, g.get("symbols", {})))
            print(f"{spec}: {len(ids)} symbols")
            for i in ids:
                print(f"  {i}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
