"""PlantUML renderer: every view as a UML 2.5.1 diagram (ADR-008; rules in knowledge/data/uml/uml-2.5.1.yaml).

Each diagram has a frame whose heading names its kind (Annex A). Shapes and paths follow the diagram type:
components and packages are related by dashed dependencies (7.7.4), deployment nodes by communication
paths (19.4.4), use cases sit in a subject rectangle (18.1.4). Stereotypes are shown only where UML allows them
(Standard Profile, notation keywords, the Task2View profile); otherwise the role stays in the view's JSON.

Approximation (flagged ``approximated``): communication diagrams, drawn as lifeline objects with numbered
messages on their links, since PlantUML has no communication diagram.
"""

from __future__ import annotations

from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.phase7.notations.base import (
    Renderer, alias, children, fragment, label_lines, multiplicity, quote, register, segments,
)
from task2view.phase7.uml_rules import frame_heading, stereotype

_CONTAINER = {"layer": "package", "module": "package", "tier": "package", "system": "component",
              "node": "node", "execution_env": "node"}
_METACLASS = {"package": "Package", "component": "Component", "node": "Node", "rectangle": "Classifier"}
# (path kind) -> (PlantUML arrow, keyword shown on it). Dependencies are dashed arrows from client to supplier
# (7.7.4); generalization a solid line with a hollow triangle; realization dashed with a hollow triangle.
_PATHS = {"uses": ("..>", "use"), "allowed-to-use": ("..>", "use"), "request-reply": ("..>", ""),
          "reads": ("..>", ""), "writes": ("..>", ""), "publishes": ("..>", ""), "subscribes": ("..>", ""),
          "attachment": ("--", ""), "is-a": ("--|>", ""), "generalization": ("--|>", ""),
          "implements": ("..|>", ""), "association": ("-->", ""), "composition": ("*--", ""),
          "include": ("..>", "include"), "extend": ("..>", "extend"), "deploys": ("..>", "deploy"),
          "allocated-to": ("..>", "deploy"), "communicates": ("--", ""), "transition": ("-->", ""),
          "crosscuts": ("..>", ""), "traces-to": ("..>", "trace"), "assigned-to": ("..>", "")}


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
        }.get(kind, self._structure)(view)
        frame = frame_heading(kind, quote(view.title))
        source = "\n".join(["@startuml", f"mainframe {frame}", "skinparam shadowing false", *body, "@enduml"])
        return self.result(view, source)

    # ---------------------------------------------------------- structure
    def _structure(self, view: ArchitectureView) -> list[str]:
        tree = children(view)
        lines: list[str] = ["allowmixing", "hide empty members", "hide circle"]  # classes next to components
        if view.model_kind == "uml-deployment":
            lines.append("left to right direction")
        else:
            lines.append("top to bottom direction")

        def emit(element, indent: str):
            nested = tree.get(element.id, [])
            if element.group or nested:
                keyword = _CONTAINER.get(element.kind, "package" if element.group else "node")
                if element.kind == "system" and view.model_kind == "uml-usecase":
                    keyword = "rectangle"  # the subject of the use cases (18.1.4)
                stereo = stereotype(element.kind, _METACLASS.get(keyword, "Package")) if element.group else ""
                lines.append(f'{indent}{keyword} "{quote(element.name)}" as {alias(element.id)}{stereo} {{')
                for child in nested:
                    emit(child, indent + "  ")
                lines.append(f"{indent}}}")
            else:
                lines.extend(f"{indent}{line}" for line in self._leaf(view, element))

        for top in tree.get(None, []):
            emit(top, "")
        for rel in view.relations:
            arrow, keyword = _PATHS.get(rel.kind, ("..>", ""))
            src_m, tgt_m = multiplicity(rel)
            left = f'{alias(rel.source)}{" " + chr(34) + src_m + chr(34) if src_m else ""}'
            right = f'{chr(34) + tgt_m + chr(34) + " " if tgt_m else ""}{alias(rel.target)}'
            text = " ".join(x for x in (f"<<{keyword}>>" if keyword else "", quote(rel.label) if rel.label else "") if x)
            lines.append(f"{left} {arrow} {right}{' : ' + text if text else ''}")
        return lines

    def _leaf(self, view: ArchitectureView, e) -> list[str]:
        a = alias(e.id)
        deployment = view.model_kind == "uml-deployment"
        if e.kind in {"entity", "class", "interface", "enum"}:
            keyword = {"interface": "interface", "enum": "enum"}.get(e.kind, "class")
            out = [f'{keyword} "{quote(e.name)}" as {a}{stereotype(e.stereotype, "Class")} {{']
            for attr in e.attributes:
                tags = (" {id}" if attr.key else "") + (" {FK}" if attr.foreign_key else "")
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
        if e.kind == "datastore":  # a database server is an execution environment (19.4.4); elsewhere a component
            if deployment:
                return [f'node "{quote(e.name)}" as {a} <<executionEnvironment>>']
            return [f'component "{quote(e.name)}" as {a} <<database>>']
        if e.kind in {"artifact", "file"}:
            return [f'artifact "{quote(e.name)}" as {a}']
        if e.kind in {"node", "execution_env"}:
            keyword = " <<executionEnvironment>>" if e.kind == "execution_env" else stereotype(e.stereotype, "Node")
            return [f'node "{quote(e.name)}" as {a}{keyword}']
        if e.kind == "external_system":
            return [f'component "{quote(e.name)}" as {a} <<external>>']
        if e.kind == "system":
            return [f'component "{quote(e.name)}" as {a} <<Subsystem>>']
        stereo = stereotype(e.stereotype, "Component")
        lines = label_lines(e)
        if len(lines) == 1:
            return [f'component "{quote(e.name)}" as {a}{stereo}']
        text = "\\n".join(quote(l) for l in lines[:1]) + "\\n--\\n" + "\\n".join(quote(l) for l in lines[1:])
        return [f'component "{text}" as {a}{stereo}']

    # ---------------------------------------------------------- behaviour
    def _sequence(self, view: ArchitectureView) -> list[str]:
        lines = []
        for e in view.content_elements():
            keyword = "actor" if e.kind == "actor" else "participant"  # a lifeline (17.3.4)
            lines.append(f'{keyword} "{quote(e.name)}" as {alias(e.id)}')
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
        lines = ["allowmixing"]  # an actor next to the lifeline objects
        lines += [f'object "{quote(e.name)}" as {alias(e.id)}' if e.kind != "actor" else f'actor "{quote(e.name)}" as {alias(e.id)}'
                  for e in view.content_elements()]  # lifelines (17.9.1)
        for st in sorted(view.interactions, key=lambda s: s.order):
            guard = f" [{quote(fragment(view, st.fragment).guard)}]" if st.fragment and fragment(view, st.fragment) else ""
            lines.append(f"{alias(st.source)} -- {alias(st.target)} : {st.order}{guard}: {quote(st.message)} >")
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
