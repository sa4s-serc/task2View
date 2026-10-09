"""Experiment helper scripts: subject preparation and post-hoc judging (no network)."""

import csv
import importlib.util
import json
import sys
from pathlib import Path

import yaml

CODE = Path(__file__).resolve().parents[1]


def _script(name):
    spec = importlib.util.spec_from_file_location(name, CODE / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prepare_subject_drops_models_and_images(tmp_path):
    src = tmp_path / "repo"
    (src / "src").mkdir(parents=True)
    (src / "docs").mkdir()
    (src / ".git").mkdir()
    (src / "src" / "A.java").write_text("class A {}")
    (src / "pom.xml").write_text("<project/>")
    (src / "docs" / "model.vpp").write_bytes(b"\x00vp")
    (src / "docs" / "class-diagram.png").write_bytes(b"\x89PNG")
    (src / ".git" / "HEAD").write_text("ref")
    dst = tmp_path / "copy"
    record = _script("prepare_subject").prepare(src, dst)
    assert (dst / "src" / "A.java").exists() and (dst / "pom.xml").exists()
    assert not (dst / "docs" / "model.vpp").exists() and not (dst / "docs" / "class-diagram.png").exists()
    assert not (dst / ".git").exists()
    assert {r["path"] for r in record["removed"]} == {"docs/model.vpp", "docs/class-diagram.png"}
    assert not (dst / "PREPARED.json").exists()
    assert json.loads(dst.with_name(f"{dst.name}.PREPARED.json").read_text())["copied_files"] == 2


def test_judge_outputs_scores_pipeline_and_plain_runs(tmp_path, monkeypatch):
    from task2view.agents.run_v2 import run_v2
    from task2view.agents.write_v2 import write_run_v2
    from task2view.llm.base import LLMClient
    from task2view.llm.registry import register_provider

    from .test_run_v2 import GOAL, SHOP, scripted

    seen = []

    @register_provider("judge-fixture", default_model="j")
    class Judge(LLMClient):
        provider = "judge-fixture"

        def complete_text(self, prompt, *, system=None, json_mode=False):
            seen.append(prompt)
            return json.dumps({"scores": {"grain": {"score": 3, "reason": "r"}},
                               "answers_questions": {"score": 4, "reason": "r"}, "overall": 3, "summary": "s"})

    runs = tmp_path / "outputs"
    write_run_v2(run_v2(GOAL, str(SHOP), generate=scripted), runs / "task2view" / "CASE-1")
    plain = runs / "plain-agent" / "CASE-1"
    plain.mkdir(parents=True)
    (plain / "view-1.puml").write_text("@startuml\ncomponent OrderService\n@enduml\n")
    goals = tmp_path / "goals.yaml"
    goals.write_text(yaml.safe_dump({"cases": {"CASE-1": {"goal": GOAL}}}))

    monkeypatch.setattr(sys, "argv", ["judge_outputs.py", "--runs", str(runs), "--goals", str(goals),
                                      "--judge-llm", "judge-fixture"])
    assert _script("judge_outputs").main() == 0
    rows = list(csv.DictReader((tmp_path / "judge_summary.csv").open()))
    assert {(r["condition"], r["view"]) for r in rows} == {
        ("plain-agent", "view-1"), ("task2view", "V1-client-server"), ("task2view", "V2-sequence")}
    assert all(r["judge"] == "judge-fixture:j" and r["score_answers-questions"] == "4" for r in rows)
    assert any("component OrderService" in p for p in seen)
    assert json.loads((plain / "judge.json").read_text())["view-1"]["status"] == "scored"
