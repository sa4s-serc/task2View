"""Excalidraw and BPMN renderers: real format checks for all 10 model kinds.

Excalidraw: the scene parses as JSON, has the scene shape, and its bindings are consistent.
BPMN: the XML is well-formed, uses the BPMN 2.0 namespaces, and every reference resolves.
"""

import json
import xml.etree.ElementTree as ET

import pytest

from task2view.phase7.notations import MODEL_KINDS, get_renderer

from .view_samples import SAMPLES

BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI = "http://www.omg.org/spec/BPMN/20100524/DI"
DC = "http://www.omg.org/spec/DD/20100524/DC"
DI = "http://www.omg.org/spec/DD/20100524/DI"


def _expected_texts(view) -> list[str]:
    out = []
    for e in view.content_elements():
        out.append(e.name)
        out += e.responsibilities
        out += [a.name for a in e.attributes]
    out += [f.guard for f in view.fragments if any(s.fragment == f.id for s in view.interactions)]
    return out


# ---------------------------------------------------------------- excalidraw

def _scene(model_kind):
    view = SAMPLES[model_kind]()
    return view, json.loads(get_renderer("excalidraw").render(view).source)


@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_excalidraw_scene_shape(model_kind):
    _, scene = _scene(model_kind)
    assert scene["type"] == "excalidraw" and scene["version"] == 2
    assert isinstance(scene["source"], str) and isinstance(scene["appState"], dict)
    ids = [el["id"] for el in scene["elements"]]
    assert len(ids) == len(set(ids)), "element ids must be unique"
    for el in scene["elements"]:
        assert el["type"] in {"rectangle", "ellipse", "diamond", "text", "arrow", "line"}
        for key in ("x", "y", "width", "height"):
            assert isinstance(el[key], (int, float))
        assert isinstance(el["boundElements"], list)


@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_excalidraw_bindings_resolve(model_kind):
    _, scene = _scene(model_kind)
    by_id = {el["id"]: el for el in scene["elements"]}
    for el in scene["elements"]:
        for b in el["boundElements"]:
            assert b["id"] in by_id and by_id[b["id"]]["type"] == b["type"]
        if el["type"] == "arrow":
            assert len(el["points"]) >= 2
            for end in ("startBinding", "endBinding"):
                target = el[end]["elementId"]
                assert target in by_id, f"arrow {el['id']} bound to missing {target}"
                assert {"id": el["id"], "type": "arrow"} in by_id[target]["boundElements"]
        if el["type"] == "text":
            assert el["text"]
            if el["containerId"] is not None:
                container = by_id[el["containerId"]]
                assert {"id": el["id"], "type": "text"} in container["boundElements"]


@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_excalidraw_all_content_is_text(model_kind):
    view, scene = _scene(model_kind)
    texts = "\n".join(el["text"] for el in scene["elements"] if el["type"] == "text")
    for expected in _expected_texts(view):
        assert expected in texts, f"{model_kind}: {expected!r} missing from text elements"


def test_excalidraw_containment_and_sequence_order():
    view, scene = _scene("uml-component")
    by_id = {el["id"]: el for el in scene["elements"]}
    layer, child = by_id["e_group_layer_presentation_8df40c"], by_id["e_cmp_web_OrderController_5b247b"]
    assert layer["x"] < child["x"] and child["x"] + child["width"] < layer["x"] + layer["width"]
    assert layer["y"] < child["y"] and child["y"] + child["height"] < layer["y"] + layer["height"]

    _, seq = _scene("uml-sequence")
    labels = {el["containerId"]: el["text"] for el in seq["elements"] if el["type"] == "text" and el["containerId"]}
    arrows = [el for el in seq["elements"] if el["type"] == "arrow"]
    ordered = [labels[a["id"]] for a in sorted(arrows, key=lambda a: a["y"])]
    assert [t.split(".")[0] for t in ordered] == ["1", "2", "3", "4"]
    assert any(el["type"] == "text" and el["text"] == "alt [order not NEW]" for el in seq["elements"])


# ---------------------------------------------------------------- bpmn

def _bpmn(model_kind):
    view = SAMPLES[model_kind]()
    result = get_renderer("bpmn").render(view)
    return view, result, ET.fromstring(result.source.encode("utf-8"))


@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_bpmn_well_formed_with_references(model_kind):
    _, _, root = _bpmn(model_kind)
    assert root.tag == f"{{{BPMN}}}definitions"
    assert root.get("targetNamespace")
    ids = [el.get("id") for el in root.iter() if el.get("id")]
    assert len(ids) == len(set(ids)), "ids must be unique"
    defined = set(ids)
    for tag in ("sequenceFlow", "messageFlow", "association"):
        for flow in root.iter(f"{{{BPMN}}}{tag}"):
            assert flow.get("sourceRef") in defined, f"{tag} {flow.get('id')} source"
            assert flow.get("targetRef") in defined, f"{tag} {flow.get('id')} target"
    for ref in root.iter(f"{{{BPMN}}}flowNodeRef"):
        assert ref.text in defined
    for p in root.iter(f"{{{BPMN}}}participant"):
        assert p.get("processRef") is None or p.get("processRef") in defined
    for g in root.iter(f"{{{BPMN}}}group"):
        assert g.get("categoryValueRef") in defined


@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_bpmn_diagram_interchange(model_kind):
    _, _, root = _bpmn(model_kind)
    defined = {el.get("id") for el in root.iter() if el.get("id")}
    planes = list(root.iter(f"{{{BPMNDI}}}BPMNPlane"))
    assert len(planes) == 1 and planes[0].get("bpmnElement") in defined
    shapes = list(root.iter(f"{{{BPMNDI}}}BPMNShape"))
    edges = list(root.iter(f"{{{BPMNDI}}}BPMNEdge"))
    assert shapes
    for s in shapes:
        assert s.get("bpmnElement") in defined
        assert s.find(f"{{{DC}}}Bounds") is not None
    for e in edges:
        assert e.get("bpmnElement") in defined
        assert len(e.findall(f"{{{DI}}}waypoint")) >= 2
    drawn = {s.get("bpmnElement") for s in shapes} | {e.get("bpmnElement") for e in edges}
    semantic = ("task", "startEvent", "endEvent", "exclusiveGateway", "participant", "lane", "sequenceFlow",
                "messageFlow", "textAnnotation", "group")
    for tag in semantic:
        for el in root.iter(f"{{{BPMN}}}{tag}"):
            if tag == "participant" and el.get("processRef") and model_kind != "uml-activity":
                continue
            assert el.get("id") in drawn, f"{tag} {el.get('id')} has no DI"


@pytest.mark.parametrize("model_kind", MODEL_KINDS)
def test_bpmn_all_content_present(model_kind):
    view, result, _ = _bpmn(model_kind)
    for expected in _expected_texts(view):
        assert expected in result.source, f"{model_kind}: {expected!r} missing"


def test_bpmn_activity_is_native_process():
    view, result, root = _bpmn("uml-activity")
    assert not result.approximated
    q = lambda tag: list(root.iter(f"{{{BPMN}}}{tag}"))  # noqa: E731
    assert len(q("startEvent")) == 1 and len(q("endEvent")) == 1
    assert len(q("task")) == len(view.interactions)
    gateways = q("exclusiveGateway")
    assert any(g.get("name") == "alt [order not NEW]" for g in gateways)
    assert {lane.get("name") for lane in q("lane")} == {e.name for e in view.content_elements()}
    # sequence flows visit the tasks in step order
    succ: dict[str, list[str]] = {}
    for f in q("sequenceFlow"):
        succ.setdefault(f.get("sourceRef"), []).append(f.get("targetRef"))
    names = {t.get("id"): t.get("name") for t in q("task")}
    order, node, seen = [], "StartEvent_1", set()
    while node in succ and node not in seen:
        seen.add(node)
        nxt = [t for t in succ[node] if t in names] or succ[node]
        node = nxt[0]
        if node in names:
            order.append(int(names[node].split(".")[0]))
    assert order == sorted(s.order for s in view.interactions)


def test_bpmn_sequence_message_flows_in_order():
    _, result, root = _bpmn("uml-sequence")
    assert result.approximated
    flows = list(root.iter(f"{{{BPMN}}}messageFlow"))
    assert [f.get("name").split(".")[0] for f in flows] == ["1", "2", "3", "4"]
    di_y = {e.get("bpmnElement"): float(e.find(f"{{{DI}}}waypoint").get("y"))
            for e in root.iter(f"{{{BPMNDI}}}BPMNEdge")}
    ys = [di_y[f.get("id")] for f in flows]
    assert ys == sorted(ys)
    assert any(c.get("value") == "alt [order not NEW]" for c in root.iter(f"{{{BPMN}}}categoryValue"))
