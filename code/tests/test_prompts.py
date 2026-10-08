"""The prompt files: human header, shared structure, placeholders, and agreement with the code."""

import re

import pytest

from task2view.phase5.card_tools import TOOLS, CardTools
from task2view.prompts import load_prompt, prompt_ids

IDS = prompt_ids()


def test_every_model_call_has_a_prompt_file():
    assert IDS == ["phase1_interpret", "phase4_investigate", "phase5_evidence", "phase8_judge"]


@pytest.mark.parametrize("prompt_id", IDS)
def test_front_matter_documents_the_call(prompt_id):
    meta = load_prompt(prompt_id).meta
    for key in ("id", "phase", "called_from", "purpose", "inputs", "output", "checked_by"):
        assert meta.get(key), f"{prompt_id}: front matter lacks {key}"
    assert set(meta["inputs"]) == load_prompt(prompt_id).placeholders, "documented inputs must match placeholders"


@pytest.mark.parametrize("prompt_id", IDS)
def test_shared_structure(prompt_id):
    body = load_prompt(prompt_id).body
    assert body.startswith("# Task2View — Phase ")
    for section in ("## Role", "## Output", "## Check before answering"):
        assert section in body, f"{prompt_id}: missing {section}"


@pytest.mark.parametrize("prompt_id", IDS)
def test_examples_do_not_use_pilot_domains(prompt_id):
    body = load_prompt(prompt_id).body.lower()
    for word in ("seat", "registration", "librar", "municipal", "citizen", "reservation"):
        assert word not in body, f"{prompt_id} mentions pilot vocabulary {word!r}"


def test_render_rejects_missing_and_unknown_placeholders():
    prompt = load_prompt("phase4_investigate")
    with pytest.raises(KeyError):
        prompt.render(card="x")
    values = {name: "v" for name in prompt.placeholders}
    with pytest.raises(KeyError):
        prompt.render(**values, extra="y")
    assert "{{" not in prompt.render(**values)


def test_phase5_documents_exactly_the_implemented_tools():
    body = load_prompt("phase5_evidence").body
    documented = set(re.findall(r'"tool": "(\w+)"', body))
    assert documented == set(TOOLS)
    tools = CardTools.__new__(CardTools)
    for name in TOOLS:
        assert hasattr(tools, name)


def test_phase1_lists_every_vocabulary_when_rendered():
    from task2view.agents.runtime import AgentRuntime
    from task2view.knowledge.catalog import load_catalog
    from task2view.phase1.needs import extract_needs

    seen = {}

    def generate(prompt, model=None):
        seen["p"] = prompt
        return {"needs": []}

    catalog = load_catalog()
    extract_needs("I am a tester. I need to see the components.", AgentRuntime(generate=generate), catalog=catalog)
    for need in catalog.needs:
        assert f"- {need}:" in seen["p"]
    for role in catalog.roles:
        assert f"- {role}:" in seen["p"]
    assert "front matter" not in seen["p"] and "checked_by" not in seen["p"]
