"""Sandboxed repository tools for analysis and extraction agents (ADR-001 D7)."""

from __future__ import annotations

import re
from pathlib import Path

from task2view.phase3.graph import RepositoryGraph

BLOCKED_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".venv", "venv",
    "node_modules", "target", "build", "dist", "__pycache__",
}
BLOCKED_EXT = {
    "png", "jpg", "jpeg", "gif", "webp", "ico", "svg", "pdf", "doc", "docx",
    "ppt", "pptx", "xls", "xlsx", "vpp", "uml", "puml", "plantuml", "mmd",
    "drawio", "form", "class", "jar", "war", "zip", "gz", "exe", "dll", "so",
    "dylib", "o", "a", "lock",
}


class RepoTools:
    def __init__(self, repo_root: str | Path, graph: RepositoryGraph | None = None):
        self.root = Path(repo_root).resolve()
        self.graph = graph

    def dispatch(self, name: str, args: dict | None) -> str:
        args = args or {}
        if name == "list_tree":
            return self.list_tree(args.get("path") or ".", int(args.get("depth") or 3))
        if name == "search":
            return self.search(str(args.get("pattern") or ""), args.get("glob"))
        if name == "read":
            return self.read(str(args.get("path") or ""), int(args.get("max_chars") or 8000))
        if name == "graph_query":
            return self.graph_query(str(args.get("name") or ""))
        if name == "traverse_graph":
            return self.traverse_graph(str(args.get("name") or ""), int(args.get("hops") or 1))
        if name == "edges_among":
            names = args.get("names") or args.get("name") or ""
            if isinstance(names, str):
                names = [n.strip() for n in names.replace(",", " ").split() if n.strip()]
            return self.edges_among(names)
        if name == "missing_neighbors":
            names = args.get("names") or args.get("name") or ""
            if isinstance(names, str):
                names = [n.strip() for n in names.replace(",", " ").split() if n.strip()]
            return self.missing_neighbors(names)
        if name == "package_of":
            return self.package_of(str(args.get("name") or ""))
        return (
            f"unknown tool {name!r}. Use list_tree, search, read, graph_query, "
            "traverse_graph, edges_among, missing_neighbors, package_of."
        )

    def _resolve(self, rel: str) -> Path | str:
        rel = rel.strip().lstrip("/")
        path = (self.root / rel).resolve()
        try:
            path.relative_to(self.root)
        except ValueError:
            return "blocked: path escapes repository"
        return path

    def _blocked_file(self, path: Path) -> bool:
        if any(p.lower() in BLOCKED_DIRS for p in path.parts):
            return True
        ext = path.suffix.lower().lstrip(".")
        return ext in BLOCKED_EXT

    def list_tree(self, rel: str = ".", depth: int = 3) -> str:
        base = self._resolve(rel)
        if isinstance(base, str):
            return base
        if not base.exists():
            return f"missing: {rel}"
        lines: list[str] = []
        max_entries = 180

        def walk(current: Path, remaining: int, prefix: str) -> None:
            if len(lines) >= max_entries or remaining < 0:
                return
            try:
                children = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except OSError as exc:
                lines.append(f"{prefix}[unreadable {exc}]")
                return
            for child in children:
                if child.name in BLOCKED_DIRS or child.name.startswith("."):
                    continue
                if child.is_file() and self._blocked_file(child):
                    continue
                rel_c = child.relative_to(self.root).as_posix()
                mark = "/" if child.is_dir() else ""
                lines.append(f"{prefix}{rel_c}{mark}")
                if child.is_dir() and remaining > 0:
                    walk(child, remaining - 1, prefix)
                if len(lines) >= max_entries:
                    lines.append("… truncated")
                    return

        walk(base if base.is_dir() else base.parent, depth, "")
        return "\n".join(lines) or "(empty)"

    def search(self, pattern: str, glob: str | None = None) -> str:
        if not pattern or len(pattern) < 2:
            return "pattern too short"
        try:
            regex = re.compile(pattern, re.I)
        except re.error:
            regex = re.compile(re.escape(pattern), re.I)
        hits: list[str] = []
        for path in self.root.rglob("*"):
            if not path.is_file() or self._blocked_file(path):
                continue
            rel = path.relative_to(self.root).as_posix()
            if glob and glob not in rel and not rel.endswith(glob.lstrip("*")):
                continue
            if regex.search(rel):
                hits.append(f"{rel}: <path match>")
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    hits.append(f"{rel}:{i}: {line.strip()[:200]}")
                    if len(hits) >= 40:
                        return "\n".join(hits) + "\n… truncated"
        return "\n".join(hits) or "no matches"

    def read(self, rel: str, max_chars: int = 8000) -> str:
        path = self._resolve(rel)
        if isinstance(path, str):
            return path
        if not path.is_file():
            return f"missing file: {rel}"
        if self._blocked_file(path):
            return f"blocked file type: {rel}"
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            return text[:max_chars] + "\n/* truncated */\n"
        return text

    def graph_query(self, name: str) -> str:
        if self.graph is None:
            return "graph unavailable"
        if not name:
            top = sorted(self.graph.nodes.values(), key=lambda n: -self.graph.degree(n.name))[:15]
            return "\n".join(
                f"{n.name} layer={n.layer} deg={self.graph.degree(n.name)} path={n.path}"
                for n in top
            )
        node = self.graph.nodes.get(name)
        if node is None:
            folded = {n.casefold(): n for n in self.graph.nodes}
            resolved = folded.get(name.casefold())
            if not resolved:
                return f"unknown type {name}"
            node = self.graph.nodes[resolved]
            name = resolved
        nbs = ", ".join(sorted(self.graph.neighbors(name))[:20])
        uses = ", ".join(sorted(self.graph.uses.get(name, ()))[:20])
        return (
            f"{name} path={node.path} layer={node.layer} deg={self.graph.degree(name)}\n"
            f"uses: {uses or '(none)'}\nneighbors: {nbs or '(none)'}"
        )

    def traverse_graph(self, name: str, hops: int = 1) -> str:
        if self.graph is None:
            return "graph unavailable"
        if not name:
            return "name required"
        folded = {n.casefold(): n for n in self.graph.nodes}
        resolved = name if name in self.graph.nodes else folded.get(name.casefold())
        if resolved is None:
            return f"unknown type {name}"
        found = self.graph.hop_from({resolved}, max(1, min(hops, 3)))
        lines = [f"{resolved} hops={hops} size={len(found)}"]
        for n in sorted(found, key=lambda x: -self.graph.degree(x))[:40]:
            node = self.graph.nodes[n]
            lines.append(f"{n} layer={node.layer} deg={self.graph.degree(n)} path={node.path}")
        return "\n".join(lines)

    def edges_among(self, names: list[str]) -> str:
        if self.graph is None:
            return "graph unavailable"
        folded = {n.casefold(): n for n in self.graph.nodes}
        resolved = []
        for raw in names:
            hit = raw if raw in self.graph.nodes else folded.get(raw.casefold())
            if hit:
                resolved.append(hit)
        want = set(resolved)
        lines = []
        for src in resolved:
            for dst in sorted(self.graph.uses.get(src, ())):
                if dst in want:
                    kind = "calls" if self.graph.has_call(src, dst) else "uses"
                    lines.append(f"{src} -{kind}-> {dst}")
        return "\n".join(lines) or "no edges among those types"

    def missing_neighbors(self, names: list[str]) -> str:
        if self.graph is None:
            return "graph unavailable"
        folded = {n.casefold(): n for n in self.graph.nodes}
        selected = set()
        for raw in names:
            hit = raw if raw in self.graph.nodes else folded.get(raw.casefold())
            if hit:
                selected.add(hit)
        seen = set()
        rows = []
        for src in selected:
            for nb in self.graph.neighbors(src):
                if nb in selected or nb in seen:
                    continue
                seen.add(nb)
                node = self.graph.nodes[nb]
                rows.append((self.graph.degree(nb), nb, node.layer, src, node.path))
        rows.sort(reverse=True)
        lines = [f"{n} layer={layer} deg={deg} via={via} path={path}" for deg, n, layer, via, path in rows[:25]]
        return "\n".join(lines) or "no missing neighbours"

    def package_of(self, name: str) -> str:
        if self.graph is None:
            return "graph unavailable"
        if not name:
            return "name required"
        folded = {n.casefold(): n for n in self.graph.nodes}
        resolved = name if name in self.graph.nodes else folded.get(name.casefold())
        if resolved is None:
            return f"unknown type {name}"
        node = self.graph.nodes[resolved]
        return f"{resolved} layer={node.layer} path={node.path} deg={self.graph.degree(resolved)}"

