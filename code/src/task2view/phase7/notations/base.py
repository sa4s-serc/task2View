"""Notation renderers for View format v2 (ADR-006 D3: every language renders every model kind).

A renderer turns an ArchitectureView into diagram source. Where a language has a
native construct for the view's model kind it uses it; otherwise it uses a
documented approximation and sets ``approximated`` so the validation report
says which notation a reader is looking at.

Support matrix: docs/redesign/03-views-reconciliation-validation.md §9.
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict

from task2view.contracts.views import ArchitectureView, Interaction, RenderResult, ViewElement

MODEL_KINDS = ("uml-component", "uml-package", "uml-class", "uml-sequence", "uml-communication", "uml-activity",
               "uml-state", "uml-usecase", "uml-deployment", "table")

# Native constructs per language (design 03 §9; N in the matrix). Everything else is approximated.
NATIVE: dict[str, set[str]] = {
    "plantuml": {"uml-component", "uml-package", "uml-class", "uml-sequence", "uml-activity", "uml-state",
                 "uml-usecase", "uml-deployment"},
    "c4plantuml": {"uml-component", "uml-package", "uml-class", "uml-sequence", "uml-communication", "uml-activity",
                   "uml-state", "uml-usecase", "uml-deployment"},
    "mermaid": {"uml-sequence", "uml-activity", "uml-state", "uml-class"},
    "d2": {"uml-component", "uml-package", "uml-sequence", "uml-class", "uml-deployment"},
    "structurizr": {"uml-component", "uml-package", "uml-communication", "uml-deployment"},
    "graphviz": set(),
    "nomnoml": {"uml-package", "uml-class", "uml-usecase"},
    "excalidraw": set(),
    "bpmn": {"uml-activity"},
}

_RENDERERS: dict[str, "Renderer"] = {}


class Renderer:
    language: str = ""
    extension: str = ""

    def render(self, view: ArchitectureView) -> RenderResult:  # pragma: no cover - interface
        raise NotImplementedError

    def result(self, view: ArchitectureView, source: str, note: str = "") -> RenderResult:
        return RenderResult(language=self.language, model_kind=view.model_kind, source=source,
                            extension=self.extension, approximated=view.model_kind not in NATIVE[self.language],
                            note=note)


def register(renderer_cls):
    instance = renderer_cls()
    _RENDERERS[instance.language] = instance
    return renderer_cls


def get_renderer(language: str) -> Renderer:
    try:
        return _RENDERERS[language]
    except KeyError as exc:
        raise KeyError(f"no renderer for {language!r}; registered: {sorted(_RENDERERS)}") from exc


def renderers() -> dict[str, Renderer]:
    return dict(_RENDERERS)


# ---------------------------------------------------------------- helpers shared by renderers

def alias(element_id: str) -> str:
    """Stable identifier usable in every language: letters, digits, underscore.

    Ids that differ only in punctuation ("a.b" vs "a:b") would collide after
    sanitising, so a short hash of the original id is appended whenever
    characters were replaced.
    """
    clean = re.sub(r"[^A-Za-z0-9]", "_", element_id)
    if clean == element_id:
        return "e_" + clean
    return f"e_{clean}_{hashlib.sha1(element_id.encode('utf-8')).hexdigest()[:6]}"


def quote(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', "'").replace("\n", " ")


def children(view: ArchitectureView) -> dict[str | None, list[ViewElement]]:
    """parent id -> elements nested directly in it (None = top level)."""
    out: dict[str | None, list[ViewElement]] = defaultdict(list)
    parent = {e.id: e.parent for e in view.elements}

    def anchored(eid: str) -> bool:  # the parent chain reaches the top without a cycle
        seen = set()
        while parent.get(eid) is not None:
            if eid in seen or parent[eid] not in parent:
                return False
            seen.add(eid)
            eid = parent[eid]
        return True

    for e in view.elements:
        ok = e.parent in parent and anchored(e.id)
        out[e.parent if ok else None].append(e)
    return out


def segments(view: ArchitectureView) -> list[tuple[str | None, list[Interaction]]]:
    """Consecutive interactions grouped by fragment: [(fragment id or None, [steps])]."""
    out: list[tuple[str | None, list[Interaction]]] = []
    for step in sorted(view.interactions, key=lambda s: s.order):
        if out and out[-1][0] == step.fragment:
            out[-1][1].append(step)
        else:
            out.append((step.fragment, [step]))
    return out


def fragment(view: ArchitectureView, fragment_id: str | None):
    return next((f for f in view.fragments if f.id == fragment_id), None)


def label_lines(element: ViewElement) -> list[str]:
    """Name, then responsibilities (inside the element, never on edges), then attributes."""
    lines = [element.name]
    lines += [f"- {r}" for r in element.responsibilities]
    lines += [f"{a.name}{': ' + a.type if a.type else ''}{' {PK}' if a.key else ''}{' {FK}' if a.foreign_key else ''}"
              for a in element.attributes]
    return lines


def multiplicity(rel) -> tuple[str, str]:
    """(source end, target end). "*..1" -> ("*", "1"); a single value applies to the target end."""
    if not rel.multiplicity:
        return "", ""
    if ".." in rel.multiplicity:
        a, b = rel.multiplicity.split("..", 1)
        return a, b
    return "", rel.multiplicity


def table_rows(view: ArchitectureView) -> list[list[str]]:
    rows = [["Element", "Kind", "Responsibilities / details", "Files"]]
    trace = {t.element: t for t in view.traceability}
    for e in view.content_elements():
        t = trace.get(e.id)
        rows.append([e.name, e.kind, "; ".join(e.responsibilities) or "", ", ".join(t.files) if t else ""])
    return rows
