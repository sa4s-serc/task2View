"""ADR-007 step 3: abstraction of verified evidence into named parts, and their C4 rendering (no model call)."""

import shutil
import subprocess

import pytest

from task2view.contracts.card import Symbol
from task2view.phase5.abstract import abstract_view, role_of
from task2view.phase7.c4 import readability, render_c4

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


def test_c4_rendering_compiles(view, tmp_path):
    source = render_c4(view, system="java_shop")
    assert source.startswith("@startuml") and "Rel(api, service, " in source
    if shutil.which("plantuml"):
        (tmp_path / "v.puml").write_text(source)
        proc = subprocess.run(["plantuml", "-checkonly", str(tmp_path / "v.puml")], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr


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
