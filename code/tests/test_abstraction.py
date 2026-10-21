"""ADR-007 step 3: abstraction of verified evidence into named parts; ADR-008: their UML rendering (no model call)."""

import shutil
import subprocess

import pytest

from task2view.contracts.card import Symbol
from task2view.phase5.abstract import abstract_view, role_of
from task2view.phase7.uml_arch import readability, render_arch

from .test_run_v2 import result  # noqa: F401  (scripted end-to-end run on the java_shop fixture)


def _sym(name, package="com.x", **kw):
    return Symbol(id=f"{package}.{name}", name=name, kind=kw.pop("kind", "class"), file=f"src/{name}.java",
                  start_line=1, end_line=9, language="java", package=package, **kw)


@pytest.mark.parametrize("sym,entries,entities,role", [
    (_sym("OrderController", annotations=["RestController"]), {}, set(), "api"),
    (_sym("OrderService", annotations=["Service"]), {}, set(), "service"),
    (_sym("ReportService", package="app.Entity"), {}, set(), "service"),       # name beats package
    (_sym("PersistenceService", package="app.Database"), {}, set(), "data_access"),
    (_sym("OrderRegistry", package="app.entity"), {}, set(), "data_access"),
    (_sym("Order", package="app.entity"), {}, {"app.entity.Order"}, "domain"),
    (_sym("OrderDTO"), {}, set(), "helper"),
    (_sym("Registration", package="app.boundary.Swing"), {"app.boundary.Swing.Registration": {"main"}}, set(), "ui"),
    (_sym("ShopApplication"), {"com.x.ShopApplication": {"main"}}, set(), "bootstrap"),  # start-up only as last resort
    (_sym("MailGateway"), {}, set(), "integration"),
])
def test_roles_follow_general_conventions(result, sym, entries, entities, role):  # noqa: F811
    assert role_of(sym, result.card, {k: set(v) for k, v in entries.items()}, entities) == role


@pytest.fixture(scope="module")
def view(result):  # noqa: F811
    return abstract_view(result.card, result.aem, target="order payment")


def test_parts_are_roles_with_their_classes(view):
    roles = {p.role for p in view.parts}
    assert {"api", "service", "domain", "data_access"} <= roles
    api = next(p for p in view.parts if p.role == "api")
    assert api.name == "REST API" and "com.shop.web.OrderController" in api.members
    assert all(p.members or p.files for p in view.parts)


def test_connectors_are_lifted_from_code_and_follow_the_layers(view):
    pairs = {(c.source, c.target) for c in view.connectors}
    assert ("api", "service") in pairs and ("service", "data_access") in pairs
    assert all(c.weight > 0 and c.evidence for c in view.connectors)
    assert readability(view)["method_names_on_arrows"] == 0


def _compiles(source, tmp_path):
    if shutil.which("plantuml"):
        (tmp_path / "v.puml").write_text(source)
        proc = subprocess.run(["plantuml", "-checkonly", str(tmp_path / "v.puml")], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize("viewpoint,frame", [("client-server", "cmp"), ("decomposition", "pkg"), ("uses", "pkg")])
def test_uml_rendering_compiles_with_a_frame(view, tmp_path, viewpoint, frame):
    v = view.model_copy(deep=True)
    v.focus = [v.parts[0].id]
    v.connectors[0].against_layering = True  # the constraint and colour must compile too
    source = render_arch(v, "java_shop", viewpoint)
    assert source.startswith("@startuml") and f"mainframe {frame} " in source
    assert "!include" not in source and "Rel(" not in source  # no C4 macros
    if viewpoint == "decomposition":
        assert ".>" not in source  # containment, no dependencies
    elif viewpoint == "uses":
        assert "<<use>>" in source
    else:
        assert "p_api .> p_service" in source.replace("..>", ".>") or "p_api ..> p_service" in source
    _compiles(source, tmp_path)


def test_naming_checks_names_and_splits(view, result):  # noqa: F811
    from task2view.agents.runtime import AgentRuntime
    from task2view.phase5.abstract import name_parts

    svc = next(p for p in view.parts if p.role == "service")
    members = [result.card.symbols[m].name for m in svc.members]
    helper_only = [m for m in members if m.endswith(("Gateway", "DTO"))] or members[-1:]
    reply = {"parts": [{"id": "domain", "name": "Order", "description": "x"},  # a class name for a multi-class part: rejected
                       {"id": "api", "name": "Order API", "description": "receives payment requests"}],
             "splits": [{"id": "service", "into": [{"name": "Payment flow", "members": [m for m in members if m not in helper_only]},
                                                   {"name": "Data types", "members": helper_only}]}]}
    named = name_parts(view.model_copy(deep=True), result.card, result.aem,
                       AgentRuntime(generate=lambda p, model=None: reply), goal="g", max_parts=3)
    assert next(p for p in named.parts if p.role == "domain").name == "Domain model"
    assert next(p for p in named.parts if p.role == "api").name == "Order API"
    assert sum(p.role == "service" for p in named.parts) == 1 and any("split" in n for n in named.notes)


def test_interaction_wording_keeps_behaviour_and_defaults_cannot_remove_it():
    from task2view.knowledge.catalog import load_catalog
    from task2view.phase1.needs import validate_needs, apply_clarifications

    cat = load_catalog()
    goal = ("I need to understand the main components and how they interact with each other, "
            "and which parts are affected by a change.")
    overview = validate_needs(goal, {"needs": [{"need": "collaboration", "evidence": "how they interact with each other"}]}, cat)
    assert overview.detail_level == "overview" and overview.spec.behaviour == "structure"  # concise: one view
    raw = {"needs": [{"need": "collaboration", "evidence": "how they interact with each other", "salience": "primary"},
                     {"need": "change-impact", "evidence": "which parts are affected by a change", "salience": "primary"}],
           "clarifications": [{"field": "behaviour", "question": "Order of calls too?", "default": "structure"}]}
    profile = validate_needs(goal, raw, cat)
    assert profile.spec.behaviour == "both"
    log = apply_clarifications(profile, cat)
    assert profile.spec.behaviour == "both" and "kept both" in log[0]
    assert any(n.need == "interaction-order" and n.salience == "primary" for n in profile.needs)


def test_uses_view_centres_on_the_part_being_changed(view, result):  # noqa: F811
    from task2view.phase5.abstract import shape_for_viewpoint

    v = view.model_copy(deep=True)
    shape_for_viewpoint(v, "uses", result.aem, set())
    assert v.focus and all(c.target in {p.id for p in v.parts} for c in v.connectors)
    assert any(c.label == "depends on" for c in v.connectors) or not v.connectors
