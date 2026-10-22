"""ADR-008: draw an ArchView (parts with their classes, connectors lifted from code) as a UML 2.5.1 diagram in
PlantUML. Rules from knowledge/data/uml/uml-2.5.1.yaml:

package diagram (decomposition, layered, uses; 12.2.4)
    parts are packages with their main classes drawn inside (members inside the folder, the name in the tab);
    decomposition and layered views nest them in layer packages. Uses and layered views add «use»
    dependencies between parts (7.7.4); the part being changed is marked with a comment (7.2.4).
component diagram (component-and-connector styles; 11.6.4, 11.6.5)
    parts are components; the classes behind a part are listed in a 'realizations' compartment. Arrows are
    dependencies (dashed, client to supplier) named by intent, with the protocol as a property in braces.

Every diagram has a frame whose heading names its kind (Annex A: pkg, cmp). Stereotypes are the Standard
Profile's «Entity» for the domain model and the Task2View profile's «layer» and «database».
Diagram sources replace the earlier C4-PlantUML rendering (ADR-007), removed by ADR-008.
"""

from __future__ import annotations

import re

from task2view.contracts.architecture import ArchView

_RANK = {"web_client": 0, "ui": 0, "presentation": 0, "api": 1, "job": 1, "service": 2, "application": 2,
         "integration": 3, "domain": 3, "data_access": 4}  # coarse parts carry the layer as their role
_LAYER_OF = {"web_client": "Presentation", "ui": "Presentation", "api": "Presentation", "presentation": "Presentation",
             "job": "Application", "service": "Application", "integration": "Application", "application": "Application",
             "domain": "Domain", "data_access": "Data access"}
_STEREO = {"domain": "Entity", "database": "database"}  # Standard Profile «Entity» (Table 22.1); Task2View «database»
LAYERED_VIEWS = {"decomposition", "layered"}  # package diagrams with layers
PACKAGE_VIEWS = LAYERED_VIEWS | {"uses"}  # the catalogue's uml-package viewpoints


def _q(text: str) -> str:
    return text.replace('"', "'")


def _alias(pid: str) -> str:
    return "p_" + re.sub(r"\W", "_", pid)  # never a PlantUML keyword (a part id may be "database", "component", …)


def _text(part) -> str:
    """What a part does, a few of its classes (the rest are in architecture.json), and the request's subjects
    it answers; used in the view's JSON and the traceability table."""
    examples = ", ".join(part.examples) + (", …" if len(part.members) + len(part.files) > len(part.examples) else "")
    answers = ("answers: " + "; ".join(part.answers[:2]) + ("; …" if len(part.answers) > 2 else "")) if part.answers else ""
    return "\\n".join(x for x in (part.description, examples, answers) if x)


def _ordered(view: ArchView) -> list:
    return sorted((p for p in view.parts if p.role != "database"), key=lambda p: _RANK.get(p.role, 9))


def _layers(view: ArchView) -> dict[str, list]:
    layers: dict[str, list] = {}
    for p in _ordered(view):
        layers.setdefault(_LAYER_OF.get(p.role, "Other"), []).append(p)
    return layers


def _more(p) -> int:
    return len(p.members) + len(p.files) - len(p.examples)


def _header(kind: str, view: ArchView) -> list[str]:
    return ["@startuml", f"mainframe {kind} {_q(view.title)}", "skinparam shadowing false", "hide empty members",
            "hide circle", "top to bottom direction"]


def _package(p, indent: str, focus: bool) -> list[str]:
    stereo = f" <<{_STEREO[p.role]}>>" if p.role in _STEREO and p.role != "domain" else ""
    ids = [f"{_alias(p.id)}_{i}" for i in range(len(p.examples))]
    out = [f'{indent}package "{_q(p.name)}" as {_alias(p.id)}{stereo} {{']
    out += [f'{indent}  class "{_q(ex)}" as {a}' for ex, a in zip(p.examples, ids)]
    notes = ([f"and {_more(p)} more"] if _more(p) > 0 else []) + (["the part being changed"] if focus else [])
    if notes:  # comments, not classes: the full member list is in architecture.json
        out.append(f'{indent}  note "{" / ".join(notes)}" as {_alias(p.id)}_note')
    out += [f"{indent}  {a} -[hidden]right- {b}" for a, b in zip(ids, ids[1:])]  # members in one row
    out.append(f"{indent}}}")
    return out


def render_package(view: ArchView, system: str, *, layers: bool, arrows: bool = True) -> str:
    """``layers``: parts nested in layer packages, stacked top to bottom (decomposition, layered); otherwise
    the parts side by side with their «use» dependencies (uses)."""
    lines = _header("pkg", view) + [""]
    groups = _layers(view) if layers else {"": _ordered(view)}
    for k, (layer, parts) in enumerate(groups.items()):
        indent = "  " if layer else ""
        if layer:
            lines.append(f'package "{layer}" as layer{k} <<layer>> {{')
        for p in parts:
            lines += _package(p, indent, p.id in view.focus)
        if layer:
            lines.append("}")
    # a database is not a module, so a package view does not draw it (component and deployment views do)
    if layers:  # layers stacked top to bottom: hidden links from every member of a layer to every member of the next
        rows = [[f"{_alias(p.id)}_{i}" for p in parts for i in range(len(p.examples))] for parts in groups.values()]
        lines += [f"{a} -[hidden]-> {b}" for upper, lower in zip(rows, rows[1:]) for a in upper for b in lower]
    drawn = {p.id for p in view.parts if p.role != "database"}
    for c in view.connectors if arrows else []:  # decomposition views show containment only
        if c.source in drawn and c.target in drawn:
            lines.append(_dependency(c, "<<use>>"))
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def _component(p, focus: bool) -> list[str]:
    stereo = f" <<{_STEREO[p.role]}>>" if p.role in _STEREO else ""
    body = [_q(p.name)]
    if p.description:
        body += ["--", _q(p.description)]
    if p.examples:
        body += ["..realizations..", _q(", ".join(p.examples) + (f", … {_more(p)} more" if _more(p) > 0 else ""))]
    elif p.technology:
        body += ["--", _q(p.technology)]
    out = [f"component {_alias(p.id)}{stereo} [", *body, "]"]
    if focus:
        out += [f"note right of {_alias(p.id)} : the part being changed"]
    return out


def _dependency(c, label: str) -> str:
    color = "[#A32D2D]" if c.against_layering else ""
    constraint = " {against the layering}" if c.against_layering else ""
    return f"{_alias(c.source)} .{color}.> {_alias(c.target)} : {label}{constraint}"


def render_component(view: ArchView, system: str) -> str:
    lines = _header("cmp", view) + ["skinparam componentStyle uml2", "", f'package "{_q(system)}" as system {{']
    for p in _ordered(view):
        lines += ["  " + line for line in _component(p, p.id in view.focus)]
    lines.append("}")
    for p in view.parts:
        if p.role == "database":
            lines += _component(p, False)
    for c in view.connectors:
        proto = f" {{{_q(c.protocol)}}}" if c.protocol else ""
        lines.append(_dependency(c, f"{_q(c.label)}{proto}"))
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def render_arch(view: ArchView, system: str, viewpoint_id: str) -> str:
    if viewpoint_id in PACKAGE_VIEWS:
        return render_package(view, system, layers=viewpoint_id in LAYERED_VIEWS, arrows=viewpoint_id != "decomposition")
    return render_component(view, system)


def readability(view: ArchView) -> dict:
    """Counts behind the 'readable?' check (crossings need the laid-out drawing and are measured separately)."""
    method_like = re.compile(r"\b[a-z]+[A-Z]\w*\(|\bget[A-Z]|\bset[A-Z]|\bfind[A-Z]")
    return {"boxes": len(view.parts), "arrows": len(view.connectors),
            "method_names_on_arrows": sum(bool(method_like.search(c.label)) for c in view.connectors),
            "against_layering": sum(c.against_layering for c in view.connectors),
            "omitted_relations": len(view.omitted),
            "classes_behind_boxes": sum(len(p.members) for p in view.parts)}
