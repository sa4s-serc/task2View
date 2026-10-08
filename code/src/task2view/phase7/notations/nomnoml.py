"""nomnoml renderer: native for package, class (data model) and use case diagrams.

nomnoml has no identifiers: a classifier *is* its name, so element names are the identifiers (aliases from
``base.alias`` cannot be used) and characters nomnoml reserves (``[ ] | ; #`` and ``-``/``<``/``>`` in edge
labels) are replaced by look-alikes. Edges can only join classifiers in the same compartment, so an edge
between elements in different containers is drawn between their outermost distinct containers at the lowest
common level, and labelled "<source name> → <target name>" so the real endpoints stay visible.

Native:
- uml-package: ``[<package> name| ...]`` with nested members; responsibilities as compartment lines.
- uml-class: class boxes ``[<class> Name|attr: Type {PK};...|responsibility;...]``; generalization ``-:>``,
  implementation ``--:>``, composition ``+->``, aggregation ``o->``, multiplicities as edge-end labels.
- uml-usecase: ``[<frame>]`` system boundary holding ``[<usecase>]``s, ``[<actor>]``s outside, ``«include»`` /
  ``«extend»`` labels on dashed ``-->`` edges.

Approximations (flagged ``approximated``):
- uml-component / uml-deployment: ``[<package>]`` / ``[<frame>]`` containers (nodes as ``<frame>``), boxes with
  responsibilities in a second compartment, ``[<database>]`` datastores, ``[<actor>]`` actors.
- uml-sequence / uml-communication: participants as boxes (``[<actor>]`` for actors) with one numbered edge per
  message ("<order>. message"; a fragment step reads "<order>. <kind> [<guard>] message"); returns are dashed.
  The sequence variant lays out left to right.
- uml-activity: ``[<start>]`` → numbered ``[<state>]`` actions "<order>. <performer>: <message>" →
  ``[<end>]``, a ``[<choice>]`` per fragment guard (yes / no branches; loops get a back edge); nomnoml has no
  swimlanes, so the performer is named in the action and a ``[<note> participants|...]`` lists every lane.
- uml-state: ``[<start>]`` initial pseudo-state, ``[<state>]`` states (``<package>`` for composite states).
- table: the native-looking ``[<table> title| c | c || c | c ]`` classifier, rows from ``table_rows``.
"""

from __future__ import annotations

from task2view.contracts.views import ArchitectureView, RenderResult, ViewElement
from task2view.phase7.notations.base import (
    Renderer, children, fragment, label_lines, multiplicity, quote, register, segments, table_rows,
)
from task2view.phase7.notations.mermaid import activity_flow

_ARROWS = {"is-a": "-:>", "generalization": "-:>", "implements": "--:>", "composition": "+->",
           "aggregation": "o->", "association": "->", "include": "-->", "extend": "-->", "allowed-to-use": "-->",
           "deploys": "-->", "crosscuts": "-->", "traces-to": "-->", "assigned-to": "-->", "allocated-to": "-->",
           "attachment": "-", "communicates": "-", "return": "-->"}


def t(value: str) -> str:
    """Text inside a classifier: replace nomnoml's reserved characters."""
    return (quote(value).replace("[", "(").replace("]", ")").replace("|", "/").replace(";", ",")
            .replace("#", "No."))


def lab(value: str) -> str:
    """Edge-end label: additionally keep arrow characters out."""
    return t(value).replace("-", "‐").replace("<", "‹").replace(">", "›")


def _tag(e) -> str:
    return {"actor": "actor", "use_case": "usecase", "datastore": "database", "state": "state",
            "entity": "class", "class": "class", "interface": "abstract", "enum": "class",
            "artifact": "reference", "file": "reference", "external_system": "reference",
            "node": "frame", "execution_env": "frame", "system": "frame", "start": "start"}.get(e.kind, "")


def ref(e) -> str:
    """A reference to an already declared classifier (same tag, so nomnoml merges it with the declaration)."""
    tag = _tag(e)
    return f"[<{tag}> {t(e.name)}]" if tag else f"[{t(e.name)}]"


def declare(e) -> str:
    tag = f"<{_tag(e)}> " if _tag(e) else ""
    name = t(e.name)
    if e.kind in {"actor", "use_case", "datastore", "state", "start"}:
        return f"[{tag}{name}]"
    parts = [name]
    attrs = [f"{a.name}{': ' + a.type if a.type else ''}{' {PK}' if a.key else ''}{' {FK}' if a.foreign_key else ''}"
             for a in e.attributes]
    resp = [f"- {r}" for r in e.responsibilities]
    if e.stereotype:
        resp = [f"«{e.stereotype}»", *resp]
    if attrs:
        parts.append(";".join(t(a) for a in attrs))
    if resp:
        parts.append(";".join(t(r) for r in resp))
    return f"[{tag}{'|'.join(parts)}]"


@register
class NomnomlRenderer(Renderer):
    language = "nomnoml"
    extension = "noml"

    def render(self, view: ArchitectureView) -> RenderResult:
        body = {
            "uml-sequence": self._messages,
            "uml-communication": self._messages,
            "uml-activity": self._activity,
            "uml-state": self._state,
            "table": self._table,
        }.get(view.model_kind, self._structure)(view)
        title = t(view.title).replace(":", " ")
        direction = "right" if view.model_kind in {"uml-sequence", "uml-deployment", "uml-usecase"} else "down"
        source = "\n".join([f"#title: {title}", f"#direction: {direction}", *body])
        return self.result(view, source)

    # ---------------------------------------------------------- structure with containment
    def _structure(self, view: ArchitectureView, extra_edges=None, head=None) -> list[str]:
        """Containers as nested classifiers; each edge is placed in the compartment of the lowest common
        container of its endpoints. extra_edges: [(source id, target id, arrow, source label, target label)]."""
        tree = children(view)
        ids = {e.id: e for e in view.elements}

        def chain(eid):  # [outermost ... element]
            out, cur, seen = [], ids.get(eid), set()
            while cur is not None and cur.id not in seen:
                seen.add(cur.id)
                out.append(cur)
                cur = ids.get(cur.parent) if cur.parent else None
            return list(reversed(out))

        edges = list(extra_edges or [])
        for rel in view.relations:
            src_m, tgt_m = multiplicity(rel)
            label = f"«{rel.kind}»" if rel.kind in {"include", "extend"} else (rel.label or "")
            src, tgt = (rel.target, rel.source) if rel.kind == "subscribes" else (rel.source, rel.target)
            edges.append((src, tgt, _ARROWS.get(rel.kind, "->"), src_m, " ".join(x for x in (tgt_m, label) if x)))

        placed: dict[str | None, list[str]] = {}
        for src, tgt, arrow, src_label, tgt_label in edges:
            a, b = chain(src), chain(tgt)
            if not a or not b:
                continue
            k = 0
            while k < min(len(a), len(b)) - 1 and a[k].id == b[k].id:
                k += 1
            scope = a[k - 1].id if k > 0 else None
            ea, eb = a[k], b[k]
            if (ea.id, eb.id) != (src, tgt):
                real = f"{ids[src].name} → {ids[tgt].name}"
                tgt_label = f"{real}{': ' + tgt_label if tgt_label else ''}"
            line = f"{self._ref(ea, tree)} {lab(src_label)} {arrow} {lab(tgt_label)} {self._ref(eb, tree)}"
            placed.setdefault(scope, []).append(" ".join(line.split()))

        lines: list[str] = list(head or [])

        def emit(e, indent: str):
            nested = tree.get(e.id, [])
            if e.group or nested:
                tag = "frame" if e.kind in {"system", "node", "execution_env"} else "package"
                lines.append(f"{indent}[<{tag}> {t(e.name)}|")
                for child in nested:
                    emit(child, indent + "  ")
                lines.extend(f"{indent}  {edge}" for edge in placed.get(e.id, []))
                lines.append(f"{indent}]")
            else:
                lines.append(indent + declare(e))

        for top in tree.get(None, []):
            emit(top, "")
        lines += placed.get(None, [])
        return lines

    def _ref(self, e, tree) -> str:
        if e.group or tree.get(e.id):
            tag = "frame" if e.kind in {"system", "node", "execution_env"} else "package"
            return f"[<{tag}> {t(e.name)}]"
        return ref(e)

    # ---------------------------------------------------------- behaviour
    def _messages(self, view: ArchitectureView) -> list[str]:
        edges = []
        for st in sorted(view.interactions, key=lambda x: x.order):
            frag = fragment(view, st.fragment)
            guard = f" {frag.kind} [{frag.guard}]" if frag else ""
            edges.append((st.source, st.target, "-->" if st.kind == "return" else "->", "",
                          f"{st.order}.{guard} {st.message}"))
        return self._structure(view.model_copy(update={"relations": []}), extra_edges=edges)

    def _activity(self, view: ArchitectureView) -> list[str]:
        nodes, edges = activity_flow(view)
        names = {e.id: e.name for e in view.elements}
        decl = {}
        for node_id, kind, label, lane in nodes:
            if kind == "start":
                decl[node_id] = "[<start> start]"
            elif kind == "end":
                decl[node_id] = "[<end> end]"
            elif kind == "decision":
                decl[node_id] = f"[<choice> {t(label)}]"
            else:
                decl[node_id] = f"[<state> {t(names.get(lane, lane) + ': ' + label)}]"
        lines = [f"[<note> participants|{';'.join(t(e.name) for e in view.content_elements())}]"]
        for src, tgt, label in edges:
            lines.append(" ".join(f"{decl[src]} -> {lab(label)} {decl[tgt]}".split()))
        return lines

    def _state(self, view: ArchitectureView) -> list[str]:
        content = view.content_elements()
        targets = {r.target for r in view.relations}
        initial = [e for e in content if e.id not in targets][:1] or content[:1]
        rels = [r.model_copy(update={"kind": "transition"}) for r in view.relations]
        # the initial pseudo-state sits next to the initial state, so the edge stays in one compartment
        starts = [ViewElement(id=f"initial:{e.id}", kind="start", name="initial", parent=e.parent) for e in initial]
        edges = [(f"initial:{e.id}", e.id, "->", "", "") for e in initial]
        return self._structure(view.model_copy(update={"relations": rels, "elements": view.elements + starts}),
                               extra_edges=edges)

    def _table(self, view: ArchitectureView) -> list[str]:
        rows = table_rows(view)
        body = " || ".join(" | ".join(t(c) or " " for c in row) for row in rows)
        return [f"[<table> {t(view.title)}| {body} ]"]
