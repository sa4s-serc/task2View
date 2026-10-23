"""ADR-006 step 1: V&B catalog, Phase 1 needs, deterministic covering selection.

The golden cases are the ten pilot goals. Their expected views come from the
expert's review: component + sequence for the detailed IS goals, layers around
the GR10 decomposition, a data model for the DBA, a use-case view for the analyst.
"""

from pathlib import Path

import pytest
import yaml

from task2view.agents.runtime import AgentRuntime
from task2view.knowledge.catalog import load_catalog
from task2view.phase1.needs import detail_level, extract_needs, validate_needs
from task2view.phase3.selection import RepoFacts, SelectionInput, select_views

FIXTURE = yaml.safe_load((Path(__file__).parent / "fixtures" / "pilot_goals.yaml").read_text())
CASES = FIXTURE["cases"]
CATALOG = load_catalog()


def _facts(system: str) -> RepoFacts:
    return RepoFacts(signals=set(FIXTURE["facts"][system]["signals"]))


# ---------------------------------------------------------------- catalog

def test_catalog_is_the_full_views_and_beyond_set():
    families = [vp.family for vp in CATALOG.viewpoints.values()]
    assert len(families) == 30
    assert {f: families.count(f) for f in set(families)} == {
        "module": 6, "cnc": 9, "allocation": 5, "behavior": 5, "beyond": 5,
    }


def test_every_need_is_framed_and_every_reference_resolves():
    # load_catalog() validates cross-references; reaching here means it passed.
    framed = {n for vp in CATALOG.viewpoints.values() for n in vp.covers()}
    assert framed == set(CATALOG.needs)


def test_behaviour_views_never_cover_structural_needs():
    for vp in CATALOG.viewpoints.values():
        categories = {CATALOG.needs[n].category for n in vp.covers()}
        if vp.family == "behavior":
            assert "structure" not in categories, vp.id
        else:
            assert "behavior" not in categories, vp.id


def test_role_aliases():
    assert CATALOG.resolve_role("database engineer") == "data-engineer"
    assert CATALOG.resolve_role("I am a DevOps engineer") == "devops"
    assert CATALOG.resolve_role("integration tester") == "tester"
    assert CATALOG.resolve_role("astronaut") is None


# ---------------------------------------------------------------- golden pilot cases

@pytest.mark.parametrize("case_id", sorted(CASES))
def test_pilot_goal_selects_expected_views(case_id):
    case = CASES[case_id]
    profile = validate_needs(case["goal"], case["phase1"], CATALOG)
    assert profile.dropped == [], profile.dropped
    expect = case["expect"]
    assert profile.detail_level == expect["detail_level"]

    plan = select_views(profile.selection_input(), CATALOG, _facts(case["system"]))
    assert [v.viewpoint_id for v in plan.views] == expect["views"]
    assert plan.uncovered_needs == []
    by_id = {v.viewpoint_id: v for v in plan.views}
    for vp_id, overlays in (expect.get("overlays") or {}).items():
        assert by_id[vp_id].overlays == overlays
    for vp_id, count in (expect.get("subjects_on") or {}).items():
        assert len(by_id[vp_id].subjects) == count
    assert all(v.evidence_gap is None for v in plan.views)
    assert all(v.detail_level == expect["detail_level"] for v in plan.views)
    assert all(v.granularity.get("max_elements") for v in plan.views)


def test_selection_is_deterministic():
    case = CASES["IS-seat-L3"]
    profile = validate_needs(case["goal"], case["phase1"], CATALOG)
    plans = [select_views(profile.selection_input(), CATALOG, _facts("progetto-is")) for _ in range(3)]
    assert len({p.model_dump_json() for p in plans}) == 1


# ---------------------------------------------------------------- selection rules

def test_cnc_style_comes_from_repository_evidence_not_wording():
    request = SelectionInput(needs=["collaboration"])
    assert select_views(request, CATALOG, _facts("progetto-is")).views[0].viewpoint_id == "client-server"
    gr10 = select_views(request, CATALOG, _facts("gr10")).views[0]
    assert gr10.viewpoint_id == "cnc-generic" and gr10.specialised_from is None
    events = select_views(request, CATALOG, RepoFacts(signals={"event-bus"})).views[0]
    assert events.viewpoint_id == "publish-subscribe" and events.specialised_from == "cnc-generic"


def test_style_viewpoint_not_selected_without_its_signal():
    plan = select_views(SelectionInput(needs=["lifecycle"]), CATALOG, RepoFacts(signals=set()))
    assert plan.views == [] and plan.uncovered_needs == ["lifecycle"]


def test_viewpoints_without_a_uml_diagram_are_never_selected():
    # ADR-008: work assignment is documented as a table, which is not a UML diagram type
    plan = select_views(SelectionInput(needs=["ownership"]), CATALOG, _facts("gr10"))
    assert not plan.views and "ownership" in plan.uncovered_needs


def test_role_prior_fills_in_when_goal_states_no_need():
    role = CATALOG.roles["devops"]
    top = max(role.priors.values())
    plan = select_views(SelectionInput(needs=[], role="devops"), CATALOG, _facts("gr10"))
    assert plan.needs_from_role
    assert set(plan.needs) == {n for n, w in role.priors.items() if w == top}
    assert "Table 9.1" in plan.notes[0]


def test_role_priors_are_derived_from_vb_table_9_1():
    tester = CATALOG.roles["tester"]
    assert tester.vb_row == "tester-and-integrator" and "Table 9.1" in tester.prior_source
    # Table 9.1: tester-and-integrator has interface-spec "d" and C&C "s".
    assert tester.priors["interface-contract"] == 1.0
    assert tester.priors["collaboration"] == 0.66
    # Table 9.1 has no behaviour column, so no V&B role has a behavioural prior.
    behavioural = {n for n, need in CATALOG.needs.items() if need.category == "behavior"}
    for role in CATALOG.roles.values():
        if role.vb_row:
            assert not behavioural & set(role.priors), role.id
    assert CATALOG.roles["data-engineer"].prior_source.startswith("extension")


def test_view_cap_reports_uncovered_needs():
    request = SelectionInput(needs=["actors-goals", "deployment", "data-structure", "lifecycle"])
    plan = select_views(request, CATALOG, _facts("gr10"), max_views=3)
    assert len(plan.views) == 3 and len(plan.uncovered_needs) == 1


def test_layering_alone_on_unlayered_repo_is_not_an_overlay():
    plan = select_views(SelectionInput(needs=["layering"]), CATALOG, RepoFacts(signals=set()))
    assert plan.views == [] and plan.uncovered_needs == ["layering"]


# ---------------------------------------------------------------- Phase 1 validation

def test_detail_level_rule_uses_profile_not_wording():
    rule = CATALOG.detail_rule
    assert detail_level(1, 0, rule) == "overview"
    assert detail_level(2, 0, rule) == "feature"
    assert detail_level(1, 1, rule) == "feature"
    assert detail_level(1, 2, rule) == "detailed"


def test_phase1_drops_unsupported_needs_and_subjects():
    goal = CASES["IS-reg-L1"]["goal"]
    raw = {
        "role_label": "integration tester",
        "role": "not-a-role",
        "needs": [
            {"need": "collaboration", "evidence": "which system components are involved"},
            {"need": "deployment", "evidence": "where it is deployed"},
            {"need": "made-up", "evidence": "test"},
        ],
        "subjects": [{"text": "payment gateway", "needs": ["collaboration"]}],
        "quality_attributes": ["reliability", "speed"],
    }
    profile = validate_needs(goal, raw, CATALOG)
    assert [n.need for n in profile.needs] == ["collaboration"]
    assert profile.role == "tester"
    assert profile.subjects == []
    assert profile.quality_attributes == ["reliability"]
    assert len(profile.dropped) == 3


def test_extract_needs_sends_catalog_and_validates_reply():
    case = CASES["GR10-Q4"]
    seen = {}

    def generate(prompt, model=None):
        seen["prompt"] = prompt
        return case["phase1"]

    profile = extract_needs(case["goal"], AgentRuntime(generate=generate), catalog=CATALOG)
    assert "actors-goals" in seen["prompt"] and "data-engineer" in seen["prompt"]
    assert case["goal"] in seen["prompt"]
    assert [n.need for n in profile.needs] == ["actors-goals"]


def test_select_views_cli_with_fake_provider(capsys):
    import json

    from task2view.cli import main
    from task2view.llm.base import LLMClient
    from task2view.llm.registry import register_provider

    case = CASES["GR10-Q3"]

    @register_provider("pilot-fixture", default_model="m")
    class FixtureClient(LLMClient):
        provider = "pilot-fixture"

        def complete_text(self, prompt, *, system=None, json_mode=False):
            return json.dumps(case["phase1"])

    signals = ",".join(FIXTURE["facts"]["gr10"]["signals"])
    code = main(["select-views", "--goal", case["goal"], "--llm", "pilot-fixture", "--signals", signals])
    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert [v["viewpoint_id"] for v in out["plan"]["views"]] == ["data-model"]  # one view per request
    assert "change-impact" in out["plan"]["uncovered_needs"] or out["plan"]["uncovered_needs"]
    assert main(["select-views", "--goal", "x", "--signals", "not-a-signal"]) == 2


# ---------------------------------------------------------------- primary / secondary needs

def test_secondary_need_never_adds_a_view():
    request = SelectionInput(needs=["data-structure"], secondary_needs=["lifecycle", "change-impact"])
    plan = select_views(request, CATALOG, _facts("gr10"))
    assert [v.viewpoint_id for v in plan.views] == ["data-model"]
    assert plan.secondary_not_shown == ["lifecycle", "change-impact"]
    assert plan.uncovered_needs == []


def test_secondary_need_is_shown_when_a_chosen_view_covers_it():
    request = SelectionInput(needs=["collaboration"], secondary_needs=["dependencies"])
    plan = select_views(request, CATALOG, _facts("progetto-is"))
    assert [v.viewpoint_id for v in plan.views] == ["client-server"]
    assert "dependencies" in plan.views[0].needs and plan.secondary_not_shown == []


def test_secondary_coverage_breaks_ties_between_equally_small_sets():
    # decomposition and layered both frame decomposition; only layered also covers layering.
    request = SelectionInput(needs=["decomposition"], secondary_needs=["layering"])
    plan = select_views(request, CATALOG, _facts("gr10"))
    assert len(plan.views) == 1 and plan.secondary_not_shown == []


def test_all_secondary_needs_are_promoted():
    plan = select_views(SelectionInput(needs=[], secondary_needs=["deployment"]), CATALOG, _facts("gr10"))
    assert [v.viewpoint_id for v in plan.views] == ["deployment"]
    assert "treated as primary" in plan.notes[0]


def test_phase1_salience_splits_selection_input():
    goal = CASES["GR10-Q3"]["goal"]
    raw = {
        "role_label": "database engineer",
        "needs": [
            {"need": "data-structure", "evidence": "the main data entities stored by the system", "salience": "primary"},
            {"need": "lifecycle", "evidence": "throughout the lifecycle of a report", "salience": "secondary"},
            {"need": "change-impact", "evidence": "which parts of the application depend on this persisted information"},
        ],
    }
    profile = validate_needs(goal, raw, CATALOG)
    request = profile.selection_input()
    assert request.needs == ["data-structure", "change-impact"]
    assert request.secondary_needs == ["lifecycle"]
    assert profile.detail_level == "feature"
