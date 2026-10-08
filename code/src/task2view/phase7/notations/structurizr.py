"""Structurizr DSL renderer: one workspace per view (model + views + styles).

Every view gets a software system named after the view title; architecture elements live in one container
inside it, so they can be shown in a component (or dynamic) view. Actors become top-level ``person``
elements and external systems top-level ``softwareSystem`` elements. Nesting (layers, modules, system
boundaries, any element with children) is expressed with nested ``group`` blocks (``structurizr.groupSeparator``
is set to ``/``). Responsibilities and attributes form the element description. Each element is tagged with its
kind (and stereotype) and the ``styles`` block gives kinds their shape (datastore -> Cylinder, use_case ->
Ellipse, state -> RoundedBox, queue -> Pipe, person -> Person).

Native constructs:
- uml-component, uml-package: component view of the container.
- uml-communication: dynamic view (Structurizr numbers the steps); the fragment guard prefixes the step text.
- uml-deployment: ``deploymentEnvironment`` with nested ``deploymentNode`` and ``containerInstance``;
  deployable leaves are containers of the software system; leaves outside any node go into a
  ``(unallocated)`` node; relations touching nodes are declared between deployment elements.

Approximations (flagged ``approximated``):
- uml-sequence, uml-activity: the same dynamic view as communication (order kept by Structurizr's numbering,
  fragment as ``[<kind> <guard>]`` prefix; returns prefixed ``return``).
- uml-class: classes/entities as components whose description lists attributes; relationships labelled with
  the association name and ``[src..tgt]`` multiplicity; generalization tagged ``Generalization`` (styled solid,
  labelled ``«generalization»``).
- uml-state: states as components (tag ``state``, rounded) and transitions as labelled relationships; the initial
  state carries the extra tag ``initial``.
- uml-usecase: actors as persons, use cases as components (tag ``use_case``, ellipse) in a group named after the
  system; include/extend relationships labelled ``«include»`` / ``«extend»`` and dashed.
- table: one component per row with the row cells as element ``properties`` and the details as the description.
Relations whose endpoint is a group (no Structurizr element) are dropped and counted in the result note.
"""

from __future__ import annotations

from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.phase7.notations.base import (
    Renderer, alias, children, fragment, label_lines, multiplicity, quote, register, table_rows,
)

_SYSTEM, _CONTAINER, _UNALLOCATED = "sys", "app", "unallocated"
_DEPLOYABLE_NODES = {"node", "execution_env", "device", "tier"}
_STYLED = {"Generalization": ["dashed false"], "Include": ["dashed true"]}


def _q(text: str | None) -> str:
    return '"' + quote(text or "") + '"'


@register
class StructurizrRenderer(Renderer):
    language = "structurizr"
    extension = "dsl"

    def render(self, view: ArchitectureView) -> RenderResult:
        self._view = view
        self._ids: set[str] = set()
        self._dropped = 0
        deployment = view.model_kind == "uml-deployment"
        model = self._deployment_model() if deployment else self._model()
        views = self._views()
        lines = [f"workspace {_q(view.title)} {_q(view.purpose)} {{", "  model {",
                 '    properties {', '      "structurizr.groupSeparator" "/"', "    }",
                 *("    " + l for l in model), "  }", "  views {", *("    " + l for l in views), "  }", "}"]
        note = f"dropped {self._dropped} relation(s) whose endpoint is a group" if self._dropped else ""
        return self.result(view, "\n".join(lines), note)

    # ---------------------------------------------------------- elements
    def _tags(self, e, *extra: str) -> str:
        tags = [e.kind, *([e.stereotype] if e.stereotype else []), *extra]
        return ",".join(quote(t) for t in tags)

    def _description(self, e) -> str:
        if self._view.model_kind == "table":
            row = next((r for r in table_rows(self._view)[1:] if r[0] == e.name), None)
            if row:
                return row[2]
        return "; ".join(line[2:] if line.startswith("- ") else line for line in label_lines(e)[1:])

    def _component(self, e, keyword: str = "component", extra_tags: tuple[str, ...] = ()) -> list[str]:
        a = alias(e.id)
        self._ids.add(a)
        head = (f"{a} = {keyword} {_q(e.name)} {_q(self._description(e))} {_q(e.stereotype or e.kind)} "
                f"{_q(self._tags(e, *extra_tags))}")
        if self._view.model_kind != "table":
            return [head]
        rows = table_rows(self._view)
        row = next((r for r in rows[1:] if r[0] == e.name), None)
        if not row:
            return [head]
        props = [f"{_q(k)} {_q(v)}" for k, v in zip(rows[0], row) if v]
        return [head + " {", "  properties {", *("    " + p for p in props), "  }", "}"]

    def _top_level(self, e) -> list[str] | None:
        """Elements that cannot live in a container."""
        a = alias(e.id)
        if e.kind == "actor":
            self._ids.add(a)
            return [f"{a} = person {_q(e.name)} {_q(self._description(e))} {_q(self._tags(e))}"]
        if e.kind in {"external_system", "system"} and not e.group:
            self._ids.add(a)
            return [f"{a} = softwareSystem {_q(e.name)} {_q(self._description(e))} {_q(self._tags(e))}"]
        return None

    def _model(self) -> list[str]:
        view, tree = self._view, children(self._view)
        top: list[str] = []
        initial = self._initial_state()

        def emit(element, indent: str) -> list[str]:
            hoisted = self._top_level(element)
            if hoisted:
                top.extend(hoisted)
                for child in tree.get(element.id, []):
                    inner.extend(emit(child, indent))
                return []
            nested = tree.get(element.id, [])
            out: list[str] = []
            if not element.group:
                extra = ("initial",) if element.id == initial else ()
                out += [indent + l for l in self._component(element, extra_tags=extra)]
            if element.group or nested:
                out.append(f"{indent}group {_q(element.name)} {{")
                for child in nested:
                    out += emit(child, indent + "  ")
                out.append(f"{indent}}}")
            return out

        inner: list[str] = []
        for element in tree.get(None, []):
            inner.extend(emit(element, "    "))
        lines = [*top, f"{_SYSTEM} = softwareSystem {_q(view.title)} {_q(view.purpose)} {{",
                 f"  {_CONTAINER} = container {_q(view.viewpoint_name)} {_q(view.scenario or view.purpose)} {{",
                 *inner, "  }", "}"]
        return lines + self._relationships(lambda element_id: alias(element_id))

    def _initial_state(self) -> str | None:
        if self._view.model_kind != "uml-state":
            return None
        targets = {r.target for r in self._view.relations}
        states = self._view.content_elements()
        first = [e for e in states if e.id not in targets][:1] or states[:1]
        return first[0].id if first else None

    def _relationships(self, ref) -> list[str]:
        """Model relationships: declared relations, plus one per directed pair used by interactions."""
        view, lines, seen = self._view, [], set()
        for rel in view.relations:
            src, tgt = ref(rel.source), ref(rel.target)
            if src not in self._ids or tgt not in self._ids:
                self._dropped += 1
                continue
            label, tags = rel.label or "", rel.kind
            if rel.kind in {"is-a", "generalization", "implements"}:
                label, tags = label or f"«{rel.kind}»", f"{rel.kind},Generalization"
            elif rel.kind in {"include", "extend"}:
                label, tags = f"«{rel.kind}»", f"{rel.kind},Include"
            src_m, tgt_m = multiplicity(rel)
            if src_m or tgt_m:
                label = f"{label} [{src_m}..{tgt_m}]".strip()
            key = (src, tgt, label)
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"{src} -> {tgt} {_q(label)} {_q(rel.kind)} {_q(tags)}")
        pairs = {(ref(s.source), ref(s.target)) for s in view.interactions}
        for src, tgt in sorted(pairs):
            if src in self._ids and tgt in self._ids and not any(k[:2] == (src, tgt) for k in seen):
                seen.add((src, tgt, ""))
                lines.append(f'{src} -> {tgt} "interacts" "" "interaction"')
        return lines

    # ---------------------------------------------------------- deployment
    def _deployment_model(self) -> list[str]:
        view, tree = self._view, children(self._view)
        containers: list[str] = []
        top: list[str] = []
        instance: dict[str, str] = {}
        nodes: set[str] = set()

        def is_node(e) -> bool:
            return e.group or bool(tree.get(e.id)) or e.kind in _DEPLOYABLE_NODES

        def emit(element, indent: str) -> list[str]:
            a = alias(element.id)
            if is_node(element):
                self._ids.add(a)
                nodes.add(a)
                out = [f"{indent}{a} = deploymentNode {_q(element.name)} {_q(self._description(element))} "
                       f"{_q(element.stereotype or element.kind)} {{"]
                for child in tree.get(element.id, []):
                    out += emit(child, indent + "  ")
                out.append(f"{indent}}}")
                return out
            hoisted = self._top_level(element)
            if hoisted:
                top.extend(hoisted)
                return []
            containers.extend("  " + l for l in self._component(element, keyword="container"))
            instance[a] = f"i_{a}"
            return [f"{indent}i_{a} = containerInstance {a}"]

        env: list[str] = []
        loose: list[str] = []
        for element in tree.get(None, []):
            out = emit(element, "  ")
            if out and out[0].strip().startswith("i_"):
                loose += ["  " + l for l in out]
            else:
                env += out
        if loose:
            env += [f'  {_UNALLOCATED} = deploymentNode "(unallocated)" "" "" {{', *loose, "  }"]

        model_rels, env_rels = [], []
        for rel in view.relations:
            src, tgt = alias(rel.source), alias(rel.target)
            if src not in self._ids or tgt not in self._ids:
                self._dropped += 1
                continue
            label = _q(rel.label)
            if src in nodes or tgt in nodes:
                env_rels.append(f"  {instance.get(src, src)} -> {instance.get(tgt, tgt)} {label} {_q(rel.kind)}")
            else:
                model_rels.append(f"{src} -> {tgt} {label} {_q(rel.kind)}")
        return [*top, f"{_SYSTEM} = softwareSystem {_q(view.title)} {_q(view.purpose)} {{", *containers, "}",
                *model_rels, 'deploymentEnvironment "Default" {', *env, *env_rels, "}"]

    # ---------------------------------------------------------- views
    def _views(self) -> list[str]:
        view, kind = self._view, self._view.model_kind
        key = "v_" + alias(view.id)[2:]
        if kind == "uml-deployment":
            body = [f'deployment * "Default" "{key}" {_q(view.title)} {{', "  include *", "  autolayout lr", "}"]
        elif kind in {"uml-sequence", "uml-communication", "uml-activity"}:
            body = [f"dynamic {_CONTAINER} {_q(key)} {_q(view.scenario or view.title)} {{"]
            for st in sorted(view.interactions, key=lambda s: s.order):
                src, tgt = alias(st.source), alias(st.target)
                if src not in self._ids or tgt not in self._ids:
                    continue
                frag = fragment(view, st.fragment) if st.fragment else None
                text = (f"[{frag.kind} {frag.guard}] " if frag else "") + ("return " if st.kind == "return" else "")
                body.append(f"  {src} -> {tgt} {_q(text + st.message)}")
            body += ["  autolayout lr", "}"]
        else:
            direction = "lr" if kind == "uml-usecase" else "tb"
            body = [f"component {_CONTAINER} {_q(key)} {_q(view.title)} {{", "  include *", f"  autolayout {direction}", "}"]
        styles = ["styles {",
                  '  element "Person" {', "    shape Person", "  }",
                  '  element "datastore" {', "    shape Cylinder", "  }",
                  '  element "queue" {', "    shape Pipe", "  }",
                  '  element "use_case" {', "    shape Ellipse", "  }",
                  '  element "state" {', "    shape RoundedBox", "  }"]
        for tag, props in _STYLED.items():
            styles += [f"  relationship {_q(tag)} {{", *("    " + p for p in props), "  }"]
        styles.append("}")
        return body + styles
