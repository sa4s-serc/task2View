"""Mermaid renderer: native for sequence, activity (flowchart), state and class diagrams.

Native:
- uml-sequence: ``sequenceDiagram`` with ``actor`` / ``participant``, ``alt`` / ``opt`` / ``loop`` blocks; the
  message order is prefixed ("<order>.") so it survives in the label.
- uml-activity: ``flowchart TB`` with one subgraph swimlane per performer, a start / end circle, a rhombus per
  fragment guard (yes branch into the fragment, no branch around it; loops get a back edge).
- uml-state: ``stateDiagram-v2`` with ``[*]`` initial transitions and composite states for nesting.
- uml-class: ``classDiagram`` with attributes ({PK}/{FK} as ``PK``/``FK`` suffixes), responsibilities as
  ``responsibility`` members, multiplicities on associations, ``namespace`` for top-level groups.

Approximations (flagged ``approximated``):
- uml-component / uml-package / uml-deployment / uml-usecase: ``flowchart`` with nested ``subgraph`` blocks for
  every container; shapes encode the element kind (cylinder datastore, stadium use case, circle actor, subroutine
  node, hexagon external system); responsibilities / attributes are ``<br/>`` lines inside the node label;
  dotted arrows carry ``«include»`` / ``«extend»``; ``is-a`` / generalization edges are labelled ``«is-a»``;
  multiplicities are written in the edge label as ``src..tgt``.
- uml-communication: ``flowchart LR`` of the participants with one numbered edge per message ("<order>. [guard]
  message").
- table: Mermaid has no table, so a ``flowchart TB`` subgraph holding one node per row, top to bottom (header
  row first); each node label lists ``column: value`` pairs on ``<br/>``-separated lines.
"""

from __future__ import annotations

from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.phase7.notations.base import (
    Renderer, alias, children, fragment, label_lines, multiplicity, quote, register, segments, table_rows,
)

_DOTTED = {"allowed-to-use", "implements", "include", "extend", "deploys", "crosscuts", "traces-to",
           "assigned-to", "allocated-to"}
_UNDIRECTED = {"attachment", "communicates"}


def text(value: str) -> str:
    """Escape for a double-quoted Mermaid label (also safe in sequence message text)."""
    return (quote(value).replace("#", "#35;").replace("<", "#lt;").replace(">", "#gt;")
            .replace(";", "#59;"))


def activity_flow(view: ArchitectureView):
    """Shared activity-flow construction: (nodes, edges).

    nodes: list of (node id, kind, text, performer element id or None); kind in start|action|decision|end.
    edges: list of (source node id, target node id, label or "").
    Each interaction becomes an action performed by its source; a fragment becomes a decision whose "yes"
    branch runs the fragment steps and whose "no" branch skips them (loops also get a back edge).
    """
    nodes = [("flow_start", "start", "start", None)]
    edges: list[tuple[str, str, str]] = []
    pending: list[tuple[str, str]] = [("flow_start", "")]

    def connect(node_id: str):
        nonlocal pending
        edges.extend((src, node_id, label) for src, label in pending)
        pending = [(node_id, "")]

    for i, (frag_id, steps) in enumerate(segments(view)):
        frag = fragment(view, frag_id)
        decision = None
        if frag:
            decision = f"flow_d{i}"
            nodes.append((decision, "decision", f"{frag.kind} [{frag.guard}]", None))
            connect(decision)
            pending = [(decision, "yes")]
        for st in steps:
            node_id = f"flow_a{st.order}"
            nodes.append((node_id, "action", f"{st.order}. {st.message}", st.source))
            connect(node_id)
        if decision:
            if frag.kind == "loop":
                edges.append((pending[0][0], decision, "repeat"))
            pending = pending + [(decision, "no")]
    nodes.append(("flow_end", "end", "end", None))
    edges.extend((src, "flow_end", label) for src, label in pending)
    return nodes, edges


@register
class MermaidRenderer(Renderer):
    language = "mermaid"
    extension = "mmd"

    def render(self, view: ArchitectureView) -> RenderResult:
        body = {
            "uml-sequence": self._sequence,
            "uml-communication": self._communication,
            "uml-activity": self._activity,
            "uml-state": self._state,
            "uml-class": self._class,
            "table": self._table,
        }.get(view.model_kind, self._structure)(view)
        title = quote(view.title).replace(":", " -")
        source = "\n".join(["---", f'title: "{title}"', "---", *body])
        return self.result(view, source)

    # ---------------------------------------------------------- flowchart structure (approximation)
    def _node(self, e) -> str:
        a = alias(e.id)
        lines = label_lines(e)
        if e.stereotype:
            lines.insert(1, f"«{e.stereotype}»")
        label = "<br/>".join(text(line) for line in lines)
        shape = {"datastore": ('[("', '")]'), "use_case": ('(["', '"])'), "actor": ('(("', '"))'),
                 "node": ('[["', '"]]'), "execution_env": ('[["', '"]]'), "external_system": ('{{"', '"}}'),
                 "artifact": ('[/"', '"/]'), "file": ('[/"', '"/]'), "state": ('("', '")')}.get(e.kind, ('["', '"]'))
        return f"{a}{shape[0]}{label}{shape[1]}"

    def _structure(self, view: ArchitectureView) -> list[str]:
        tree = children(view)
        direction = "LR" if view.model_kind in {"uml-deployment", "uml-usecase"} else "TB"
        lines = [f"flowchart {direction}"]

        def emit(element, indent: str):
            nested = tree.get(element.id, [])
            if element.group or nested:
                lines.append(f'{indent}subgraph {alias(element.id)}["{text(element.name)}"]')
                for child in nested:
                    emit(child, indent + "  ")
                lines.append(f"{indent}end")
            else:
                lines.append(indent + self._node(element))

        for top in tree.get(None, []):
            emit(top, "  ")
        for rel in view.relations:
            lines.append("  " + self._edge(rel))
        return lines

    def _edge(self, rel) -> str:
        label = rel.label or ""
        if rel.kind in {"include", "extend"}:
            label = f"«{rel.kind}»"
        elif rel.kind in {"is-a", "generalization"}:
            label = "«is-a»" + (f" {label}" if label else "")
        elif rel.kind == "implements":
            label = "«implements»" + (f" {label}" if label else "")
        src_m, tgt_m = multiplicity(rel)
        if src_m or tgt_m:
            label = f"{src_m}..{tgt_m}" + (f" {label}" if label else "")
        arrow = "-.->" if rel.kind in _DOTTED else ("---" if rel.kind in _UNDIRECTED else "-->")
        if rel.kind == "subscribes":
            src, tgt = alias(rel.target), alias(rel.source)
        else:
            src, tgt = alias(rel.source), alias(rel.target)
        middle = f'{arrow}|"{text(label)}"|' if label else arrow
        return f"{src} {middle} {tgt}"

    # ---------------------------------------------------------- native kinds
    def _class(self, view: ArchitectureView) -> list[str]:
        tree = children(view)
        lines = ["classDiagram"]

        def klass(e, indent: str):
            a = alias(e.id)
            lines.append(f'{indent}class {a}["{text(e.name)}"] {{')
            if e.kind == "interface":
                lines.append(f"{indent}  <<interface>>")
            elif e.kind == "enum":
                lines.append(f"{indent}  <<enumeration>>")
            elif e.stereotype:
                lines.append(f"{indent}  <<{_ident(e.stereotype)}>>")
            for attr in e.attributes:
                tags = (" PK" if attr.key else "") + (" FK" if attr.foreign_key else "")
                kind = f"{_ident(attr.type)} " if attr.type else ""
                lines.append(f"{indent}  +{kind}{_ident(attr.name)}{tags}")
            for r in e.responsibilities:
                lines.append(f"{indent}  +{_ident(r)}()")
            lines.append(f"{indent}}}")

        def leaves(e):
            nested = tree.get(e.id, [])
            if e.group or nested:
                for child in nested:
                    yield from leaves(child)
            else:
                yield e

        for top in tree.get(None, []):
            nested = tree.get(top.id, [])
            if top.group or nested:
                lines.append(f"  namespace {alias(top.id)} {{")
                for leaf in leaves(top):
                    klass(leaf, "    ")
                lines.append("  }")
                lines.append(f"  note \"{text(top.name)}\"")  # namespace label (namespaces take identifiers only)
            else:
                klass(top, "  ")
        arrows = {"is-a": "<|--", "generalization": "<|--", "implements": "<|..", "composition": "*--",
                  "aggregation": "o--", "association": "-->", "uses": "..>", "allowed-to-use": "..>"}
        for rel in view.relations:
            arrow = arrows.get(rel.kind, "-->")
            src_m, tgt_m = multiplicity(rel)
            if arrow.startswith("<|"):  # parent <|-- child
                left, right = alias(rel.target), alias(rel.source)
                src_m, tgt_m = tgt_m, src_m
            else:
                left, right = alias(rel.source), alias(rel.target)
            left += f' "{src_m}"' if src_m else ""
            right = (f'"{tgt_m}" ' if tgt_m else "") + right
            label = f" : {_ident(rel.label)}" if rel.label else ""
            lines.append(f"  {left} {arrow} {right}{label}")
        return lines

    def _sequence(self, view: ArchitectureView) -> list[str]:
        lines = ["sequenceDiagram"]
        for e in view.content_elements():
            keyword = "actor" if e.kind == "actor" else "participant"
            stereo = f" «{e.stereotype}»" if e.stereotype else ""
            lines.append(f"  {keyword} {alias(e.id)} as {text(e.name)}{stereo}")
        for frag_id, steps in segments(view):
            frag = fragment(view, frag_id)
            indent = "  "
            if frag:
                keyword = frag.kind if frag.kind in {"alt", "opt", "loop", "par", "critical", "break"} else "opt"
                lines.append(f"  {keyword} {text(frag.guard)}")
                indent = "    "
            for st in steps:
                arrow = "-->>" if st.kind == "return" else "->>"
                lines.append(f"{indent}{alias(st.source)}{arrow}{alias(st.target)}: {st.order}. {text(st.message)}")
            if frag:
                lines.append("  end")
        return lines

    def _communication(self, view: ArchitectureView) -> list[str]:
        lines = ["flowchart LR"]
        lines += ["  " + self._node(e) for e in view.content_elements()]
        for st in sorted(view.interactions, key=lambda s: s.order):
            frag = fragment(view, st.fragment)
            guard = f" [{frag.guard}]" if frag else ""
            arrow = "-.->" if st.kind == "return" else "-->"
            lines.append(f'  {alias(st.source)} {arrow}|"{text(f"{st.order}.{guard} {st.message}")}"| {alias(st.target)}')
        return lines

    def _activity(self, view: ArchitectureView) -> list[str]:
        nodes, edges = activity_flow(view)
        lines = ["flowchart TB"]
        by_lane: dict[str, list] = {}
        for node in nodes:
            if node[3]:
                by_lane.setdefault(node[3], []).append(node)
        shapes = {"start": ('(("', '"))'), "end": ('((("', '")))'), "decision": ('{"', '"}'), "action": ('("', '")')}
        for node_id, kind, label, lane in nodes:
            if not lane:
                lines.append(f"  {node_id}{shapes[kind][0]}{text(label)}{shapes[kind][1]}")
        for e in view.content_elements():
            lines.append(f'  subgraph {alias(e.id)}["{text(e.name)}"]')
            for node_id, kind, label, _ in by_lane.get(e.id, []):
                lines.append(f"    {node_id}{shapes[kind][0]}{text(label)}{shapes[kind][1]}")
            if not by_lane.get(e.id):
                lines.append(f'    {alias(e.id)}_idle[" "]')  # Mermaid needs a member to draw the lane
            lines.append("  end")
        for src, tgt, label in edges:
            lines.append(f'  {src} -->|"{text(label)}"| {tgt}' if label else f"  {src} --> {tgt}")
        return lines

    def _state(self, view: ArchitectureView) -> list[str]:
        tree = children(view)
        lines = ["stateDiagram-v2"]

        def emit(e, indent: str):
            lines.append(f'{indent}state "{text(e.name)}" as {alias(e.id)}')
            nested = tree.get(e.id, [])
            if nested:
                lines.append(f"{indent}state {alias(e.id)} {{")
                for child in nested:
                    emit(child, indent + "  ")
                lines.append(f"{indent}}}")

        for top in tree.get(None, []):
            emit(top, "  ")
        content = view.content_elements()
        targets = {r.target for r in view.relations}
        initial = [e for e in content if e.id not in targets][:1] or content[:1]
        lines += [f"  [*] --> {alias(e.id)}" for e in initial]
        for r in view.relations:
            label = f" : {text(r.label).replace(':', ' ')}" if r.label else ""
            lines.append(f"  {alias(r.source)} --> {alias(r.target)}{label}")
        return lines

    def _table(self, view: ArchitectureView) -> list[str]:
        rows = table_rows(view)
        header = rows[0]
        lines = ["flowchart TB", f'  subgraph table["{text(view.title)}"]', "    direction TB"]
        ids = []
        for i, row in enumerate(rows):
            node_id = f"row{i}"
            ids.append(node_id)
            if i == 0:
                label = "<br/>".join(f"<b>{text(c)}</b>" for c in header)
            else:
                label = "<br/>".join(f"{text(h)}: {text(c)}" for h, c in zip(header, row) if c)
            lines.append(f'    {node_id}["{label}"]')
        lines.append("  end")
        lines += [f"  {a} ~~~ {b}" for a, b in zip(ids, ids[1:])]
        return lines


def _ident(value: str | None) -> str:
    """Mermaid class members / labels: drop characters the classDiagram grammar reserves."""
    out = quote(value or "")
    for ch in "{}<>[]()\"#;:~":
        out = out.replace(ch, " " if ch not in "<>" else "")
    return " ".join(out.split()) or "_"
