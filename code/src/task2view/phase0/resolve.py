"""Resolve raw references from all files into a directed, code-only dependency graph.

A reference becomes an edge only if it resolves to a symbol declared in the
repository. External types (java.util.List, requests, react) are dropped, and so
are self-references. Resolution order for a simple name (Java):
explicit import -> same package -> enclosing type -> wildcard import -> the one
repository symbol with that simple name (only if unique). Python and JS
references are dotted names resolved by longest declared prefix.
"""

from __future__ import annotations

from collections import defaultdict

from task2view.contracts.card import Edge, Symbol
from task2view.phase0.languages.base import FileUnit


class Resolver:
    def __init__(self, units: list[FileUnit]):
        self.symbols: dict[str, Symbol] = {}
        self.unit_of: dict[str, FileUnit] = {}
        for unit in units:
            for s in unit.symbols:
                self.symbols.setdefault(s.id, s)
                self.unit_of.setdefault(s.id, unit)
        self.by_simple: dict[str, list[str]] = defaultdict(list)
        for sid, s in self.symbols.items():
            if s.kind != "module":
                self.by_simple[s.name].append(sid)

    # ------------------------------------------------------------------ java
    def resolve_java(self, name: str, unit: FileUnit, source_id: str) -> str | None:
        name = name.strip()
        if not name:
            return None
        if name in self.symbols:
            return name
        head, _, rest = name.partition(".")
        base = self._java_simple(head, unit, source_id)
        if base is None:
            return None
        candidate = f"{base}.{rest}" if rest else base
        return candidate if candidate in self.symbols else (base if not rest else None)

    def _java_simple(self, simple: str, unit: FileUnit, source_id: str) -> str | None:
        for imp in unit.imports:
            if not imp.wildcard and imp.name.rsplit(".", 1)[-1] == simple:
                return imp.name if imp.name in self.symbols else None
        same_pkg = f"{unit.package}.{simple}" if unit.package else simple
        if same_pkg in self.symbols:
            return same_pkg
        enclosing = source_id
        while "." in enclosing:
            enclosing = enclosing.rsplit(".", 1)[0]
            if f"{enclosing}.{simple}" in self.symbols:
                return f"{enclosing}.{simple}"
        for imp in unit.imports:
            if imp.wildcard and f"{imp.name}.{simple}" in self.symbols:
                return f"{imp.name}.{simple}"
        matches = self.by_simple.get(simple, [])
        if len(matches) == 1 and self.symbols[matches[0]].language == "java":
            return matches[0]
        return None

    # ------------------------------------------------------- python / js
    def resolve_dotted(self, name: str) -> str | None:
        parts = name.split(".")
        for i in range(len(parts), 0, -1):
            candidate = ".".join(parts[:i])
            if candidate in self.symbols:
                return candidate
        return None

    def resolve(self, name: str, unit: FileUnit, source_id: str) -> str | None:
        if unit.language == "java":
            return self.resolve_java(name, unit, source_id)
        return self.resolve_dotted(name)


def build_edges(units: list[FileUnit], resolver: Resolver) -> list[Edge]:
    edges: list[Edge] = []
    seen: set[tuple] = set()
    for unit in units:
        for ref in unit.refs:
            if ref.kind == "calls":
                type_part, _, method = ref.target.rpartition(".")
                target = resolver.resolve(type_part, unit, ref.source) if type_part else None
                detail = f"{method}" if target else ""
            else:
                target = resolver.resolve(ref.target, unit, ref.source)
                detail = ref.detail
            if target is None or target == ref.source:
                continue
            key = (ref.source, target, ref.kind, ref.line, detail)
            if key in seen:
                continue
            seen.add(key)
            edges.append(Edge(source=ref.source, target=target, kind=ref.kind, file=unit.path, line=ref.line, detail=detail))
        for imp in unit.imports:
            if unit.language != "java":
                continue
            target = imp.name if imp.name in resolver.symbols else None
            for s in unit.symbols:
                if target and target != s.id and "." not in s.id[len(unit.package) + 1:]:
                    key = (s.id, target, "imports", imp.line, "")
                    if key not in seen:
                        seen.add(key)
                        edges.append(Edge(source=s.id, target=target, kind="imports", file=unit.path, line=imp.line))
    # rewrite raw call strings on methods to resolved "symbol.method"
    resolved_calls: dict[tuple[str, int], list[str]] = defaultdict(list)
    for e in edges:
        if e.kind == "calls":
            resolved_calls[(e.source, e.line)].append(f"{e.target}.{e.detail}")
    for unit in units:
        for s in unit.symbols:
            for m in s.methods:
                m.calls = sorted({c for (src, line), cs in resolved_calls.items()
                                  if src == s.id and m.start_line <= line <= m.end_line for c in cs})
    return edges
