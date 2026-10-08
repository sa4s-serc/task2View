"""PlantUML renderer: native for every UML model kind except communication diagrams and tables.

Approximations (flagged ``approximated``):
- uml-communication: components with numbered message labels on the links.
- table: a creole table in a legend.
"""

from __future__ import annotations

from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.phase7.notations.base import (
    Renderer, alias, children, fragment, label_lines, multiplicity, quote, register, segments, table_rows,
)

_CONTAINER = {"layer": "package", "module": "package", "tier": "package", "system": "rectangle",
              "node": "node", "execution_env": "node"}
_ARROWS = {"uses": "-->", "request-reply": "-->", "attachment": "--", "reads": "-->", "writes": "-->",
           "allowed-to-use": "..>", "is-a": "--|>", "generalization": "--|>", "implements": "..|>",
           "association": "-->", "composition": "*--", "include": "..>", "extend": "..>", "deploys": "..>",
           "communicates": "--", "transition": "-->", "publishes": "-->", "subscribes": "<--",
           "crosscuts": "..>", "traces-to": "..>", "assigned-to": "..>", "allocated-to": "..>"}


@register
class PlantUMLRenderer(Renderer):
    language = "plantuml"
    extension = "puml"

    def render(self, view: ArchitectureView) -> RenderResult:
        kind = view.model_kind
        body = {
            "uml-sequence": self._sequence,
            "uml-communication": self._communication,
            "uml-activity": self._activity,
            "uml-state": self._state,
            "uml-usecase": self._usecase,
            "table": self._table,
        }.get(kind, self._structure)(view)
        source = "\n".join(["@startuml", f"title {quote(view.title)}", *body, "@enduml"])
        return self.result(view, source)

    # ---------------------------------------------------------- structure
    def _structure(self, view: ArchitectureView) -> list[str]:
        tree = children(view)
        lines: list[str] = []
        if view.model_kind == "uml-deployment":
            lines.append("left to right direction")
        else:
            lines.append("top to bottom direction")

        def emit(element, indent: str):
            nested = tree.get(element.id, [])
            if element.group or nested:
                keyword = _CONTAINER.get(element.kind, "package" if element.group else "node")
                stereo = f" <<{element.kind}>>" if element.group else ""
                lines.append(f'{indent}{keyword} "{quote(element.name)}" as {alias(element.id)}{stereo} {{')
                for child in nested:
                    emit(child, indent + "  ")
                lines.append(f"{indent}}}")
            else:
                lines.extend(f"{indent}{line}" for line in self._leaf(view, element))

        for top in tree.get(None, []):
            emit(top, "")
        for rel in view.relations:
            arrow = _ARROWS.get(rel.kind, "-->")
            src_m, tgt_m = multiplicity(rel)
            left = f'{alias(rel.source)}{" " + chr(34) + src_m + chr(34) if src_m else ""}'
            right = f'{chr(34) + tgt_m + chr(34) + " " if tgt_m else ""}{alias(rel.target)}'
            label = f" : {quote(rel.label)}" if rel.label else ""
            if rel.kind in {"include", "extend"}:
                label = f" : <<{rel.kind}>>"
            lines.append(f"{left} {arrow} {right}{label}")
        return lines

    def _leaf(self, view: ArchitectureView, e) -> list[str]:
        a, stereo = alias(e.id), f" <<{e.stereotype}>>" if e.stereotype else ""
        if e.kind in {"entity", "class", "interface", "enum"}:
            keyword = {"interface": "interface", "enum": "enum"}.get(e.kind, "class")
            out = [f'{keyword} "{quote(e.name)}" as {a}{stereo} {{']
            for attr in e.attributes:
                tags = (" {PK}" if attr.key else "") + (" {FK}" if attr.foreign_key else "")
                out.append(f"  {quote(attr.name)}{' : ' + quote(attr.type) if attr.type else ''}{tags}")
            if e.responsibilities:
                out.append("  --")
                out += [f"  {quote(r)}" for r in e.responsibilities]
            out.append("}")
            return out
        if e.kind == "actor":
            return [f'actor "{quote(e.name)}" as {a}']
        if e.kind == "use_case":
            return [f'usecase "{quote(e.name)}" as {a}']
        if e.kind == "datastore":
            return [f'database "{quote(e.name)}" as {a}']
        if e.kind in {"artifact", "file"}:
            return [f'artifact "{quote(e.name)}" as {a}']
        if e.kind in {"node", "execution_env"}:
            return [f'node "{quote(e.name)}" as {a}{stereo}']
        if e.kind == "external_system":
            return [f'component "{quote(e.name)}" as {a} <<external>>']
        if e.kind == "system":
            return [f'rectangle "{quote(e.name)}" as {a} <<system>>']
        keyword = "component" if e.kind in {"component", "service", "filter", "process", "tier"} else "rectangle"
        lines = label_lines(e)
        if len(lines) == 1:
            return [f'{keyword} "{quote(e.name)}" as {a}{stereo}']
        text = "\\n".join(quote(l) for l in lines[:1]) + "\\n--\\n" + "\\n".join(quote(l) for l in lines[1:])
        return [f'{keyword} "{text}" as {a}{stereo}']

    # ---------------------------------------------------------- behaviour
    def _sequence(self, view: ArchitectureView) -> list[str]:
        lines = []
        for e in view.content_elements():
            keyword = "actor" if e.kind == "actor" else "participant"
            stereo = f" <<{e.stereotype}>>" if e.stereotype else ""
            lines.append(f'{keyword} "{quote(e.name)}" as {alias(e.id)}{stereo}')
        for frag_id, steps in segments(view):
            frag = fragment(view, frag_id)
            if frag:
                lines.append(f"{frag.kind} {quote(frag.guard)}")
            for st in steps:
                arrow = "-->" if st.kind == "return" else "->"
                lines.append(f"{alias(st.source)} {arrow} {alias(st.target)} : {st.order}. {quote(st.message)}")
            if frag:
                lines.append("end")
        return lines

    def _communication(self, view: ArchitectureView) -> list[str]:
        lines = [f'component "{quote(e.name)}" as {alias(e.id)}' if e.kind != "actor" else f'actor "{quote(e.name)}" as {alias(e.id)}'
                 for e in view.content_elements()]
        for st in sorted(view.interactions, key=lambda s: s.order):
            guard = f" [{quote(fragment(view, st.fragment).guard)}]" if st.fragment and fragment(view, st.fragment) else ""
            lines.append(f"{alias(st.source)} --> {alias(st.target)} : {st.order}{guard}: {quote(st.message)}")
        return lines

    def _activity(self, view: ArchitectureView) -> list[str]:
        names = {e.id: e.name for e in view.elements}
        lanes = [quote(e.name) for e in view.content_elements()]
        lines = [f"|{lane}|" for lane in lanes]  # swimlanes must be declared before start
        lines += [f"|{lanes[0]}|", "start"] if lanes else ["start"]
        for frag_id, steps in segments(view):
            frag = fragment(view, frag_id)
            if frag:
                lines.append(f"if ({quote(frag.guard)}) then (yes)")
            for st in steps:
                lines.append(f"|{quote(names.get(st.source, st.source))}|")  # the caller performs the action
                lines.append(f":{quote(st.message)};")
            if frag:
                lines.append("endif")
        lines.append("stop")
        return lines

    def _state(self, view: ArchitectureView) -> list[str]:
        lines = [f'state "{quote(e.name)}" as {alias(e.id)}' for e in view.content_elements()]
        targets = {r.target for r in view.relations}
        initial = [e for e in view.content_elements() if e.id not in targets][:1] or view.content_elements()[:1]
        lines += [f"[*] --> {alias(e.id)}" for e in initial]
        lines += [f"{alias(r.source)} --> {alias(r.target)}{' : ' + quote(r.label) if r.label else ''}" for r in view.relations]
        return lines

    def _usecase(self, view: ArchitectureView) -> list[str]:
        return ["left to right direction", *self._structure(view)[1:]]

    def _table(self, view: ArchitectureView) -> list[str]:
        rows = table_rows(view)
        lines = ["legend top left"]
        lines.append("|= " + " |= ".join(quote(c) for c in rows[0]) + " |")
        lines += ["| " + " | ".join(quote(c) or " " for c in row) + " |" for row in rows[1:]]
        lines.append("endlegend")
        return lines
