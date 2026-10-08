"""Excalidraw renderer: an Excalidraw scene (JSON, ``{"type": "excalidraw", "version": 2, ...}``).

Excalidraw is a free-form whiteboard with no UML semantics, so every model kind is an approximation
(``approximated`` is set from NATIVE). The scene is laid out deterministically on a grid; ids and
seeds are derived from the view, so the same view always yields the same JSON. Conventions:

- Every label is a text element: either bound to its container (``containerId`` + the container's
  ``boundElements``) or free-standing with an explicit position (titles, frame captions).
- Every arrow is bound to existing start/end elements (``startBinding``/``endBinding``) and listed in
  their ``boundElements``; arrow labels are text bound to the arrow.

Approximations per model kind:
- uml-component / uml-package / uml-class / uml-deployment / uml-usecase: one shape per element
  (rectangle; ellipse for actors, use cases and datastores; diamond for decisions) whose bound text is
  ``«stereotype»``, the name, responsibilities and attributes (label_lines). Nesting (group elements or
  elements with children) is a rectangle enclosing its children (dashed for projection groups) with a
  caption at its top-left. Relations are bound arrows labelled with the relation label; multiplicity as
  ``src .. label .. tgt`` text on association arrows; ``«include»``/``«extend»`` labels on dashed
  arrows; triangle heads for is-a/generalization/implements; dashed arrows for dependency-like kinds.
- uml-state: rounded rectangles per state, a filled small ellipse as the initial pseudo-state, and
  bound arrows labelled with the transition labels.
- uml-sequence: a column per participant (header box with the name, a thin dashed rectangle as the
  lifeline); messages are horizontal bound arrows top-to-bottom in order, labelled ``<order>. message``
  (returns dashed). Fragments are labelled rectangles (``alt [guard]``) around their steps.
- uml-communication: participant boxes on a circle with one bound arrow per message, labelled
  ``<order>. [guard] message``; parallel messages between the same pair are offset.
- uml-activity: a swimlane column per participant (rectangle + caption); start/end ellipses, a rounded
  rectangle per step (``<order>. message``) in the lane of its sender, and a decision diamond
  ``kind [guard]`` plus a merge diamond around each fragment (``[guard]`` / ``[else]`` arrows).
- table: a grid of rectangles, one bound text per cell, rows from table_rows() (header shaded).
"""

from __future__ import annotations

import json
import math
import zlib

from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.phase7.notations.base import (
    Renderer, alias, children, fragment, label_lines, multiplicity, register, segments, table_rows,
)

_FONT, _LINE_H, _CHAR_W = 16, 20, 9
_DASHED = {"allowed-to-use", "implements", "include", "extend", "deploys", "crosscuts", "traces-to",
           "assigned-to", "allocated-to", "depends-on", "dependency", "subscribes"}
_TRIANGLE = {"is-a", "generalization", "implements"}
_NO_HEAD = {"attachment", "communicates"}


def _seed(key: str) -> int:
    return zlib.crc32(key.encode("utf-8")) & 0x7FFFFFFF or 1


def _text_size(text: str, size: int = _FONT) -> tuple[float, float]:
    lines = text.split("\n") or [""]
    scale = size / _FONT
    return max(len(line) for line in lines) * _CHAR_W * scale + 4, len(lines) * _LINE_H * scale


class _Scene:
    def __init__(self, view: ArchitectureView):
        self.view = view
        self.elements: list[dict] = []
        self.by_id: dict[str, dict] = {}
        self._n = 0

    def _new_id(self, hint: str) -> str:
        self._n += 1
        return f"{hint}-{self._n}"

    def _common(self, eid: str, etype: str, x: float, y: float, w: float, h: float) -> dict:
        el = {"id": eid, "type": etype, "x": round(x, 2), "y": round(y, 2), "width": round(w, 2),
              "height": round(h, 2), "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
              "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1, "opacity": 100,
              "groupIds": [], "frameId": None, "roundness": None, "seed": _seed(self.view.id + eid),
              "version": 1, "versionNonce": _seed(eid + self.view.id), "isDeleted": False, "boundElements": [],
              "updated": 1, "link": None, "locked": False}
        self.elements.append(el)
        self.by_id[eid] = el
        return el

    def shape(self, eid: str, kind: str, x: float, y: float, w: float, h: float, text: str | None = None,
              dashed: bool = False, fill: str | None = None, rounded: bool = False, stroke: int = 2) -> dict:
        el = self._common(eid, kind, x, y, w, h)
        el["strokeWidth"] = stroke
        if dashed:
            el["strokeStyle"] = "dashed"
        if fill:
            el["backgroundColor"] = fill
        if rounded or kind == "ellipse" or kind == "diamond":
            el["roundness"] = {"type": 2} if kind != "rectangle" else {"type": 3}
        if text:
            self.text(text, container=el)
        return el

    def text(self, text: str, x: float = 0, y: float = 0, container: dict | None = None, size: int = _FONT,
             align: str = "left") -> dict:
        tw, th = _text_size(text, size)
        if container is not None:
            if container["type"] == "arrow":
                pts = container["points"]
                mx, my = pts[len(pts) // 2] if len(pts) > 2 else ((pts[0][0] + pts[-1][0]) / 2,
                                                                  (pts[0][1] + pts[-1][1]) / 2)
                x, y = container["x"] + mx - tw / 2, container["y"] + my - th / 2
            else:
                x = container["x"] + (container["width"] - tw) / 2
                y = container["y"] + (container["height"] - th) / 2
            align = "center"
        el = self._common(self._new_id("text"), "text", x, y, tw, th)
        el.update({"text": text, "originalText": text, "fontSize": size, "fontFamily": 1, "textAlign": align,
                   "verticalAlign": "middle" if container is not None else "top",
                   "containerId": container["id"] if container is not None else None, "lineHeight": 1.25,
                   "autoResize": True})
        el["strokeWidth"] = 1
        if container is not None:
            container["boundElements"].append({"id": el["id"], "type": "text"})
        return el

    def line(self, x: float, y: float, points: list[list[float]], dashed: bool = True) -> dict:
        el = self._common(self._new_id("line"), "line", x, y, *_extent(points))
        el.update({"points": points, "lastCommittedPoint": None, "startBinding": None, "endBinding": None,
                   "startArrowhead": None, "endArrowhead": None})
        if dashed:
            el["strokeStyle"] = "dashed"
        return el

    def arrow(self, src: str, tgt: str, label: str | None = None, dashed: bool = False, head: str | None = "arrow",
              start_head: str | None = None, offset: float = 0, start: tuple | None = None,
              points: list[list[float]] | None = None) -> dict:
        a, b = self.by_id[src], self.by_id[tgt]
        if start is None:
            ca, cb = _center(a), _center(b)
            dx, dy = cb[0] - ca[0], cb[1] - ca[1]
            norm = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / norm * offset, dx / norm * offset  # perpendicular shift for parallel arrows
            p0 = _boundary(a, (cb[0] + nx, cb[1] + ny), (nx, ny))
            p1 = _boundary(b, (ca[0] + nx, ca[1] + ny), (nx, ny))
            start = p0
            points = [[0, 0], [round(p1[0] - p0[0], 2), round(p1[1] - p0[1], 2)]]
        el = self._common(self._new_id("arrow"), "arrow", start[0], start[1], *_extent(points))
        el.update({"points": points, "lastCommittedPoint": None,
                   "startBinding": {"elementId": src, "focus": 0, "gap": 4},
                   "endBinding": {"elementId": tgt, "focus": 0, "gap": 4},
                   "startArrowhead": start_head, "endArrowhead": head, "roundness": {"type": 2}})
        if dashed:
            el["strokeStyle"] = "dashed"
        a["boundElements"].append({"id": el["id"], "type": "arrow"})
        if tgt != src:
            b["boundElements"].append({"id": el["id"], "type": "arrow"})
        if label:
            self.text(label, container=el, size=14)
        return el

    def json(self) -> str:
        scene = {"type": "excalidraw", "version": 2, "source": "task2view",
                 "elements": self.elements,
                 "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20}, "files": {}}
        return json.dumps(scene, indent=2, ensure_ascii=False)


def _extent(points: list[list[float]]) -> tuple[float, float]:
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return max(xs) - min(xs), max(ys) - min(ys)


def _center(el: dict) -> tuple[float, float]:
    return el["x"] + el["width"] / 2, el["y"] + el["height"] / 2


def _boundary(el: dict, toward: tuple[float, float], shift: tuple[float, float] = (0, 0)) -> tuple[float, float]:
    """Point where the ray from the (shifted) centre towards ``toward`` leaves the element's box."""
    cx, cy = _center(el)
    cx, cy = cx + shift[0], cy + shift[1]
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    hw, hh = el["width"] / 2, el["height"] / 2
    t = min(hw / abs(dx) if dx else math.inf, hh / abs(dy) if dy else math.inf)
    if el["type"] in {"ellipse", "diamond"}:
        t *= 0.85
    return round(cx + dx * t, 2), round(cy + dy * t, 2)


def _element_text(e) -> str:
    lines = label_lines(e)
    if e.stereotype:
        lines = [f"«{e.stereotype}»", *lines]
    return "\n".join(lines)


def _leaf_shape(kind: str) -> str:
    if kind in {"actor", "use_case", "datastore", "database"}:
        return "ellipse"
    if kind in {"decision", "choice"}:
        return "diamond"
    return "rectangle"


@register
class ExcalidrawRenderer(Renderer):
    language = "excalidraw"
    extension = "excalidraw"

    def render(self, view: ArchitectureView) -> RenderResult:
        scene = _Scene(view)
        scene.text(view.title, x=40, y=10, size=24)
        note = {"uml-sequence": self._sequence, "uml-communication": self._communication,
                "uml-activity": self._activity, "table": self._table}.get(view.model_kind, self._structure)(view, scene)
        return self.result(view, scene.json(), note or "")

    # ---------------------------------------------------------- structure (component, package, class, ...)
    def _structure(self, view: ArchitectureView, scene: _Scene) -> str:
        tree = children(view)
        pad, header, gap = 20, 30, 40

        def leaf_size(e) -> tuple[float, float]:
            tw, th = _text_size(_element_text(e))
            w, h = max(140, tw + 30), max(60, th + 30)
            if _leaf_shape(e.kind) != "rectangle":
                w, h = w * 1.4, h * 1.4
            return w, h

        def grid(items, per_row: int) -> tuple[list[tuple[float, float]], float, float]:
            """Offsets of ``items`` (sizes) laid out in rows; returns offsets, width, height."""
            offsets, x, y, row_h, width = [], 0.0, 0.0, 0.0, 0.0
            for i, (w, h) in enumerate(items):
                if i and i % per_row == 0:
                    x, y, row_h = 0.0, y + row_h + gap, 0.0
                offsets.append((x, y))
                x += w + gap
                row_h = max(row_h, h)
                width = max(width, x - gap)
            return offsets, width, y + row_h

        sizes: dict[str, tuple[float, float]] = {}

        def size(e) -> tuple[float, float]:
            nested = tree.get(e.id, [])
            if not nested:
                sizes[e.id] = leaf_size(e)
                return sizes[e.id]
            _, w, h = grid([size(c) for c in nested], 3)
            cap_w, cap_h = _text_size(_caption(e))
            sizes[e.id] = (max(w, cap_w) + 2 * pad, h + 2 * pad + max(header, cap_h + 10))
            return sizes[e.id]

        def _caption(e) -> str:
            text = _element_text(e)
            return f"«{e.kind}» {text}" if e.group and not e.stereotype else text

        def place(e, x: float, y: float):
            nested = tree.get(e.id, [])
            w, h = sizes[e.id]
            if not nested:
                scene.shape(alias(e.id), _leaf_shape(e.kind), x, y, w, h, _element_text(e), rounded=e.kind == "state")
                return
            scene.shape(alias(e.id), "rectangle", x, y, w, h, dashed=e.group, fill="#f8f9fa" if e.group else None)
            cap = _caption(e)
            scene.text(cap, x=x + 10, y=y + 8)
            top = y + pad + max(header, _text_size(cap)[1] + 10)
            offsets, _, _ = grid([sizes[c.id] for c in nested], 3)
            for c, (ox, oy) in zip(nested, offsets):
                place(c, x + pad + ox, top + oy)

        top_level = tree.get(None, [])
        origin_x, origin_y = 40.0, 70.0
        if view.model_kind == "uml-state" and view.content_elements():
            targets = {r.target for r in view.relations}
            initial = next((e for e in view.content_elements() if e.id not in targets), view.content_elements()[0])
            scene.shape("initial", "ellipse", origin_x, origin_y + 15, 30, 30, fill="#1e1e1e")
            origin_x += 100
        else:
            initial = None
        offsets, _, _ = grid([size(e) for e in top_level], 4)
        for e, (ox, oy) in zip(top_level, offsets):
            place(e, origin_x + ox, origin_y + oy)
        if initial is not None:
            scene.arrow("initial", alias(initial.id))

        skipped = []
        pair_count: dict[tuple[str, str], int] = {}
        for rel in view.relations:
            src, tgt = alias(rel.source), alias(rel.target)
            if src not in scene.by_id or tgt not in scene.by_id:
                skipped.append(rel.id)
                continue
            key = tuple(sorted((src, tgt)))
            k = pair_count.get(key, 0)
            pair_count[key] = k + 1
            label = rel.label or ""
            if rel.kind in {"include", "extend"}:
                label = f"«{rel.kind}»"
            elif rel.kind in _TRIANGLE and not label:
                label = f"«{rel.kind}»"
            src_m, tgt_m = multiplicity(rel)
            if src_m or tgt_m:
                label = f"{src_m} .. {label} .. {tgt_m}" if label else f"{src_m} .. {tgt_m}"
            if src == tgt:
                el = scene.by_id[src]
                start = (el["x"] + el["width"], el["y"] + el["height"] / 3)
                pts = [[0, 0], [40, 0], [40, el["height"] / 3], [0, el["height"] / 3]]
                scene.arrow(src, tgt, label or None, start=start, points=pts)
                continue
            scene.arrow(src, tgt, label or None, dashed=rel.kind in _DASHED,
                        head=None if rel.kind in _NO_HEAD else ("triangle" if rel.kind in _TRIANGLE else "arrow"),
                        start_head="diamond" if rel.kind == "composition" else None, offset=k * 16)
        return f"relations not drawn (endpoint not in view): {', '.join(skipped)}" if skipped else ""

    # ---------------------------------------------------------- sequence
    def _sequence(self, view: ArchitectureView, scene: _Scene) -> str:
        parts = view.content_elements()
        col = {p.id: i for i, p in enumerate(parts)}
        texts = {p.id: _element_text(p) for p in parts}
        col_w = max([200.0] + [_text_size(t)[0] + 60 for t in texts.values()])
        msg_w = max([0.0] + [_text_size(f"{s.order}. {s.message}", 14)[0] + 40 for s in view.interactions])
        col_w = max(col_w, msg_w)
        head_h = max([60.0] + [_text_size(t)[1] + 30 for t in texts.values()])
        top, row = 70.0, 60.0
        # rows: one per step, plus a caption row before each fragment
        rows: list[tuple[str, object]] = []
        for frag_id, steps in segments(view):
            frag = fragment(view, frag_id)
            if frag:
                rows.append(("frag-start", frag))
            rows += [("step", s) for s in steps]
            if frag:
                rows.append(("frag-end", frag))
        n_rows = len(rows) + 1
        life_top = top + head_h + 10
        life_h = n_rows * row + 40
        centers = {}
        for p in parts:
            x = 40 + col[p.id] * col_w
            scene.shape(alias(p.id) + "_head", "ellipse" if p.kind == "actor" else "rectangle",
                        x + 10, top, col_w - 20, head_h, texts[p.id])
            cx = x + col_w / 2
            centers[p.id] = cx
            scene.shape(alias(p.id), "rectangle", cx - 6, life_top, 12, life_h, dashed=True, stroke=1)
        y = life_top + 40
        open_frames: list[tuple[object, float]] = []
        skipped = []
        for kind, item in rows:
            if kind == "frag-start":
                open_frames.append((item, y))
                y += row / 2
                continue
            if kind == "frag-end":
                frag, y0 = open_frames.pop()
                steps = [s for k, s in rows if k == "step" and s.fragment == frag.id]
                cols = [col[i] for s in steps for i in (s.source, s.target) if i in col] or [0]
                x0 = 40 + min(cols) * col_w + 4
                x1 = 40 + (max(cols) + 1) * col_w - 4
                scene.shape(scene._new_id("fragment"), "rectangle", x0, y0 - 10, x1 - x0, y - y0 + 10 - row / 3,
                            dashed=True, stroke=1)
                scene.text(f"{frag.kind} [{frag.guard}]", x=x0 + 8, y=y0 - 6, size=14)
                continue
            st = item
            if st.source not in col or st.target not in col:
                skipped.append(str(st.order))
                y += row
                continue
            label = f"{st.order}. {st.message}"
            src, tgt = alias(st.source), alias(st.target)
            sx, tx = centers[st.source], centers[st.target]
            if src == tgt:
                pts = [[0, 0], [50, 0], [50, row / 2], [0, row / 2]]
                scene.arrow(src, tgt, label, start=(sx + 6, y), points=pts, dashed=st.kind == "return")
            else:
                direction = 1 if tx > sx else -1
                x_start, x_end = sx + 6 * direction, tx - 6 * direction
                scene.arrow(src, tgt, label, start=(x_start, y), points=[[0, 0], [round(x_end - x_start, 2), 0]],
                            dashed=st.kind == "return")
            y += row
        return f"interactions not drawn (participant not in view): {', '.join(skipped)}" if skipped else ""

    # ---------------------------------------------------------- communication
    def _communication(self, view: ArchitectureView, scene: _Scene) -> str:
        parts = view.content_elements()
        n = max(len(parts), 1)
        radius = max(180.0, n * 70.0)
        cx, cy = 40 + radius + 120, 70 + radius + 60
        for i, p in enumerate(parts):
            text = _element_text(p)
            tw, th = _text_size(text)
            w, h = max(160, tw + 30), max(60, th + 30)
            angle = -math.pi / 2 + 2 * math.pi * i / n
            x, y = cx + radius * math.cos(angle) - w / 2, cy + radius * math.sin(angle) - h / 2
            scene.shape(alias(p.id), "ellipse" if p.kind == "actor" else "rectangle", round(x, 2), round(y, 2),
                        w * (1.3 if p.kind == "actor" else 1), h, text)
        pair_count: dict[tuple[str, str], int] = {}
        skipped = []
        for st in sorted(view.interactions, key=lambda s: s.order):
            src, tgt = alias(st.source), alias(st.target)
            if src not in scene.by_id or tgt not in scene.by_id:
                skipped.append(str(st.order))
                continue
            frag = fragment(view, st.fragment) if st.fragment else None
            guard = f"[{frag.guard}] " if frag else ""
            label = f"{st.order}. {guard}{st.message}"
            if src == tgt:
                el = scene.by_id[src]
                start = (el["x"] + el["width"], el["y"] + el["height"] / 3)
                scene.arrow(src, tgt, label, start=start,
                            points=[[0, 0], [40, 0], [40, el["height"] / 3], [0, el["height"] / 3]])
                continue
            key = tuple(sorted((src, tgt)))
            k = pair_count.get(key, 0)
            pair_count[key] = k + 1
            sign = 1 if (src, tgt) == key else -1
            offset = sign * (k + 0.5) * 18
            scene.arrow(src, tgt, label, offset=offset, dashed=st.kind == "return")
        return f"interactions not drawn (participant not in view): {', '.join(skipped)}" if skipped else ""

    # ---------------------------------------------------------- activity
    def _activity(self, view: ArchitectureView, scene: _Scene) -> str:
        lanes = view.content_elements()
        lane_idx = {e.id: i for i, e in enumerate(lanes)}
        captions = {e.id: _element_text(e) for e in lanes}
        step_w = max([180.0] + [_text_size(f"{s.order}. {s.message}")[0] + 30 for s in view.interactions])
        guard_w = max([0.0] + [_text_size(f"{f.kind} [{f.guard}]", 14)[0] * 1.6 for f in view.fragments])
        lane_w = max([step_w + 60, guard_w + 40] + [_text_size(c)[0] + 30 for c in captions.values()])
        cap_h = max([30.0] + [_text_size(c)[1] + 20 for c in captions.values()])
        row, top = 100.0, 70.0

        nodes: list[tuple[str, str, str | None, int]] = []  # (id, shape, text, lane index)
        edges: list[tuple[str, str, str | None]] = []
        ordered = sorted(view.interactions, key=lambda s: s.order)
        first_lane = lane_idx.get(ordered[0].source, 0) if ordered else 0
        nodes.append(("start", "start", None, first_lane))
        prev = ["start"]  # open ends that flow into the next node

        def link(target: str, label: str | None = None):
            for p in prev:
                edges.append((p, target, label))

        for frag_id, steps in segments(view):
            frag = fragment(view, frag_id)
            if frag:
                lane = lane_idx.get(steps[0].source, first_lane)
                dec, merge = scene._new_id("decision"), scene._new_id("merge")
                nodes.append((dec, "diamond", f"{frag.kind} [{frag.guard}]", lane))
                link(dec)
                prev = [dec]
                first = True
                for st in steps:
                    sid = f"step_{st.order}"
                    nodes.append((sid, "step", f"{st.order}. {st.message}", lane_idx.get(st.source, lane)))
                    for p in prev:
                        edges.append((p, sid, f"[{frag.guard}]" if first else None))
                    prev, first = [sid], False
                nodes.append((merge, "diamond", None, lane))
                link(merge)
                edges.append((dec, merge, "[else]" if frag.kind != "loop" else "[done]"))
                if frag.kind == "loop":
                    edges.append((prev[0], dec, "repeat"))
                prev = [merge]
            else:
                for st in steps:
                    sid = f"step_{st.order}"
                    nodes.append((sid, "step", f"{st.order}. {st.message}", lane_idx.get(st.source, first_lane)))
                    link(sid)
                    prev = [sid]
        last_lane = nodes[-1][3]
        nodes.append(("end", "end", None, last_lane))
        link("end")

        height = cap_h + (len(nodes) + 1) * row
        for e in lanes:
            x = 40 + lane_idx[e.id] * lane_w
            scene.shape(alias(e.id), "rectangle", x, top, lane_w, height, stroke=1)
            scene.text(captions[e.id], x=x + 10, y=top + 8)
        if not lanes:
            scene.shape("lane_default", "rectangle", 40, top, lane_w, height, stroke=1)
        ids: dict[str, str] = {}
        for i, (nid, shape, text, lane) in enumerate(nodes):
            cx = 40 + lane * lane_w + lane_w / 2
            cy = top + cap_h + (i + 0.5) * row
            eid = f"{nid}_node" if nid.startswith("step_") else nid
            ids[nid] = eid
            if shape in {"start", "end"}:
                scene.shape(eid, "ellipse", cx - 18, cy - 18, 36, 36, fill="#1e1e1e" if shape == "start" else None,
                            stroke=2 if shape == "start" else 4)
            elif shape == "diamond":
                w = max(60.0, _text_size(text or "", 14)[0] * 1.6) if text else 50
                h = 70 if text else 50
                el = scene.shape(eid, "diamond", cx - w / 2, cy - h / 2, w, h)
                if text:
                    scene.text(text, container=el, size=14)
            else:
                scene.shape(eid, "rectangle", cx - step_w / 2, cy - 30, step_w, 60, text, rounded=True)
        for src, tgt, label in edges:
            scene.arrow(ids[src], ids[tgt], label, offset=-30 if label in {"[else]", "[done]", "repeat"} else 0)
        return ""

    # ---------------------------------------------------------- table
    def _table(self, view: ArchitectureView, scene: _Scene) -> str:
        rows = table_rows(view)
        n_cols = max(len(r) for r in rows)
        widths = [max(80.0, max(_text_size(r[c] if c < len(r) else "", 14)[0] for r in rows) + 20)
                  for c in range(n_cols)]
        y = 70.0
        for ri, row in enumerate(rows):
            h = max(40.0, max(_text_size(c or " ", 14)[1] for c in row) + 16)
            x = 40.0
            for ci in range(n_cols):
                cell = row[ci] if ci < len(row) else ""
                el = scene.shape(f"cell_{ri}_{ci}", "rectangle", x, y, widths[ci], h,
                                 fill="#e9ecef" if ri == 0 else None, stroke=1)
                if cell:
                    scene.text(cell, container=el, size=14)
                x += widths[ci]
            y += h
        return ""
