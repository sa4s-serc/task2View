"""ADR-008: the UML 2.5.1 rules the renderers apply, read from knowledge/data/uml/uml-2.5.1.yaml."""

from __future__ import annotations

from task2view.knowledge.catalog import load_uml, uml_diagram_type


def frame_heading(model_kind: str, name: str) -> str:
    """Annex A: a diagram frame's heading is [<kind>]<name>, the kind in its short form (pkg, cmp, sd, …)."""
    diagram = uml_diagram_type(model_kind)
    if diagram is None:
        raise ValueError(f"{model_kind!r} is not a UML diagram type (ADR-008)")
    return f"{load_uml()['diagram_types'][diagram]['frame']} {name}"


def allowed_stereotype(name: str, metaclass: str) -> bool:
    """A stereotype a view may show on an element of this metaclass: a keyword of the notation clauses, a
    Standard Profile stereotype that applies to it (Table 22.1), or one of the Task2View profile's."""
    uml = load_uml()
    if name in uml["keywords"]:
        return True
    for table in ("standard_stereotypes", "task2view_profile"):
        applies = uml[table].get(name) or uml[table].get(name[:1].upper() + name[1:])
        if applies:
            applies = applies if isinstance(applies, list) else [applies]
            if metaclass in applies or "Classifier" in applies and metaclass in {"Class", "Component", "Interface"}:
                return True
    return False


def stereotype(name: str | None, metaclass: str) -> str:
    """`` <<name>>`` when UML allows it on this metaclass, else nothing (the view's JSON keeps the role)."""
    if not name:
        return ""
    standard = {k.lower(): k for k in load_uml()["standard_stereotypes"]}
    shown = standard.get(name.lower(), name)
    return f" <<{shown}>>" if allowed_stereotype(shown, metaclass) else ""
