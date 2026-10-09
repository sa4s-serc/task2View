"""Language extractors for the repository card, keyed by language id.

Languages without an extractor still get typed files and a file-level module
symbol (``generic_unit``), so the card covers every repository, with the
limitation recorded in the card notes.
"""

from __future__ import annotations

from task2view.contracts.card import Symbol
from task2view.phase0.languages.base import FileUnit, LanguageExtractor

_FACTORIES = {
    "java": lambda path: _java(),
    "python": lambda path: _python(),
    "javascript": lambda path: _js(False, False),
    "typescript": lambda path: _js(True, path.endswith(".tsx")),
}
_CACHE: dict[tuple, LanguageExtractor] = {}


def _java():
    from task2view.phase0.languages.java import JavaExtractor

    return _CACHE.setdefault(("java",), JavaExtractor())


def _python():
    from task2view.phase0.languages.python import PythonExtractor

    return _CACHE.setdefault(("python",), PythonExtractor())


def _js(typescript: bool, tsx: bool):
    from task2view.phase0.languages.javascript import JavaScriptExtractor

    return _CACHE.setdefault(("js", typescript, tsx), JavaScriptExtractor(typescript=typescript, tsx=tsx))


def extractor_for(language: str | None, path: str) -> LanguageExtractor | None:
    factory = _FACTORIES.get(language or "")
    return factory(path) if factory else None


def supported_languages() -> set[str]:
    return set(_FACTORIES)


def generic_unit(path: str, language: str, *, lines: int, is_test: bool) -> FileUnit:
    mid = path.rsplit(".", 1)[0].replace("/", ".")
    unit = FileUnit(path=path, language=language, package=mid.rsplit(".", 1)[0] if "." in mid else "")
    unit.symbols.append(Symbol(id=mid, name=mid.rsplit(".", 1)[-1], kind="module", file=path, start_line=1,
                               end_line=max(lines, 1), language=language, package=unit.package, is_test=is_test))
    return unit
