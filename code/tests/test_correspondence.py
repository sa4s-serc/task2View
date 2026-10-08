from task2view.knowledge.correspondence import select_correspondence, viewpoints_for_concerns, with_viewpoint
from task2view.knowledge.loader import load_knowledge


def _corr(role: str, task: str):
    kb = load_knowledge()
    return select_correspondence(role, task, kb, goal=task)


def test_developer_modify_booking_is_module_components():
    corr = _corr(
        "member-of-development-team",
        "I am a software developer. I need to modify the seat booking functionality "
        "and understand the main system components involved and how they interact.",
    )
    assert corr.viewpoint_id == "module-decomposition"
    assert corr.grain.unit == "component"
    assert corr.view_type == "component_view"
    assert corr.concerns == ["maintainability"]
    assert "control-flow" not in corr.concerns
    assert "connectivity" not in corr.concerns


def test_tester_l2_registration_stays_cnc_runtime():
    corr = _corr(
        "tester-and-integrator",
        "I am an integration tester. I need to design integration tests for the user "
        "registration functionality. Before defining the tests, I need to understand the "
        "main components involved in registration, their responsibilities, and how they "
        "interact when a new user creates an account.",
    )
    assert corr.viewpoint_id == "cnc-runtime"
    assert corr.view_type == "component_view"
    corr = _corr(
        "tester-and-integrator",
        "I am an integration tester. I need to test the user registration functionality "
        "and understand which system components are involved and how they interact.",
    )
    assert corr.viewpoint_id == "cnc-runtime"
    assert corr.grain.unit == "component"
    assert corr.view_type == "component_view"


def test_architect_organization_stays_module_grain():
    corr = _corr(
        "current-and-future-architect",
        "I am a software architect. I need to review the overall organization of the "
        "system before planning its future evolution. I want to understand the main "
        "architectural components, their responsibilities, how the system is decomposed "
        "into different layers or subsystems, and the main dependencies among them.",
    )
    assert corr.viewpoint_id == "module-decomposition"
    assert corr.grain.unit == "component"


def test_devops_deploy_is_allocation():
    corr = _corr(
        "infrastructure-support-personnel",
        "I am a DevOps engineer. I need to deploy and configure the system in a new "
        "execution environment. Before preparing the deployment, I need to understand "
        "which runtime environments and software artifacts are required.",
    )
    assert corr.viewpoint_id == "allocation-deployment"
    assert corr.grain.unit == "component"
    assert corr.view_type == "deployment_view"


def test_database_engineer_is_code_mapping_types():
    corr = _corr(
        "analyst",
        "I am a database engineer. I need to modify the persistence layer to support "
        "future changes to the management of municipal reports. Before modifying the "
        "database, I need to understand the main data entities stored by the system "
        "and the relationships among them.",
    )
    assert corr.viewpoint_id == "code-mapping"
    assert corr.grain.unit == "type"
    assert corr.view_type == "class_view"


def test_business_analyst_is_context():
    corr = _corr(
        "customer",
        "I am a business analyst. I need to understand at a high level how a system "
        "for reporting and managing problems in a municipal area is expected to work. "
        "I need to identify the main types of users that interact with the system.",
    )
    assert corr.viewpoint_id == "context"
    assert corr.grain.unit == "context"
    assert corr.view_type == "context_view"


def test_viewpoints_follow_chosen_concerns_not_phrases():
    kb = load_knowledge()
    ids, framed = viewpoints_for_concerns(
        kb,
        ["maintainability"],
    )
    assert framed is True
    assert ids[0] == "module-decomposition"
    assert "cnc-runtime" not in ids
    text = (
        "I need to design integration tests for the user registration functionality "
        "and understand how a request is processed."
    )
    opened, covered = viewpoints_for_concerns(kb, ["control-flow"])
    assert covered is False
    assert "cnc-runtime" in opened
    assert "module-decomposition" in opened
    ranked = select_correspondence("tester-and-integrator", text, kb)
    assert ranked.viewpoint_id == "cnc-runtime"


def test_given_concerns_replace_cue_matches():
    kb = load_knowledge()
    corr = select_correspondence(
        "member-of-development-team",
        "I need to modify the seat booking functionality and understand the main components involved.",
        kb,
        extra_concerns=["deployment", "not-a-concern"],
    )
    assert corr.concerns == ["deployment"]
    assert "maintainability" not in corr.concerns


def test_model_viewpoint_overrides_catalog_rank():
    kb = load_knowledge()
    corr = select_correspondence(
        "member-of-development-team",
        "modify seat booking and understand the main components involved",
        kb,
    )
    assert corr.viewpoint_id == "module-decomposition"
    assert corr.decided_by == "catalog"
    chosen = with_viewpoint(corr, "allocation-deployment", kb)
    assert chosen.viewpoint_id == "allocation-deployment"
    assert chosen.decided_by == "model"
    unknown = with_viewpoint(corr, "trust-boundary", kb)
    assert unknown.viewpoint_id == corr.viewpoint_id
    assert unknown.decided_by == "catalog"


def test_aliases_for_evaluation_roles():
    kb = load_knowledge()
    assert kb.resolve_role("software architect") == "current-and-future-architect"
    assert kb.resolve_role("integration tester") == "tester-and-integrator"
    assert kb.resolve_role("DevOps engineer") == "infrastructure-support-personnel"
    assert kb.resolve_role("database engineer") == "analyst"
    assert kb.resolve_role("business analyst") == "customer"
