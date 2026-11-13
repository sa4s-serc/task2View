"""Jobs: one request on one repository, run in the background in two stages around the stakeholder's answers.

  prepare    get the repository, copy it for the agents, build the static graph, pre-fill the questions
             -> state "questions", waiting for the stakeholder
  generate   propose the views, generate each in order, check them together, write the report
             -> state "done"

Everything about a job is in its folder under T2V_HOME/jobs/<id>/; job.json holds its state.
"""

from __future__ import annotations

import json
import re
import secrets
import shutil
import threading
import traceback
from datetime import datetime
from pathlib import Path

from . import config, phase1, phase2, repo, report
from .claude import ClaudeError

JOB_ID = re.compile(r"\d{8}-\d{6}-[0-9a-f]{6}")
RUNNING = ("preparing", "generating")
_lock = threading.Lock()
_active: set[str] = set()


class Job:
    def __init__(self, job_id: str):
        if not JOB_ID.fullmatch(job_id):
            raise KeyError(job_id)
        self.id = job_id
        self.dir = config.T2V_HOME / "jobs" / job_id
        self.upload = self.dir / "upload.zip"
        self.source = self.dir / "source"       # the repository as given
        self.repo = self.dir / "repo"           # the copy the agents get
        self.graph = self.dir / "repo-graph.json"
        self.work = self.dir / "work"           # one working copy per view
        self.out = self.dir / "out"             # the result: README.md, inputs.yaml, view-N/
        self.logs = self.dir / "logs"

    def read(self) -> dict:
        try:
            return json.loads((self.dir / "job.json").read_text())
        except OSError:
            raise KeyError(self.id) from None

    def update(self, **changes) -> dict:
        with _lock:
            state = {**self.read(), **changes}
            state["version"] = state.get("version", 0) + 1
            tmp = self.dir / "job.json.tmp"
            tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
            tmp.replace(self.dir / "job.json")
            return state


def create(request: str, source: dict) -> Job:
    job = Job(f"{datetime.now():%Y%m%d-%H%M%S}-{secrets.token_hex(3)}")
    job.dir.mkdir(parents=True)
    (job.dir / "job.json").write_text(json.dumps({
        "id": job.id, "created": f"{datetime.now():%Y-%m-%d %H:%M}", "request": request, "source": source,
        "state": "preparing", "step": "Waiting to start", "version": 0}), encoding="utf-8")
    return job


def all_jobs() -> list[dict]:
    root = config.T2V_HOME / "jobs"
    ids = sorted((p.name for p in root.iterdir() if JOB_ID.fullmatch(p.name)), reverse=True) if root.exists() else []
    return [Job(i).read() for i in ids if (root / i / "job.json").exists()]


def mark_interrupted() -> None:
    """Called when the tool starts: a job still marked as running was cut off when the tool stopped."""
    for state in all_jobs():
        if state["state"] in RUNNING:
            Job(state["id"]).update(state="failed", failed_stage=_stage_of(state),
                                    error="The tool was stopped while this job was running.")


def _stage_of(state: dict) -> str:
    return "generate" if state.get("answers") else "prepare"


def start(job: Job, stage: str) -> None:
    """Run a stage in the background; a job runs one stage at a time."""
    with _lock:
        if job.id in _active:
            return
        _active.add(job.id)
    job.update(state="preparing" if stage == "prepare" else "generating", error=None)
    threading.Thread(target=_run, args=(job, stage), daemon=True).start()


def retry(job: Job) -> None:
    state = job.read()
    if state["state"] == "failed":
        start(job, state.get("failed_stage") or _stage_of(state))


def _run(job: Job, stage: str) -> None:
    try:
        (prepare if stage == "prepare" else generate)(job)
    except (ClaudeError, repo.RepoError) as e:
        job.update(state="failed", failed_stage=stage, error=str(e))
    except Exception as e:
        (job.dir / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        job.update(state="failed", failed_stage=stage, error=f"{type(e).__name__}: {e} (details in error.txt)")
    finally:
        _active.discard(job.id)


def prepare(job: Job) -> None:
    state = job.read()
    for folder in (job.source, job.repo):
        if folder.exists():
            shutil.rmtree(folder)
    if state["source"]["kind"] == "github":
        job.update(step="Cloning the repository")
        repo.clone(state["source"]["url"], job.source)
    else:
        job.update(step="Unpacking the repository")
        repo.unpack_zip(job.upload, job.source)
    job.update(step="Building the static dependency graph")
    prepared = repo.prepare(repo.root_of(job.source), job.repo)
    summary = repo.summary(job.repo, repo.build_graph(job.repo, job.graph))
    job.update(step="Reading your request", summary=summary, prepared=prepared)
    prefilled = phase1.prefill(state["request"], repo.summary_text(summary), job.dir / "calls")
    job.update(state="questions", step="", prefill=prefilled)


def generate(job: Job) -> None:
    state = job.read()
    records = state.get("records")
    if not records:
        job.update(step="Choosing the views")
        views = phase1.propose(state["request"], state["answers"], job.dir / "calls")
        records = phase1.records(state["request"], state["answers"], views)
        state = job.update(records=records, progress={r["id"]: "waiting" for r in records})
    report.write_inputs(job.out, records)

    progress = state["progress"]
    for i, record in enumerate(records):
        case = record["id"]
        if progress[case] == "done":
            continue

        def step(name: str, case: str = case) -> None:
            progress[case] = name
            job.update(step=f"View {case.split('-')[1]} of {len(records)}: {name}", progress=progress)

        phase2.run_view(record, records[:i], job.repo, job.graph, job.work / case / job.repo.name, job.out,
                        job.logs, step)
        step("done")
    phase2.check_consistency([r["id"] for r in records], job.out)
    report.write_readme(job.out, state["request"], records)
    job.update(state="done", step="")
