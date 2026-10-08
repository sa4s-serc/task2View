"""Graphviz (DOT) renderer: every model kind is an approximation (Graphviz has no diagram semantics).

Conventions (all flagged ``approximated``):
- Nesting (groups, layers, modules, nodes, system boundaries, any element with children) -> ``subgraph cluster_*``
  labelled ``«kind» name``; each cluster holds an invisible anchor node so relations to a group are drawn as
  compound edges (``lhead`` / ``ltail``).
- Elements -> HTML-like labels: bold name, then responsibilities, then attributes, inside the node. Shapes by kind:
  component -> ``component``, datastore -> ``cylinder``, node -> ``box3d``, artifact -> ``note``, use case ->
  ``ellipse``, actor -> rounded box labelled ``«actor»``, external system -> dashed box, state -> rounded box,
  class / entity / interface / enum -> ``plain`` shape with a UML-like compartment table (stereotype + name |
  attributes | responsibilities).
- Relations: generalization / is-a -> hollow arrowhead (``onormal``); implements -> dashed hollow arrowhead;
  composition -> diamond tail; include / extend / allowed-to-use / deploys -> dashed with ``«kind»`` label for
  include / extend; attachment / communicates -> undirected; association multiplicity -> ``taillabel`` /
  ``headlabel``.
- uml-state: rounded state boxes, a filled-point initial pseudo-state, labelled transition edges.
- uml-sequence: lifeline heads in one rank, messages as edges labelled ``<order>. <message>`` (returns dashed),
  fragment steps prefixed ``[<kind> <guard>]`` and a note node listing each fragment and its steps.
- uml-communication: the same numbered edges with free layout (no lifeline rank).
- uml-activity: one swimlane cluster per participant, an action node per step (in the caller's lane) chained
  by control flow from an initial to a final node; a fragment becomes a decision diamond (guard) whose
  ``[guard]`` branch runs the fragment steps and whose ``[else]`` branch skips to a merge diamond.
- table: a single ``plain`` node whose HTML label is the table (header row bold), rows from ``table_rows``.
"""

from __future__ import annotations

from html import escape

from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.phase7.notations.base import (
    Renderer, alias, children, fragment, label_lines, multiplicity, quote, register, segments, table_rows,
)

_SHAPES = {"component": "component", "service": "component", "filter": "component", "process": "component",
           "datastore": "cylinder", "database": "cylinder", "queue": "cds", "node": "box3d", "execution_env": "box3d",
           "device": "box3d", "artifact": "note", "file": "note", "use_case": "ellipse", "module": "tab"}
_CLASSES = {"entity", "class", "interface", "enum"}
_EDGES = {"is-a": 'arrowhead="onormal"', "generalization": 'arrowhead="onormal"',
          "implements": 'arrowhead="onormal", style="dashed"', "composition": 'dir="both", arrowtail="diamond"',
          "include": 'style="dashed"', "extend": 'style="dashed"', "allowed-to-use": 'style="dashed"',
          "deploys": 'style="dashed"', "crosscuts": 'style="dashed"', "traces-to": 'style="dashed"',
          "assigned-to": 'style="dashed"', "allocated-to": 'style="dashed"', "attachment": 'dir="none"',
          "communicates": 'dir="none"', "subscribes": 'dir="back"'}


def _h(text: str) -> str:
    return escape(text, quote=True)


def _attrs(**kw: str) -> str:
    return "[" + ", ".join(f'{k}="{quote(v)}"' if not v.startswith("<") else f"{k}={v}" for k, v in kw.items()) + "]"


@register
class GraphvizRenderer(Renderer):
    language = "graphviz"
    extension = "dot"

    def render(self, view: ArchitectureView) -> RenderResult:
        kind = view.model_kind
        body = {
            "uml-sequence": self._sequence,
            "uml-communication": self._communication,
            "uml-activity": self._activity,
            "uml-state": self._state,
            "table": self._table,
        }.get(kind, self._structure)(view)
        rankdir = "LR" if kind in {"uml-deployment", "uml-usecase", "uml-communication"} else "TB"
        source = "\n".join([
            f"digraph {alias(view.id)} {{",
            f'  graph [label="{quote(view.title)}", labelloc="t", fontname="Helvetica", compound="true", '
            f'rankdir="{rankdir}", newrank="true"];',
            '  node [fontname="Helvetica", fontsize="11"];',
            '  edge [fontname="Helvetica", fontsize="10"];',
            *("  " + line for line in body),
            "}",
        ])
        return self.result(view, source)

    # ---------------------------------------------------------- nodes
    def _label(self, e) -> str:
        """HTML-like label: name, responsibilities, attributes (inside the node)."""
        if e.kind in _CLASSES:
            head = (f"<TR><TD>«{_h(e.stereotype)}»</TD></TR>" if e.stereotype else "") + f"<TR><TD><B>{_h(e.name)}</B></TD></TR>"
            attrs = "".join(f'<TR><TD ALIGN="LEFT">{_h(line)}</TD></TR>'
                            for line in label_lines(e)[1 + len(e.responsibilities):])
            resp = "".join(f'<TR><TD ALIGN="LEFT">{_h(r)}</TD></TR>' for r in e.responsibilities)
            rows = head + "<HR/>" + (attrs or "<TR><TD> </TD></TR>") + ("<HR/>" + resp if resp else "")
            return f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">{rows}</TABLE>>'
        stereo = f"«{_h(e.stereotype)}»<BR/>" if e.stereotype else ""
        if e.kind == "actor":
            stereo = "«actor»<BR/>"
        lines = label_lines(e)
        rest = "".join(f'<BR ALIGN="LEFT"/>{_h(line)}' for line in lines[1:])
        return f"<{stereo}<B>{_h(lines[0])}</B>{rest}>"

    def _node(self, e) -> str:
        a = alias(e.id)
        if e.kind in _CLASSES:
            return f"{a} {_attrs(shape='plain', label=self._label(e))};"
        style = {"actor": "rounded", "state": "rounded", "external_system": "dashed"}.get(e.kind, "")
        shape = _SHAPES.get(e.kind, "box")
        kw = {"shape": shape, "label": self._label(e)}
        if style:
            kw["style"] = style
        return f"{a} {_attrs(**kw)};"

    def _tree(self, view: ArchitectureView) -> tuple[list[str], set[str]]:
        """Nodes and clusters; returns the lines and the ids drawn as clusters."""
        tree, lines, clusters = children(view), [], set()

        def emit(element, indent: str):
            nested = tree.get(element.id, [])
            if element.group or nested:
                a = alias(element.id)
                clusters.add(element.id)
                title = f"«{_h(element.kind)}»<BR/>" if element.group else ""
                body = "".join(f'<BR ALIGN="LEFT"/>{_h(l)}' for l in label_lines(element)[1:])
                lines.append(f"{indent}subgraph cluster_{a} {{")
                lines.append(f'{indent}  label=<{title}<B>{_h(element.name)}</B>{body}>; style="rounded";')
                lines.append(f'{indent}  {a} [shape="point", style="invis", width="0", label=""];')
                for child in nested:
                    emit(child, indent + "  ")
                lines.append(f"{indent}}}")
            else:
                lines.append(indent + self._node(element))

        for top in tree.get(None, []):
            emit(top, "")
        return lines, clusters

    # ---------------------------------------------------------- structure
    def _structure(self, view: ArchitectureView) -> list[str]:
        lines, clusters = self._tree(view)
        for rel in view.relations:
            kw = [_EDGES.get(rel.kind, "")]
            label = rel.label or ""
            if rel.kind in {"include", "extend"}:
                label = f"«{rel.kind}»"
            if label:
                kw.append(f'label="{quote(label)}"')
            src_m, tgt_m = multiplicity(rel)
            if src_m:
                kw.append(f'taillabel="{quote(src_m)}"')
            if tgt_m:
                kw.append(f'headlabel="{quote(tgt_m)}"')
            if rel.source in clusters:
                kw.append(f'ltail="cluster_{alias(rel.source)}"')
            if rel.target in clusters:
                kw.append(f'lhead="cluster_{alias(rel.target)}"')
            attrs = ", ".join(k for k in kw if k)
            lines.append(f"{alias(rel.source)} -> {alias(rel.target)}{' [' + attrs + ']' if attrs else ''};")
        return lines

    def _state(self, view: ArchitectureView) -> list[str]:
        lines = self._structure(view)
        targets = {r.target for r in view.relations}
        states = view.content_elements()
        initial = [e for e in states if e.id not in targets][:1] or states[:1]
        lines.insert(0, 'initial_state [shape="point", width="0.15", label=""];')
        lines += [f"initial_state -> {alias(e.id)};" for e in initial]
        return lines

    # ---------------------------------------------------------- behaviour
    def _messages(self, view: ArchitectureView) -> list[str]:
        lines = []
        for st in sorted(view.interactions, key=lambda s: s.order):
            frag = fragment(view, st.fragment) if st.fragment else None
            prefix = f"[{frag.kind} {frag.guard}] " if frag else ""
            style = ', style="dashed"' if st.kind == "return" else ""
            lines.append(f'{alias(st.source)} -> {alias(st.target)} [label="{quote(prefix + f"{st.order}. " + st.message)}"{style}];')
        return lines

    def _fragment_notes(self, view: ArchitectureView) -> list[str]:
        lines = []
        for i, (frag_id, steps) in enumerate(segments(view)):
            frag = fragment(view, frag_id)
            if frag:
                orders = ", ".join(str(s.order) for s in steps)
                lines.append(f'fragment_{i} [shape="note", label="{quote(f"{frag.kind} [{frag.guard}]: steps {orders}")}"];')
        return lines

    def _sequence(self, view: ArchitectureView) -> list[str]:
        lines, _ = self._tree(view)
        heads = " ".join(f"{alias(e.id)};" for e in view.content_elements())
        return [*lines, f"{{ rank=same; {heads} }}", *self._fragment_notes(view), *self._messages(view)]

    def _communication(self, view: ArchitectureView) -> list[str]:
        lines, _ = self._tree(view)
        return [*lines, *self._fragment_notes(view), *self._messages(view)]

    def _activity(self, view: ArchitectureView) -> list[str]:
        lanes: dict[str, list[str]] = {e.id: [] for e in view.content_elements()}
        flow: list[str] = []
        prev = "start"
        for i, (frag_id, steps) in enumerate(segments(view)):
            frag = fragment(view, frag_id)
            branch_label = ""
            if frag:
                flow.append(f'decision_{i} [shape="diamond", label="{quote(frag.guard)}"];')
                flow.append(f"{prev} -> decision_{i};")
                prev, branch_label = f"decision_{i}", f"[{frag.guard}]"
            for st in steps:
                node = f"action_{st.order}"
                lanes.setdefault(st.source, []).append(
                    f'{node} [shape="box", style="rounded", label="{quote(st.message)}"];')
                label = f' [label="{quote(branch_label)}"]' if branch_label else ""
                flow.append(f"{prev} -> {node}{label};")
                prev, branch_label = node, ""
            if frag:
                flow.append(f'merge_{i} [shape="diamond", label=""];')
                flow.append(f"{prev} -> merge_{i};")
                flow.append(f'decision_{i} -> merge_{i} [label="[else]"];')
                prev = f"merge_{i}"
        names = {e.id: e.name for e in view.elements}
        lines = ['start [shape="circle", style="filled", fillcolor="black", width="0.2", label=""];']
        for lane_id, actions in lanes.items():
            lines.append(f"subgraph cluster_{alias(lane_id)} {{")
            lines.append(f'  label=<<B>{_h(names.get(lane_id, lane_id))}</B>>; style="rounded";')
            lines += ["  " + a for a in actions] or [f'  {alias(lane_id)} [shape="point", style="invis", label=""];']
            lines.append("}")
        lines.append('end [shape="doublecircle", style="filled", fillcolor="black", width="0.15", label=""];')
        return [*lines, *flow, f"{prev} -> end;"]

    def _table(self, view: ArchitectureView) -> list[str]:
        rows = table_rows(view)
        header = "<TR>" + "".join(f"<TD><B>{_h(c)}</B></TD>" for c in rows[0]) + "</TR>"
        body = "".join("<TR>" + "".join(f'<TD ALIGN="LEFT">{_h(c)}</TD>' for c in row) + "</TR>" for row in rows[1:])
        return [f'table [shape="plain", label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
                f"{header}{body}</TABLE>>];"]
