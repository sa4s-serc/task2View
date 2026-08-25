"""Filesystem architecture graph: kept files, parent directories, import-like edges.

The core does not parse a language AST. A node is a kept file (keyed by stem).
``layer`` is the parent directory name. Uses/calls come from import-like lines
and identifier mentions that resolve to other kept files.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from task2view.contracts.models import CleanedCorpus

_IDENT = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]{2,})\b")
_IMPORT_LINE = re.compile(
    r"""(?mx)
    ^\s*(?:
        import\s+(?:static\s+)?(?P<java>[\w.]+)\s*;?
      | from\s+(?P<pyfrom>[\w.]+)\s+import
      | import\s+(?P<pyimp>[\w.]+)
      | (?:from|import)\s+['"](?P<modpath>[^'"]+)['"]
      | require\(\s*['"](?P<req>[^'"]+)['"]
      | \#include\s+[<'"](?P<inc>[^>'"]+)[>'"]
      | using\s+(?P<using>[\w.]+)
    )
    """
)
_SKIP_IDENTS = {
    "class", "interface", "enum", "record", "public", "private", "protected",
    "static", "final", "void", "return", "import", "package", "extends",
    "implements", "throws", "this", "super", "null", "true", "false",
    "else", "for", "while", "switch", "case", "break", "continue",
    "try", "catch", "finally", "throw", "from", "with",
    "not", "and", "lambda", "self", "none",
    "function", "const", "let", "var", "export", "default", "typeof",
    "string", "int", "long", "boolean", "float", "double", "object", "list",
    "map", "set", "optional", "override", "system", "java", "javax",
    "the", "that",
}


@dataclass
class RepoNode:
    name: str
    path: str
    layer: str
    kind: str = "file"


@dataclass
class RepositoryGraph:
    nodes: dict[str, RepoNode] = field(default_factory=dict)
    uses: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    calls: dict[str, set[tuple[str, str]]] = field(default_factory=lambda: defaultdict(set))
    extends: dict[str, str] = field(default_factory=dict)
    parse_failures: list[str] = field(default_factory=list)
    path_to_types: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    aliases: dict[str, str] = field(default_factory=dict)

    def resolve(self, name: str) -> str | None:
        if name in self.nodes:
            return name
        if name in self.aliases:
            return self.aliases[name]
        folded = {n.casefold(): n for n in self.nodes}
        hit = folded.get(name.casefold())
        if hit:
            return hit
        path_folded = {n.path.casefold(): n.name for n in self.nodes.values()}
        return path_folded.get(name.casefold().replace("\\", "/"))

    def degree(self, name: str) -> int:
        inbound = sum(1 for dsts in self.uses.values() if name in dsts)
        return len(self.uses.get(name, ())) + inbound

    def neighbors(self, name: str) -> set[str]:
        out = set(self.uses.get(name, ()))
        for src, dsts in self.uses.items():
            if name in dsts:
                out.add(src)
        return out

    def call_neighbors(self, name: str) -> set[str]:
        out = {target for target, _ in self.calls.get(name, ())}
        for src, calls in self.calls.items():
            if any(target == name for target, _ in calls):
                out.add(src)
        return out or self.neighbors(name)

    def known(self, name: str) -> bool:
        return self.resolve(name) is not None

    def has_edge(self, a: str, b: str) -> bool:
        src, dst = self.resolve(a), self.resolve(b)
        if not src or not dst:
            return False
        return dst in self.uses.get(src, ()) or src in self.uses.get(dst, ())

    def has_call(self, a: str, b: str) -> bool:
        src, dst = self.resolve(a), self.resolve(b)
        if not src or not dst:
            return False
        if any(t == dst for t, _ in self.calls.get(src, ())):
            return True
        return self.has_edge(src, dst)

    def pagerank(
        self,
        alpha: float = 0.85,
        personalization: dict[str, float] | None = None,
        max_iter: int = 100,
        tol: float = 1.0e-6,
    ) -> dict[str, float]:
        names = list(self.nodes)
        n = len(names)
        if n == 0:
            return {}
        out: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for src, dsts in self.uses.items():
            for dst in dsts:
                if dst in self.nodes:
                    out[src][dst] += 1.0
        for src, calls in self.calls.items():
            for dst, _method in calls:
                if dst in self.nodes:
                    out[src][dst] += 0.5
        out_sum = {src: sum(dsts.values()) for src, dsts in out.items()}
        if personalization:
            raw = {name: max(0.0, float(personalization.get(name, 0.0))) for name in names}
            total = sum(raw.values())
            pers = {name: (raw[name] / total if total else 1.0 / n) for name in names}
        else:
            pers = {name: 1.0 / n for name in names}
        rank = dict(pers)
        dangling = [name for name in names if out_sum.get(name, 0.0) <= 0]
        for _ in range(max_iter):
            dangling_mass = alpha * sum(rank[name] for name in dangling)
            nxt = {}
            for v in names:
                incoming = 0.0
                for u, dsts in out.items():
                    w = dsts.get(v, 0.0)
                    if w:
                        incoming += rank[u] * w / out_sum[u]
                nxt[v] = (1.0 - alpha) * pers[v] + dangling_mass * pers[v] + alpha * incoming
            err = sum(abs(nxt[v] - rank[v]) for v in names)
            rank = nxt
            if err < n * tol:
                break
        return rank

    def hop_from(self, seeds: set[str], hops: int) -> set[str]:
        seen = {s for s in (self.resolve(x) or x for x in seeds) if s in self.nodes}
        frontier = set(seen)
        for _ in range(max(0, hops)):
            nxt: set[str] = set()
            for name in frontier:
                nxt |= self.neighbors(name)
            nxt -= seen
            seen |= nxt
            frontier = nxt
        return seen

    def summary(self, limit: int = 80, prefer: list[str] | None = None) -> str:
        lines = [
            f"files={len(self.nodes)} uses_edges={sum(len(v) for v in self.uses.values())}",
            "Nodes are kept source files. [dir] is the parent directory, not a style layer.",
            "Uses edges come from import-like lines and identifier mentions of other kept files.",
        ]
        seen: set[str] = set()
        ordered: list[str] = []
        for name in prefer or []:
            resolved = self.resolve(name)
            if resolved and resolved not in seen:
                ordered.append(resolved)
                seen.add(resolved)
        for name in sorted(self.nodes, key=lambda n: -self.degree(n)):
            if len(ordered) >= max(limit, len(seen)):
                break
            if name not in seen:
                ordered.append(name)
                seen.add(name)
        for name in ordered:
            node = self.nodes[name]
            dst = ", ".join(sorted(self.uses.get(name, ()))[:8])
            lines.append(f"{name} [dir={node.layer}] path={node.path} deg={self.degree(name)} uses-> {dst}")
        omitted = max(0, len(self.nodes) - len(ordered))
        if omitted:
            lines.append(f"omitted_from_listing={omitted}")
        if self.parse_failures:
            lines.append("unreadable: " + ", ".join(self.parse_failures[:10]))
        return "\n".join(lines)


def _parent_dir(rel: str) -> str:
    parent = Path(rel).parent
    if not parent.parts or str(parent) in {".", ""}:
        return "root"
    return parent.name


def _stem_key(rel: str, taken: set[str]) -> str:
    stem = Path(rel).stem
    if stem and stem not in taken:
        return stem
    return rel.replace("\\", "/")


def _tokens_from_import(match: re.Match[str]) -> list[str]:
    raw = next((g for g in match.groups() if g), "")
    if not raw:
        return []
    cleaned = raw.replace("\\", "/").split(" as ")[0].strip()
    parts = re.split(r"[./\\\\]", cleaned)
    return [p for p in parts if p and p not in {"*", ""}]


def build_graph(repo_root: str | Path, corpus: CleanedCorpus) -> RepositoryGraph:
    root = Path(repo_root)
    graph = RepositoryGraph()
    taken: set[str] = set()
    files: list[tuple[str, str]] = []
    for item in corpus.kept:
        rel = item.path.replace("\\", "/")
        key = _stem_key(rel, taken)
        taken.add(key)
        layer = _parent_dir(rel)
        graph.nodes[key] = RepoNode(name=key, path=rel, layer=layer, kind="file")
        graph.path_to_types[rel].append(key)
        graph.aliases[rel] = key
        graph.aliases[Path(rel).name] = key
        files.append((key, rel))

    stem_index = {n.casefold(): n for n in graph.nodes}

    for key, rel in files:
        path = root / rel
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            graph.parse_failures.append(rel)
            continue
        for match in _IMPORT_LINE.finditer(text):
            for token in _tokens_from_import(match):
                target = stem_index.get(token.casefold())
                if target and target != key:
                    graph.uses[key].add(target)
        for ident in _IDENT.findall(text):
            if ident.casefold() in _SKIP_IDENTS:
                continue
            target = stem_index.get(ident.casefold())
            if target and target != key:
                graph.uses[key].add(target)
                graph.calls[key].add((target, ident))

    project = set(graph.nodes)
    for src, dsts in list(graph.uses.items()):
        graph.uses[src] = {d for d in dsts if d in project and d != src}
    for src, calls in list(graph.calls.items()):
        graph.calls[src] = {(t, m) for t, m in calls if t in project and t != src}
    return graph
