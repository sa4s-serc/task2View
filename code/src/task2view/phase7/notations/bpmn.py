"""BPMN 2.0 renderer: BPMN 2.0 XML (OMG namespaces) with a ``bpmndi`` diagram (shapes and edges with
bounds and waypoints) so modelling tools such as bpmn.io / Camunda Modeler can open it.

Native (``approximated`` false):
- uml-activity: a collaboration with one pool whose process has a lane per participant, a startEvent,
  one task per step (``<order>. message``) in the lane of its sender, an exclusiveGateway split
  (named ``kind [guard]``) and merge around each fragment (``[guard]`` and ``[else]`` flows; loops add
  a ``repeat`` flow back to the split), an endEvent, and sequenceFlows in step order. Participant
  responsibilities/attributes are the lanes' documentation.

Approximations (flagged ``approximated``):
- uml-component / uml-package / uml-class / uml-usecase / uml-deployment: a collaboration with one
  black-box pool (participant) per content element, stacked vertically. Responsibilities, attributes
  and ``«stereotype»``/``«kind»`` are a textAnnotation drawn inside the pool (linked by an association)
  and the participant's documentation. Nesting (groups, or elements with children) is a BPMN ``group``
  (with a categoryValue carrying the container name) enclosing the children's pools; a non-group parent
  also keeps its own pool. Relations are messageFlows named with the label, ``«include»``/``«extend»``,
  ``«generalization»``/``«is-a»``, and multiplicity as ``src .. label .. tgt``. Relations whose
  endpoints are not pools (e.g. a group) are listed in the result note.
- uml-sequence / uml-communication: vertical pools side by side (one per participant, like lifelines);
  each message is a horizontal messageFlow, top-to-bottom in order, named ``<order>. message``
  (``(return)`` suffix for replies; communication adds ``[guard]``). Fragments are groups named
  ``kind [guard]`` around their messages' rows. Self-messages (not allowed as messageFlows) are
  textAnnotations inside the pool.
- uml-state: a process with a task per state (name + responsibilities), a startEvent into the initial
  state (the first state without incoming transitions), sequenceFlows per transition named with the
  label, and an endEvent after each state without outgoing transitions.
- table: a process with one task per table row (cells joined by `` | ``) stacked vertically and the
  header row as a textAnnotation; no flows (a table has no order).
"""

from __future__ import annotations

from xml.sax.saxutils import escape, quoteattr

from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.phase7.notations.base import (
    Renderer, alias, children, fragment, label_lines, multiplicity, register, segments, table_rows,
)

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
}


def _attrs(**kw) -> str:
    return "".join(f" {k}={quoteattr(str(v))}" for k, v in kw.items() if v is not None)


class _Doc:
    """Collects semantic XML and DI shapes/edges; geometry is remembered for edge routing."""

    def __init__(self):
        self.categories: list[str] = []
        self.shapes: list[str] = []
        self.edges: list[str] = []
        self.bounds: dict[str, tuple[float, float, float, float]] = {}
        self._n = 0

    def new_id(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}_{self._n}"

    def shape(self, element_id: str, x: float, y: float, w: float, h: float, horizontal: bool | None = None):
        self.bounds[element_id] = (x, y, w, h)
        hz = None if horizontal is None else str(horizontal).lower()
        self.shapes.append(f'      <bpmndi:BPMNShape{_attrs(id=element_id + "_di", bpmnElement=element_id, isHorizontal=hz)}>'
                           f'<dc:Bounds{_attrs(x=_n(x), y=_n(y), width=_n(w), height=_n(h))} /></bpmndi:BPMNShape>')

    def edge(self, element_id: str, points: list[tuple[float, float]]):
        wps = "".join(f'<di:waypoint{_attrs(x=_n(px), y=_n(py))} />' for px, py in points)
        self.edges.append(f'      <bpmndi:BPMNEdge{_attrs(id=element_id + "_di", bpmnElement=element_id)}>{wps}</bpmndi:BPMNEdge>')

    def category(self, value: str) -> str:
        cat, val = self.new_id("Category"), self.new_id("CategoryValue")
        self.categories.append(f'  <bpmn:category{_attrs(id=cat)}><bpmn:categoryValue{_attrs(id=val, value=value)} />'
                               f'</bpmn:category>')
        return val


def _n(v: float) -> str:
    return str(int(round(v)))


def _doc(lines: list[str]) -> str:
    return f"<bpmn:documentation>{escape(chr(10).join(lines))}</bpmn:documentation>" if lines else ""


def _details(e) -> list[str]:
    """Everything but the name that belongs inside the element: stereotype/kind, responsibilities, attributes."""
    head = f"«{e.stereotype}»" if e.stereotype else f"«{e.kind}»"
    return [head, *label_lines(e)[1:]]


def _relation_name(rel) -> str:
    label = rel.label or ""
    if rel.kind in {"include", "extend", "is-a", "generalization", "implements"}:
        label = f"«{rel.kind}»" + (f" {label}" if label else "")
    src_m, tgt_m = multiplicity(rel)
    if src_m or tgt_m:
        label = f"{src_m} .. {label} .. {tgt_m}" if label else f"{src_m} .. {tgt_m}"
    return label


def _mid(b):
    x, y, w, h = b
    return x + w / 2, y + h / 2


@register
class BPMNRenderer(Renderer):
    language = "bpmn"
    extension = "bpmn"

    def render(self, view: ArchitectureView) -> RenderResult:
        doc = _Doc()
        build = {"uml-activity": self._activity, "uml-sequence": self._sequence,
                 "uml-communication": self._sequence, "uml-state": self._state,
                 "table": self._table}.get(view.model_kind, self._structure)
        roots, plane_ref, note = build(view, doc)
        source = "\n".join([
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<bpmn:definitions xmlns:bpmn="{NS["bpmn"]}" xmlns:bpmndi="{NS["bpmndi"]}" xmlns:dc="{NS["dc"]}" '
            f'xmlns:di="{NS["di"]}"{_attrs(id="Definitions_" + alias(view.id), targetNamespace="https://task2view/views", exporter="task2view", exporterVersion="2")}>',
            f"  <!-- {escape(view.title).replace('--', '- -')} ({view.model_kind}) -->",
            *doc.categories,
            *roots,
            f'  <bpmndi:BPMNDiagram{_attrs(id="Diagram_" + alias(view.id), name=view.title)}>',
            f'    <bpmndi:BPMNPlane{_attrs(id="Plane_" + alias(view.id), bpmnElement=plane_ref)}>',
            *doc.shapes,
            *doc.edges,
            "    </bpmndi:BPMNPlane>",
            "  </bpmndi:BPMNDiagram>",
            "</bpmn:definitions>",
        ])
        return self.result(view, source, note)

    # ---------------------------------------------------------- activity (native)
    def _activity(self, view: ArchitectureView, doc: _Doc):
        lanes = view.content_elements()
        lane_of = {e.id: alias(e.id) for e in lanes}
        default_lane = alias(lanes[0].id) if lanes else None
        nodes: list[tuple[str, str, str | None, str | None]] = []  # (id, tag, name, lane id)
        flows: list[tuple[str, str, str, str | None, bool]] = []  # (id, src, tgt, name, routed below)
        ordered = sorted(view.interactions, key=lambda s: s.order)
        first_lane = lane_of.get(ordered[0].source, default_lane) if ordered else default_lane
        nodes.append(("StartEvent_1", "startEvent", None, first_lane))
        prev = ["StartEvent_1"]

        def flow(src, tgt, name=None, below=False):
            flows.append((doc.new_id("Flow"), src, tgt, name, below))

        for frag_id, steps in segments(view):
            frag = fragment(view, frag_id)
            if frag:
                lane = lane_of.get(steps[0].source, first_lane)
                split, merge = doc.new_id("Gateway"), doc.new_id("Gateway")
                nodes.append((split, "exclusiveGateway", f"{frag.kind} [{frag.guard}]", lane))
                for p in prev:
                    flow(p, split)
                prev, first = [split], True
                for st in steps:
                    tid = f"Task_{st.order}"
                    nodes.append((tid, "task", f"{st.order}. {st.message}", lane_of.get(st.source, lane)))
                    for p in prev:
                        flow(p, tid, f"[{frag.guard}]" if first else None)
                    prev, first = [tid], False
                nodes.append((merge, "exclusiveGateway", None, lane))
                flow(prev[0], merge)
                flow(split, merge, "[else]" if frag.kind != "loop" else "[done]", below=True)
                if frag.kind == "loop":
                    flow(prev[0], split, "repeat", below=True)
                prev = [merge]
            else:
                for st in steps:
                    tid = f"Task_{st.order}"
                    nodes.append((tid, "task", f"{st.order}. {st.message}", lane_of.get(st.source, first_lane)))
                    for p in prev:
                        flow(p, tid)
                    prev = [tid]
        nodes.append(("EndEvent_1", "endEvent", None, nodes[-1][3]))
        for p in prev:
            flow(p, "EndEvent_1")

        incoming: dict[str, list[str]] = {}
        outgoing: dict[str, list[str]] = {}
        for fid, s, t, _, _ in flows:
            outgoing.setdefault(s, []).append(fid)
            incoming.setdefault(t, []).append(fid)

        proc = ['  <bpmn:process id="Process_1" isExecutable="false">']
        if lanes:
            proc.append('    <bpmn:laneSet id="LaneSet_1">')
            for e in lanes:
                refs = "".join(f"<bpmn:flowNodeRef>{nid}</bpmn:flowNodeRef>" for nid, _, _, ln in nodes if ln == alias(e.id))
                proc.append(f'      <bpmn:lane{_attrs(id=alias(e.id), name=e.name)}>{_doc(_details(e))}{refs}</bpmn:lane>')
            proc.append("    </bpmn:laneSet>")
        for nid, tag, name, _ in nodes:
            inner = "".join(f"<bpmn:incoming>{f}</bpmn:incoming>" for f in incoming.get(nid, []))
            inner += "".join(f"<bpmn:outgoing>{f}</bpmn:outgoing>" for f in outgoing.get(nid, []))
            proc.append(f"    <bpmn:{tag}{_attrs(id=nid, name=name)}>{inner}</bpmn:{tag}>")
        for fid, s, t, name, _ in flows:
            proc.append(f"    <bpmn:sequenceFlow{_attrs(id=fid, name=name, sourceRef=s, targetRef=t)} />")
        proc.append("  </bpmn:process>")
        collab = ['  <bpmn:collaboration id="Collaboration_1">',
                  f'    <bpmn:participant{_attrs(id="Participant_1", name=view.title, processRef="Process_1")} />',
                  "  </bpmn:collaboration>"]

        # DI: pool with horizontal lanes; nodes advance left to right
        lane_h, col_w, x0, y0 = 140.0, 160.0, 160.0, 80.0
        lane_ids = [alias(e.id) for e in lanes] or [None]
        width = 120 + col_w * len(nodes) + 60
        doc.shape("Participant_1", x0, y0, width, lane_h * len(lane_ids), horizontal=True)
        lane_y = {}
        for i, lid in enumerate(lane_ids):
            lane_y[lid] = y0 + i * lane_h
            if lid:
                doc.shape(lid, x0 + 30, y0 + i * lane_h, width - 30, lane_h, horizontal=True)
        sizes = {"task": (110, 70), "exclusiveGateway": (50, 50), "startEvent": (36, 36), "endEvent": (36, 36)}
        for i, (nid, tag, _, lid) in enumerate(nodes):
            w, h = sizes[tag]
            cx, cy = x0 + 110 + i * col_w, lane_y.get(lid, y0) + lane_h / 2
            doc.shape(nid, cx - w / 2, cy - h / 2, w, h)
        for fid, s, t, _, below in flows:
            doc.edge(fid, self._route(doc.bounds[s], doc.bounds[t], below))
        return collab + proc, "Collaboration_1", ""

    @staticmethod
    def _route(a, b, below: bool = False) -> list[tuple[float, float]]:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        if below or bx <= ax:
            low = max(ay + ah, by + bh) + 25
            return [(ax + aw / 2, ay + ah), (ax + aw / 2, low), (bx + bw / 2, low), (bx + bw / 2, by + bh)]
        start, end = (ax + aw, ay + ah / 2), (bx, by + bh / 2)
        if abs(start[1] - end[1]) < 1:
            return [start, end]
        mx = (start[0] + end[0]) / 2
        return [start, (mx, start[1]), (mx, end[1]), end]

    # ---------------------------------------------------------- structure (collaboration of pools)
    def _structure(self, view: ArchitectureView, doc: _Doc):
        tree = children(view)
        participants, artifacts, flows = [], [], []
        pool_ids: dict[str, str] = {}
        x_base, width, gap = 160.0, 640.0, 40.0
        state = {"y": 80.0, "right": x_base + width}

        def pool(e, depth: int):
            pid = alias(e.id)
            pool_ids[e.id] = pid
            details = _details(e)
            participants.append(f'    <bpmn:participant{_attrs(id=pid, name=e.name)}>{_doc(details)}</bpmn:participant>')
            x, w = x_base + depth * 30, max(320.0, width - depth * 60)
            h = max(80.0, 30 + 20 * len(details))
            doc.shape(pid, x, state["y"], w, h, horizontal=True)
            ann, assoc = doc.new_id("TextAnnotation"), doc.new_id("Association")
            artifacts.append(f'    <bpmn:textAnnotation{_attrs(id=ann)}><bpmn:text>{escape(chr(10).join(details))}'
                             f'</bpmn:text></bpmn:textAnnotation>')
            artifacts.append(f'    <bpmn:association{_attrs(id=assoc, sourceRef=pid, targetRef=ann)} />')
            doc.shape(ann, x + 60, state["y"] + 10, w - 80, h - 20)
            doc.edge(assoc, [(x + 30, state["y"] + h / 2), (x + 60, state["y"] + h / 2)])
            state["y"] += h + gap

        def emit(e, depth: int):
            nested = tree.get(e.id, [])
            if not nested:
                pool(e, depth)
                return
            top = state["y"]
            state["y"] += 30  # room for the group's caption
            if not e.group:
                pool(e, depth + 1)
            for c in nested:
                emit(c, depth + 1)
            gid = doc.new_id("Group")
            val = doc.category(f"«{e.kind}» {e.name}" if e.group else e.name)
            artifacts.append(f'    <bpmn:group{_attrs(id=gid, categoryValueRef=val)}>{_doc(_details(e))}</bpmn:group>')
            x = x_base + depth * 30 + 10
            doc.shape(gid, x, top, max(320.0, width - depth * 60) - 20, state["y"] - top - gap + 15)
            state["y"] += 15

        for e in tree.get(None, []):
            emit(e, 0)

        skipped = []
        for i, rel in enumerate(view.relations):
            src, tgt = pool_ids.get(rel.source), pool_ids.get(rel.target)
            if not src or not tgt or src == tgt:
                skipped.append(rel.id)
                continue
            fid = doc.new_id("MessageFlow")
            flows.append(f'    <bpmn:messageFlow{_attrs(id=fid, name=_relation_name(rel) or None, sourceRef=src, targetRef=tgt)} />')
            sx, sy, sw, sh = doc.bounds[src]
            tx, ty, tw, th = doc.bounds[tgt]
            lane_x = state["right"] + 30 + 25 * i
            doc.edge(fid, [(sx + sw, sy + sh / 2 + 10), (lane_x, sy + sh / 2 + 10),
                           (lane_x, ty + th / 2 - 10), (tx + tw, ty + th / 2 - 10)])
        collab = ['  <bpmn:collaboration id="Collaboration_1">', *participants, *flows, *artifacts,
                  "  </bpmn:collaboration>"]
        note = f"relations not drawn (endpoint is not a pool, or a self-relation): {', '.join(skipped)}" if skipped else ""
        return collab, "Collaboration_1", note

    # ---------------------------------------------------------- sequence / communication
    def _sequence(self, view: ArchitectureView, doc: _Doc):
        parts = view.content_elements()
        col = {p.id: i for i, p in enumerate(parts)}
        communication = view.model_kind == "uml-communication"
        col_w, pool_w, x0, y0, row, head = 240.0, 200.0, 160.0, 80.0, 60.0, 110.0
        rows: list[tuple[str, object]] = []
        for frag_id, steps in segments(view):
            frag = fragment(view, frag_id)
            if frag:
                rows.append(("frag", frag))
            rows += [("step", s) for s in steps]
        height = head + row * (len(rows) + 1)
        participants, flows, artifacts = [], [], []
        for p in parts:
            pid, details = alias(p.id), _details(p)
            participants.append(f'    <bpmn:participant{_attrs(id=pid, name=p.name)}>{_doc(details)}</bpmn:participant>')
            x = x0 + col[p.id] * col_w
            doc.shape(pid, x, y0, pool_w, height, horizontal=False)
            ann, assoc = doc.new_id("TextAnnotation"), doc.new_id("Association")
            artifacts.append(f'    <bpmn:textAnnotation{_attrs(id=ann)}><bpmn:text>{escape(chr(10).join(details))}'
                             f'</bpmn:text></bpmn:textAnnotation>')
            artifacts.append(f'    <bpmn:association{_attrs(id=assoc, sourceRef=pid, targetRef=ann)} />')
            doc.shape(ann, x + 10, y0 + 35, pool_w - 20, head - 45)
            doc.edge(assoc, [(x + pool_w / 2, y0 + 30), (x + pool_w / 2, y0 + 35)])
        y = y0 + head + row / 2
        frame: dict[str, list[float]] = {}
        skipped = []
        for kind, item in rows:
            if kind == "frag":
                frame[item.id] = [y - row / 3]
                y += row / 2
                continue
            st = item
            frag = fragment(view, st.fragment) if st.fragment else None
            guard = f"[{frag.guard}] " if communication and frag else ""
            name = f"{st.order}. {guard}{st.message}{' (return)' if st.kind == 'return' else ''}"
            if st.source not in col or st.target not in col:
                skipped.append(str(st.order))
            elif st.source == st.target:
                pid = alias(st.source)
                ann, assoc = doc.new_id("TextAnnotation"), doc.new_id("Association")
                artifacts.append(f'    <bpmn:textAnnotation{_attrs(id=ann)}><bpmn:text>{escape(name + " (self)")}'
                                 f'</bpmn:text></bpmn:textAnnotation>')
                artifacts.append(f'    <bpmn:association{_attrs(id=assoc, sourceRef=pid, targetRef=ann)} />')
                x = x0 + col[st.source] * col_w
                doc.shape(ann, x + 20, y - 20, pool_w - 40, 40)
                doc.edge(assoc, [(x + 10, y), (x + 20, y)])
            else:
                fid = doc.new_id("MessageFlow")
                flows.append(f'    <bpmn:messageFlow{_attrs(id=fid, name=name, sourceRef=alias(st.source), targetRef=alias(st.target))} />')
                sx, tx = x0 + col[st.source] * col_w, x0 + col[st.target] * col_w
                if tx > sx:
                    pts = [(sx + pool_w, y), (tx, y)]
                else:
                    pts = [(sx, y), (tx + pool_w, y)]
                doc.edge(fid, pts)
            if frag and frag.id in frame:
                frame[frag.id].append(y)
            y += row
        for frag in view.fragments:
            ys = frame.get(frag.id)
            if not ys:
                continue
            cols = [col[i] for s in view.interactions if s.fragment == frag.id for i in (s.source, s.target) if i in col] or [0]
            gid = doc.new_id("Group")
            val = doc.category(f"{frag.kind} [{frag.guard}]")
            artifacts.append(f'    <bpmn:group{_attrs(id=gid, categoryValueRef=val)} />')
            gx0, gx1 = x0 + min(cols) * col_w - 15, x0 + max(cols) * col_w + pool_w + 15
            doc.shape(gid, gx0, ys[0], gx1 - gx0, max(ys) - ys[0] + row / 2)
        collab = ['  <bpmn:collaboration id="Collaboration_1">', *participants, *flows, *artifacts,
                  "  </bpmn:collaboration>"]
        note = f"interactions not drawn (participant not in view): {', '.join(skipped)}" if skipped else ""
        return collab, "Collaboration_1", note

    # ---------------------------------------------------------- state machine (process approximation)
    def _state(self, view: ArchitectureView, doc: _Doc):
        states = view.content_elements()
        ids = {e.id: alias(e.id) for e in states}
        targets = {r.target for r in view.relations}
        sources = {r.source for r in view.relations}
        initial = next((e for e in states if e.id not in targets), states[0] if states else None)
        flows: list[tuple[str, str, str, str | None]] = []
        if initial is not None:
            flows.append((doc.new_id("Flow"), "StartEvent_1", ids[initial.id], None))
        skipped = []
        for rel in view.relations:
            if rel.source in ids and rel.target in ids:
                flows.append((doc.new_id("Flow"), ids[rel.source], ids[rel.target], rel.label))
            else:
                skipped.append(rel.id)
        finals = [e for e in states if e.id not in sources]
        ends = []
        for e in finals:
            end = doc.new_id("EndEvent")
            ends.append((end, e))
            flows.append((doc.new_id("Flow"), ids[e.id], end, None))
        proc = ['  <bpmn:process id="Process_1" isExecutable="false">', '    <bpmn:startEvent id="StartEvent_1" />']
        for e in states:
            proc.append(f'    <bpmn:task{_attrs(id=ids[e.id], name=chr(10).join(label_lines(e)))}>{_doc(_details(e))}</bpmn:task>')
        proc += [f'    <bpmn:endEvent{_attrs(id=end)} />' for end, _ in ends]
        proc += [f"    <bpmn:sequenceFlow{_attrs(id=f, name=n, sourceRef=s, targetRef=t)} />" for f, s, t, n in flows]
        proc.append("  </bpmn:process>")
        y = 200.0
        doc.shape("StartEvent_1", 150, y - 18, 36, 36)
        for i, e in enumerate(states):
            h = max(80.0, 30 + 20 * len(label_lines(e)))
            doc.shape(ids[e.id], 250 + i * 200, y - h / 2, 130, h)
        for end, e in ends:
            x, _, w, _ = doc.bounds[ids[e.id]]
            doc.shape(end, x + w / 2 - 18, y + 90, 36, 36)
        for f, s, t, _ in flows:
            a, b = doc.bounds[s], doc.bounds[t]
            if t.startswith("EndEvent"):
                pts = [(a[0] + a[2] / 2, a[1] + a[3]), (b[0] + b[2] / 2, b[1])]
            elif s == t:
                ax, ay, aw, ah = a
                pts = [(ax + aw, ay + ah / 3), (ax + aw + 30, ay + ah / 3), (ax + aw + 30, ay - 20),
                       (ax + aw / 2, ay - 20), (ax + aw / 2, ay)]
            elif b[0] <= a[0]:
                top = min(a[1], b[1]) - 30
                pts = [(a[0] + a[2] / 2, a[1]), (a[0] + a[2] / 2, top), (b[0] + b[2] / 2, top), (b[0] + b[2] / 2, b[1])]
            else:
                pts = self._route(a, b)
            doc.edge(f, pts)
        note = f"transitions not drawn (state not in view): {', '.join(skipped)}" if skipped else ""
        return proc, "Process_1", note

    # ---------------------------------------------------------- table (task per row)
    def _table(self, view: ArchitectureView, doc: _Doc):
        rows = table_rows(view)
        proc = ['  <bpmn:process id="Process_1" isExecutable="false">']
        header = " | ".join(rows[0])
        doc.shape("TextAnnotation_header", 160, 80, 640, 40)
        for i, row in enumerate(rows[1:], start=1):
            tid = f"Task_row_{i}"
            name = " | ".join(c or "-" for c in row)
            cells = [f"{h}: {c}" for h, c in zip(rows[0], row) if c]
            proc.append(f'    <bpmn:task{_attrs(id=tid, name=name)}>{_doc(cells)}</bpmn:task>')
            doc.shape(tid, 160, 80 + i * 100, 640, 80)
        proc.append(f'    <bpmn:textAnnotation id="TextAnnotation_header"><bpmn:text>{escape(header)}</bpmn:text>'
                    f'</bpmn:textAnnotation>')  # artifacts follow flow elements (BPMN 2.0 XSD order)
        proc.append("  </bpmn:process>")
        return proc, "Process_1", ""
