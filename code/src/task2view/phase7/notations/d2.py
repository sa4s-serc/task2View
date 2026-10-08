"""D2 renderer: native for component, package, sequence, class (data model) and deployment diagrams.

Native:
- uml-component / uml-package / uml-deployment: nested containers for every group / parent element; leaves
  carry the element kind as a shape (``cylinder`` datastore, ``person`` actor, ``page`` artifact, 3-D box for
  nodes); responsibilities are lines inside the label; edges reference elements by their full container path.
- uml-sequence: a ``shape: sequence_diagram`` container; actors use ``shape: person``; each fragment is a group
  inside the diagram labelled "<kind> [<guard>]"; returns are dashed; labels are prefixed "<order>.".
- uml-class: ``shape: sql_table`` for entities (``primary_key`` / ``foreign_key`` constraints) and
  ``shape: class`` for classes / interfaces (attributes as fields, responsibilities as methods);
  multiplicities as arrowhead labels; generalization as an unfilled triangle arrowhead.

Approximations (flagged ``approximated``):
- uml-communication: participants as boxes (``person`` for actors) with one numbered edge per message
  ("<order>. [guard] message").
- uml-activity: a start circle, one container per performer (swimlane) holding its actions, a ``diamond`` per
  fragment guard (yes branch into the fragment, no branch around it; loops get a back edge), an end circle.
- uml-state: rounded rectangles for states (containers for composite states), a filled start circle, labelled
  transition edges.
- uml-usecase: the system boundary as a container, ``person`` actors, ``oval`` use cases, dashed
  ``«include»`` / ``«extend»`` edges.
- table: a Markdown table block (``|`md ... `|``) inside the diagram — D2 has no table shape beyond sql_table.
"""

from __future__ import annotations

from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.phase7.notations.base import (
    Renderer, alias, children, fragment, label_lines, multiplicity, quote, register, segments, table_rows,
)
from task2view.phase7.notations.mermaid import activity_flow

_DASHED = {"allowed-to-use", "implements", "include", "extend", "deploys", "crosscuts", "traces-to",
           "assigned-to", "allocated-to", "return"}
_UNDIRECTED = {"attachment", "communicates"}
_SHAPE = {"datastore": "cylinder", "actor": "person", "use_case": "oval", "artifact": "page", "file": "page",
          "external_system": "hexagon", "queue": "queue", "state": "rectangle"}


def s(value: str) -> str:
    """A double-quoted D2 string."""
    return '"' + quote(value) + '"'


def ml(lines: list[str]) -> str:
    """A double-quoted multi-line D2 label (\\n escapes)."""
    return '"' + "\\n".join(quote(line) for line in lines) + '"'


@register
class D2Renderer(Renderer):
    language = "d2"
    extension = "d2"

    def render(self, view: ArchitectureView) -> RenderResult:
        body = {
            "uml-sequence": self._sequence,
            "uml-communication": self._communication,
            "uml-activity": self._activity,
            "uml-state": self._state,
            "uml-class": self._class,
            "table": self._table,
        }.get(view.model_kind, self._structure)(view)
        head = [f"title: {s(view.title)} {{", "  shape: text", "  near: top-center", "  style.font-size: 24", "}"]
        return self.result(view, "\n".join([*head, *body]))

    # ---------------------------------------------------------- helpers
    def _paths(self, view: ArchitectureView) -> dict[str, str]:
        ids = {e.id: e for e in view.elements}
        out = {}
        for e in view.elements:
            chain, cur, seen = [], e, set()
            while cur is not None and cur.id not in seen:
                seen.add(cur.id)
                chain.append(alias(cur.id))
                cur = ids.get(cur.parent) if cur.parent else None
            out[e.id] = ".".join(reversed(chain))
        return out

    def _edge(self, src: str, tgt: str, kind: str, label: str = "", mult: tuple[str, str] = ("", "")) -> list[str]:
        if kind == "subscribes":
            src, tgt = tgt, src
        arrow = "--" if kind in _UNDIRECTED else "->"
        attrs = []
        if kind in _DASHED:
            attrs.append("style.stroke-dash: 3")
        if kind in {"is-a", "generalization", "implements"}:
            attrs += ["target-arrowhead.shape: triangle", "target-arrowhead.style.filled: false"]
        if kind in {"composition", "aggregation"}:
            attrs += ["source-arrowhead.shape: diamond",
                      f"source-arrowhead.style.filled: {'true' if kind == 'composition' else 'false'}"]
        if mult[0]:
            attrs.append(f"source-arrowhead.label: {s(mult[0])}")
        if mult[1]:
            attrs.append(f"target-arrowhead.label: {s(mult[1])}")
        head = f"{src} {arrow} {tgt}" + (f": {s(label)}" if label else "")
        if not attrs:
            return [head]
        return [head + " {", *[f"  {a}" for a in attrs], "}"]

    def _leaf(self, e, indent: str) -> list[str]:
        a = alias(e.id)
        lines = label_lines(e)
        if e.stereotype:
            lines.insert(1, f"«{e.stereotype}»")
        attrs = []
        shape = _SHAPE.get(e.kind)
        if shape:
            attrs.append(f"shape: {shape}")
        if e.kind in {"node", "execution_env"}:
            attrs.append("style.3d: true")
        if e.kind == "state":
            attrs.append("style.border-radius: 12")
        out = [f"{indent}{a}: {ml(lines)}" + (" {" if attrs else "")]
        if attrs:
            out += [f"{indent}  {x}" for x in attrs] + [f"{indent}}}"]
        return out

    def _tree(self, view: ArchitectureView, leaf=None) -> list[str]:
        tree = children(view)
        leaf = leaf or self._leaf
        lines: list[str] = []

        def emit(e, indent: str):
            nested = tree.get(e.id, [])
            if e.group or nested:
                lines.append(f"{indent}{alias(e.id)}: {s(e.name)} {{")
                if e.kind in {"node", "execution_env"}:
                    lines.append(f"{indent}  style.3d: true")
                if e.group:
                    lines.append(f"{indent}  tooltip: {s(e.kind)}")
                for child in nested:
                    emit(child, indent + "  ")
                lines.append(f"{indent}}}")
            else:
                lines.extend(leaf(e, indent))

        for top in tree.get(None, []):
            emit(top, "")
        return lines

    # ---------------------------------------------------------- structure
    def _structure(self, view: ArchitectureView) -> list[str]:
        lines = ["direction: right" if view.model_kind in {"uml-deployment", "uml-usecase"} else "direction: down"]
        lines += self._tree(view)
        paths = self._paths(view)
        for rel in view.relations:
            if rel.source not in paths or rel.target not in paths:
                continue
            label = f"«{rel.kind}»" if rel.kind in {"include", "extend"} else (rel.label or "")
            lines += self._edge(paths[rel.source], paths[rel.target], rel.kind, label, multiplicity(rel))
        return lines

    def _class(self, view: ArchitectureView) -> list[str]:
        def leaf(e, indent: str) -> list[str]:
            a = alias(e.id)
            if e.kind == "entity" or any(x.key or x.foreign_key for x in e.attributes):
                out = [f"{indent}{a}: {s(e.name)} {{", f"{indent}  shape: sql_table"]
                for attr in e.attributes:
                    cons = [c for c, on in (("primary_key", attr.key), ("foreign_key", attr.foreign_key)) if on]
                    tail = f" {{constraint: [{'; '.join(cons)}]}}" if cons else ""
                    out.append(f"{indent}  {s(attr.name)}: {s(attr.type or '')}{tail}")
                out += [f"{indent}  {s('- ' + r)}: {s('responsibility')}" for r in e.responsibilities]
                if e.stereotype:
                    out.append(f"{indent}  tooltip: {s('«' + e.stereotype + '»')}")
                return out + [f"{indent}}}"]
            out = [f"{indent}{a}: {s(e.name)} {{", f"{indent}  shape: class"]
            out += [f"{indent}  {s('+' + attr.name)}: {s(attr.type or '')}" for attr in e.attributes]
            out += [f"{indent}  {s('+' + r + '()')}" for r in e.responsibilities]
            return out + [f"{indent}}}"]

        lines = ["direction: right", *self._tree(view, leaf)]
        paths = self._paths(view)
        for rel in view.relations:
            if rel.source in paths and rel.target in paths:
                lines += self._edge(paths[rel.source], paths[rel.target], rel.kind, rel.label or "", multiplicity(rel))
        return lines

    # ---------------------------------------------------------- behaviour
    def _sequence(self, view: ArchitectureView) -> list[str]:
        lines = ["sequence: {", "  shape: sequence_diagram"]
        for e in view.content_elements():
            name = e.name + (f" «{e.stereotype}»" if e.stereotype else "")
            lines.append(f"  {alias(e.id)}: {s(name)}" + (" {shape: person}" if e.kind == "actor" else ""))
        for i, (frag_id, steps) in enumerate(segments(view)):
            frag = fragment(view, frag_id)
            indent = "  "
            if frag:
                lines.append(f"  fragment_{i}: {s(f'{frag.kind} [{frag.guard}]')} {{")
                indent = "    "
            for st in steps:
                edge = f"{indent}{alias(st.source)} -> {alias(st.target)}: {s(f'{st.order}. {st.message}')}"
                lines.append(edge + (" {style.stroke-dash: 3}" if st.kind == "return" else ""))
            if frag:
                lines.append("  }")
        lines.append("}")
        return lines

    def _communication(self, view: ArchitectureView) -> list[str]:
        lines = ["direction: right"]
        for e in view.content_elements():
            lines.append(f"{alias(e.id)}: {ml(label_lines(e))}" + (" {shape: person}" if e.kind == "actor" else ""))
        for st in sorted(view.interactions, key=lambda x: x.order):
            frag = fragment(view, st.fragment)
            guard = f" [{frag.guard}]" if frag else ""
            lines += self._edge(alias(st.source), alias(st.target), "return" if st.kind == "return" else "call",
                                f"{st.order}.{guard} {st.message}")
        return lines

    def _activity(self, view: ArchitectureView) -> list[str]:
        nodes, edges = activity_flow(view)
        lines = ["direction: down"]
        path = {}
        for node_id, kind, label, lane in nodes:
            if lane:
                continue
            path[node_id] = node_id
            if kind == "decision":
                lines.append(f"{node_id}: {s(label)} {{shape: diamond}}")
            else:
                lines.append(f"{node_id}: {s(label)} {{shape: circle}}")
        for e in view.content_elements():
            lines.append(f"{alias(e.id)}: {s(e.name)} {{")
            for node_id, kind, label, lane in nodes:
                if lane == e.id:
                    path[node_id] = f"{alias(e.id)}.{node_id}"
                    lines.append(f"  {node_id}: {s(label)} {{style.border-radius: 12}}")
            lines.append("}")
        for src, tgt, label in edges:
            lines.append(f"{path[src]} -> {path[tgt]}" + (f": {s(label)}" if label else ""))
        return lines

    def _state(self, view: ArchitectureView) -> list[str]:
        lines = ["direction: right", "initial: \" \" {", "  shape: circle", "  width: 20",
                 "  style.fill: black", "}"]
        lines += self._tree(view)
        paths = self._paths(view)
        content = view.content_elements()
        targets = {r.target for r in view.relations}
        initial = [e for e in content if e.id not in targets][:1] or content[:1]
        lines += [f"initial -> {paths[e.id]}" for e in initial]
        for r in view.relations:
            if r.source in paths and r.target in paths:
                lines += self._edge(paths[r.source], paths[r.target], "transition", r.label or "")
        return lines

    def _table(self, view: ArchitectureView) -> list[str]:
        def cell(value: str) -> str:
            return quote(value).replace("|", "\\|").replace("`", "'") or " "

        rows = table_rows(view)
        md = ["| " + " | ".join(cell(c) for c in rows[0]) + " |", "|" + "---|" * len(rows[0])]
        md += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows[1:]]
        return ["view_table: |`md", *[f"  {line}" for line in md], "`|"]
