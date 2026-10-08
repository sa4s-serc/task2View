"""C4-PlantUML renderer: C4 macros where C4 has a diagram, plain PlantUML (which C4-PlantUML is) elsewhere.

Every include is a PlantUML stdlib include (``!include <C4/...>``), so the source compiles offline.

Native constructs:
- uml-component, uml-package: C4_Component. Groups / nesting -> ``Boundary`` (System_Boundary for systems),
  components -> ``Component`` (datastores ``ComponentDb``, queues ``ComponentQueue``, actors ``Person``,
  external systems ``System_Ext``); responsibilities and attributes form the element description.
  Generalization / implements use plain PlantUML ``--|>`` / ``..|>`` arrows; association multiplicity is
  appended to the ``Rel`` label as ``[src..tgt]``.
- uml-sequence: C4_Sequence (participants as Person/Component, ``Rel`` messages prefixed with their order,
  returns as dashed plain arrows, plain ``alt/opt/loop ... end`` fragments, ``Boundary``/``Boundary_End`` groups).
- uml-communication: C4_Dynamic with ``RelIndex(order, ...)``; the fragment guard prefixes the label.
- uml-deployment: C4_Deployment (``Deployment_Node`` nesting, artifacts as ``Container``, datastores ``ContainerDb``).
- uml-usecase: C4_Context ``Person`` actors and ``System_Boundary`` around plain PlantUML ``usecase`` elements;
  include/extend as ``..>`` with ``<<include>>`` / ``<<extend>>``.
- uml-class, uml-activity, uml-state: plain PlantUML class / activity / state diagrams (same as the PlantUML renderer).

Approximations (flagged ``approximated``):
- table: a creole table in a legend (as in the PlantUML renderer).
"""

from __future__ import annotations

from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.phase7.notations.base import (
    alias, children, fragment, label_lines, multiplicity, quote, register, segments,
)
from task2view.phase7.notations.plantuml import PlantUMLRenderer

_PLAIN_ARROWS = {"is-a": "--|>", "generalization": "--|>", "implements": "..|>"}


def _descr(element) -> str:
    return "\\n".join(quote(line) for line in label_lines(element)[1:])


@register
class C4PlantUMLRenderer(PlantUMLRenderer):
    language = "c4plantuml"
    extension = "puml"

    def render(self, view: ArchitectureView) -> RenderResult:
        kind = view.model_kind
        include, body = {
            "uml-component": ("C4_Component", self._c4_structure),
            "uml-package": ("C4_Component", self._c4_structure),
            "uml-deployment": ("C4_Deployment", self._c4_structure),
            "uml-sequence": ("C4_Sequence", self._c4_sequence),
            "uml-communication": ("C4_Dynamic", self._c4_dynamic),
            "uml-usecase": ("C4_Context", self._c4_usecase),
            "uml-class": (None, self._structure),
            "uml-activity": (None, self._activity),
            "uml-state": (None, self._state),
            "table": (None, self._table),
        }.get(kind, ("C4_Component", self._c4_structure))
        head = ["@startuml"]
        if include:
            head.append(f"!include <C4/{include}>")
        source = "\n".join([*head, f"title {quote(view.title)}", *body(view), "@enduml"])
        return self.result(view, source)

    # ---------------------------------------------------------- C4 elements
    def _c4_leaf(self, view: ArchitectureView, e) -> str:
        a, name, techn, descr = alias(e.id), quote(e.name), quote(e.stereotype or e.kind), _descr(e)
        deployment = view.model_kind == "uml-deployment"
        if e.kind == "actor":
            return f'Person({a}, "{name}", "{descr}")'
        if e.kind == "external_system":
            return f'System_Ext({a}, "{name}", "{descr}")'
        if e.kind == "system":
            return f'System({a}, "{name}", "{descr}")'
        if e.kind == "use_case":
            return f'usecase "{name}" as {a}'
        if e.kind in {"node", "execution_env", "device"} and deployment:
            return f'Deployment_Node({a}, "{name}", "{techn}")'
        prefix = "Container" if deployment else "Component"
        suffix = {"datastore": "Db", "database": "Db", "queue": "Queue", "topic": "Queue"}.get(e.kind, "")
        return f'{prefix}{suffix}({a}, "{name}", "{techn}", "{descr}")'

    def _c4_boundary(self, view: ArchitectureView, e) -> str:
        a, name = alias(e.id), quote(e.name)
        if view.model_kind == "uml-deployment":
            return f'Deployment_Node({a}, "{name}", "{quote(e.stereotype or e.kind)}")'
        if e.kind == "system":
            return f'System_Boundary({a}, "{name}")'
        return f'Boundary({a}, "{name}", "{quote(e.kind)}")'

    def _c4_tree(self, view: ArchitectureView, leaf=None) -> list[str]:
        tree, lines = children(view), []
        leaf = leaf or self._c4_leaf

        def emit(element, indent: str):
            nested = tree.get(element.id, [])
            if element.group or nested:
                lines.append(f"{indent}{self._c4_boundary(view, element)} {{")
                for child in nested:
                    emit(child, indent + "  ")
                lines.append(f"{indent}}}")
            else:
                lines.append(indent + leaf(view, element))

        for top in tree.get(None, []):
            emit(top, "")
        return lines

    def _c4_relations(self, view: ArchitectureView) -> list[str]:
        lines = []
        for rel in view.relations:
            src, tgt = alias(rel.source), alias(rel.target)
            if rel.kind in _PLAIN_ARROWS:
                label = f" : {quote(rel.label)}" if rel.label else ""
                lines.append(f"{src} {_PLAIN_ARROWS[rel.kind]} {tgt}{label}")
                continue
            if rel.kind in {"include", "extend"}:
                lines.append(f"{src} ..> {tgt} : <<{rel.kind}>>")
                continue
            label = quote(rel.label or "")
            src_m, tgt_m = multiplicity(rel)
            if src_m or tgt_m:
                label = f"{label} [{src_m}..{tgt_m}]".strip()
            lines.append(f'Rel({src}, {tgt}, "{label}")')
        return lines

    # ---------------------------------------------------------- kinds
    def _c4_structure(self, view: ArchitectureView) -> list[str]:
        layout = "LAYOUT_LEFT_RIGHT()" if view.model_kind == "uml-deployment" else "LAYOUT_TOP_DOWN()"
        return [layout, *self._c4_tree(view), *self._c4_relations(view)]

    def _c4_usecase(self, view: ArchitectureView) -> list[str]:
        return ["left to right direction", *self._c4_tree(view), *self._c4_relations(view)]

    def _participant(self, view: ArchitectureView, e) -> str:
        a, name, descr = alias(e.id), quote(e.name), _descr(e)
        if e.kind == "actor":
            return f'Person({a}, "{name}", "{descr}")'
        if e.kind in {"datastore", "database"}:
            return f'ComponentDb({a}, "{name}", "{quote(e.stereotype or e.kind)}", "{descr}")'
        if e.kind == "external_system":
            return f'System_Ext({a}, "{name}", "{descr}")'
        return f'Component({a}, "{name}", "{quote(e.stereotype or e.kind)}", "{descr}")'

    def _c4_sequence(self, view: ArchitectureView) -> list[str]:
        tree, lines = children(view), []

        def emit(element):
            nested = tree.get(element.id, [])
            if element.group or nested:
                lines.append(f'Boundary({alias(element.id)}, "{quote(element.name)}")')
                for child in nested:
                    emit(child)
                lines.append("Boundary_End()")
            else:
                lines.append(self._participant(view, element))

        for top in tree.get(None, []):
            emit(top)
        for frag_id, steps in segments(view):
            frag = fragment(view, frag_id)
            if frag:
                lines.append(f"{frag.kind} {quote(frag.guard)}")
            for st in steps:
                text = f"{st.order}. {quote(st.message)}"
                if st.kind == "return":
                    lines.append(f"{alias(st.source)} --> {alias(st.target)} : {text}")
                else:
                    lines.append(f'Rel({alias(st.source)}, {alias(st.target)}, "{text}")')
            if frag:
                lines.append("end")
        return lines

    def _c4_dynamic(self, view: ArchitectureView) -> list[str]:
        lines = ["LAYOUT_TOP_DOWN()", *self._c4_tree(view, self._participant)]
        for st in sorted(view.interactions, key=lambda s: s.order):
            frag = fragment(view, st.fragment) if st.fragment else None
            guard = f"[{quote(frag.guard)}] " if frag else ""
            ret = "return " if st.kind == "return" else ""
            lines.append(f'RelIndex({st.order}, {alias(st.source)}, {alias(st.target)}, "{guard}{ret}{quote(st.message)}")')
        return lines
