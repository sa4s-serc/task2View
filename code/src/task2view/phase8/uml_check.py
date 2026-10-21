"""Phase 8 — UML 2.5.1 conformance of a diagram (ADR-008), by rules from knowledge/data/uml/uml-2.5.1.yaml.

Works on any PlantUML source, so it also checks diagrams Task2View did not draw (the agent conditions).

- diagram type: the view's model kind gives it; for other sources it is read from the frame heading
  (Annex A) or, failing that, from the primary symbols. C4 macros or non-UML shapes make it "not UML".
- symbols: a shape that is not a UML 2.5.1 symbol at all (the `database` cylinder, `cloud`, ER `entity`,
  C4 macros) — error. A UML symbol of another diagram type (an actor in a component diagram) — warning, since
  Annex A does not strictly enforce the boundaries between diagram types.
- paths: an arrow that is not a path of this diagram type (e.g. a solid association arrow between components,
  where UML draws a dashed dependency or a connector) — warning.
- stereotypes: a «stereotype» outside the notation keywords, the Standard Profile and the Task2View profile —
  warning (UML needs a profile for it, 12.3).
- frame: a frame whose heading names the diagram kind (Annex A) — warning when missing or wrong.
"""

from __future__ import annotations

import re

from task2view.knowledge.catalog import load_uml, uml_diagram_type

# PlantUML element keyword -> UML symbol (None: not a UML 2.5.1 symbol)
_SYMBOL = {"class": "class", "abstract": "class", "interface": "interface", "enum": "enumeration",
           "component": "component", "package": "package", "namespace": "package", "node": "node",
           "artifact": "artifact", "actor": "actor", "usecase": "use-case", "object": "instance",
           "participant": "lifeline", "state": "state", "note": "comment", "port": "port",
           "portin": "port", "portout": "port", "rectangle": "subject",
           "database": None, "cloud": None, "queue": None, "storage": None, "folder": None, "frame": None,
           "card": None, "agent": None, "stack": None, "hexagon": None, "file": None, "collections": None,
           "boundary": None, "control": None, "entity": None, "person": None, "label": None, "circle": None}
_DECL = re.compile(r"^\s*(abstract\s+class|" + "|".join(sorted(_SYMBOL, key=len, reverse=True)) + r")\b(?!\s*(of|right|left|top|bottom|over)\b)")
_C4 = re.compile(r"^\s*(!include\s+<C4|!include.*C4|(Person|System|Container|Component|ComponentDb|Rel|Boundary|"
                 r"System_Boundary|Container_Boundary|Enterprise_Boundary)(_Ext)?\s*\()")
_ARROW = re.compile(r"^\s*([\w.\"\[\]]+)\s*(\"[^\"]*\"\s*)?([.\-=~]*[<>|*o#x+]*[.\-]+(?:\[[^\]]*\])?[.\-]*[<>|*o#x+]*[.\-]*)\s*"
                    r"(\"[^\"]*\"\s*)?([\w.\"\[\]]+)\s*(:.*)?$")
_STEREO = re.compile(r"<<\s*([^>]+?)\s*>>")
_FRAME = re.compile(r"^\s*mainframe\s+(\S+)")
_ACTIVITY = re.compile(r"^\s*(start|stop|end|:.*;|if\s*\(|else|endif|fork|end fork|while|endwhile|repeat|\|.*\|)\s*$")
_FRAGMENT = re.compile(r"^\s*(alt|opt|loop|par|break|critical|group|else|end|ref|neg|assert)\b")


def _path_kind(arrow: str, diagram: str, label: str) -> str:
    dashed = "." in arrow
    if "|>" in arrow or "<|" in arrow:
        return "realization" if dashed else "generalization"
    if "*" in arrow:
        return "composition"
    if re.search(r"(^o|o$)", arrow.strip("-.")) or arrow.startswith("o") or arrow.endswith("o"):
        return "aggregation"
    if diagram == "sequence":
        if ">>" in arrow:
            return "asynchronous-message"
        return "reply-message" if dashed else "synchronous-message"
    if dashed:
        if "include" in label:
            return "include"
        if "extend" in label:
            return "extend"
        if "deploy" in label:
            return "deployment"
        if "manifest" in label:
            return "manifestation"
        return "usage" if "use" in label else "dependency"
    if diagram in {"state-machine"}:
        return "transition"
    if diagram in {"activity"}:
        return "control-flow"
    if diagram == "deployment":
        return "communication-path"
    if diagram in {"communication", "object"}:
        return "link"
    if diagram == "component" and ">" not in arrow and "<" not in arrow:
        return "assembly"  # a connector: solid line between components (11.6.3)
    return "association"


_BY_FRAME = {"act": "activity", "activity": "activity", "cmp": "component", "component": "component",
             "dep": "deployment", "deployment": "deployment", "pkg": "package", "package": "package",
             "stm": "state-machine", "uc": "use-case", "class": "class"}


def infer_diagram(source: str) -> str | None:
    """The UML diagram type of a PlantUML source: from the frame heading (Annex A), else from its primary
    symbols. None for C4-PlantUML or when no UML diagram is recognised."""
    lines = source.splitlines()
    if any(_C4.match(line) for line in lines):
        return None
    frame = next((m.group(1).lower() for m in map(_FRAME.match, lines) if m), None)
    has = set(re.findall(r"^\s*(\w+)", source, re.M))
    if frame in _BY_FRAME:
        return _BY_FRAME[frame]
    if frame in {"sd", "interaction"}:
        return "sequence" if "participant" in has or not "object" in has else "communication"
    if "[*]" in source:
        return "state-machine"
    structural = has & {"usecase", "component", "class", "package", "node", "artifact", "interface", "entity", "rectangle"}
    if "participant" in has or (re.search(r"^\s*\w+\s*->>?\s*\w+\s*:", source, re.M) and not structural):
        return "sequence"
    for diagram, marks in (("use-case", {"usecase"}), ("state-machine", {"state"}), ("deployment", {"node", "artifact"}),
                           ("component", {"component"}), ("class", {"class", "interface", "enum", "abstract"}),
                           ("object", {"object"}), ("package", {"package", "namespace"})):
        if has & marks:
            return diagram
    if "start" in has and re.search(r"^\s*:.*;\s*$", source, re.M):
        return "activity"
    return None


def check_uml(source: str, model_kind: str | None = None) -> tuple[list[dict], dict]:
    """(findings, metrics). ``model_kind``: the view's kind; None infers the diagram type from the source."""
    uml = load_uml()
    diagram = uml_diagram_type(model_kind) if model_kind else infer_diagram(source)
    findings: list[dict] = []
    if diagram is None:
        why = "C4-PlantUML macros" if any(_C4.match(l) for l in source.splitlines()) else "no UML diagram type recognised"
        findings.append({"check": "uml: diagram type", "severity": "error", "mark": "view",
                         "message": f"not a UML 2.5.1 diagram ({why}; Annex A lists the diagram types)"})
        return findings, {"uml_diagram": None, "non_uml_symbols": 0, "non_uml_paths": 0, "non_standard_stereotypes": 0}
    spec = uml["diagram_types"][diagram]
    symbols, paths = set(spec["symbols"]) | {"comment"}, set(spec["paths"]) | {"comment-link"}
    bad_symbols, bad_paths, odd_stereo = [], [], set()
    allowed_stereo = set(uml["keywords"]) | set(uml["standard_stereotypes"]) | set(uml["task2view_profile"])
    allowed_lower = {s.lower() for s in allowed_stereo}
    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith(("'", "@", "!", "skinparam", "hide", "show", "title", "mainframe", "allowmixing",
                                        "top to", "left to", "legend", "endlegend", "end note", "}", "{", "]", "--", "..")):
            continue
        for st in _STEREO.findall(line):
            if st.strip().lower() not in allowed_lower:
                odd_stereo.add(st.strip())
        if diagram == "activity" and _ACTIVITY.match(line):
            continue
        if diagram == "sequence" and (_FRAGMENT.match(line) or line.startswith(("activate", "deactivate", "return", "== ", "...", "|||", "autonumber", "create", "destroy", "box", "end box"))):
            continue
        if _C4.match(line):
            bad_symbols.append(line[:60])
            continue
        m = _DECL.match(line)
        if m:
            kw = m.group(1).split()[0].lower()
            sym = _SYMBOL.get(kw, None)
            if kw == "rectangle" and diagram != "use-case":
                sym = None
            if kw == "object" and diagram in {"communication", "object"}:
                sym = "lifeline" if diagram == "communication" else "instance"
            if kw == "entity" and diagram == "sequence":
                sym = None
            if kw == "state" and diagram == "state-machine":
                sym = "state"
            if sym is None or (sym not in symbols and not (sym == "lifeline" and diagram == "communication")):
                bad_symbols.append(f"{kw} ({line[:50]})")
            continue
        a = _ARROW.match(line)
        if a and a.group(3) and set(a.group(3)) & set("-.") and not line.startswith(("note", "[*]")) or (
                a and line.startswith("[*]")):
            label = (a.group(6) or "").lower()
            kind = _path_kind(re.sub(r"\[[^\]]*\]", "", a.group(3)), diagram, label)
            if "hidden" in a.group(3):
                continue
            if kind not in paths and not (diagram == "state-machine" and kind in {"transition", "association"}):
                bad_paths.append(f"{kind} ({line[:50]})")
    all_symbols = {x for dt in uml["diagram_types"].values() for x in dt["symbols"]}
    for b in bad_symbols:
        sym = b.split(" (")[0]
        other = _SYMBOL.get(sym) in all_symbols and sym != "rectangle"
        findings.append({"check": "uml: symbols", "severity": "warning" if other else "error", "mark": "view",
                         "message": (f"{b}: a UML symbol of another diagram type in a {diagram} diagram" if other else
                                     f"{b}: not a UML 2.5.1 symbol") + f" ({spec['clause']})"})
    for b in bad_paths:
        findings.append({"check": "uml: paths", "severity": "warning", "mark": "view",
                         "message": f"{b}: not a path of a UML {diagram} diagram ({spec['clause']})"})
    for s in sorted(odd_stereo):
        findings.append({"check": "uml: stereotypes", "severity": "warning", "mark": "view",
                         "message": f"«{s}» is not a UML keyword or Standard Profile stereotype (Table 22.1) and no profile defines it"})
    frame = next((_FRAME.match(l) for l in source.splitlines() if _FRAME.match(l)), None)
    if frame is None:
        findings.append({"check": "uml: frame", "severity": "warning", "mark": "view",
                         "message": f"no diagram frame; its heading should name the kind '{spec['frame']}' (Annex A)"})
    elif frame.group(1).lower() not in {spec["frame"], *(k for k, v in uml["frame_kinds"].items() if v == spec["frame"])}:
        findings.append({"check": "uml: frame", "severity": "warning", "mark": "view",
                         "message": f"frame heading kind '{frame.group(1)}' does not match a {diagram} diagram ('{spec['frame']}', Annex A)"})
    metrics = {"uml_diagram": diagram, "non_uml_symbols": len(bad_symbols), "non_uml_paths": len(bad_paths),
               "non_standard_stereotypes": len(odd_stereo)}
    return findings, metrics
