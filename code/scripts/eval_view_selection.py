"""Live check of ADR-006 step 1: Phase 1 needs (real LLM) + covering selection.

Runs the ten pilot goals from tests/fixtures/pilot_goals.yaml through
extract_needs with the chosen model and compares the selected views with the
views the expert review implies. The pilot goals are also the golden test set,
so this measures agreement on known cases, not generalisation.

    .venv/bin/python scripts/eval_view_selection.py --llm anthropic:claude-opus-5-5 --runs 3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from task2view.agents.runtime import AgentRuntime
from task2view.knowledge.catalog import load_catalog
from task2view.phase1.needs import extract_needs
from task2view.phase3.selection import RepoFacts, select_views

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pilot_goals.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--llm", help="provider:model (default: TASK2VIEW_LLM, else gemini)")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--out", help="Write per-case JSON lines here")
    args = parser.parse_args()

    fixture = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    catalog = load_catalog()
    runtime = AgentRuntime(model=args.llm)
    rows = []
    for run in range(1, args.runs + 1):
        for case_id, case in fixture["cases"].items():
            facts = RepoFacts(signals=set(fixture["facts"][case["system"]]["signals"]))
            row = {"run": run, "case": case_id, "want": case["expect"]["views"]}
            try:
                profile = extract_needs(case["goal"], runtime, catalog=catalog)
                plan = select_views(profile.selection_input(), catalog, facts)
                row.update(
                    got=[v.viewpoint_id for v in plan.views],
                    needs=[n.need for n in profile.needs],
                    want_needs=[n["need"] for n in case["phase1"]["needs"]],
                    detail=profile.detail_level,
                    dropped=profile.dropped,
                )
                row["ok"] = row["got"] == row["want"]
            except Exception as exc:  # report and continue; one failed call should not hide the rest
                row.update(ok=False, error=str(exc)[:300])
            rows.append(row)
            mark = "OK " if row["ok"] else "NO "
            print(f"run {run} {case_id:11} {mark} got={row.get('got')} needs={row.get('needs')}"
                  + (f" error={row['error']}" if "error" in row else ""), flush=True)
        ok = sum(r["ok"] for r in rows if r["run"] == run)
        print(f"run {run}: {ok}/{len(fixture['cases'])} goals select the expected views", flush=True)
    if args.out:
        Path(args.out).write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
