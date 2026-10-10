"""Changes made after the 2026-10 literature check: grounding strength, agent context, component grain,
reflexion, correspondence, the per-theme judge and the retrieval baseline. Scripted models only."""

import json

import pytest

from task2view.agents.runtime import AgentRuntime
from task2view.agents.run_v2 import run_v2
from task2view.contracts.aem import InvestigationTask, Seeds
from task2view.llm.claude import _content
from task2view.phase5.agent import run_evidence_task
from task2view.phase5.card_tools import CardTools
from task2view.phase5.collect import collect_evidence
from task2view.phase5.verify import ClaimVerifier
from task2view.phase8.judge import THEMES, judge_view

from .test_evidence_model import CATALOG, GOAL, GOOD_CLAIMS, SVC, _scripted_agent, setup  # noqa: F401
from .test_run_v2 import SHOP, judge, scripted


@pytest.fixture(scope="module")
def card(setup):  # noqa: F811
    return setup[0]


# ------------------------------------------------------------------ grounding

def test_invented_member_does_not_resolve_to_its_type(card):
    index = ClaimVerifier(card).index
    assert index.resolve("com.shop.service.OrderService.pay") == "com.shop.service.OrderService"
    assert index.resolve("com.shop.service.OrderService.refundEverything") is None


def test_element_cited_outside_its_file_is_only_inferred(card):
    claim = dict(GOOD_CLAIMS[0], evidence=[{"file": "src/main/java/com/shop/web/OrderController.java",
                                            "lines": [15, 15], "excerpt": "return orderService.pay(id);"}])
    verified, _ = ClaimVerifier(card).verify(claim, claim_id="C1", task_id="T", question_ids=[])
    assert verified.support == "inferred"


def test_relation_is_not_observed_from_a_reverse_edge(card):
    claim = {"kind": "relation", "source": "OrderService", "target": "OrderController", "relation": "uses",
             "evidence": [{"file": SVC, "lines": [11, 11], "excerpt": "repository.findById(id)"}]}
    verified, _ = ClaimVerifier(card).verify(claim, claim_id="C1", task_id="T", question_ids=[])
    assert verified.support == "inferred"


def test_one_character_excerpt_locates_nothing(card):
    claim = dict(GOOD_CLAIMS[0], evidence=[{"file": SVC, "lines": [12, 13], "excerpt": "}"}])
    verified, reason = ClaimVerifier(card).verify(claim, claim_id="C1", task_id="T", question_ids=[])
    assert verified is None and "too short" in reason


def test_ambiguous_tool_lookup_lists_candidates(card):
    tools = CardTools(card, ["code"])
    assert tools.symbol("NoSuchThing").startswith("error: no symbol")
    assert tools.symbol("OrderService").startswith("com.shop.service.OrderService")


# --------------------------------------------------------------- agent context

def _task():
    return InvestigationTask(id="T1", view_id="V1", viewpoint_id="client-server", question_ids=[], need="collaboration", goal="g",
                             seeds=Seeds(symbols=["com.shop.service.OrderService"], classes=["code"]), budget_steps=8)


def test_old_results_are_elided_and_repeats_caught(card):
    seen = []

    def generate(prompt, model=None):
        seen.append(prompt)
        step = prompt.count("CALL ")
        if step < 6:  # two identical reads, then distinct ones
            start = 1 if step < 2 else step
            return {"tool": "read", "args": {"path": SVC, "start": start, "end": start + 1}}
        return {"final": {"claims": []}}

    _, _, calls = run_evidence_task(_task(), [], card, AgentRuntime(generate=generate), card_text="card",
                                    viewpoint_name="Client-Server", keep_results=2)
    assert "repeated call" in seen[2]
    assert seen[-1].count("[result elided") == 4 and calls["read"] == 5


def test_claude_blocks_cache_the_prefix_and_the_last_step():
    blocks = _content(["prompt and card", "step 1", "step 2"])
    assert [("cache_control" in b) for b in blocks] == [True, False, True]
    assert _content("plain") == "plain"


def test_retrieval_baseline_answers_in_one_call(setup):  # noqa: F811
    card, profile, plan, questions = setup
    from task2view.phase4.investigate import plan_investigation
    tasks = plan_investigation(plan, questions, card, CATALOG, target=profile.target)
    prompts = []

    def generate(prompt, model=None):
        prompts.append(prompt)
        return {"final": {"claims": GOOD_CLAIMS[:1]}}

    model = collect_evidence(tasks, questions, card, AgentRuntime(generate=generate), CATALOG, card_text="card",
                             mode="retrieval")
    assert len(prompts) == len(tasks) and "RETRIEVED CODE" in prompts[0] and "OrderService.java" in prompts[0]
    assert model.claims


# ----------------------------------------------------------- grain and reflexion

def test_package_grain_names_components_after_packages(setup):  # noqa: F811
    card, _, _, questions = setup
    from task2view.phase4.investigate import plan_investigation
    tasks = plan_investigation(setup[2], questions, card, CATALOG, target="order payment")
    model = collect_evidence(tasks, questions, card, AgentRuntime(generate=_scripted_agent(GOOD_CLAIMS)), CATALOG,
                             card_text="card", grain="package")
    names = {e.name for e in model.elements.values() if e.kind == "component"}
    assert {"service", "web"} <= names and "OrderService" not in names


@pytest.fixture(scope="module")
def result():
    return run_v2(GOAL, str(SHOP), generate=scripted, judge_generate=judge)


def test_reflexion_separates_agreement_omission_and_claim_only(result):
    rx = result.aem.reflexion
    claimed = result.aem.relations[rx["convergence"][0]]
    assert claimed.claims and claimed.member_edges
    assert all(not result.aem.relations[r].claims for r in rx.get("divergence", []))


def test_sequence_participants_correspond_to_the_component_view(result):
    assert result.viewset.correspondence_gaps == []


# -------------------------------------------------------------------- judge

def test_judge_scores_one_theme_per_call_with_reason_first(result):
    report = result.validation["V1-client-server"].task_fit
    assert set(report["scores"]) == set(THEMES) and report["rubric"] == "v1"
    assert list(report["scores"]["layers"]) == ["reason", "score"]


def test_judge_reports_unusable_replies_without_failing(result):
    view = result.viewset.views[0]
    replies = iter([{"score": 9}] + [{"reason": "r", "score": 3}] * (len(THEMES) - 1))
    report = judge_view(view, result.questions, GOAL, "src", "plantuml",
                        AgentRuntime(generate=lambda p, model=None: next(replies)), judge_spec="a:x", generator_spec="b:y")
    assert report.status == "partial" and report.independent is True
    assert json.dumps(report.scores) and len(report.scores) == len(THEMES) - 1


def test_small_overflow_keeps_detail_unless_whole_system(result):
    from task2view.phase6.decide import decide
    planned = result.plan.views[0]
    view = result.viewset.views[0].model_copy(deep=True)
    view.gaps, view.max_elements = [], 6

    def decision(overflow, whole_system):
        view.overflow = [f"cmp:x{i}" for i in range(overflow)]
        return decide(view, planned, result.questions, result.aem, evidence_rounds_left=0,
                      whole_system=whole_system).decision

    assert decision(1, whole_system=False) == "confirm"
    assert decision(1, whole_system=True) == "simplify"
    assert decision(7, whole_system=False) == "simplify"
