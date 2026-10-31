"""Central question: given the 42010:2022 inputs (inputs.yaml) and the repository, can a view be generated?

One headless Claude Code session per case, in a fresh prepared copy of the repository, with prompt.txt
filled from the case's inputs. The view and README go to outputs/<case>/, the event stream to logs/.
A case whose outputs exist is skipped.

Conditions (--condition):
  A  the agent alone (outputs/)
  B  A + the uml-view and plantuml-diagrams skills, whose render-check-look loop is the feedback (outputs-B/)
  C  B + memory: one notes file per repository, read before and updated after each case, cases in sheet
     order (outputs-C/, memory/)

    cd Task2View/code && .venv/bin/python ../experiments/view-generation-2026-10/run_generate.py [--condition B] [--only GR10-Q1] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1] / "code"
SUBJECTS = Path.home() / "t2v-subjects" / "view-generation"
MODEL = "claude-sonnet-5-5"
SKILLS = {"uml-view": HERE / "skill" / "uml-view",
          "plantuml-diagrams": Path.home() / "t2v-subjects" / "vendor" / "plantuml-diagrams-skill" / "skills" / "plantuml-diagrams"}
TOOLS = ["Bash(python3 .claude/skills/plantuml-diagrams/scripts/*)", "Bash(.claude/skills/plantuml-diagrams/scripts/*)",
         "Bash(plantuml *)"]


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def build_prompt(case: str, c: dict, entities: dict, cond: str) -> str:
    details = "\n".join(f"  - {d}" for d in c.get("concern_details", []))
    extra = "" if cond == "A" else (HERE / f"prompt-{cond}.txt").read_text()
    return ((HERE / "prompt.txt").read_text() + extra).format(
        request=c["request"], entity=entities[c["entity_of_interest"]]["description"],
        stakeholder=c["stakeholder"], perspective=c["perspective"], concern=c["concern"], details=details,
        aspect=c["aspect"], viewpoint=c["viewpoint"], model_kind=c["model_kind"], case=case)


def run_case(case: str, c: dict, entities: dict, cond: str, dry: bool) -> bool:
    out_dir = HERE / ("outputs" if cond == "A" else f"outputs-{cond}") / case
    if (out_dir / "view.puml").exists():
        log(f"skip {case}: already generated")
        return True
    src = Path(entities[c["entity_of_interest"]]["repository"]).expanduser()
    workdir = SUBJECTS / ("" if cond == "A" else cond) / case / src.name
    prompt = build_prompt(case, c, entities, cond)
    if dry:
        log(f"would run {case} in {workdir}\n{prompt}")
        return True
    if not workdir.exists():
        subprocess.run([sys.executable, str(CODE / "scripts" / "prepare_subject.py"), "--src", str(src),
                        "--dst", str(workdir)], check=True, cwd=CODE)
    cmd = ["claude", "-p", prompt, "--model", MODEL, "--permission-mode", "auto",
           "--output-format", "stream-json", "--verbose"]
    if cond != "A":
        for name, path in SKILLS.items():
            shutil.copytree(path, workdir / ".claude" / "skills" / name, dirs_exist_ok=True)
        cmd += ["--allowedTools", *TOOLS]
    memory = HERE / "memory" / f"{c['entity_of_interest']}.md"
    if cond == "C":
        memory.parent.mkdir(exist_ok=True)
        memory.touch()
        (workdir / "memory").mkdir(exist_ok=True)
        shutil.copy(memory, workdir / "memory" / memory.name)
    logs = HERE / ("logs" if cond == "A" else f"logs-{cond}")
    logs.mkdir(exist_ok=True)
    log(f"running {case} (condition {cond})")
    with (logs / f"{case}.jsonl").open("w", encoding="utf-8") as stream:
        subprocess.run(cmd, cwd=workdir, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
    if cond == "C":
        shutil.copy(workdir / "memory" / memory.name, memory)
        shutil.copy(memory, HERE / "memory" / f"{memory.stem}.after-{case}.md")
    produced = workdir / "view-out" / case
    if not (produced / "view.puml").exists():
        log(f"stop: {case} wrote no view.puml; see logs/{case}.jsonl")
        return False
    shutil.copytree(produced, out_dir, dirs_exist_ok=True)
    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    if shutil.which("plantuml") and not (out_dir / "view.png").exists():
        with (out_dir / "view.puml").open("rb") as src_puml, (out_dir / "view.png").open("wb") as png:
            subprocess.run(["plantuml", "-tpng", "-pipe"], stdin=src_puml, stdout=png)
    log(f"done {case}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--condition", choices=["A", "B", "C"], default="A")
    parser.add_argument("--only")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sheet = yaml.safe_load((HERE / "inputs.yaml").read_text())
    for case, c in sheet["cases"].items():
        if args.only and case != args.only:
            continue
        if not run_case(case, c, sheet["entities_of_interest"], args.condition, args.dry_run):
            return 2
    log("all cases done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
