"""ADR-007 D1/D3: one architecture model, each structural view in its own notation.

``choose_notation`` reads knowledge/data/vb/notations.yaml: the viewpoint's notation for a technical
reader, plain boxes and arrows for an overview reader (the role's audience), or the family the person
asked for in the view spec. ``render_arch`` draws an ArchView in that notation:

uml-package     UML package symbols (Graphviz): layers contain parts, parts list their main classes
uml-dependency  PlantUML components with dashed <<use>> dependencies; the changed part highlighted
c4-component    C4-PlantUML components (phase7/c4.py)
boxes           Graphviz boxes and arrows with the parts' names and what they do, nothing technical
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

import yaml

from task2view.contracts.architecture import ArchView
from task2view.phase7.c4 import _LAYER_OF, _RANK, _q, _text, render_c4
from task2view.phase7.c4 import _alias as _c4_alias

_FOCUS, _AGAINST = "#FAC775", "#A32D2D"


def _alias(pid: str) -> str:
    return "p_" + _c4_alias(pid)  # never a keyword (a part id may be "database", "component", ...)


@lru_cache(maxsize=1)
def notation_table() -> dict:
    path = resources.files("task2view.knowledge.data").joinpath("vb", "notations.yaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def choose_notation(viewpoint_id: str, audience: str = "technical", preference: str = "auto") -> str:
    table = notation_table()
    if preference != "auto":
        family = table["families"][preference]
        return family.get(viewpoint_id, family["default"])
    if audience == "overview":
        return table["overview"]
    return table["technical"].get(viewpoint_id, "c4-component")


def language_of(notation: str) -> str:
    return notation_table()["notations"][notation]["language"]


def _dashed(c) -> str:
    return f".[{_AGAINST}].>" if c.against_layering else "..>"


def _ordered(view: ArchView) -> list:
    return sorted((p for p in view.parts if p.role != "database"), key=lambda p: _RANK.get(p.role, 9))


def _legend(lines: list[str], rows: list[str]) -> None:
    lines += ["legend right", *rows, "endlegend"]


def render_uml_package(view: ArchView, system: str) -> str:
    """UML package symbols (tabbed boxes) listing their main classes, one band per layer, stacked top to
    bottom. Drawn with Graphviz, which keeps the layers in rows (PlantUML's nested packages drift)."""
    lines = ["digraph view {", "  rankdir=TB; newrank=true; labelloc=t; fontname=Helvetica; fontsize=16; nodesep=0.3; ranksep=0.35;",
             f"  label=<<b>{_html(view.title)}</b>>;",
             '  node [shape=tab, style=filled, fillcolor="#F1EFE8", color="#444441", fontname=Helvetica, fontsize=11];',
             '  edge [color="#444441", style=dashed, fontname=Helvetica, fontsize=10];',
             f'  subgraph cluster_system {{ label=<<b>{_html(system)}</b>>; style=rounded; color="#444441";']
    layers: dict[str, list] = {}
    for p in _ordered(view):
        layers.setdefault(_LAYER_OF.get(p.role, "Other"), []).append(p)
    for k, (layer, parts) in enumerate(layers.items()):
        lines.append(f'    subgraph cluster_layer{k} {{ label=<<i>«layer»</i> {_html(layer)}>; style="dashed"; color="#888780";')
        for p in parts:
            more = len(p.members) + len(p.files) - len(p.examples)
            classes = "".join(f"<br/>{_html(ex)}" for ex in p.examples) + (f"<br/><i>… {more} more</i>" if more > 0 else "")
            desc = f'<br/><font point-size="9">{_html(p.description)}</font>' if p.description else ""
            lines.append(f'      {_alias(p.id)} [label=<<b>{_html(p.name)}</b>{desc}<font point-size="10">{classes}</font>>];')
        lines.append("    }")
    lines.append("  }")
    for p in view.parts:
        if p.role == "database":
            lines.append(f'  {_alias(p.id)} [shape=cylinder, label=<<b>{_html(p.name)}</b><br/>{_html(p.technology)}>];')
    rows = list(layers.values())
    for upper, lower in zip(rows, rows[1:]):  # one row per layer, in layer order
        lines += [f"  {_alias(a.id)} -> {_alias(lower[0].id)} [style=invis];" for a in upper]
    lines += ["  { rank=same; " + " ".join(_alias(p.id) for p in row) + " }" for row in rows]
    for c in view.connectors:  # layered views: allowed-to-use; decomposition views have none
        color = f', color="{_AGAINST}", fontcolor="{_AGAINST}"' if c.against_layering else ""
        lines.append(f'  {_alias(c.source)} -> {_alias(c.target)} [label=<{_html(c.label)}>{color}];')
    lines += ['  subgraph cluster_legend { label="Legend"; fontsize=10; style=dashed; color="#B4B2A9";',
              '    lg_layer [shape=plaintext, label="dashed frame = layer", fontsize=9];',
              '    lg_pkg [label="part (UML package) with its main classes", fontsize=9]; }', "}"]
    return "\n".join(lines) + "\n"


def render_uml_dependency(view: ArchView, system: str) -> str:
    lines = ["@startuml", f"title {_q(view.title)}", "top to bottom direction", "skinparam componentStyle uml2",
             "skinparam shadowing false", "", f'package "{_q(system)}" {{']
    for p in _ordered(view):
        color = f" {_FOCUS}" if p.id in view.focus else ""
        lines.append(f'  component "{_q(p.name)}\\n----\\n{_q(_text(p))}" as {_alias(p.id)} <<{p.role}>>{color}')
    lines.append("}")
    for p in view.parts:
        if p.role == "database":
            lines.append(f'database "{_q(p.name)}\\n<size:10>{_q(p.technology)}</size>" as {_alias(p.id)}')
    for c in view.connectors:
        lines.append(f"{_alias(c.source)} {_dashed(c)} {_alias(c.target)} : <<use>>")
    _legend(lines, ["dashed arrow <<use>> = the source needs the target to be correct (V&B uses relation)",
                    *([f"<back:{_FOCUS}>highlighted</back> = the part being changed"] if view.focus else []),
                    *(["<color:#A32D2D>red arrow</color> = dependency against the layering"]
                      if any(c.against_layering for c in view.connectors) else [])])
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def _html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_boxes(view: ArchView, system: str) -> str:
    """Plain boxes and arrows for overview readers: names, what each part does, what each arrow is for."""
    lines = ["digraph view {", "  rankdir=TB; labelloc=t; fontname=Helvetica; fontsize=16;",
             f'  label=<<b>{_html(view.title)}</b>>;',
             '  node [shape=box, style="rounded,filled", fillcolor="#E6F1FB", color="#185FA5", fontname=Helvetica, '
             'fontsize=12, margin="0.2,0.1"];',
             '  edge [color="#444441", fontname=Helvetica, fontsize=10];',
             f'  subgraph cluster_system {{ label=<{_html(system)}>; style="rounded,dashed"; color="#888780";']
    for p in _ordered(view):
        fill = f', fillcolor="{_FOCUS}"' if p.id in view.focus else ""
        desc = f'<br/><font point-size="10">{_html(p.description)}</font>' if p.description else ""
        lines.append(f'    {_alias(p.id)} [label=<<b>{_html(p.name)}</b>{desc}>{fill}];')
    lines.append("  }")
    for p in view.parts:
        if p.role == "database":
            lines.append(f'  {_alias(p.id)} [shape=cylinder, label=<<b>{_html(p.name)}</b>>, fillcolor="#F1EFE8"];')
    for c in view.connectors:
        lines.append(f'  {_alias(c.source)} -> {_alias(c.target)} [label=<{_html(c.label)}>];')
    lines += ['  subgraph cluster_legend { label="Legend"; fontsize=10; style=dashed; color="#B4B2A9";',
              '    lg_box [label="part of the system", fontsize=9];',
              '    lg_db [shape=cylinder, label="stored data", fontsize=9, fillcolor="#F1EFE8"];',
              '    lg_box -> lg_db [label="uses", fontsize=9]; }', "}"]
    return "\n".join(lines) + "\n"


def render_arch(view: ArchView, system: str, notation: str) -> str:
    if notation == "uml-package":
        return render_uml_package(view, system)
    if notation == "uml-dependency":
        return render_uml_dependency(view, system)
    if notation == "boxes":
        return render_boxes(view, system)
    return render_c4(view, system)


def has_title_and_legend(source: str, notation: str) -> bool:
    if notation in {"boxes", "uml-package"}:
        return "labelloc=t" in source and "cluster_legend" in source
    if notation == "c4-component":
        return "title " in source and "SHOW_LEGEND" in source
    return "title " in source and "legend" in source and "endlegend" in source
