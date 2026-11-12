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
  E  D with the detail level given in the stakeholder perspective (inputs.yaml) instead of chosen by the agent;
     the critic judges against it and the inventory is checked against its budget (outputs-E/)
  F  E with a static dependency graph of the repository (.claude/repo-graph.json, built before the session with
     the Phase 0 repository card, tree-sitter): the agent finds the concern's code with graph_query.py, gives
     each element its members, and check_inventory.py checks the drawn relations against the graph (outputs-F/)
  G  F with component views built from a checked UML component model (model.json -> component_model.py, which
     draws the PlantUML), and a tighter critic (critic-G.txt): item-by-item findings marked blocking or minor,
     findings about the code count only if their citation exists, the program (not the critic) asks for the one
     revision when a checked blocking finding remains, and the version with fewer checked blocking findings is
     kept (outputs-G/)
  H  F on the inputs elicited in Phase 1 (inputs-elicited.yaml, written by elicit.py: fixed 42010 questions, a
     stakeholder's answers, the agent's proposed views; every plausible viewpoint becomes a view, so one request
     may give several views: case, case-2, ...); the skill adds the reviewer's rules (one viewpoint per view,
     use-case boundary, plain words instead of codes, styling stereotypes hidden) and check_view.py, readability rules
     checked on the rendered view (house style, fits a 1600 px screen, one reading direction, grouping) and, for
     the views of one task, shared names checked by check_consistency.py (later views read the earlier ones'
     inventories); no element budget; component views drawn by hand as in F (outputs-H/)

B and C ran with the skills as of commit 91dc18a, D with skills, critic.txt and check_inventory.py as of
e381c51, E as of 137e9ac, F as of 00a3ef1; built-in auto memory is off for every run.

    cd Task2View/code && .venv/bin/python ../experiments/view-generation-2026-10/run_generate.py [--condition B] [--only GR10-Q1] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
VIEW_FILES = ["view.puml", "view.png", "inventory.json", "README.md", "model.json"]
GRAPH = Path(".claude") / "repo-graph.json"


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def perspective(c: dict, with_level: bool) -> str:
    """The perspective's description, with its detail level when that is part of the input (condition E on)."""
    p = c["perspective"]
    if isinstance(p, str):
        return p
    return f"{p['description']}; detail level: {p['detail_level']}" if with_level else p["description"]


def fill(template: str, case: str, c: dict, entities: dict, with_level: bool = False, **extra: str) -> str:
    details = "\n".join(f"  - {d}" for d in c.get("concern_details", []))
    level = c["perspective"]["detail_level"] if isinstance(c["perspective"], dict) else ""
    return template.format(
        detail_level=level, request=c["request"], entity=entities[c["entity_of_interest"]]["description"],
        stakeholder=c["stakeholder"], perspective=perspective(c, with_level), concern=c["concern"], details=details,
        aspect=c["aspect"], viewpoint=c["viewpoint"], model_kind=c["model_kind"], case=case, **extra)


def build_graph(workdir: Path) -> None:
    """Write the static dependency graph (the Phase 0 repository card) for the repository copy, leaving out the
    copied skills and the agent's output folder."""
    from task2view.phase0.card import build_card

    card = json.loads(build_card(workdir).model_dump_json())
    own = (".claude/", "view-out/")
    outside = lambda path: not str(path).startswith(own)
    card["root"] = "."
    card["files"] = [f for f in card["files"] if outside(f["path"])]
    card["symbols"] = {k: s for k, s in card["symbols"].items() if outside(s["file"])}
    card["edges"] = [e for e in card["edges"] if outside(e["file"]) and e["target"] in card["symbols"]]
    card["entry_points"] = [e for e in card["entry_points"] if outside(e["file"])]
    (workdir / GRAPH).parent.mkdir(exist_ok=True)
    (workdir / GRAPH).write_text(json.dumps(card), encoding="utf-8")


def build_prompt(case: str, c: dict, entities: dict, cond: str) -> str:
    extra = "" if cond == "A" else (HERE / f"prompt-{cond}.txt").read_text()
    return fill((HERE / "prompt.txt").read_text() + extra, case, c, entities, with_level=cond in ("E", "F", "G", "H"))


class SessionFailed(RuntimeError):
    """A session ended on an API error (e.g. usage limit); the case is left unrecorded so a rerun redoes it."""


def claude(prompt: str, workdir: Path, log_file: Path, model: str, tools: list[str], resume: str = "") -> str:
    """Run one headless session; return its session id."""
    cmd = ["claude", "-p", prompt, "--model", model, "--permission-mode", "auto",
           "--output-format", "stream-json", "--verbose"] + (["--resume", resume] if resume else [])
    if tools:
        cmd += ["--allowedTools", *tools]
    with log_file.open("w", encoding="utf-8") as stream:
        subprocess.run(cmd, cwd=workdir, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, env=ENV)
    session = ""
    for line in log_file.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        session = session or event.get("session_id", "")
        if event.get("type") == "result" and event.get("api_error_status"):
            raise SessionFailed(f"{log_file.name}: {event.get('api_error')} ({event.get('result')})")
    return session


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


def critic_loop(case: str, c: dict, entities: dict, workdir: Path, logs: Path, session: str, lvl: bool) -> dict:
    produced = workdir / "view-out" / case
    critic = (HERE / "critic.txt").read_text()
    claude(fill(critic, case, c, entities, lvl, out="critique-1.json"), workdir, logs / f"{case}.critic-1.jsonl",
           CRITIC_MODEL, ["Read", "Grep", "Glob", f"Write(view-out/{case}/critique-1.json)"])
    first = score(produced / "critique-1.json")
    loop = {"critique_1": first, "revised": False, "kept": "v1"}
    try:
        verdict = json.loads((produced / "critique-1.json").read_text()).get("verdict")
    except (OSError, ValueError):
        verdict = None
    if verdict != "revise" or not session:
        return loop
    claude(fill((HERE / "revise.txt").read_text(), case, c, entities, lvl), workdir, logs / f"{case}.revise.jsonl",
           MODEL, TOOLS, resume=session)
    if not (produced / "v1" / "view.puml").exists():
        return {**loop, "note": "revision did not keep v1; kept what it wrote"}
    claude(fill(critic, case, c, entities, lvl, out="critique-2.json"), workdir, logs / f"{case}.critic-2.jsonl",
           CRITIC_MODEL, ["Read", "Grep", "Glob", f"Write(view-out/{case}/critique-2.json)"])
    second = score(produced / "critique-2.json")
    loop.update(revised=True, critique_2=second, kept="v2" if second >= first else "v1")
    if second < first:
        for f in VIEW_FILES:
            if (produced / "v1" / f).exists():
                shutil.copy(produced / "v1" / f, produced / f)
    return loop


def cites_code(evidence, repo: Path) -> bool:
    """True if at least one path:line or path:start-end citation exists in the repository."""
    for e in evidence if isinstance(evidence, list) else [evidence]:
        m = re.match(r"^(?P<path>[^:]+):(?P<a>\d+)(?:-(?P<b>\d+))?$", str(e).strip())
        f = repo / m["path"] if m else None
        if f and f.is_file() and 1 <= int(m["a"]) <= int(m["b"] or m["a"]) <= sum(1 for _ in f.open(errors="replace")):
            return True
    return False


def blocking(critique: Path, repo: Path) -> list[dict] | None:
    """The critique's blocking findings that hold: a concern detail answered "no" counts; a finding about the code
    ("unsupported", "missing") counts only if it cites code that exists. None if the critique is unreadable."""
    try:
        cr = json.loads(critique.read_text())
    except (OSError, ValueError):
        return None
    found = [f for f in cr.get("findings", []) if f.get("severity") == "blocking"
             and (f.get("kind") not in ("unsupported", "missing") or cites_code(f.get("evidence", []), repo))]
    named = {f.get("claim", "") for f in found}
    found += [{"severity": "blocking", "kind": "concern", "element": None, "claim": f"not answered: {d.get('detail')}",
               "fix": d.get("why", "")} for d in cr.get("concern_details", [])
              if d.get("answered") == "no" and f"not answered: {d.get('detail')}" not in named]
    return found


def critic_loop_g(case: str, c: dict, entities: dict, workdir: Path, logs: Path, session: str) -> dict:
    """Condition G: the program decides on the revision from the critic's checked blocking findings."""
    produced = workdir / "view-out" / case
    critic = (HERE / "critic-G.txt").read_text()
    tools = lambda out: ["Read", "Grep", "Glob", f"Write(view-out/{case}/{out})"]
    claude(fill(critic, case, c, entities, True, out="critique-1.json"), workdir, logs / f"{case}.critic-1.jsonl",
           CRITIC_MODEL, tools("critique-1.json"))
    first = blocking(produced / "critique-1.json", workdir)
    loop = {"blocking_1": None if first is None else len(first), "revised": False, "kept": "v1"}
    if not first or not session:
        return {**loop, "note": "critique unreadable" if first is None else "no checked blocking finding"}
    listed = "\n".join(f"- [{f.get('kind')}] {f.get('element') or '(missing)'}: {f.get('claim')} Fix: {f.get('fix')}"
                        for f in first)
    claude(fill((HERE / "revise-G.txt").read_text(), case, c, entities, True, findings=listed), workdir,
           logs / f"{case}.revise.jsonl", MODEL, TOOLS, resume=session)
    if not (produced / "v1" / "view.puml").exists():
        return {**loop, "note": "revision did not keep v1; kept what it wrote"}
    claude(fill(critic, case, c, entities, True, out="critique-2.json"), workdir, logs / f"{case}.critic-2.jsonl",
           CRITIC_MODEL, tools("critique-2.json"))
    second = blocking(produced / "critique-2.json", workdir)
    better = second is not None and len(second) < len(first)
    loop.update(revised=True, blocking_2=None if second is None else len(second), kept="v2" if better else "v1")
    if not better:
        for f in VIEW_FILES:
            if (produced / "v1" / f).exists():
                shutil.copy(produced / "v1" / f, produced / f)
    return loop


def task_of(case: str) -> str:
    """Condition H: the views of one task are case, case-2, case-3 ..."""
    return re.sub(r"-\d+$", "", case)


def run_case(case: str, c: dict, entities: dict, cond: str, dry: bool, earlier: list[tuple[str, dict]] = ()) -> bool:
    out_dir = HERE / ("outputs" if cond == "A" else f"outputs-{cond}") / case
    if (out_dir / "view.puml").exists():
        log(f"skip {case}: already generated")
        return True
    src = Path(entities[c["entity_of_interest"]]["repository"]).expanduser()
    workdir = SUBJECTS / ("" if cond == "A" else cond) / case / src.name
    prompt = build_prompt(case, c, entities, cond)
    if earlier:
        listed = "\n".join(f"  - {e} ({ec['viewpoint']}): ./view-out/{e}/inventory.json" for e, ec in earlier)
        prompt += ("\nThis task has more than one view. Views already drawn for it:\n" + listed + "\nRead their "
                   "inventories first: an element that stands for the same code keeps the same name and styling. "
                   "Then run check_consistency.py on all the inventories, as the skill describes, and fix what it "
                   "reports in your view.\n")
    if dry:
        log(f"would run {case} in {workdir}\n{prompt}")
        return True
    if not workdir.exists():
        subprocess.run([sys.executable, str(CODE / "scripts" / "prepare_subject.py"), "--src", str(src),
                        "--dst", str(workdir)], check=True, cwd=CODE)
    if cond != "A":
        for name, path in SKILLS.items():
            shutil.copytree(path, workdir / ".claude" / "skills" / name, dirs_exist_ok=True)
    if cond in ("F", "G", "H"):
        build_graph(workdir)
    for e, _ in earlier:
        done = HERE / f"outputs-{cond}" / e
        (workdir / "view-out" / e).mkdir(parents=True, exist_ok=True)
        for f in ("inventory.json", "view.puml"):
            if (done / f).exists():
                shutil.copy(done / f, workdir / "view-out" / e / f)
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
    lvl = cond in ("E", "F", "G", "H")
    loop = (critic_loop_g(case, c, entities, workdir, logs, session) if cond == "G" else
            critic_loop(case, c, entities, workdir, logs, session, lvl) if cond in ("D", "E", "F", "H") else None)
    shutil.copytree(produced, out_dir, dirs_exist_ok=True)
    if loop:
        (out_dir / "loop.json").write_text(json.dumps(loop, indent=2), encoding="utf-8")
    if lvl and (out_dir / "inventory.json").exists():
        graph = ["--graph", str(workdir / GRAPH)] if cond in ("F", "G", "H") else []
        check = subprocess.run([sys.executable, "-I", str(SKILLS["uml-view"] / "scripts" / "check_inventory.py"),
                                str(out_dir / "inventory.json"), "--repo", str(workdir),
                                "--level", c["perspective"]["detail_level"], *graph], capture_output=True, text=True)
        (out_dir / "inventory-check.txt").write_text(check.stdout, encoding="utf-8")
    if cond == "G" and (out_dir / "model.json").exists():
        check = subprocess.run([sys.executable, "-I", str(SKILLS["uml-view"] / "scripts" / "component_model.py"),
                                "check", str(out_dir / "model.json"), "--graph", str(workdir / GRAPH)],
                               capture_output=True, text=True)
        (out_dir / "model-check.txt").write_text(check.stdout, encoding="utf-8")
    if cond == "H":
        check = subprocess.run([sys.executable, "-I", str(SKILLS["uml-view"] / "scripts" / "check_view.py"),
                                str(out_dir / "view.puml")], capture_output=True, text=True)
        (out_dir / "view-check.txt").write_text(check.stdout, encoding="utf-8")
    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    if shutil.which("plantuml") and not (out_dir / "view.png").exists():
        with (out_dir / "view.puml").open("rb") as src_puml, (out_dir / "view.png").open("wb") as png:
            subprocess.run(["plantuml", "-tpng", "-pipe"], stdin=src_puml, stdout=png)
    log(f"done {case}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--condition", choices=["A", "B", "C", "D", "E", "F", "G", "H"], default="A")
    parser.add_argument("--only")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sheet = yaml.safe_load((HERE / ("inputs-elicited.yaml" if args.condition == "H" else "inputs.yaml")).read_text())
    for case, c in sheet["cases"].items():
        if args.only and task_of(case) != args.only:
            continue
        earlier = [(e, ec) for e, ec in sheet["cases"].items() if args.condition == "H" and e != case
                   and task_of(e) == task_of(case) and list(sheet["cases"]).index(e) < list(sheet["cases"]).index(case)]
        try:
            ok = run_case(case, c, sheet["entities_of_interest"], args.condition, args.dry_run, earlier)
        except SessionFailed as e:
            log(f"stop: {case} not recorded; {e}. Delete its workdir before rerunning.")
            return 2
        if not ok:
            return 2
    if args.condition == "H" and not args.dry_run:
        tasks: dict[str, list[str]] = {}
        for case in sheet["cases"]:
            tasks.setdefault(task_of(case), []).append(case)
        for task, views in tasks.items():
            invs = [HERE / "outputs-H" / v / "inventory.json" for v in views]
            if len(views) > 1 and all(i.exists() for i in invs):
                check = subprocess.run([sys.executable, "-I", str(SKILLS["uml-view"] / "scripts" /
                                        "check_consistency.py"), *map(str, invs)], capture_output=True, text=True)
                for v in views:
                    (HERE / "outputs-H" / v / "consistency-check.txt").write_text(check.stdout, encoding="utf-8")
    log("all cases done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
