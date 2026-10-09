"""Repository tools for Phase 5 evidence agents, built on the Phase 0 card.

list_tree, search, read (with line numbers), symbol, neighbours. Reads are
limited to the corpus classes of the task (code, config, deploy, ...); UML model
files and binaries are never readable, so evidence cannot come from the
reference diagrams a view will be evaluated against.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from task2view.contracts.card import RepositoryCard

TOOLS = ("list_tree", "search", "read", "symbol", "neighbours")  # documented in prompts/phase5_evidence.md

class CardTools:
    def __init__(self, card: RepositoryCard, classes: list[str], *, max_read_lines: int = 200, max_hits: int = 40):
        self.card = card
        self.root = Path(card.root)
        self.readable = {f.path for f in card.files if f.file_class in set(classes) | {"code"}}
        self.max_read_lines = max_read_lines
        self.max_hits = max_hits
        self.opened: set[str] = set()
        self.calls: Counter = Counter()  # telemetry: how often each tool was used

    def dispatch(self, name: str, args: dict) -> str:
        self.calls[name if name in TOOLS else "unknown-tool"] += 1
        try:
            if name == "list_tree":
                return self.list_tree(str(args.get("path", ".")), int(args.get("depth", 2)))
            if name == "search":
                return self.search(str(args.get("pattern", "")), args.get("path"))
            if name == "read":
                return self.read(str(args.get("path", "")), int(args.get("start", 1)), args.get("end"))
            if name == "symbol":
                return self.symbol(str(args.get("id", "")))
            if name == "neighbours":
                return self.neighbours(str(args.get("id", "")), str(args.get("direction", "out")))
        except (ValueError, TypeError) as exc:
            return f"error: {exc}"
        return f"error: unknown tool {name!r}"

    def list_tree(self, path: str = ".", depth: int = 2) -> str:
        prefix = "" if path in {"", "."} else path.rstrip("/") + "/"
        seen: dict[str, str] = {}
        for f in self.card.files:
            if not f.path.startswith(prefix):
                continue
            parts = f.path[len(prefix):].split("/")
            key = "/".join(parts[:depth])
            seen.setdefault(key + ("/" if len(parts) > depth else ""), f.file_class if len(parts) <= depth else "dir")
        return "\n".join(f"{k} [{v}]" for k, v in sorted(seen.items())[:300]) or "no files"

    def search(self, pattern: str, path: str | None = None) -> str:
        try:
            rx = re.compile(pattern, re.I)
        except re.error as exc:
            return f"error: bad regex: {exc}"
        hits = []
        for rel in sorted(self.readable):
            if path and not rel.startswith(path.rstrip("/")):
                continue
            for i, line in enumerate(self._lines(rel), 1):
                if rx.search(line):
                    hits.append(f"{rel}:{i}: {line.strip()[:160]}")
                    if len(hits) >= self.max_hits:
                        return "\n".join(hits) + "\n… more hits; narrow the pattern"
        return "\n".join(hits) or "no hits"

    def read(self, path: str, start: int = 1, end=None) -> str:
        if path not in self.readable:
            return f"error: {path!r} is not readable for this task (unknown file or excluded class)"
        lines = self._lines(path)
        start = max(1, start)
        end = min(len(lines), int(end) if end else start + self.max_read_lines - 1, start + self.max_read_lines - 1)
        self.opened.add(path)
        return "\n".join(f"{i:5d}  {lines[i - 1]}" for i in range(start, end + 1)) or "empty"

    def _lookup(self, ref: str):
        """(symbol, error): an id, or a simple name that names exactly one symbol."""
        if ref in self.card.symbols:
            return self.card.symbols[ref], ""
        found = self.card.by_simple_name(ref)
        if len(found) == 1:
            return found[0], ""
        if found:
            return None, f"error: {ref!r} is ambiguous; use one of: {', '.join(sorted(s.id for s in found)[:10])}"
        return None, f"error: no symbol {ref!r}"

    def symbol(self, ref: str) -> str:
        sym, error = self._lookup(ref)
        if sym is None:
            return error
        out = [f"{sym.id} [{sym.kind}] {sym.file}:{sym.start_line}-{sym.end_line} layer={sym.layer}"]
        if sym.annotations:
            out.append("annotations: " + ", ".join(sym.annotations))
        if sym.extends or sym.implements:
            out.append(f"extends: {sym.extends} implements: {sym.implements}")
        if sym.fields:
            out.append("fields: " + ", ".join(f"{f.name}: {f.type}" for f in sym.fields[:30]))
        for m in sym.methods[:40]:
            out.append(f"  {m.name}({', '.join(m.params)}) lines {m.start_line}-{m.end_line}"
                       + (f" calls {', '.join(m.calls[:8])}" if m.calls else ""))
        return "\n".join(out)

    def neighbours(self, ref: str, direction: str = "out") -> str:
        sym, error = self._lookup(ref)
        if sym is None:
            return error
        edges = [e for e in self.card.edges if (e.source if direction == "out" else e.target) == sym.id and e.kind != "imports"]
        rows = sorted({f"{e.source} -{e.kind}{'(' + e.detail + ')' if e.detail else ''}-> {e.target}  [{e.file}:{e.line}]"
                       for e in edges})
        return "\n".join(rows[:80]) or "no edges"

    def _lines(self, rel: str) -> list[str]:
        try:
            return (self.root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
