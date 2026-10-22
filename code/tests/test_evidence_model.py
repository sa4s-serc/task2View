"""ADR-006 step 3: questions per view, investigation plan, evidence agents, verification, AEM.

Uses the synthetic java_shop repository and a scripted agent (no model call).
"""

from pathlib import Path

import pytest

from task2view.agents.runtime import AgentRuntime
from task2view.knowledge.catalog import load_catalog
from task2view.phase0.card import build_card, render_card, repo_facts
from task2view.phase1.needs import validate_needs
from task2view.phase2.view_questions import derive_view_questions
from task2view.phase3.selection import select_views
from task2view.phase4.investigate import plan_investigation, suggest_seeds, tokens
from task2view.phase5.collect import collect_evidence
from task2view.phase5.verify import ClaimVerifier

SHOP = Path(__file__).parent / "fixtures" / "repos" / "java_shop"
CATALOG = load_catalog()
GOAL = ("I am a developer. I need to change how orders are paid and understand the components involved in order "
        "payment, their responsibilities, and how they interact when an order is paid.")

SVC = "src/main/java/com/shop/service/OrderService.java"
CTL = "src/main/java/com/shop/web/OrderController.java"

GOOD_CLAIMS = [
    {"kind": "element", "element_kind": "component", "name": "OrderService", "symbol": "com.shop.service.OrderService",
     "responsibilities": ["checks that an order is payable", "charges the payment gateway"],
     "evidence": [{"file": SVC, "lines": [12, 13], "excerpt": "if (order.getStatus() != OrderStatus.NEW) {"}],
     "confidence": 0.9},
    {"kind": "relation", "source": "OrderController", "target": "OrderService", "relation": "uses", "label": "pay",
     "evidence": [{"file": CTL, "lines": [15, 15], "excerpt": "return orderService.pay(id);"}], "confidence": 0.9},
    {"kind": "interaction", "scenario": "pay order", "order": 1, "source": "OrderController", "target": "OrderService",
     "label": "pay(id)", "evidence": [{"file": CTL, "lines": [15, 15], "excerpt": "orderService.pay(id)"}]},
    {"kind": "interaction", "scenario": "pay order", "order": 2, "source": "OrderService", "target": "OrderRepository",
     "label": "findById(id)", "evidence": [{"file": SVC, "lines": [11, 11], "excerpt": "repository.findById(id)"}]},
    {"kind": "interaction", "scenario": "pay order", "order": 3, "source": "OrderService", "target": "PaymentGateway",
     "label": "charge(order)", "condition": "order status is NEW",
     "evidence": [{"file": SVC, "lines": [15, 15], "excerpt": "gateway.charge(order);"}]},
]
BAD_CLAIMS = [
    {"kind": "element", "element_kind": "component", "name": "Payment Processing Component",
     "evidence": [{"file": SVC, "lines": [10, 10], "excerpt": "public Order pay(Long id) {"}]},
    {"kind": "relation", "source": "OrderController", "target": "OrderRepository", "relation": "uses",
     "evidence": [{"file": CTL, "lines": [15, 15], "excerpt": "repository.save(order)"}]},
    {"kind": "element", "element_kind": "component", "name": "OrderService", "symbol": "com.shop.service.OrderService",
     "evidence": [{"file": "docs/model.vpp", "excerpt": "OrderService"}]},
]


def _scripted_agent(claims):
    def generate(prompt, model=None):
        if "Phase 5: Evidence extraction" not in prompt:
            return {"symbols": [], "paths": [], "goal": ""}
        if "RESULT:" not in prompt:
            return {"tool": "read", "args": {"path": SVC, "start": 1, "end": 20}}
        return {"final": {"claims": claims}}
    return generate


@pytest.fixture(scope="module")
def setup():
    card = build_card(SHOP)
    raw = {"role_label": "developer", "target": "order payment", "needs": [
        {"need": "collaboration", "evidence": "the components involved in order payment, their responsibilities",
         "salience": "primary"},
        {"need": "interaction-order", "evidence": "how they interact when an order is paid", "salience": "primary"}]}
    profile = validate_needs(GOAL, raw, CATALOG)
    plan = select_views(profile.selection_input(), CATALOG, repo_facts(card))
    questions = derive_view_questions(profile, plan, CATALOG)
    return card, profile, plan, questions


def test_questions_are_per_view_and_at_its_grain(setup):
    _, _, plan, questions = setup
    assert [v.viewpoint_id for v in plan.views] == ["client-server", "sequence"]
    by_view = {q.view_id for q in questions}
    assert by_view == {"V1-client-server", "V2-sequence"}
    seq = next(q for q in questions if q.viewpoint_id == "sequence")
    assert seq.relation_kinds == ["message", "return"] and "order payment" in seq.text


def test_seed_suggestions_use_identifiers_not_paths():
    card = build_card(SHOP)
    assert tokens("ReservationManager handles bookings") == {"reservation", "manager", "handle", "booking"}
    from task2view.phase4.investigate import related
    assert related("handle", "handling") and related("pay", "payment") and not related("order", "user")
    seeds = dict(suggest_seeds(card, "order payment", limit=6, neighbours=2))
    assert "com.shop.service.OrderService" in seeds
    assert all(sid in card.symbols for sid in seeds)


def test_investigation_tasks_have_budget_and_origin(setup):
    card, profile, plan, questions = setup
    tasks = plan_investigation(plan, questions, card, CATALOG, target=profile.target)
    assert {t.view_id for t in tasks} == {"V1-client-server", "V2-sequence"}
    assert all(t.budget_steps == 16 for t in tasks)  # detail level "feature"
    assert all(t.suggested_by and t.seeds.classes for t in tasks)


def test_planning_agent_cannot_invent_starting_points(setup):
    card, profile, plan, questions = setup

    def generate(prompt, model=None):
        return {"symbols": ["com.shop.service.OrderService", "com.fake.Nothing"], "paths": ["no/such/file"], "goal": "g"}

    tasks = plan_investigation(plan, questions, card, CATALOG, target=profile.target, runtime=AgentRuntime(generate=generate))
    assert tasks[0].seeds.symbols == ["com.shop.service.OrderService"] and tasks[0].seeds.paths == []
    assert "planning-agent" in tasks[0].suggested_by


@pytest.fixture(scope="module")
def model(setup):
    card, profile, plan, questions = setup
    tasks = plan_investigation(plan, questions, card, CATALOG, target=profile.target)[:1]
    runtime = AgentRuntime(generate=_scripted_agent(GOOD_CLAIMS + BAD_CLAIMS))
    return collect_evidence(tasks, questions, card, runtime, CATALOG, card_text=render_card(card))


def test_bad_claims_are_rejected_with_reasons(model):
    reasons = [r["reason"] for r in model.rejected_claims]
    assert len(reasons) == 3
    assert any("not a symbol" in r for r in reasons)
    assert any("excerpt not found" in r for r in reasons)
    assert any("not in the repository" in r or "not evidence" in r for r in reasons)


def test_components_are_named_after_code_and_carry_responsibilities(model):
    comps = {e.name: e for e in model.elements.values() if e.kind == "component"}
    assert {"OrderController", "OrderService", "OrderRepository", "PaymentGateway"} <= set(comps)
    assert [r.text for r in comps["OrderService"].responsibilities] == [
        "checks that an order is payable", "charges the payment gateway"]
    assert all(e.named_by == "symbol" for e in comps.values())


def test_relations_are_lifted_from_graph_edges(model):
    rel = next(r for r in model.relations.values()
               if r.source == "cmp:com.shop.web.OrderController" and r.target == "cmp:com.shop.service.OrderService")
    assert rel.kind == "uses" and rel.label == "pay" and rel.member_edges and rel.claims


def test_claim_support_is_decided_by_verification(model):
    rel_claim = next(c for c in model.claims.values() if c.kind == "relation")
    assert rel_claim.support == "observed"  # graph edge OrderController -> OrderService exists


def test_entities_attributes_and_associations(model):
    order = next(e for e in model.elements.values() if e.kind == "entity" and e.name == "Order")
    assert [(a.name, a.key) for a in order.attributes] == [("id", True), ("status", False)]
    assoc = next(r for r in model.relations.values() if r.kind == "association" and r.source == order.id)
    assert assoc.target == "ent:com.shop.domain.Customer" and assoc.multiplicity == "*..1" and assoc.label == "customer"


def test_deployment_elements_from_facts(model):
    kinds = {(e.kind, e.name) for e in model.elements.values() if e.kind in {"artifact", "node", "datastore", "execution_env"}}
    assert ("artifact", "shop-service.jar") in kinds and ("node", "shop") in kinds and ("datastore", "db") in kinds
    assert any(r.kind == "communicates" for r in model.relations.values())


def test_states_from_status_enum(model):
    states = sorted(e.name for e in model.elements.values() if e.kind == "state")
    assert states == ["NEW", "PAID", "SHIPPED"]


def test_scenario_is_ordered_with_alternative_fragment(model):
    scn = model.scenarios["scn:pay-order"]
    assert [(s.order, s.message) for s in scn.steps] == [(1, "pay(id)"), (2, "findById(id)"), (3, "charge(order)")]
    assert scn.fragments[0].guard == "order status is NEW" and scn.steps[2].fragment == scn.fragments[0].id


def test_verifier_rejects_line_out_of_range():
    card = build_card(SHOP)
    v = ClaimVerifier(card)
    claim, reason = v.verify({"kind": "element", "symbol": "com.shop.service.OrderService",
                              "evidence": [{"file": SVC, "lines": [999, 999], "excerpt": "x"}]},
                             claim_id="C1", task_id="T", question_ids=[])
    assert claim is None and "does not exist" in reason


def test_relations_may_end_at_verified_non_code_elements():
    # an actor and a use case have no code symbol; their relation is checked against their own verified claims
    card = build_card(SHOP)
    v = ClaimVerifier(card)
    cite = [{"file": SVC, "lines": [10, 10], "excerpt": "public Order pay(Long id) {"}]
    relation = {"kind": "relation", "source": "Customer", "target": "Pay order", "relation": "association", "evidence": cite}
    assert v.verify(relation, claim_id="C0", task_id="T", question_ids=[])[0] is None  # nothing verified yet
    for name, kind in (("Customer", "actor"), ("Pay order", "use_case")):
        claim, _ = v.verify({"kind": "element", "element_kind": kind, "name": name, "evidence": cite},
                            claim_id=name, task_id="T", question_ids=[])
        v.register(claim)
    claim, reason = v.verify(relation, claim_id="C3", task_id="T", question_ids=[])
    assert claim is not None, reason
    assert (claim.source, claim.target) == ("Customer", "Pay order")  # the actor, though a Customer class exists
    unknown = dict(relation, target="Refund order")  # an end nobody verified is still rejected
    assert v.verify(unknown, claim_id="C4", task_id="T", question_ids=[])[0] is None
