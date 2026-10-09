"""ADR-006 end to end on the synthetic java_shop repository with a scripted model (no network)."""

import json
from pathlib import Path

import pytest

from task2view.agents.run_v2 import run_v2
from task2view.agents.write_v2 import write_run_v2
from task2view.knowledge.catalog import load_catalog
from task2view.phase0.card import build_card
from task2view.phase7.project import project_view
from task2view.phase3.selection import PlannedView

from .test_evidence_model import BAD_CLAIMS, GOAL, GOOD_CLAIMS

SHOP = Path(__file__).parent / "fixtures" / "repos" / "java_shop"
CATALOG = load_catalog()

PHASE1 = {"role_label": "developer", "role": "developer", "target": "order payment", "needs": [
    {"need": "collaboration", "evidence": "the components involved in order payment, their responsibilities",
     "salience": "primary"},
    {"need": "interaction-order", "evidence": "how they interact when an order is paid", "salience": "primary"}],
    "subjects": [], "quality_attributes": []}


def scripted(prompt, model=None):
    if "Phase 1: Stakeholder-task interpretation" in prompt:
        return PHASE1
    if "Phase 4: Investigation planning" in prompt:
        return {}
    if "Phase 5: Evidence extraction" in prompt:
        if "RESULT:" not in prompt:
            return {"tool": "symbol", "args": {"id": "OrderService"}}
        return {"final": {"claims": GOOD_CLAIMS + BAD_CLAIMS}}
    raise AssertionError("unexpected prompt")


def judge(prompt, model=None):
    assert "Phase 8: Task-fit review" in prompt
    return {"scores": {"grain": {"score": 4, "reason": "fits"}}, "overall": 4, "summary": "ok"}


@pytest.fixture(scope="module")
def result():
    return run_v2(GOAL, str(SHOP), generate=scripted, judge_generate=judge, languages=["plantuml", "plantuml"])


def test_selects_component_and_sequence_views(result):
    assert [v.viewpoint_id for v in result.viewset.views] == ["client-server", "sequence"]
    assert result.viewset.stakeholder == "developer"


def test_component_view_layers_responsibilities_and_evidence(result):
    view = result.viewset.views[0]
    layers = [e for e in view.elements if e.kind == "layer"]
    assert layers and all(e.group for e in layers)
    svc = next(e for e in view.elements if e.name == "OrderService")
    assert svc.parent == "group:layer:application" and "charges the payment gateway" in svc.responsibilities
    assert any(r.label == "pay" for r in view.relations)
    row = next(t for t in view.traceability if t.name == "OrderService")
    assert row.files == ["src/main/java/com/shop/service/OrderService.java"]


def test_sequence_view_orders_messages_with_alternative(result):
    seq = result.viewset.views[1]
    assert [i.message for i in seq.interactions] == ["pay(id)", "findById(id)", "charge(order)"]
    assert seq.fragments and seq.fragments[0].guard == "order status is NEW"


def test_validation_layers_and_judge(result):
    for vid, report in result.validation.items():
        assert report.verdict in {"pass", "pass_with_limitations"}, (vid, report.constraints, report.faithfulness)
        assert report.notation["model_kind_matches"]
        # scripted models have no spec, so independence cannot be established
        assert report.task_fit["status"] == "scored" and report.task_fit["independent"] is None
    assert result.decisions["V1-client-server"].coverage


def test_rejected_claims_never_reach_a_view(result):
    names = {e.name for v in result.viewset.views for e in v.elements}
    assert "Payment Processing Component" not in names
    assert len(result.aem.rejected_claims) >= 3


def test_correspondence_ties_shared_elements(result):
    assert any(any(ref.endswith("cmp:com.shop.service.OrderService") for ref in c.elements)
               for c in result.viewset.correspondences)


def test_run_package_written(result, tmp_path):
    out = write_run_v2(result, tmp_path / "run")
    for name in ("repository_card.json", "stakeholder_profile.json", "view_plan.json", "architectural_questions.json",
                 "investigation_plan.json", "evidence_model.json", "reconciliation.json", "viewset.json",
                 "validation_report.json", "traceability.md", "README.md", "run.log"):
        assert (out / name).exists(), name
    assert (out / "V1-client-server" / "view.puml").read_text().startswith("@startuml")
    assert "Client-Server" in (out / "README.md").read_text()
    assert json.loads((out / "viewset.json").read_text())["views"]


# ----------------------------------------------------- projection without any claims (facts only)

def _planned(vp_id, overlays=(), detail="feature"):
    return PlannedView(viewpoint_id=vp_id, family=CATALOG.viewpoint(vp_id).family, model_kind=CATALOG.viewpoint(vp_id).model_kind,
                       needs=[], overlays=list(overlays), detail_level=detail,
                       granularity=CATALOG.granularity(vp_id, detail))


def test_fact_based_views_from_card_only(result):
    card = result.card
    aem = result.aem
    data = project_view("V-dm", _planned("data-model"), [], aem, card, CATALOG)
    order = next(e for e in data.elements if e.name == "Order")
    assert [a.name for a in order.attributes] == ["id", "status"]
    assert any(r.kind == "association" and r.multiplicity == "*..1" for r in data.relations)
    dep = project_view("V-dep", _planned("deployment"), [], aem, card, CATALOG)
    jar = next(e for e in dep.elements if e.kind == "artifact")
    assert jar.parent and dep.element(jar.parent).kind in {"node", "execution_env"}
    states = project_view("V-st", _planned("state-machine"), [], aem, card, CATALOG)
    assert sorted(e.name for e in states.elements) == ["NEW", "PAID", "SHIPPED"]
    assert any("transitions were not evidenced" in l for l in states.limitations)


def test_fold_and_exclude(result):
    card, aem = result.card, result.aem
    folded = project_view("V-f", _planned("client-server", ["layered"]), [], aem, card, CATALOG, fold=True)
    assert all(e.id.startswith("fold:") for e in folded.content_elements())
    assert any("OrderService" in r for e in folded.elements for r in e.responsibilities)
    excluded = project_view("V-x", _planned("client-server", ["layered"]), [], aem, card, CATALOG,
                            exclude={"cmp:com.shop.service.OrderService"})
    assert all(e.name != "OrderService" for e in excluded.elements)
    assert all("OrderService" not in r.source for r in excluded.relations)


def test_cli_run_v2_writes_package(tmp_path, capsys):
    from task2view.cli import main
    from task2view.llm.base import LLMClient
    from task2view.llm.registry import register_provider

    @register_provider("scripted-run", default_model="m")
    class Scripted(LLMClient):
        provider = "scripted-run"

        def complete_text(self, prompt, *, system=None, json_mode=False):
            return json.dumps(scripted(prompt))

    out = tmp_path / "cli-run"
    code = main(["run", "--code", str(SHOP), "--goal", GOAL, "--out", str(out), "--llm", "scripted-run",
                 "--notations", "plantuml,mermaid", "--no-compile-check"])
    summary = json.loads(capsys.readouterr().out)
    assert code == 0
    assert [v["viewpoint"] for v in summary["views"]] == ["client-server", "sequence"]
    assert summary["generator"] == "scripted-run:m" and summary["judge"] is None
    assert (out / "V2-sequence" / "view.mermaid.mmd").exists()
