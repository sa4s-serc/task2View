from task2view.knowledge.loader import load_knowledge


def test_vb_table_tester_row_is_verbatim():
    kb = load_knowledge()
    row = kb.vb_table["rows"]["tester-and-integrator"]
    assert row["decomposition"] == "d"
    assert row["uses"] == "d"
    assert row["cnc"] == "s"
    assert row["deployment"] == "s"
    assert row["interface-spec"] == "d"
    assert "work-assignment" not in row


def test_role_aliases_resolve_to_vb_rows():
    kb = load_knowledge()
    assert kb.resolve_role("Tester") == "tester-and-integrator"
    assert kb.resolve_role("developer") == "member-of-development-team"
    assert kb.resolve_role("software developer") == "member-of-development-team"
    assert kb.resolve_role("new contributor") == "new-stakeholder"
    assert kb.resolve_role("SRE") == "infrastructure-support-personnel"


def test_every_vb_viewpoint_exists_in_catalog():
    kb = load_knowledge()
    missing = []
    for column in kb.vb_table["columns"]:
        vid = column.get("viewpoint")
        if vid and vid not in kb.viewpoints:
            missing.append(vid)
    assert missing == []


def test_view_projection_is_view_type_keyed():
    kb = load_knowledge()
    assert kb.edge_insertion_mode("sequence_view") == "none"
    assert kb.edge_insertion_mode("component_view") == "none"
    assert kb.edge_insertion_mode("class_view") == "all_selected"
    assert "system" in kb.keep_without_graph()
    assert "actor" in kb.keep_without_graph()
    assert kb.view_unit("component_view") == "component"
    assert kb.view_unit("class_view") == "type"
    assert kb.view_unit("sequence_view") == "component"
    assert kb.view_unit("context_view") == "context"
    assert kb.published_grain("context")["unit"] == "context"
    assert kb.published_grain("data-model")["unit"] == "type"
    assert kb.published_grain("scenario")["unit"] == "component"
    assert kb.view_unit("class_view", "data-model") == "type"
    assert kb.view_unit("component_view", "module-decomposition") == "component"
    missing = [vid for vid in kb.viewpoints if vid not in (kb.view_projection.get("published_grain") or {})]
    assert missing == []

