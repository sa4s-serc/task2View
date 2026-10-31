"""Central question: given the 42010:2022 inputs (inputs.yaml) and the repository, can a view be generated?

One headless Claude Code session per case, in a fresh prepared copy of the repository, with prompt.txt
filled from the case's inputs. The view and README go to outputs/<case>/, the event stream to logs/.
A case whose outputs exist is skipped.

Conditions (--condition):
  A  the agent alone (outputs/)
  B  A + the uml-view and plantuml-diagrams skills, whose render-check-look loop is the feedback (outputs-B/)
  C  B + memory: one notes file per repository, read before and updated after each case, cases in sheet
     order (outputs-C/, memory/)
  D  B with the revised skill (inventory.json checked by a script, examples, no self-review of the image) and a
     separate critic: a fresh session on a different model reviews the view (critique-1.json); if it asks for a
     revision, the generator session is resumed once with the critique; the critic reviews again
     (critique-2.json) and the better-scored version is kept (loop.json). No memory (outputs-D/)

B and C ran with the skills as of commit 91dc18a; built-in auto memory is off for every run.

    cd Task2View/code && .venv/bin/python ../experiments/view-generation-2026-10/run_generate.py [--condition B] [--only GR10-Q1] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
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
CRITIC_MODEL = "claude-opus-5-5"
SKILLS = {"uml-view": HERE / "skill" / "uml-view", "plantuml-diagrams": HERE / "skill" / "plantuml-diagrams"}
TOOLS = ["Bash(python3 -I .claude/skills/*)", "Bash(python3 .claude/skills/*)", "Bash(.claude/skills/*)",
         "Bash(plantuml *)"]
ENV = {**os.environ, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
VIEW_FILES = ["view.puml", "view.png", "inventory.json", "README.md"]


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def fill(template: str, case: str, c: dict, entities: dict, **extra: str) -> str:
    details = "\n".join(f"  - {d}" for d in c.get("concern_details", []))
    return template.format(
        request=c["request"], entity=entities[c["entity_of_interest"]]["description"],
        stakeholder=c["stakeholder"], perspective=c["perspective"], concern=c["concern"], details=details,
        aspect=c["aspect"], viewpoint=c["viewpoint"], model_kind=c["model_kind"], case=case, **extra)


def build_prompt(case: str, c: dict, entities: dict, cond: str) -> str:
    extra = "" if cond == "A" else (HERE / f"prompt-{cond}.txt").read_text()
    return fill((HERE / "prompt.txt").read_text() + extra, case, c, entities)


def claude(prompt: str, workdir: Path, log_file: Path, model: str, tools: list[str], resume: str = "") -> str:
    """Run one headless session; return its session id."""
    cmd = ["claude", "-p", prompt, "--model", model, "--permission-mode", "auto",
           "--output-format", "stream-json", "--verbose"] + (["--resume", resume] if resume else [])
    if tools:
        cmd += ["--allowedTools", *tools]
    with log_file.open("w", encoding="utf-8") as stream:
        subprocess.run(cmd, cwd=workdir, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, env=ENV)
    for line in log_file.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("session_id"):
            return event["session_id"]
    return ""


def score(critique: Path) -> tuple[int, int]:
    """Critic score of one version: answered concern details, level fit, minus unsupported items."""
    try:
        cr = json.loads(critique.read_text())
    except (OSError, ValueError):
        return (-99, 0)
    points = {"yes": 2, "partly": 1}
    s = sum(points.get(d.get("answered"), 0) for d in cr.get("concern_details", []))
    s += 2 if cr.get("level") == "right" else 0
    return (s - len(cr.get("unsupported", [])), 1 if cr.get("verdict") == "accept" else 0)


def critic_loop(case: str, c: dict, entities: dict, workdir: Path, logs: Path, session: str) -> dict:
    produced = workdir / "view-out" / case
    critic = (HERE / "critic.txt").read_text()
    claude(fill(critic, case, c, entities, out="critique-1.json"), workdir, logs / f"{case}.critic-1.jsonl",
           CRITIC_MODEL, ["Read", "Grep", "Glob", f"Write(view-out/{case}/critique-1.json)"])
    first = score(produced / "critique-1.json")
    loop = {"critique_1": first, "revised": False, "kept": "v1"}
    try:
        verdict = json.loads((produced / "critique-1.json").read_text()).get("verdict")
    except (OSError, ValueError):
        verdict = None
    if verdict != "revise" or not session:
        return loop
    claude(fill((HERE / "revise.txt").read_text(), case, c, entities), workdir, logs / f"{case}.revise.jsonl",
           MODEL, TOOLS, resume=session)
    if not (produced / "v1" / "view.puml").exists():
        return {**loop, "note": "revision did not keep v1; kept what it wrote"}
    claude(fill(critic, case, c, entities, out="critique-2.json"), workdir, logs / f"{case}.critic-2.jsonl",
           CRITIC_MODEL, ["Read", "Grep", "Glob", f"Write(view-out/{case}/critique-2.json)"])
    second = score(produced / "critique-2.json")
    loop.update(revised=True, critique_2=second, kept="v2" if second >= first else "v1")
    if second < first:
        for f in VIEW_FILES:
            if (produced / "v1" / f).exists():
                shutil.copy(produced / "v1" / f, produced / f)
    return loop


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
    if cond != "A":
        for name, path in SKILLS.items():
            shutil.copytree(path, workdir / ".claude" / "skills" / name, dirs_exist_ok=True)
    memory = HERE / "memory" / f"{c['entity_of_interest']}.md"
    if cond == "C":
        memory.parent.mkdir(exist_ok=True)
        memory.touch()
        (workdir / "memory").mkdir(exist_ok=True)
        shutil.copy(memory, workdir / "memory" / memory.name)
    logs = HERE / ("logs" if cond == "A" else f"logs-{cond}")
    logs.mkdir(exist_ok=True)
    log(f"running {case} (condition {cond})")
    session = claude(prompt, workdir, logs / f"{case}.jsonl", MODEL, [] if cond == "A" else TOOLS)
    if cond == "C":
        shutil.copy(workdir / "memory" / memory.name, memory)
        shutil.copy(memory, HERE / "memory" / f"{memory.stem}.after-{case}.md")
    produced = workdir / "view-out" / case
    if not (produced / "view.puml").exists():
        log(f"stop: {case} wrote no view.puml; see {logs.name}/{case}.jsonl")
        return False
    loop = critic_loop(case, c, entities, workdir, logs, session) if cond == "D" else None
    shutil.copytree(produced, out_dir, dirs_exist_ok=True)
    if loop:
        (out_dir / "loop.json").write_text(json.dumps(loop, indent=2), encoding="utf-8")
    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    if shutil.which("plantuml") and not (out_dir / "view.png").exists():
        with (out_dir / "view.puml").open("rb") as src_puml, (out_dir / "view.png").open("wb") as png:
            subprocess.run(["plantuml", "-tpng", "-pipe"], stdin=src_puml, stdout=png)
    log(f"done {case}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--condition", choices=["A", "B", "C", "D"], default="A")
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
