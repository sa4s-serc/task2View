"""Typed repository graph from source. Java uses javalang (LocAgent/RepoGraph style)."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from task2view.contracts.models import CleanedCorpus

INSTANCEOF_PATTERN = re.compile(
    r"\binstanceof\s+((?:final\s+)?[A-Za-z_$][\w$.]*(?:\s*<[^<>()]*(?:<[^<>()]*>)?[^<>()]*>)?)"
    r"\s+([a-z_$][\w$]*)\b"
)


def _matching(src: str, open_idx: int, open_ch: str, close_ch: str) -> int:
    depth = 0
    for idx in range(open_idx, len(src)):
        ch = src[idx]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return idx
    return -1


def _elide_switch_expressions(src: str) -> str:
    """javalang cannot parse Java 14 switch expressions (`case x ->`)."""
    result = src
    changed = True
    while changed:
        changed = False
        cursor = 0
        while True:
            match = re.search(r"\bswitch\s*\(", result[cursor:])
            if not match:
                break
            abs_start = cursor + match.start()
            paren_open = cursor + match.end() - 1
            paren_close = _matching(result, paren_open, "(", ")")
            if paren_close < 0:
                break
            brace_open = paren_close + 1
            while brace_open < len(result) and result[brace_open].isspace():
                brace_open += 1
            if brace_open >= len(result) or result[brace_open] != "{":
                cursor = paren_close + 1
                continue
            brace_close = _matching(result, brace_open, "{", "}")
            if brace_close < 0:
                break
            body = result[brace_open : brace_close + 1]
            if "->" not in body:
                cursor = brace_close + 1
                continue
            prefix = result[:abs_start]
            ret = re.search(r"return\s+$", prefix)
            start = ret.start() if ret else abs_start
            replacement = "return null;" if ret else "null"
            result = result[:start] + replacement + result[brace_close + 1 :]
            changed = True
            cursor = start + len(replacement)
    return result


def _normalize_java(src: str) -> str:
    return _elide_switch_expressions(INSTANCEOF_PATTERN.sub(r"instanceof \1", src))


@dataclass
class RepoNode:
    name: str
    path: str
    layer: str
    kind: str = "class"


@dataclass
class RepositoryGraph:
    nodes: dict[str, RepoNode] = field(default_factory=dict)
    uses: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    calls: dict[str, set[tuple[str, str]]] = field(default_factory=lambda: defaultdict(set))
    extends: dict[str, str] = field(default_factory=dict)
    parse_failures: list[str] = field(default_factory=list)
    path_to_types: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))

    def degree(self, name: str) -> int:
        inbound = sum(1 for dsts in self.uses.values() if name in dsts)
        return len(self.uses.get(name, ())) + inbound

    def neighbors(self, name: str) -> set[str]:
        out = set(self.uses.get(name, ()))
        for src, dsts in self.uses.items():
            if name in dsts:
                out.add(src)
        return out

    def known(self, name: str) -> bool:
        return name in self.nodes

    def has_edge(self, a: str, b: str) -> bool:
        return b in self.uses.get(a, ()) or a in self.uses.get(b, ())

    def has_call(self, a: str, b: str) -> bool:
        return any(t == b for t, _ in self.calls.get(a, ()))

    def pagerank(
        self,
        alpha: float = 0.85,
        personalization: dict[str, float] | None = None,
        max_iter: int = 100,
        tol: float = 1.0e-6,
    ) -> dict[str, float]:
        """Weighted PageRank (Aider RepoMap: ``nx.pagerank(..., weight='weight')``, α=0.85).

        Edges: uses weight 1.0; each call adds 0.5 (Aider uses sqrt of ref counts).
        Dangling mass is redistributed using the personalization vector.
        """
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

    def call_neighbors(self, name: str) -> set[str]:
        out = {target for target, _ in self.calls.get(name, ())}
        for src, calls in self.calls.items():
            if any(target == name for target, _ in calls):
                out.add(src)
        return out

    def hop_from(self, seeds: set[str], hops: int) -> set[str]:
        seen = {s for s in seeds if s in self.nodes}
        frontier = set(seen)
        for _ in range(max(0, hops)):
            nxt: set[str] = set()
            for name in frontier:
                nxt |= self.neighbors(name)
            nxt -= seen
            seen |= nxt
            frontier = nxt
        return seen

    def summary(self, limit: int = 80) -> str:
        lines = [
            f"types={len(self.nodes)} uses_edges={sum(len(v) for v in self.uses.values())}"
        ]
        ranked = sorted(self.nodes.items(), key=lambda kv: -self.degree(kv[0]))
        for name, node in ranked[:limit]:
            dst = ", ".join(sorted(self.uses.get(name, ()))[:8])
            lines.append(f"{name} [{node.layer}] deg={self.degree(name)} uses-> {dst}")
        if self.parse_failures:
            lines.append("parse_failures: " + ", ".join(self.parse_failures[:10]))
        return "\n".join(lines)


def _layer_of(rel: str) -> str:
    parts = Path(rel).parts
    for marker in ("java", "kotlin", "scala"):
        if marker in parts:
            idx = parts.index(marker)
            if idx + 1 < len(parts) - 1:
                return parts[idx + 1]
    if len(parts) >= 2:
        return parts[-2]
    return "default"


def _parse_java(root: Path, rel: str, graph: RepositoryGraph) -> None:
    import javalang

    path = root / rel
    src = _normalize_java(path.read_text(encoding="utf-8", errors="replace"))
    try:
        tree = javalang.parse.parse(src)
    except Exception:
        graph.parse_failures.append(rel)
        stem = Path(rel).stem
        graph.nodes[stem] = RepoNode(name=stem, path=rel, layer=_layer_of(rel), kind="class")
        graph.path_to_types[rel].append(stem)
        return
    for _, node in tree.filter(javalang.tree.TypeDeclaration):
        name = node.name
        graph.nodes[name] = RepoNode(
            name=name, path=rel, layer=_layer_of(rel), kind=type(node).__name__
        )
        graph.path_to_types[rel].append(name)
        ext = getattr(node, "extends", None)
        if ext is not None:
            base = ext[0].name if isinstance(ext, list) else ext.name
            graph.extends[name] = base
            graph.uses[name].add(base)
        for impl in getattr(node, "implements", None) or []:
            graph.uses[name].add(impl.name)
        for kind in (javalang.tree.FieldDeclaration, javalang.tree.LocalVariableDeclaration):
            for _, decl in node.filter(kind):
                t = getattr(decl.type, "name", None)
                if t:
                    graph.uses[name].add(t)
        for _, param in node.filter(javalang.tree.FormalParameter):
            t = getattr(param.type, "name", None)
            if t:
                graph.uses[name].add(t)
        for _, creator in node.filter(javalang.tree.ClassCreator):
            t = getattr(creator.type, "name", None)
            if t:
                graph.uses[name].add(t)
        var_types: dict[str, str] = {}
        for kind in (
            javalang.tree.FieldDeclaration,
            javalang.tree.LocalVariableDeclaration,
            javalang.tree.FormalParameter,
        ):
            for _, decl in node.filter(kind):
                t = getattr(decl.type, "name", None)
                decls = getattr(decl, "declarators", None) or [decl]
                for dec in decls:
                    if getattr(dec, "name", None) and t:
                        var_types[dec.name] = t
        for _, inv in node.filter(javalang.tree.MethodInvocation):
            recv = inv.qualifier
            if not recv:
                continue
            target = var_types.get(recv, recv)
            graph.calls[name].add((target, inv.member))
            graph.uses[name].add(target)


def build_graph(repo_root: str | Path, corpus: CleanedCorpus) -> RepositoryGraph:
    root = Path(repo_root)
    graph = RepositoryGraph()
    for item in corpus.kept:
        rel = item.path
        if rel.endswith(".java"):
            _parse_java(root, rel, graph)
        else:
            stem = Path(rel).stem
            graph.nodes[stem] = RepoNode(name=stem, path=rel, layer=_layer_of(rel), kind="file")
            graph.path_to_types[rel].append(stem)
    project = set(graph.nodes)
    for src_name, dsts in list(graph.uses.items()):
        graph.uses[src_name] = {d for d in dsts if d in project and d != src_name}
    for src_name, calls in list(graph.calls.items()):
        graph.calls[src_name] = {(t, m) for t, m in calls if t in project and t != src_name}
    return graph
