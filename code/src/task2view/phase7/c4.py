"""ADR-007 step 4 — render an ArchView as C4-PlantUML: parts inside the system boundary, layers top to
bottom, arrows labelled with intent and protocol, dependencies against the layering dashed and red."""

from __future__ import annotations

import re

from task2view.contracts.architecture import ArchView

_RANK = {"web_client": 0, "ui": 0, "api": 1, "job": 1, "service": 2, "integration": 3, "domain": 3, "data_access": 4}


def _q(text: str) -> str:
    return text.replace('"', "'")


_LAYER_OF = {"web_client": "Presentation", "ui": "Presentation", "api": "Presentation", "presentation": "Presentation",
             "job": "Application", "service": "Application", "integration": "Application", "application": "Application",
             "domain": "Domain", "data_access": "Data access"}


def _text(part) -> str:
    """The box text: what the part does, a few of its classes (the rest are in the view's JSON), and the
    request's subjects it answers."""
    examples = ", ".join(part.examples) + (", …" if len(part.members) + len(part.files) > len(part.examples) else "")
    answers = ("answers: " + "; ".join(part.answers[:2]) + ("; …" if len(part.answers) > 2 else "")) if part.answers else ""
    return "\\n".join(x for x in (part.description, examples, answers) if x)


def _alias(pid: str) -> str:
    return re.sub(r"\W", "_", pid)


def render_c4(view: ArchView, system: str, *, by_layer: bool = False) -> str:
    """``by_layer``: group the parts in layer boundaries (decomposition views: containment, no arrows)."""
    lines = ["@startuml", "!include <C4/C4_Component>", "LAYOUT_TOP_DOWN()",
             'AddRelTag("against", $textColor="#A32D2D", $lineColor="#A32D2D", $lineStyle=DashedLine(), '
             '$legendText="dependency against the layering (found in code)")',
             'AddElementTag("focus", $bgColor="#FAC775", $fontColor="#412402", $borderColor="#854F0B", '
             '$legendText="the part being changed")',
             f"title {_q(view.title)}", "", f'System_Boundary(app, "{_q(system)}") {{']
    inside = sorted((p for p in view.parts if p.role != "database"), key=lambda p: _RANK.get(p.role, 9))

    def component(p, indent):
        tag = ', $tags="focus"' if p.id in view.focus else ""
        return f'{indent}Component({_alias(p.id)}, "{_q(p.name)}", "{_q(p.technology)}", "{_q(_text(p))}"{tag})'

    if by_layer:
        layers: dict[str, list] = {}
        for p in inside:
            layers.setdefault(_LAYER_OF.get(p.role, "Other"), []).append(p)
        for k, (layer, parts) in enumerate(layers.items()):
            lines.append(f'  Boundary(layer{k}, "{layer}") {{')
            lines += [component(p, "    ") for p in parts]
            lines.append("  }")
    else:
        lines += [component(p, "  ") for p in inside]
    lines.append("}")
    for p in view.parts:
        if p.role == "database":
            lines.append(f'ComponentDb({_alias(p.id)}, "{_q(p.name)}", "{_q(p.technology)}", "{_q(_text(p))}")')
    lines.append("")
    for c in view.connectors:
        tag = ', $tags="against"' if c.against_layering else ""
        proto = f', "{_q(c.protocol)}"' if c.protocol else ""
        lines.append(f'Rel({_alias(c.source)}, {_alias(c.target)}, "{_q(c.label)}"{proto}{tag})')
    lines += ["", "SHOW_LEGEND()", "@enduml"]
    return "\n".join(lines) + "\n"


def readability(view: ArchView) -> dict:
    """Counts behind the 'readable?' check (crossings need the laid-out drawing and are measured separately)."""
    method_like = re.compile(r"\b[a-z]+[A-Z]\w*\(|\bget[A-Z]|\bset[A-Z]|\bfind[A-Z]")
    return {"boxes": len(view.parts), "arrows": len(view.connectors),
            "method_names_on_arrows": sum(bool(method_like.search(c.label)) for c in view.connectors),
            "against_layering": sum(c.against_layering for c in view.connectors),
            "omitted_relations": len(view.omitted),
            "classes_behind_boxes": sum(len(p.members) for p in view.parts)}
