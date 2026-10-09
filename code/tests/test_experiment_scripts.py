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
            return json.dumps({"reason": "r", "score": 4})

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

    # a blind rating sheet, one rater's scores, and their agreement with the judge
    out = tmp_path / "rating"
    monkeypatch.setattr(sys, "argv", ["make_rating_sheet.py", "--runs", str(runs), "--goals", str(goals),
                                      "--out", str(out), "--rater", "r1"])
    assert _script("make_rating_sheet").main() == 0
    sheet = list(csv.DictReader((out / "rating_sheet.csv").open()))
    assert len(sheet) == 3 and "condition" not in sheet[0] and (out / "items" / "I001.puml").exists()
    for i, row in enumerate(sheet):
        row["answers-questions"] = "3" if i == 0 else "4"
    with (tmp_path / "ratings.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(sheet[0]))
        writer.writeheader()
        writer.writerows(sheet)
    lines = _script("judge_agreement").from_ratings(tmp_path / "ratings.csv", out / "rating_key.csv",
                                                    tmp_path / "judge_summary.csv")
    assert any(line.startswith("answers-questions | r1 vs judge | 3 |") for line in lines)


def test_weighted_kappa():
    kappa = _script("judge_agreement").weighted_kappa
    assert kappa([1, 3, 5], [1, 3, 5]) == 1.0
    assert kappa([1, 5], [5, 1]) < 0
    assert kappa([3], [3]) is None


def test_expert_labels_are_compared_descriptively(tmp_path):
    run = tmp_path / "outputs" / "plain-agent" / "italian-reviewed" / "G1"
    run.mkdir(parents=True)
    (run / "judge.json").write_text(json.dumps({"view-1": {"scores": {"layout": {"reason": "r", "score": 2}}}}))
    labels = tmp_path / "review" / "expert_labels.yaml"
    labels.parent.mkdir()
    labels.write_text(yaml.safe_dump({"rater": "e1", "rubric": "v1", "entries": [
        {"condition": "plain-agent", "case": "G1", "run_dir": "outputs/plain-agent/italian-reviewed/G1",
         "problems": ["layout"], "praised": []}]}))
    lines = _script("judge_agreement").from_labels(labels)
    assert "layout | 1, 2.00, 100% | 0" in lines


def test_pilot_expert_labels_cover_the_reviewed_outputs():
    doc = yaml.safe_load((CODE.parent / "experiments" / "pilot-2026-09" / "review" / "expert_labels.yaml").read_text())
    from task2view.phase8.judge import THEMES
    assert len(doc["entries"]) == 20
    for e in doc["entries"]:
        assert set(e["problems"]) | set(e["praised"]) <= set(THEMES)
        assert (CODE.parent / "experiments" / "pilot-2026-09" / e["run_dir"]).is_dir()


def test_run_stability_compares_repeated_runs(tmp_path, capsys, monkeypatch):
    import shutil

    from task2view.agents.run_v2 import run_v2
    from task2view.agents.write_v2 import write_run_v2

    from .test_run_v2 import GOAL, SHOP, scripted

    first = write_run_v2(run_v2(GOAL, str(SHOP), generate=scripted), tmp_path / "task2view" / "CASE-1@1")
    shutil.copytree(first, tmp_path / "task2view" / "CASE-1@2")
    monkeypatch.setattr(sys, "argv", ["run_stability.py", "--runs", str(tmp_path)])
    assert _script("run_stability").main() == 0
    assert "task2view | CASE-1 | 2 | 1/1 | 1.00 | 1.00" in capsys.readouterr().out
