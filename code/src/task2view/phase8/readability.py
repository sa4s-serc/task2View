"""ADR-007 D4 — "readable?" and "matches its spec?", by rules, for views built by the abstraction step.

Rules (evidence in reports/Realistic architecture diagram generation.md; thresholds are proposals to
calibrate beyond the pilot):
- no method names on arrows (error);
- edge crossings in the laid-out graph (Graphviz, same engine family as PlantUML) above max(1, 10% of
  the arrows) (warning);
- box text: description of at most 12 words (warning);
- a UML diagram frame whose heading names the diagram kind (UML 2.5.1 Annex A) (warning);
- spec conformance: coarse views have at most 6 parts; medium and coarse views do not show single
  classes as parts; feature views include where requests enter; decomposition views have no arrows,
  other views have at least one when they show two or more parts.
"""

from __future__ import annotations

import re
import shutil
import subprocess

from task2view.contracts.architecture import ArchView

_METHOD = re.compile(r"\b[a-z]+[A-Z]\w*\(|\bget[A-Z]|\bset[A-Z]|\bfind[A-Z]|\bgetInstance\b")
_ENTRY_ROLES = {"ui", "api", "web_client", "job", "presentation"}


def crossings(view: ArchView) -> int | None:
    """Edge crossings after a top-down layered layout of the parts; None when Graphviz is missing."""
    if shutil.which("dot") is None or len(view.connectors) < 2:
        return None if shutil.which("dot") is None else 0
    ids = {p.id: f"n{i}" for i, p in enumerate(view.parts)}
    src = ["digraph G { rankdir=TB; node [shape=box];"] + [f'{n} [label="{n}"];' for n in ids.values()]
    src += [f"{ids[c.source]} -> {ids[c.target]};" for c in view.connectors]
    out = subprocess.run(["dot", "-Tplain"], input="\n".join(src + ["}"]), capture_output=True, text=True).stdout
    lines = []
    for row in out.splitlines():
        parts = row.split()
        if parts and parts[0] == "edge":
            n = int(parts[3])
            pts = [(float(parts[4 + 2 * k]), float(parts[5 + 2 * k])) for k in range(n)]
            lines.append((parts[1], parts[2], pts))
    count = 0
    for i, (a1, b1, p1) in enumerate(lines):
        for a2, b2, p2 in lines[i + 1:]:
            if {a1, b1} & {a2, b2}:
                continue  # arrows sharing a box meet there, which is not a crossing
            if any(_intersect(p1[k], p1[k + 1], p2[m], p2[m + 1]) for k in range(len(p1) - 1) for m in range(len(p2) - 1)):
                count += 1
    return count


def _intersect(p, q, r, s) -> bool:
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = orient(r, s, p), orient(r, s, q), orient(p, q, r), orient(p, q, s)
    return d1 * d2 < 0 and d3 * d4 < 0


def check(view: ArchView, source: str, *, viewpoint_id: str, spec) -> tuple[list[dict], dict]:
    findings, n_arrows = [], len(view.connectors)
    for c in view.connectors:
        if _METHOD.search(c.label):
            findings.append({"check": "labels", "severity": "error", "mark": c.source,
                             "message": f"arrow label {c.label!r} is a method name, not an intent"})
    cross = crossings(view)
    if cross is not None and cross > max(1, round(0.1 * n_arrows)):
        findings.append({"check": "crossings", "severity": "warning", "mark": "view",
                         "message": f"{cross} crossing arrows in the layered layout"})
    for p in view.parts:
        if len(p.description.split()) > 12:
            findings.append({"check": "box text", "severity": "warning", "mark": p.id,
                             "message": f"{p.name}: description longer than 12 words"})
    if "mainframe " not in source:
        findings.append({"check": "frame heading", "severity": "warning", "mark": "view",
                         "message": "no UML diagram frame with a heading (UML 2.5.1 Annex A)"})
    # spec conformance
    if spec.granularity == "coarse" and len(view.parts) > 6:
        findings.append({"check": "spec: granularity", "severity": "warning", "mark": "view",
                         "message": f"{len(view.parts)} parts for a coarse view (at most 6)"})
    if spec.granularity in {"coarse", "medium"}:
        for p in view.parts:
            if len(p.members) == 1 and p.role not in {"database", "web_client"} and p.name == p.members[0].rsplit(".", 1)[-1]:
                findings.append({"check": "spec: granularity", "severity": "warning", "mark": p.id,
                                 "message": f"{p.name} is a single class shown as a part"})
    if spec.scope == "feature" and not any(p.role in _ENTRY_ROLES for p in view.parts):
        findings.append({"check": "spec: scope", "severity": "warning", "mark": "view",
                         "message": "the view does not show where requests for this feature enter"})
    if viewpoint_id == "decomposition" and n_arrows:
        findings.append({"check": "spec: view type", "severity": "error", "mark": "view",
                         "message": "a decomposition view shows containment, not arrows"})
    elif viewpoint_id != "decomposition" and len(view.parts) >= 2 and not n_arrows:
        findings.append({"check": "spec: view type", "severity": "warning", "mark": "view", "message": "no arrows between the parts"})
    metrics = {"parts": len(view.parts), "arrows": n_arrows, "crossings": cross,
               "against_layering": sum(c.against_layering for c in view.connectors), "omitted_relations": len(view.omitted),
               "classes_behind_parts": sum(len(p.members) for p in view.parts)}
    return findings, metrics
