"""Language extractor interface for the repository card.

An extractor turns one source file into raw facts: its package/module, its
imports, the symbols it declares, and unresolved references from those symbols
to type or module names. ``phase0/graph.py`` resolves the references against
the whole repository, so extractors never need global knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from task2view.contracts.card import Symbol


@dataclass
class Import:
    name: str  # fully qualified (java) or dotted module (python) or resolved module id (js)
    line: int
    wildcard: bool = False
    alias: str | None = None  # local name the import binds (python/js)


@dataclass
class RawRef:
    source: str  # symbol id in this file
    target: str  # name as written: simple, qualified, or "Type.method"
    kind: str  # EdgeKind
    line: int
    detail: str = ""


@dataclass
class RawEntry:
    kind: str
    symbol: str
    line: int
    detail: str = ""


@dataclass
class FileUnit:
    path: str
    language: str
    package: str = ""
    imports: list[Import] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    refs: list[RawRef] = field(default_factory=list)
    entries: list[RawEntry] = field(default_factory=list)
    module_id: str | None = None  # python/js module symbol id


class LanguageExtractor:
    language: str = ""

    def extract(self, path: str, source: bytes, *, is_test: bool) -> FileUnit:  # pragma: no cover - interface
        raise NotImplementedError


def text(node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def walk(node):
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))
