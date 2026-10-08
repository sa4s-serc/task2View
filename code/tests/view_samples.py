"""One ArchitectureView per model kind, shared by every renderer test (not tied to any repository)."""

from task2view.contracts.views import (
    ArchitectureView, Interaction, TraceRow, ViewAttribute, ViewElement, ViewFragment, ViewRelation,
)


def _view(model_kind: str, viewpoint: str, **kw) -> ArchitectureView:
    return ArchitectureView(id=f"V-{viewpoint}", viewpoint_id=viewpoint, viewpoint_name=viewpoint.title(),
                            vb_ref="test", model_kind=model_kind, title=f"{viewpoint} sample", purpose="test",
                            detail_level="feature", max_elements=10, **kw)


def component_view() -> ArchitectureView:
    return _view("uml-component", "client-server", overlays=["layered"], elements=[
        ViewElement(id="group:layer:presentation", kind="layer", name="Presentation", group=True),
        ViewElement(id="group:layer:application", kind="layer", name="Application", group=True),
        ViewElement(id="cmp:web.OrderController", kind="component", name="OrderController", stereotype="presentation",
                    parent="group:layer:presentation", responsibilities=["accepts payment requests"]),
        ViewElement(id="cmp:svc.OrderService", kind="component", name="OrderService", stereotype="application",
                    parent="group:layer:application", responsibilities=["checks order state", "charges the gateway"]),
        ViewElement(id="datastore:shop", kind="datastore", name="shop"),
    ], relations=[
        ViewRelation(id="r1", kind="uses", source="cmp:web.OrderController", target="cmp:svc.OrderService", label="pay"),
        ViewRelation(id="r2", kind="writes", source="cmp:svc.OrderService", target="datastore:shop"),
    ], traceability=[TraceRow(element="cmp:svc.OrderService", name="OrderService", files=["svc/OrderService.java"])])


def package_view() -> ArchitectureView:
    return _view("uml-package", "decomposition", elements=[
        ViewElement(id="group:module:web", kind="module", name="web", group=True),
        ViewElement(id="cmp:web.A", kind="module", name="A", parent="group:module:web", responsibilities=["does a"]),
        ViewElement(id="cmp:web.B", kind="module", name="B", parent="group:module:web"),
    ])


def class_view() -> ArchitectureView:
    return _view("uml-class", "data-model", elements=[
        ViewElement(id="ent:Order", kind="entity", name="Order", stereotype="entity", attributes=[
            ViewAttribute(name="id", type="Long", key=True), ViewAttribute(name="customer_id", type="Long", foreign_key=True)]),
        ViewElement(id="ent:Customer", kind="entity", name="Customer", stereotype="entity",
                    attributes=[ViewAttribute(name="id", type="Long", key=True)]),
        ViewElement(id="ent:VipCustomer", kind="entity", name="VipCustomer", stereotype="entity"),
    ], relations=[
        ViewRelation(id="r1", kind="association", source="ent:Order", target="ent:Customer", label="customer", multiplicity="*..1"),
        ViewRelation(id="r2", kind="generalization", source="ent:VipCustomer", target="ent:Customer"),
    ])


def sequence_view() -> ArchitectureView:
    return _view("uml-sequence", "sequence", scenario="pay order", elements=[
        ViewElement(id="actor:customer", kind="actor", name="Customer"),
        ViewElement(id="cmp:web.OrderController", kind="lifeline", name="OrderController", stereotype="presentation"),
        ViewElement(id="cmp:svc.OrderService", kind="lifeline", name="OrderService", stereotype="application"),
    ], interactions=[
        Interaction(order=1, source="actor:customer", target="cmp:web.OrderController", message="POST /orders/1/pay"),
        Interaction(order=2, source="cmp:web.OrderController", target="cmp:svc.OrderService", message="pay(id)"),
        Interaction(order=3, source="cmp:svc.OrderService", target="cmp:web.OrderController", message="rejected",
                    fragment="f1"),
        Interaction(order=4, source="cmp:svc.OrderService", target="cmp:web.OrderController", message="order", kind="return"),
    ], fragments=[ViewFragment(id="f1", kind="alt", guard="order not NEW")])


def communication_view() -> ArchitectureView:
    v = sequence_view()
    v.model_kind, v.viewpoint_id = "uml-communication", "communication"
    return v


def activity_view() -> ArchitectureView:
    v = sequence_view()
    v.model_kind, v.viewpoint_id = "uml-activity", "activity"
    return v


def state_view() -> ArchitectureView:
    return _view("uml-state", "state-machine", scenario="OrderStatus", elements=[
        ViewElement(id="state:new", kind="state", name="NEW"),
        ViewElement(id="state:paid", kind="state", name="PAID"),
        ViewElement(id="state:shipped", kind="state", name="SHIPPED"),
    ], relations=[
        ViewRelation(id="t1", kind="transition", source="state:new", target="state:paid", label="pay"),
        ViewRelation(id="t2", kind="transition", source="state:paid", target="state:shipped", label="ship"),
    ])


def usecase_view() -> ArchitectureView:
    return _view("uml-usecase", "use-case", elements=[
        ViewElement(id="group:system", kind="system", name="Shop", group=True),
        ViewElement(id="actor:customer", kind="actor", name="Customer"),
        ViewElement(id="uc:pay", kind="use_case", name="Pay order", parent="group:system"),
        ViewElement(id="uc:login", kind="use_case", name="Log in", parent="group:system"),
    ], relations=[
        ViewRelation(id="r1", kind="association", source="actor:customer", target="uc:pay"),
        ViewRelation(id="r2", kind="include", source="uc:pay", target="uc:login"),
    ])


def deployment_view() -> ArchitectureView:
    return _view("uml-deployment", "deployment", elements=[
        ViewElement(id="node:shop", kind="node", name="shop"),
        ViewElement(id="artifact:shop-service", kind="artifact", name="shop-service.jar", parent="node:shop"),
        ViewElement(id="datastore:db", kind="datastore", name="db"),
    ], relations=[
        ViewRelation(id="r1", kind="communicates", source="artifact:shop-service", target="datastore:db", label="postgresql"),
    ])


def table_view() -> ArchitectureView:
    return _view("table", "decisions", elements=[
        ViewElement(id="decision_record:adr-001", kind="decision_record", name="Use PostgreSQL",
                    responsibilities=["relational store for orders"]),
    ], traceability=[TraceRow(element="decision_record:adr-001", name="Use PostgreSQL", files=["docs/adr/adr-001.md"])])


SAMPLES = {
    "uml-component": component_view,
    "uml-package": package_view,
    "uml-class": class_view,
    "uml-sequence": sequence_view,
    "uml-communication": communication_view,
    "uml-activity": activity_view,
    "uml-state": state_view,
    "uml-usecase": usecase_view,
    "uml-deployment": deployment_view,
    "table": table_view,
}
