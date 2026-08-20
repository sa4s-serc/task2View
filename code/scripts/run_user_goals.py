#!/usr/bin/env python3
"""Run pagerank + ciao + plantuml on the user's exact goal texts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parents[1] / "data_points"
OUT_ROOT = ROOT / "runs" / "user-goals"
TASK2VIEW = ROOT / ".venv" / "bin" / "task2view"

IS_REPO = DATA / "Progetto-IS-main-English"
GR10_REPO = DATA / "progetto_ing_software_gr10-main-English"

JOBS = [
    {
        "id": "IS-seat-L1",
        "code": IS_REPO,
        "goal": (
            "I am a software developer. I need to modify the seat booking functionality "
            "and understand the main system components involved and how they interact."
        ),
    },
    {
        "id": "IS-seat-L2",
        "code": IS_REPO,
        "goal": (
            "I am a software developer. I need to modify the seat booking functionality "
            "to introduce new booking rules. Before changing the code, I need to understand "
            "the main components involved in this functionality, their responsibilities, "
            "and how they interact with each other. I also want to identify which parts of "
            "the system may be affected by the modification."
        ),
    },
    {
        "id": "IS-seat-L3",
        "code": IS_REPO,
        "goal": (
            "I am a software developer. I need to modify the seat booking functionality "
            "to introduce new booking rules. Before making changes to the code, I need to "
            "understand the high-level architecture supporting this functionality. I want "
            "to identify the main components involved in the booking process, their "
            "responsibilities, and the interactions and dependencies among them. In particular, "
            "I need to understand which components are responsible for handling booking requests, "
            "checking seat availability, applying booking rules, managing and storing reservations, "
            "and interacting with external services such as the notification service. This "
            "understanding will help me identify which parts of the system need to be modified "
            "and which other components may be affected by the changes."
        ),
    },
    {
        "id": "IS-reg-L1",
        "code": IS_REPO,
        "goal": (
            "I am an integration tester. I need to test the user registration functionality "
            "and understand which system components are involved and how they interact."
        ),
    },
    {
        "id": "IS-reg-L2",
        "code": IS_REPO,
        "goal": (
            "I am an integration tester. I need to design integration tests for the user "
            "registration functionality. Before defining the tests, I need to understand the "
            "main components involved in registration, their responsibilities, and how they "
            "interact when a new user creates an account. I also need to identify the main "
            "integration points that should be exercised during the tests."
        ),
    },
    {
        "id": "IS-reg-L3",
        "code": IS_REPO,
        "goal": (
            "I am an integration tester. I need to design integration tests for the user "
            "registration functionality. Before defining the tests, I need to understand the "
            "high-level architecture supporting this functionality. I want to identify the main "
            "components involved in the registration process, their responsibilities, and the "
            "interactions and dependencies among them. In particular, I need to understand which "
            "components handle the registration request, validate the user's personal information "
            "and selected role, manage role-specific data such as the student ID or librarian "
            "identifier, verify the validity and uniqueness of the account, and persist the newly "
            "created user. I also need to understand how these components collaborate when invalid "
            "or already existing user data is provided, so that I can identify the main integration "
            "points and interactions that should be covered by the tests."
        ),
    },
    {
        "id": "GR10-Q1",
        "code": GR10_REPO,
        "goal": (
            "I am a software architect. I need to review the overall organization of the system "
            "before planning its future evolution. I want to understand the main architectural "
            "components, their responsibilities, how the system is decomposed into different layers "
            "or subsystems, and the main dependencies among them. I also need to identify how "
            "user-facing functionality, application logic, domain entities, and data persistence "
            "are separated and how these parts collaborate to provide the main system functionalities."
        ),
    },
    {
        "id": "GR10-Q2",
        "code": GR10_REPO,
        "goal": (
            "I am a DevOps engineer. I need to deploy and configure the system in a new execution "
            "environment. Before preparing the deployment, I need to understand which runtime "
            "environments and software artifacts are required, where the application and its data "
            "are executed and stored, and how the main runtime elements communicate with each other. "
            "I also need to identify the technologies and runtime dependencies involved in the "
            "communication between the application and the database."
        ),
    },
    {
        "id": "GR10-Q3",
        "code": GR10_REPO,
        "goal": (
            "I am a database engineer. I need to modify the persistence layer to support future "
            "changes to the management of municipal reports. Before modifying the database, I need "
            "to understand the main data entities stored by the system, the relationships among them, "
            "and which information must be persisted throughout the lifecycle of a report. In particular, "
            "I need to understand how users, reports, locations, categories, states, state changes, "
            "internal notes, and notifications are related, and which parts of the application depend "
            "on this persisted information."
        ),
    },
    {
        "id": "GR10-Q4",
        "code": GR10_REPO,
        "goal": (
            "I am a business analyst. I need to understand at a high level how a system for reporting "
            "and managing problems in a municipal area is expected to work. I know that the application "
            "should allow people to report issues in the territory and support the municipality in "
            "managing them, but I do not yet know the specific user roles or the functionalities "
            "available to each of them. I need to identify the main types of users that interact with "
            "the system, the main goals they can achieve through it, and how the different functionalities "
            "are related to each other."
        ),
    },
]


def summarize(run_dir: Path) -> dict:
    summary: dict = {"id": run_dir.name, "path": str(run_dir)}
    cleaned = run_dir / "cleaned_corpus.json"
    if cleaned.exists():
        data = json.loads(cleaned.read_text())
        summary["kept"] = data.get("counts", {}).get("kept")
        summary["dropped"] = data.get("counts", {}).get("dropped")
        summary["languages"] = data.get("counts", {}).get("languages")
    spec = run_dir / "view_specification.json"
    if spec.exists():
        data = json.loads(spec.read_text())
        selected = data.get("selected_view") or {}
        summary["viewpoint"] = selected.get("viewpoint_id")
        summary["view_type"] = selected.get("view_type")
    vm = run_dir / "view_model.json"
    if vm.exists():
        data = json.loads(vm.read_text())
        summary["elements"] = [e.get("name") for e in data.get("elements", [])]
        summary["n_relations"] = len(data.get("relations", []))
    report = run_dir / "validation_report.json"
    if report.exists():
        data = json.loads(report.read_text())
        summary["verdict"] = data.get("verdict")
    render = run_dir / "render_report.json"
    if render.exists():
        data = json.loads(render.read_text())
        summary["render"] = data.get("status") or data.get("ok")
    summary["images"] = sorted(
        p.name for p in run_dir.glob("architecture_view.*") if p.suffix in {".png", ".svg", ".jpeg", ".puml"}
    )
    return summary


def main() -> int:
    if not TASK2VIEW.exists():
        print(f"missing {TASK2VIEW}", file=sys.stderr)
        return 1
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    results = []
    for job in JOBS:
        out = OUT_ROOT / job["id"]
        cmd = [
            str(TASK2VIEW),
            "run",
            "--code",
            str(job["code"]),
            "--goal",
            job["goal"],
            "--out",
            str(out),
            "--scope-strategy",
            "pagerank",
            "--extract-backend",
            "ciao",
            "--diagram-language",
            "plantuml",
            "--request-id",
            job["id"],
        ]
        print(f"\n=== {job['id']} ===", flush=True)
        proc = subprocess.run(cmd, cwd=ROOT)
        if proc.returncode != 0:
            print(f"FAILED {job['id']} exit={proc.returncode}", flush=True)
            compile_cmd = [
                str(TASK2VIEW),
                "compile",
                "--run-dir",
                str(out),
            ]
            subprocess.run(compile_cmd, cwd=ROOT)
        summary = summarize(out)
        summary["exit"] = proc.returncode
        results.append(summary)
        print(json.dumps(summary, indent=2), flush=True)

    (OUT_ROOT / "summary.json").write_text(json.dumps(results, indent=2))
    print("\nWrote", OUT_ROOT / "summary.json")
    return 0 if all(r["exit"] == 0 for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
