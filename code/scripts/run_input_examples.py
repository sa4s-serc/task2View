#!/usr/bin/env python3
"""Run Task2View on input_example_task2view.txt goals."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "code"
DATA = ROOT.parent / "data_points"
IS = DATA / "Progetto-IS-main-English"
GR10 = DATA / "progetto_ing_software_gr10-main-English"
PY = CODE / ".venv" / "bin" / "python"

JOBS = [
    ("IS-seat-L1", IS, "IS-seat-L1",
     "I am a software developer. I need to modify the seat booking functionality and understand the main system components involved and how they interact."),
    ("IS-seat-L2", IS, "IS-seat-L2",
     "I am a software developer. I need to modify the seat booking functionality to introduce new booking rules. Before changing the code, I need to understand the main components involved in this functionality, their responsibilities, and how they interact with each other. I also want to identify which parts of the system may be affected by the modification."),
    ("IS-seat-L3", IS, "IS-seat-L3",
     "I am a software developer. I need to modify the seat booking functionality to introduce new booking rules. Before making changes to the code, I need to understand the high-level architecture supporting this functionality. I want to identify the main components involved in the booking process, their responsibilities, and the interactions and dependencies among them. In particular, I need to understand which components are responsible for handling booking requests, checking seat availability, applying booking rules, managing and storing reservations, and interacting with external services such as the notification service. This understanding will help me identify which parts of the system need to be modified and which other components may be affected by the changes."),
    ("IS-reg-L1", IS, "IS-reg-L1",
     "I am an integration tester. I need to test the user registration functionality and understand which system components are involved and how they interact."),
    ("IS-reg-L2", IS, "IS-reg-L2",
     "I am an integration tester. I need to design integration tests for the user registration functionality. Before defining the tests, I need to understand the main components involved in registration, their responsibilities, and how they interact when a new user creates an account. I also need to identify the main integration points that should be exercised during the tests."),
    ("IS-reg-L3", IS, "IS-reg-L3",
     "I am an integration tester. I need to design integration tests for the user registration functionality. Before defining the tests, I need to understand the high-level architecture supporting this functionality. I want to identify the main components involved in the registration process, their responsibilities, and the interactions and dependencies among them. In particular, I need to understand which components handle the registration request, validate the user's personal information and selected role, manage role-specific data such as the student ID or librarian identifier, verify the validity and uniqueness of the account, and persist the newly created user. I also need to understand how these components collaborate when invalid or already existing user data is provided, so that I can identify the main integration points and interactions that should be covered by the tests."),
    ("GR10-Q1", GR10, "GR10-Q1",
     "I am a software architect. I need to review the overall organization of the system before planning its future evolution. I want to understand the main architectural components, their responsibilities, how the system is decomposed into different layers or subsystems, and the main dependencies among them. I also need to identify how user-facing functionality, application logic, domain entities, and data persistence are separated and how these parts collaborate to provide the main system functionalities."),
    ("GR10-Q2", GR10, "GR10-Q2",
     "I am a DevOps engineer. I need to deploy and configure the system in a new execution environment. Before preparing the deployment, I need to understand which runtime environments and software artifacts are required, where the application and its data are executed and stored, and how the main runtime elements communicate with each other. I also need to identify the technologies and runtime dependencies involved in the communication between the application and the database."),
    ("GR10-Q3", GR10, "GR10-Q3",
     "I am a database engineer. I need to modify the persistence layer to support future changes to the management of municipal reports. Before modifying the database, I need to understand the main data entities stored by the system, the relationships among them, and which information must be persisted throughout the lifecycle of a report. In particular, I need to understand how users, reports, locations, categories, states, state changes, internal notes, and notifications are related, and which parts of the application depend on this persisted information."),
    ("GR10-Q4", GR10, "GR10-Q4",
     "I am a business analyst. I need to understand at a high level how a system for reporting and managing problems in a municipal area is expected to work. I know that the application should allow people to report issues in the territory and support the municipality in managing them, but I do not yet know the specific user roles or the functionalities available to each of them. I need to identify the main types of users that interact with the system, the main goals they can achieve through it, and how the different functionalities are related to each other."),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the 10 input-example goals.")
    parser.add_argument("--out-dir", default="ri-forced-pagerank-ciao")
    parser.add_argument("--scope-strategy", default="pagerank")
    parser.add_argument("--extract-backend", default="ciao")
    parser.add_argument("--diagram-language", default="plantuml")
    args = parser.parse_args()
    out = CODE / "runs" / args.out_dir
    if not IS.is_dir() or not GR10.is_dir():
        print(f"missing repos: IS={IS.is_dir()} GR10={GR10.is_dir()}", file=sys.stderr)
        return 2
    if not PY.is_file():
        print(f"missing venv python: {PY}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    summary = []
    for name, repo, request_id, goal in JOBS:
        dest = out / name
        print(f"\n=== {name} -> {dest} ===", flush=True)
        cmd = [
            str(PY), "-m", "task2view", "run",
            "--code", str(repo),
            "--goal", goal,
            "--out", str(dest),
            "--request-id", request_id,
            "--scope-strategy", args.scope_strategy,
            "--extract-backend", args.extract_backend,
            "--diagram-language", args.diagram_language,
        ]
        proc = subprocess.run(cmd, cwd=str(CODE))
        summary.append({"id": name, "exit": proc.returncode, "out": str(dest)})
        if proc.returncode != 0:
            print(f"FAILED {name} exit={proc.returncode}", flush=True)
    (out / "batch_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    failed = [row for row in summary if row["exit"] != 0]
    print(json.dumps(summary, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
