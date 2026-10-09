"""Phase 0 repository card on small synthetic repositories (ADR-006 step 2)."""

from pathlib import Path

import pytest

from task2view.phase0.card import build_card, render_card, repo_facts
from task2view.phase0.corpus import classify

REPOS = Path(__file__).parent / "fixtures" / "repos"


@pytest.fixture(scope="module")
def shop():
    return build_card(REPOS / "java_shop")


@pytest.fixture(scope="module")
def tasks():
    return build_card(REPOS / "py_tasks")


def _edges(card, kind=None):
    return {(e.source, e.target, e.kind) for e in card.edges if kind is None or e.kind == kind}


# ---------------------------------------------------------------- classification

@pytest.mark.parametrize("path,cls", [
    ("src/main/java/a/B.java", "code"),
    ("src/test/java/a/BTest.java", "test"),
    ("pom.xml", "build"),
    ("Dockerfile", "deploy"),
    ("docker-compose.yml", "deploy"),
    ("src/main/resources/META-INF/persistence.xml", "config"),
    ("db/schema.sql", "schema"),
    ("src/main/resources/static/index.html", "web"),
    ("README.md", "docs"),
    ("docs/model.vpp", "model"),
    ("docs/diagram.png", "binary"),
    ("tests/data.json", "test"),
    ("src/test/resources/META-INF/persistence.xml", "test"),
    ("src/main/java/com/x/charts/ChartService.java", "code"),
    ("src/main/java/com/x/MigrationService.java", "code"),
    ("src/main/java/com/x/spec/Specification.java", "code"),
    ("web/src/App.tsx", "code"),
    ("src/main/java/a/Main.form", "other"),
    ("k8s/deployment.yaml", "deploy"),
])
def test_every_file_gets_a_class(path, cls):
    assert classify(path)[0] == cls


# ---------------------------------------------------------------- java

def test_java_symbols_and_kinds(shop):
    s = shop.symbols
    assert s["com.shop.service.PaymentGateway"].kind == "interface"
    assert s["com.shop.domain.OrderStatus"].kind == "enum"
    assert s["com.shop.domain.OrderStatus"].enum_constants == ["NEW", "PAID", "SHIPPED"]
    assert s["com.shop.OrderServiceTest"].is_test


def test_java_edges_are_code_only_and_resolved(shop):
    edges = _edges(shop)
    assert ("com.shop.web.OrderController", "com.shop.service.OrderService", "field") in edges
    assert ("com.shop.service.CardPaymentGateway", "com.shop.service.PaymentGateway", "implements") in edges
    # wildcard import com.shop.domain.* resolves OrderStatus and Order
    assert ("com.shop.service.OrderService", "com.shop.domain.OrderStatus", "calls") not in edges
    assert ("com.shop.service.OrderService", "com.shop.domain.Order", "calls") in edges
    # the class name inside a string literal creates no edge
    assert not any(src == "com.shop.ShopApplication" for src, _, _ in edges)
    # external types (String, Long, IllegalStateException) never become edges
    assert all(t in shop.symbols for _, t, _ in edges)


def test_java_calls_resolved_through_declared_types(shop):
    calls = {(e.source, e.target, e.detail) for e in shop.edges if e.kind == "calls"}
    assert ("com.shop.web.OrderController", "com.shop.service.OrderService", "pay") in calls
    assert ("com.shop.service.OrderService", "com.shop.repository.OrderRepository", "findById") in calls
    assert ("com.shop.service.OrderService", "com.shop.service.PaymentGateway", "charge") in calls
    pay = next(m for m in shop.symbols["com.shop.service.OrderService"].methods if m.name == "pay")
    assert "com.shop.repository.OrderRepository.save" in pay.calls


def test_entry_points(shop):
    kinds = {(e.kind, e.symbol) for e in shop.entry_points}
    assert ("main", "com.shop.ShopApplication") in kinds
    assert ("http-route", "com.shop.web.OrderController") in kinds


def test_entities_skip_static_and_transient_and_keep_relations(shop):
    order = next(e for e in shop.entities if e.name == "Order")
    names = [f.name for f in order.fields]
    assert names == ["id", "status", "customer"]
    customer = next(f for f in order.fields if f.name == "customer")
    assert customer.relation == "many-to-one" and customer.target == "com.shop.domain.Customer"
    assert customer.foreign_key == "customer_id"
    assert next(f for f in order.fields if f.name == "id").key
    assert order.table == "orders"


def test_deploy_and_build_units(shop):
    kinds = {(u.kind, u.name) for u in shop.deploy}
    assert ("compose-service", "shop") in kinds and ("compose-service", "db") in kinds
    assert ("dockerfile", "Dockerfile") in kinds
    app_config = next(u for u in shop.deploy if u.kind == "app-config")
    assert app_config.details["spring.datasource.url"].startswith("jdbc:postgresql")
    assert shop.build[0].name == "shop-service" and "postgresql" in shop.build[0].dependencies


def test_layers_from_generic_vocabulary(shop):
    assert list(shop.layers) == ["presentation", "application", "domain", "persistence"]
    assert shop.symbols["com.shop.web.OrderController"].layer == "presentation"
    assert shop.symbols["com.shop.repository.OrderRepository"].layer == "persistence"


def test_java_signals_with_evidence(shop):
    sig = shop.signals
    assert {"rest-api", "layered", "persisted-data", "lifecycle", "deploy-config", "build-config",
            "decision-records", "tests"} <= set(sig)
    # one interface implementation is below min_inheritance_edges (2): not an architectural hierarchy
    assert not {"gui-client", "event-bus", "threads", "variability", "crosscutting", "inheritance"} & set(sig)
    assert any("OrderStatus" in ev for ev in sig["lifecycle"])
    assert repo_facts(shop).signals == set(sig)


# ---------------------------------------------------------------- python

def test_python_modules_classes_and_edges(tasks):
    s = tasks.symbols
    assert s["tasks.models"].kind == "module" and s["tasks.models.Task"].kind == "class"
    edges = _edges(tasks)
    assert ("tasks.service.TaskService", "tasks.models.Task", "instantiates") in edges
    assert ("tasks.service.TaskService", "tasks.store.save", "calls") in edges  # the function, not its module
    assert ("tasks.models.Task", "tasks.models.Base", "extends") in edges
    assert ("tasks.api", "tasks.service.TaskService", "imports") in edges  # from-import binds the class


def test_python_entry_points_entities_and_signals(tasks):
    kinds = {(e.kind, e.symbol) for e in tasks.entry_points}
    assert ("http-route", "tasks.api.create_task") in kinds and ("main", "tasks.api") in kinds
    task = next(e for e in tasks.entities if e.name == "Task")
    assert [f.name for f in task.fields] == ["id", "title", "owner_id"]
    assert {"rest-api", "persisted-data", "threads", "ownership", "build-config"} <= set(tasks.signals)


# ---------------------------------------------------------------- javascript / other

def test_javascript_imports_extends_and_routes():
    card = build_card(REPOS / "js_api")
    edges = _edges(card)
    assert ("src.lib.users.UserRepo", "src.lib.base.BaseRepo", "extends") in edges
    assert ("src.routes", "src.lib.users", "imports") in edges
    assert any(e.kind == "http-route" and "GET /users" in e.detail for e in card.entry_points)
    assert "rest-api" in card.signals and "express" in card.build[0].dependencies


def test_unsupported_language_and_sql_schema():
    card = build_card(REPOS / "mixed")
    assert any("go files: no extractor" in n for n in card.notes)
    assert "mixed.go.main" in card.symbols or any(s.language == "go" for s in card.symbols.values())
    orders = next(e for e in card.entities if e.name == "orders")
    fk = next(f for f in orders.fields if f.name == "customer_id")
    assert fk.relation == "many-to-one" and next(f for f in orders.fields if f.name == "id").key


def test_render_card_is_compact_and_complete(shop):
    text = render_card(shop)
    for part in ("REPOSITORY java_shop", "layers (top to bottom)", "entry points", "persisted entities",
                 "deployment / configuration", "build:", "signals:"):
        assert part in text
    assert len(text) < 6000
