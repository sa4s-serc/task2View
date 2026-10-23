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
