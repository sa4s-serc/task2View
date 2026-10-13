"""ADR-007 step 4 — render an ArchView as C4-PlantUML: parts inside the system boundary, layers top to
bottom, arrows labelled with intent and protocol, dependencies against the layering dashed and red."""

from __future__ import annotations

import re

from task2view.contracts.architecture import ArchView

_RANK = {"web_client": 0, "ui": 0, "api": 1, "job": 1, "service": 2, "integration": 3, "domain": 3, "data_access": 4}


def _q(text: str) -> str:
    return text.replace('"', "'")


def _alias(pid: str) -> str:
    return re.sub(r"\W", "_", pid)


def render_c4(view: ArchView, system: str) -> str:
    lines = ["@startuml", "!include <C4/C4_Component>", "LAYOUT_TOP_DOWN()",
             'AddRelTag("against", $textColor="#A32D2D", $lineColor="#A32D2D", $lineStyle=DashedLine(), '
             '$legendText="dependency against the layering (found in code)")',
             f"title {_q(view.title)}", "", f'System_Boundary(app, "{_q(system)}") {{']
    inside = sorted((p for p in view.parts if p.role != "database"), key=lambda p: _RANK.get(p.role, 9))
    for p in inside:
        lines.append(f'  Component({_alias(p.id)}, "{_q(p.name)}", "{_q(p.technology)}", "{_q(p.description)}")')
    lines.append("}")
    for p in view.parts:
        if p.role == "database":
            lines.append(f'ComponentDb({_alias(p.id)}, "{_q(p.name)}", "{_q(p.technology)}", "{_q(p.description)}")')
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
