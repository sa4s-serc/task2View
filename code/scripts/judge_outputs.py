"""Score every view of every condition with one judge model (Phase 8 layer 5, applied after the runs).

Layout expected (experiments/PROTOCOL.md):  <runs>/<condition>/<run-id>/...
- Task2View and skill runs: V*/view.json + V*/view.puml
- plain-agent runs:         view-<n>.puml (no view.json; the judge reads the source only)

Writes <run>/judge.json and <runs>/../judge_summary.csv. Every row records the judge model.

    .venv/bin/python scripts/judge_outputs.py --runs ../experiments/<name>/outputs --goals goals.yaml --judge-llm <provider:model>
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import yaml

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.aem import Question
from task2view.contracts.views import ArchitectureView
from task2view.llm.usage import UsageLedger
from task2view.phase8.judge import judge_view


def _views(run: Path) -> list[tuple[ArchitectureView, str, list[Question]]]:
    questions = []
    qfile = run / "architectural_questions.json"
    if qfile.exists():
        questions = [Question(**q) for q in json.loads(qfile.read_text())]
    out = []
    for vfile in sorted(run.glob("V*/view.json")):
        view = ArchitectureView(**json.loads(vfile.read_text()))
        src = next(iter(sorted(vfile.parent.glob("view.puml"))), None)
        out.append((view, src.read_text() if src else "", questions))
    if not out:  # plain agent: diagram source only
        for i, src in enumerate(sorted(run.glob("view-*.puml")), 1):
            view = ArchitectureView(id=f"view-{i}", viewpoint_id="unspecified", viewpoint_name="(not declared)", vb_ref="",
                                    model_kind="unspecified", title=src.stem, purpose="", detail_level="", max_elements=0)
            out.append((view, src.read_text(), []))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", required=True)
    parser.add_argument("--goals", required=True)
    parser.add_argument("--judge-llm", required=True)
    args = parser.parse_args()

    goals = {cid: c["goal"] for cid, c in yaml.safe_load(Path(args.goals).read_text())["cases"].items()}
    runtime = AgentRuntime(model=args.judge_llm)
    root = Path(args.runs)
    rows = []
    for condition in sorted(p for p in root.iterdir() if p.is_dir()):
        for run in sorted(p for p in condition.iterdir() if p.is_dir()):
            goal = goals.get(run.name)
            if goal is None:
                print(f"skip {condition.name}/{run.name}: not in the goal set")
                continue
            results = {}
            first_call = len(runtime.ledger.calls)
            for view, source, questions in _views(run):
                report = judge_view(view, questions, goal, source, "plantuml", runtime,
                                    judge_spec=runtime.spec, generator_spec=None)
                results[view.id] = report.model_dump()
                rows.append({"condition": condition.name, "run_id": run.name, "view": view.id,
                             "viewpoint": view.viewpoint_id, "judge": runtime.spec, "status": report.status,
                             "overall": report.overall,
                             **{f"score_{k}": (v or {}).get("score") for k, v in report.scores.items()}})
            (run / "judge.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
            run_ledger = UsageLedger(calls=runtime.ledger.calls[first_call:])
            (run / "judge_usage.json").write_text(json.dumps(run_ledger.summary(), indent=2), encoding="utf-8")
            print(f"{condition.name}/{run.name}: {len(results)} view(s) judged")
    total = runtime.ledger.summary()["total"]
    print(f"judge usage: {total['calls']} calls, ${total['cost_usd']:.4f}"
          + ("" if total["cost_complete"] else " (incomplete: no usage or no price for some calls)"))
    if rows:
        fields = sorted({k for r in rows for k in r}, key=lambda k: (not k.startswith(("condition", "run_id", "view", "viewpoint", "judge", "status", "overall")), k))
        with (root.parent / "judge_summary.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
