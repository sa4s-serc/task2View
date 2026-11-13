"""Phase 2: generate one view from its 42010 input record.

  static graph -> generator agent (uml-view skill) -> checks -> critic agent (fresh session, other model)
  -> at most one revision -> second critique -> the better-scored version is kept
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

from . import claude, config

SKILLS = config.PACKAGE / "skills"
SCRIPTS = SKILLS / "uml-view" / "scripts"
GENERATOR_TOOLS = ["Bash(python3 -I .claude/skills/*)", "Bash(python3 .claude/skills/*)", "Bash(.claude/skills/*)",
                   "Bash(plantuml *)"]
VIEW_FILES = ["view.puml", "view.png", "inventory.json", "README.md"]
GRAPH = Path(".claude") / "repo-graph.json"


def _prompt(name: str) -> str:
    return (config.PACKAGE / "prompts" / name).read_text()


def fill(template: str, record: dict, **extra: str) -> str:
    p = record["perspective"]
    said = record["clarifications"]
    return template.format(
        case=record["id"], request=record["request"], entity=record["entity_of_interest"], focus=record["focus"],
        stakeholder=record["stakeholder"], perspective=f"{p['description']}; detail level: {p['detail_level']}",
        detail_level=p["detail_level"], concern=record["concern"],
        details="\n".join(f"  - {d}" for d in record["concern_details"]),
        aspect=record["aspect"], viewpoint=record["viewpoint"], model_kind=record["model_kind"],
        clarifications="".join(["- Clarifications from the stakeholder:\n"] + [f"  - {s}\n" for s in said]) if said
        else "", **extra)


def generator_prompt(record: dict, earlier: list[dict]) -> str:
    prompt = fill(_prompt("generate.txt"), record)
    if earlier:
        listed = "\n".join(f"  - {e['id']} ({e['viewpoint']}): ./view-out/{e['id']}/inventory.json" for e in earlier)
        prompt += ("\nThis task has more than one view. Views already drawn for it:\n" + listed + "\nRead their "
                   "inventories first: an element that stands for the same code keeps the same name and styling. "
                   "Then run check_consistency.py on all the inventories, as the skill describes, and fix what it "
                   "reports in your view.\n")
    return prompt


def make_workdir(repo: Path, graph: Path, workdir: Path, earlier: list[dict], out: Path) -> None:
    """A fresh copy of the repository with the skills, the graph and the task's earlier views."""
    if workdir.exists():
        shutil.rmtree(workdir)
    shutil.copytree(repo, workdir)
    shutil.copytree(SKILLS, workdir / ".claude" / "skills", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(graph, workdir / GRAPH)
    for e in earlier:
        target = workdir / "view-out" / e["id"]
        target.mkdir(parents=True)
        for name in ("inventory.json", "view.puml"):
            if (out / e["id"] / name).exists():
                shutil.copy(out / e["id"] / name, target / name)


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


def critic_loop(record: dict, workdir: Path, logs: Path, session: str, step: Callable[[str], None]) -> dict:
    case = record["id"]
    produced = workdir / "view-out" / case

    def critique(n: int) -> tuple[int, int]:
        name = f"critique-{n}.json"
        claude.session(fill(_prompt("critic.txt"), record, out=name), workdir, logs / f"{case}.critic-{n}.jsonl",
                       config.CRITIC_MODEL, ["Read", "Grep", "Glob", f"Write(view-out/{case}/{name})"])
        return score(produced / name)

    step("reviewing")
    first = critique(1)
    loop = {"critique_1": first, "revised": False, "kept": "v1"}
    try:
        verdict = json.loads((produced / "critique-1.json").read_text()).get("verdict")
    except (OSError, ValueError):
        verdict = None
    if verdict != "revise":
        return loop
    step("revising")
    claude.session(fill(_prompt("revise.txt"), record), workdir, logs / f"{case}.revise.jsonl",
                   config.GENERATOR_MODEL, GENERATOR_TOOLS, resume=session)
    if not (produced / "v1" / "view.puml").exists():
        return {**loop, "note": "revision did not keep v1; kept what it wrote"}
    step("reviewing the revision")
    second = critique(2)
    loop.update(revised=True, critique_2=second, kept="v2" if second >= first else "v1")
    if second < first:
        for name in VIEW_FILES:
            if (produced / "v1" / name).exists():
                shutil.copy(produced / "v1" / name, produced / name)
    return loop


def _check(script: str, result: Path, *args: str) -> None:
    """Run a check script of the skill; its output goes to `result`, with a first line "passed" or "issues"."""
    run = subprocess.run([sys.executable, "-I", str(SCRIPTS / script), *args], capture_output=True, text=True)
    result.write_text(("passed\n" if run.returncode == 0 else "issues\n") + (run.stdout or run.stderr),
                      encoding="utf-8")


def run_view(record: dict, earlier: list[dict], repo: Path, graph: Path, workdir: Path, out: Path, logs: Path,
             step: Callable[[str], None]) -> None:
    """Generate one view into out/<view id>/. `earlier` are the records of this task's views already drawn."""
    case = record["id"]
    make_workdir(repo, graph, workdir, earlier, out)
    prompt = generator_prompt(record, earlier)
    step("drawing")
    session = claude.session(prompt, workdir, logs / f"{case}.jsonl", config.GENERATOR_MODEL, GENERATOR_TOOLS)
    produced = workdir / "view-out" / case
    if not (produced / "view.puml").exists():
        raise claude.ClaudeError(f"The generator wrote no view for {case}; see logs/{case}.jsonl")
    loop = critic_loop(record, workdir, logs, session, step)

    step("checking")
    _publish(record, workdir, out, {**loop, "session": session})
    (out / case / "prompt.txt").write_text(prompt, encoding="utf-8")


def apply_feedback(record: dict, text: str, round_no: int, workdir: Path, out: Path, logs: Path,
                   step: Callable[[str], None]) -> None:
    """Revise a finished view after the stakeholder's feedback, then review and check it again."""
    case = record["id"]
    produced = workdir / "view-out" / case
    loop = json.loads((out / case / "loop.json").read_text())
    before = produced / f"before-feedback-{round_no}"
    before.mkdir(exist_ok=True)
    for name in VIEW_FILES:
        if (produced / name).exists():
            shutil.copy(produced / name, before / name)

    step("applying your feedback")
    prompt = fill(_prompt("feedback.txt"), record, feedback=text)
    try:
        claude.session(prompt, workdir, logs / f"{case}.feedback-{round_no}.jsonl", config.GENERATOR_MODEL,
                       GENERATOR_TOOLS, resume=loop.get("session", ""))
    except claude.ClaudeError:
        if not loop.get("session"):
            raise
        claude.session(prompt, workdir, logs / f"{case}.feedback-{round_no}.jsonl", config.GENERATOR_MODEL,
                       GENERATOR_TOOLS)     # the first session can no longer be resumed; the prompt stands alone

    step("reviewing the change")
    name = f"critique-feedback-{round_no}.json"
    claude.session(fill(_prompt("critic.txt"), record, out=name), workdir,
                   logs / f"{case}.critic-feedback-{round_no}.jsonl", config.CRITIC_MODEL,
                   ["Read", "Grep", "Glob", f"Write(view-out/{case}/{name})"])
    step("checking")
    _publish(record, workdir, out, {**loop, "feedback_critique": name}, keep=("prompt.txt",))


def _publish(record: dict, workdir: Path, out: Path, loop: dict, keep: tuple[str, ...] = ()) -> None:
    """Copy the view from the agents' working copy to the result folder and run the checks on it."""
    case = record["id"]
    target = out / case
    kept = {name: (target / name).read_bytes() for name in keep if (target / name).exists()}
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(workdir / "view-out" / case, target)
    for name, content in kept.items():
        (target / name).write_bytes(content)
    (target / "loop.json").write_text(json.dumps(loop, indent=2), encoding="utf-8")
    if (target / "inventory.json").exists():
        _check("check_inventory.py", target / "inventory-check.txt", str(target / "inventory.json"),
               "--repo", str(workdir), "--level", record["perspective"]["detail_level"],
               "--graph", str(workdir / GRAPH))
    _check("check_view.py", target / "view-check.txt", str(target / "view.puml"))
    if shutil.which("plantuml"):
        with (target / "view.puml").open("rb") as src, (target / "view.png").open("wb") as png:
            subprocess.run(["plantuml", "-tpng", "-pipe"], stdin=src, stdout=png)


def check_consistency(view_ids: list[str], out: Path) -> None:
    """Same names for the same code across the views of one task."""
    inventories = [out / v / "inventory.json" for v in view_ids]
    if len(view_ids) > 1 and all(i.exists() for i in inventories):
        _check("check_consistency.py", out / view_ids[0] / "consistency-check.txt", *map(str, inventories))
        for v in view_ids[1:]:
            shutil.copy(out / view_ids[0] / "consistency-check.txt", out / v / "consistency-check.txt")
