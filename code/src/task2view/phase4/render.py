"""Deterministic notation adapters. No model call."""

from __future__ import annotations

from task2view.contracts.models import ViewModel, ViewRelation
from task2view.phase4.protocol import register_adapter


def _ids(vm: ViewModel) -> dict[str, str]:
    return {e.id: e.name for e in vm.elements}


def _ordered_rels(vm: ViewModel) -> list[ViewRelation]:
    rels = list(vm.relations)
    if any(r.order is not None for r in rels):
        rels.sort(key=lambda r: (r.order is None, r.order or 0, r.id))
    return rels


@register_adapter
class PlantUMLAdapter:
    id = "plantuml"
    supports = {
        "sequence_view",
        "component_view",
        "class_view",
        "deployment_view",
        "context_view",
        "dataflow_view",
        "state_view",
    }
    formats = {"svg", "png", "pdf"}

    def emit(self, vm: ViewModel) -> str:
        names = _ids(vm)
        if vm.view_type == "sequence_view":
            lines = ["@startuml", "hide footbox"]
            for el in vm.elements:
                if el.kind == "actor" or el.external:
                    lines.append(f'actor "{el.name}" as {el.id}')
                else:
                    lines.append(f'participant "{el.name}" as {el.id}')
            for rel in _ordered_rels(vm):
                arrow = "-->" if rel.kind == "return" else "->"
                label = rel.label or rel.kind
                lines.append(f"{rel.frm} {arrow} {rel.to}: {label}")
            lines.append("@enduml")
            return "\n".join(lines) + "\n"

        lines = ["@startuml"]
        for g in vm.groups:
            lines.append(f'package "{g.name}" {{')
            for eid in g.contains:
                if eid in names:
                    lines.append(f'  [{names[eid]}] as {eid}')
            lines.append("}")
        grouped = {eid for g in vm.groups for eid in g.contains}
        for el in vm.elements:
            if el.id not in grouped:
                shape = "actor" if el.kind == "actor" or el.external else "component"
                if shape == "actor":
                    lines.append(f'actor "{el.name}" as {el.id}')
                else:
                    lines.append(f'[{el.name}] as {el.id}')
        for rel in vm.relations:
            label = f" : {rel.label}" if rel.label else ""
            lines.append(f"{rel.frm} --> {rel.to}{label}")
        lines.append("@enduml")
        return "\n".join(lines) + "\n"


@register_adapter
class MermaidAdapter:
    id = "mermaid"
    supports = {
        "sequence_view",
        "component_view",
        "class_view",
        "state_view",
        "dataflow_view",
        "context_view",
    }
    formats = {"svg", "png"}

    def emit(self, vm: ViewModel) -> str:
        if vm.view_type == "sequence_view":
            lines = ["sequenceDiagram"]
            for el in vm.elements:
                lines.append(f"    participant {el.id} as {el.name}")
            for rel in _ordered_rels(vm):
                label = rel.label or rel.kind
                lines.append(f"    {rel.frm}->>{rel.to}: {label}")
            return "\n".join(lines) + "\n"
        lines = ["flowchart LR"]
        for el in vm.elements:
            lines.append(f'    {el.id}["{el.name}"]')
        for rel in vm.relations:
            label = f"|{rel.label}|" if rel.label else ""
            lines.append(f"    {rel.frm} -->{label} {rel.to}")
        return "\n".join(lines) + "\n"


@register_adapter
class D2Adapter:
    id = "d2"
    supports = {
        "sequence_view",
        "component_view",
        "class_view",
        "deployment_view",
        "context_view",
        "dataflow_view",
        "state_view",
    }
    formats = {"svg", "png"}

    def emit(self, vm: ViewModel) -> str:
        lines: list[str] = []
        for g in vm.groups:
            lines.append(f"{g.name}: {{")
            for eid in g.contains:
                el = next((e for e in vm.elements if e.id == eid), None)
                if el:
                    lines.append(f"  {eid}: {el.name}")
            lines.append("}")
        grouped = {eid for g in vm.groups for eid in g.contains}
        for el in vm.elements:
            if el.id not in grouped:
                lines.append(f"{el.id}: {el.name}")
        for rel in _ordered_rels(vm):
            label = f": {rel.label}" if rel.label else ""
            lines.append(f"{rel.frm} -> {rel.to}{label}")
        return "\n".join(lines) + "\n"


def _q(text: str) -> str:
    return str(text).replace('"', "'")


@register_adapter
class C4PlantUMLAdapter:
    """C4-PlantUML (stdlib include). Source only; Kroki optional later."""

    id = "c4plantuml"
    supports = {
        "component_view",
        "deployment_view",
        "context_view",
        "sequence_view",
        "class_view",
        "dataflow_view",
        "state_view",
    }
    formats = {"svg", "png", "pdf"}

    def emit(self, vm: ViewModel) -> str:
        lines = [
            "@startuml",
            "!include <C4/C4_Component>",
            f'title {_q(vm.view_type)}',
        ]
        grouped = {eid for g in vm.groups for eid in g.contains}
        for g in vm.groups:
            lines.append(f'System_Boundary({g.id}, "{_q(g.name)}") {{')
            for eid in g.contains:
                el = next((e for e in vm.elements if e.id == eid), None)
                if el:
                    lines.extend(_c4_node(el, indent="  "))
            lines.append("}")
        for el in vm.elements:
            if el.id not in grouped:
                lines.extend(_c4_node(el, indent=""))
        for rel in _ordered_rels(vm):
            label = _q(rel.label or rel.kind)
            lines.append(f'Rel({rel.frm}, {rel.to}, "{label}")')
        lines.append("@enduml")
        return "\n".join(lines) + "\n"


def _c4_node(el, *, indent: str) -> list[str]:
    name = _q(el.name)
    if el.kind == "actor" or el.external:
        return [f'{indent}Person({el.id}, "{name}")']
    if el.kind == "datastore":
        return [f'{indent}ContainerDb({el.id}, "{name}", "store")']
    if el.kind in {"service", "component"}:
        return [f'{indent}Component({el.id}, "{name}", "{el.kind}")']
    return [f'{indent}Container({el.id}, "{name}", "{el.kind}")']


@register_adapter
class StructurizrAdapter:
    id = "structurizr"
    supports = {
        "sequence_view",
        "component_view",
        "deployment_view",
        "context_view",
        "class_view",
        "dataflow_view",
        "state_view",
    }
    formats = {"svg", "png"}

    def emit(self, vm: ViewModel) -> str:
        lines = ["workspace {", "  model {"]
        for el in vm.elements:
            kind = "person" if el.kind == "actor" or el.external else "component"
            lines.append(f'    {el.id} = {kind} "{_q(el.name)}"')
        for rel in _ordered_rels(vm):
            label = _q(rel.label or rel.kind)
            lines.append(f'    {rel.frm} -> {rel.to} "{label}"')
        lines.append("  }")
        lines.append("  views {")
        lines.append("    component softwareSystem {")
        lines.append("      include *")
        lines.append("      autoLayout")
        lines.append("    }")
        lines.append("  }")
        lines.append("}")
        return "\n".join(lines) + "\n"


@register_adapter
class GraphvizAdapter:
    id = "graphviz"
    supports = {
        "component_view",
        "deployment_view",
        "class_view",
        "state_view",
        "dataflow_view",
        "sequence_view",
        "context_view",
    }
    formats = {"svg", "png", "pdf"}

    def emit(self, vm: ViewModel) -> str:
        rank = "TB" if vm.view_type == "sequence_view" else "LR"
        lines = [f"digraph G {{", f"  rankdir={rank};"]
        for el in vm.elements:
            shape = "ellipse" if el.kind == "actor" or el.external else "box"
            lines.append(f'  {el.id} [label="{_q(el.name)}", shape={shape}];')
        for rel in _ordered_rels(vm):
            label = _q(rel.label or rel.kind)
            lines.append(f'  {rel.frm} -> {rel.to} [label="{label}"];')
        lines.append("}")
        return "\n".join(lines) + "\n"


@register_adapter
class NomnomlAdapter:
    id = "nomnoml"
    supports = {
        "component_view",
        "class_view",
        "sequence_view",
        "context_view",
        "dataflow_view",
        "state_view",
        "deployment_view",
    }
    formats = {"svg", "png"}

    def emit(self, vm: ViewModel) -> str:
        lines = ["#direction: right"]
        for g in vm.groups:
            inner = " | ".join(f"[{eid}]" for eid in g.contains)
            lines.append(f"[<{g.kind}> {_q(g.name)} | {inner}]")
        grouped = {eid for g in vm.groups for eid in g.contains}
        for el in vm.elements:
            if el.id not in grouped:
                stereo = el.kind if el.kind != "component" else "component"
                lines.append(f"[<{stereo}> {_q(el.name)}|{el.id}]")
        for rel in _ordered_rels(vm):
            label = rel.label or rel.kind
            lines.append(f"[{rel.frm}]->{label}[{rel.to}]")
        return "\n".join(lines) + "\n"


@register_adapter
class ExcalidrawAdapter:
    id = "excalidraw"
    supports = {
        "component_view",
        "deployment_view",
        "dataflow_view",
        "context_view",
        "sequence_view",
        "class_view",
        "state_view",
    }
    formats = {"svg", "png"}

    def emit(self, vm: ViewModel) -> str:
        import json

        elements = []
        positions: dict[str, tuple[int, int]] = {}
        for i, el in enumerate(vm.elements):
            x = 80 + (i % 4) * 280
            y = 80 + (i // 4) * 160
            positions[el.id] = (x, y)
            elements.append(
                {
                    "id": el.id,
                    "type": "rectangle",
                    "x": x,
                    "y": y,
                    "width": 220,
                    "height": 80,
                    "angle": 0,
                    "strokeColor": "#1e1e1e",
                    "backgroundColor": "#a5d8ff",
                    "fillStyle": "solid",
                    "strokeWidth": 2,
                    "roughness": 1,
                    "opacity": 100,
                    "text": el.name,
                    "label": {"text": el.name},
                }
            )
        for rel in _ordered_rels(vm):
            if rel.frm not in positions or rel.to not in positions:
                continue
            x1, y1 = positions[rel.frm]
            x2, y2 = positions[rel.to]
            elements.append(
                {
                    "id": rel.id,
                    "type": "arrow",
                    "x": x1 + 220,
                    "y": y1 + 40,
                    "width": max(40, x2 - x1 - 220),
                    "height": (y2 + 40) - (y1 + 40),
                    "strokeColor": "#1e1e1e",
                    "label": {"text": rel.label or rel.kind},
                    "start": {"id": rel.frm},
                    "end": {"id": rel.to},
                }
            )
        payload = {
            "type": "excalidraw",
            "version": 2,
            "source": "task2view",
            "elements": elements,
        }
        return json.dumps(payload, indent=2) + "\n"


@register_adapter
class BpmnAdapter:
    id = "bpmn"
    supports = {
        "dataflow_view",
        "sequence_view",
        "component_view",
        "context_view",
        "class_view",
        "state_view",
        "deployment_view",
    }
    formats = {"svg", "png"}

    def emit(self, vm: ViewModel) -> str:
        tasks = []
        for el in vm.elements:
            tasks.append(f'    <task id="{el.id}" name="{_q(el.name)}"/>')
        flows = []
        for rel in _ordered_rels(vm):
            name = _q(rel.label or rel.kind)
            flows.append(
                f'    <sequenceFlow id="{rel.id}" sourceRef="{rel.frm}" '
                f'targetRef="{rel.to}" name="{name}"/>'
            )
        body = "\n".join(tasks + flows)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" '
            'id="Defs" targetNamespace="https://task2view.local">\n'
            '  <process id="P1" isExecutable="false">\n'
            f"{body}\n"
            "  </process>\n"
            "</definitions>\n"
        )
