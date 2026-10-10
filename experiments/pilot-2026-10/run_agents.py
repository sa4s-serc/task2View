"""Run the pilot's agent sessions unattended: all plain-agent runs, then all skill-agent runs.

Each session is headless Claude Code (`claude -p`) in its prepared copy, with the same instruction,
model and permission mode (auto) as an interactive session. Safe to stop and restart at any time:
- a run whose outputs are already in outputs/<condition>/<case>/ is skipped;
- a session that stopped (usage limit, error, Ctrl-C, closed laptop) is resumed with its saved
  session id ("continue"), so its work so far is kept;
- on a usage limit the script sleeps until the reset time Claude Code reports, then resumes.
Every session's full event stream is kept in logs/<condition>-<case>.jsonl.

    cd Task2View/code && caffeinate -i .venv/bin/python ../experiments/pilot-2026-10/run_agents.py
    (options: --only plain-agent/IS-seat-L2   --dry-run)
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
SUBJECTS = Path.home() / "t2v-subjects"
MODEL = "claude-sonnet-5-5"
CONDITIONS = ("plain-agent", "skill-agent")
REPOS = {"progetto-is": "Progetto-IS-main-English", "gr10": "progetto_ing_software_gr10-main-English"}
MAX_FAILURES = 2  # non-limit failures per session before the script stops for a person to look


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def run_claude(workdir: Path, prompt: str, session: list[str], stream: Path) -> tuple[dict | None, int | None]:
    """One `claude -p` invocation. Returns (final result event or None, reset time if a usage limit was hit)."""
    cmd = ["claude", "-p", prompt, "--model", MODEL, "--permission-mode", "auto",
           "--output-format", "stream-json", "--verbose", *session]
    result, resets_at = None, None
    with stream.open("a", encoding="utf-8") as out, \
            subprocess.Popen(cmd, cwd=workdir, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True) as proc:
        for line in proc.stdout:
            out.write(line)
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            info = event.get("rate_limit_info") or {}
            if info.get("status") == "rejected":
                resets_at = info.get("resets_at") or resets_at
            if event.get("type") == "result":
                result = event
    return result, resets_at


def wait_until(resets_at: int | None) -> None:
    target = (resets_at or time.time() + 1800) + 60
    log(f"usage limit: sleeping until {datetime.fromtimestamp(target):%Y-%m-%d %H:%M}")
    while time.time() < target:
        time.sleep(min(300, max(1, target - time.time())))


def run_session(condition: str, case: str, system: str, dry: bool) -> bool:
    out_dir = HERE / "outputs" / condition / case
    if (out_dir / "README.md").exists():
        log(f"skip {condition}/{case}: already collected")
        return True
    workdir = SUBJECTS / condition / case / REPOS[system]
    produced = workdir / "task2view-out" / case
    state_file = HERE / "logs" / f"{condition}-{case}.state.json"
    stream = HERE / "logs" / f"{condition}-{case}.jsonl"
    state = json.loads(state_file.read_text()) if state_file.exists() else None
    if state is None and produced.exists():
        log(f"stop: {workdir} already has outputs from an unrecorded session; re-prepare that copy first")
        return False
    if dry:
        log(f"would run {condition}/{case} in {workdir} ({'resume' if state else 'new'})")
        return True
    if state is None:
        state = {"session": str(uuid.uuid4()), "started": datetime.now().isoformat(timespec="seconds"),
                 "seconds": 0.0, "interruptions": 0, "turns": 0}
        prompt, session = (HERE / "instructions" / condition / f"{case}.txt").read_text(), ["--session-id", state["session"]]
    else:
        log(f"resuming {condition}/{case} (session {state['session']})")
        prompt, session = "continue", ["--resume", state["session"]]
    state_file.parent.mkdir(exist_ok=True)
    state_file.write_text(json.dumps(state))
    failures = 0
    while True:
        log(f"running {condition}/{case}")
        result, resets_at = run_claude(workdir, prompt, session, stream)
        if result is not None:
            state["seconds"] += (result.get("duration_ms") or 0) / 1000
            state["turns"] += result.get("num_turns") or 0
        if result is not None and not result.get("is_error"):
            break
        state["interruptions"] += 1
        state_file.write_text(json.dumps(state))
        prompt, session = "continue", ["--resume", state["session"]]
        if resets_at is not None:
            wait_until(resets_at)
            continue
        failures += 1
        reason = (result or {}).get("result") or (result or {}).get("subtype") or "no result event"
        log(f"session ended with an error ({str(reason)[:200]}); attempt {failures} of {MAX_FAILURES}")
        if failures >= MAX_FAILURES:
            return False
        time.sleep(60)
    if not (produced / "README.md").exists():
        log(f"stop: {condition}/{case} finished but wrote no {produced / 'README.md'}; see {stream}")
        return False
    shutil.copytree(produced, out_dir)
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.split()[0]
    with (HERE / "runs.csv").open("a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow([condition, case, MODEL, "claude-code -p", version, state["session"],
                                 state["started"][:10], round(state["seconds"] / 60),
                                 "yes" if state["interruptions"] else "no",
                                 f"headless, auto mode; {state['turns']} turns; {state['interruptions']} resume(s)"])
    log(f"done {condition}/{case}: {round(state['seconds'] / 60)} min, outputs copied")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", help="condition/case, e.g. plain-agent/IS-seat-L2")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    lock = HERE / "logs" / "run_agents.lock"
    lock.parent.mkdir(exist_ok=True)
    if lock.exists() and not args.dry_run:
        print(f"another run seems active ({lock}); delete the lock file if it is not")
        return 1
    cases = yaml.safe_load((HERE / "goals.yaml").read_text())["cases"]
    todo = [(cond, case, c["system"]) for cond in CONDITIONS for case, c in cases.items()
            if not args.only or args.only == f"{cond}/{case}"]
    if not args.dry_run:
        lock.write_text(str(datetime.now()))
    try:
        for cond, case, system in todo:
            if not run_session(cond, case, system, args.dry_run):
                return 2
    finally:
        if not args.dry_run:
            lock.unlink(missing_ok=True)
    log("all agent sessions done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
