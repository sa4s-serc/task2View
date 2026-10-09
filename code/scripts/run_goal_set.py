"""Run the full ADR-006 pipeline over a goal set and write one run package per case.

Goal-set format (same as scripts/eval_view_selection.py):

    facts:                      # optional; ignored here (the Phase 0 card computes signals)
    cases:
      <case-id>:
        code: /path/to/repo     # or `system:` with a `systems:` map of {name: path}
        goal: "free-text stakeholder goal"
        expect: {views: [...]}  # optional; compared with the selected views
    systems:
      <name>: /path/to/repo

    .venv/bin/python scripts/run_goal_set.py --goals goals.yaml --out runs/my-eval \\
        --llm anthropic:claude-sonnet-4-5 --judge-llm openai:<model> --notations plantuml,mermaid

Writes <out>/<case-id>/ (see agents/write_v2.py) and <out>/summary.jsonl. Each
line records the generator and judge models, so results from different models
are never mixed silently.
"""

from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

import yaml

from task2view.agents.run_v2 import run_v2
from task2view.agents.write_v2 import write_run_v2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--goals", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--llm")
    parser.add_argument("--judge-llm")
    parser.add_argument("--notations", default="plantuml")
    parser.add_argument("--max-views", type=int, default=3)
    parser.add_argument("--only", help="Comma-separated case ids")
    args = parser.parse_args()

    doc = yaml.safe_load(Path(args.goals).read_text(encoding="utf-8"))
    systems = doc.get("systems") or {}
    only = {c.strip() for c in args.only.split(",")} if args.only else None
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = (out / "summary.jsonl").open("a", encoding="utf-8")
    for case_id, case in doc["cases"].items():
        if only and case_id not in only:
            continue
        code = case.get("code") or systems.get(case.get("system", ""))
        row = {"case": case_id, "llm": args.llm, "judge_llm": args.judge_llm, "code": code}
        try:
            if not code:
                raise ValueError(f"no repository path for {case_id} (set `code:` or a `systems:` entry)")
            result = run_v2(case["goal"], code, llm=args.llm, judge_llm=args.judge_llm, max_views=args.max_views,
                            languages=[n.strip() for n in args.notations.split(",") if n.strip()])
            write_run_v2(result, out / case_id)
            got = [v.viewpoint_id for v in result.viewset.views]
            want = (case.get("expect") or {}).get("views")
            row.update(views=got, expected=want, match=None if want is None else got == want,
                       verdicts={vid: v.verdict for vid, v in result.validation.items()},
                       judge={vid: {k: s["score"] for k, s in v.task_fit.get("scores", {}).items()}
                              for vid, v in result.validation.items()},
                       claims=len(result.aem.claims), rejected=len(result.aem.rejected_claims),
                       usage=result.usage.get("total", {}))
        except Exception as exc:  # one failing case must not stop the set; the error is recorded
            row.update(error=str(exc)[:500], trace=traceback.format_exc(limit=3))
        summary.write(json.dumps(row) + "\n")
        summary.flush()
        print(json.dumps({k: v for k, v in row.items() if k != "trace"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
