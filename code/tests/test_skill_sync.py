"""The single-agent skill stays in step with the pipeline (run scripts/sync_skill.py to fix)."""

import importlib.util
import re
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
SKILL = CODE.parent / "skill"


def _sync_module():
    spec = importlib.util.spec_from_file_location("sync_skill", CODE / "scripts" / "sync_skill.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_knowledge_copies_are_identical():
    sync = _sync_module()
    for name in sync.COPIED:
        assert (SKILL / "knowledge" / Path(name).name).read_bytes() == (sync.SOURCE / name).read_bytes(), \
            f"skill/knowledge/{Path(name).name} is stale: run scripts/sync_skill.py"


def test_generated_references_are_current():
    from task2view.knowledge.catalog import load_catalog

    sync = _sync_module()
    assert (SKILL / "references" / "catalogs.md").read_text() == sync.catalogs_markdown(load_catalog())
    assert (SKILL / "references" / "goal-sets.md").read_text() == sync.goal_sets_markdown()


def test_goal_sets_carry_no_answer_key():
    text = (SKILL / "references" / "goal-sets.md").read_text()
    assert "expect" not in text.replace("expected to work", "")
    assert "viewpoint" not in text.lower()


def test_skill_output_files_match_the_pipeline_writer():
    writer = (CODE / "src" / "task2view" / "agents" / "write_v2.py").read_text()
    written = set(re.findall(r'"([a-z_]+\.(?:json|md|txt))"', writer))
    schema = (SKILL / "references" / "output-schema.md").read_text()
    for name in written - {"run.log"}:
        assert name in schema, f"output-schema.md does not document {name}"


def test_skill_links_resolve():
    for md in [SKILL / "SKILL.md", SKILL / "README.md", *(SKILL / "references").glob("*.md")]:
        for target in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text()):
            if target.startswith("http"):
                continue
            assert (md.parent / target).exists(), f"{md.name} links to missing {target}"
