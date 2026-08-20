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
