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
        --llm anthropic:claude-sonnet-5-5 --judge-llm openai:<model> --notations plantuml,mermaid

Writes <out>/<run-id>/ (run id = case id, or <case>@<k> with --repeat; see agents/write_v2.py) and <out>/summary.jsonl. Each
line records the generator and judge models, so results from different models
are never mixed silently.

Resumable: every model reply is cached in <out>/.llm-cache, and a run whose package is complete
is skipped. When a subscription usage limit is hit (claude-code:<model>), the batch stops and says
when the limit resets; run the same command again after that, or pass --wait to sleep until the
reset and continue by itself. No finished call is ever paid for twice.
"""

from __future__ import annotations

import argparse
import json
import time
import traceback
from datetime import datetime
from pathlib import Path

import yaml

from task2view.agents.run_v2 import run_v2
from task2view.agents.write_v2 import write_run_v2
from task2view.llm.claude_agent import UsageLimitReached


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--goals", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--llm")
    parser.add_argument("--judge-llm")
    parser.add_argument("--notations", default="plantuml")
    parser.add_argument("--max-views", type=int, default=3)
    parser.add_argument("--evidence", choices=["agent", "retrieval"], default="agent", help="retrieval = baseline B1")
    parser.add_argument("--only", help="Comma-separated case ids")
    parser.add_argument("--repeat", type=int, default=1, help="Runs per case; with more than 1, run ids are <case>@<k>")
    parser.add_argument("--wait", action="store_true", help="On a usage limit, sleep until it resets and continue")
    parser.add_argument("--redo", action="store_true", help="Run cases again even if their run package exists")
    args = parser.parse_args()

    doc = yaml.safe_load(Path(args.goals).read_text(encoding="utf-8"))
    systems = doc.get("systems") or {}
    only = {c.strip() for c in args.only.split(",")} if args.only else None
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = (out / "summary.jsonl").open("a", encoding="utf-8")
    runs = [(cid, case, f"{cid}@{k}" if args.repeat > 1 else cid)
            for k in range(1, args.repeat + 1) for cid, case in doc["cases"].items() if not only or cid in only]
    cache = out / ".llm-cache"
    pending = list(runs)
    while pending:
        case_id, case, run_id = pending[0]
        if (out / run_id / "README.md").exists() and not args.redo:
            print(f"skip {run_id}: already complete", flush=True)
            pending.pop(0)
            continue
        code = case.get("code") or systems.get(case.get("system", ""))
        row = {"case": case_id, "run_id": run_id, "llm": args.llm, "judge_llm": args.judge_llm,
               "evidence": args.evidence, "code": code}
        try:
            if not code:
                raise ValueError(f"no repository path for {case_id} (set `code:` or a `systems:` entry)")
            result = run_v2(case["goal"], code, llm=args.llm, judge_llm=args.judge_llm, max_views=args.max_views,
                            evidence_mode=args.evidence, cache_dir=cache,
                            languages=[n.strip() for n in args.notations.split(",") if n.strip()])
            write_run_v2(result, out / run_id)
            got = [v.viewpoint_id for v in result.viewset.views]
            want = (case.get("expect") or {}).get("views")
            row.update(views=got, expected=want, match=None if want is None else got == want,
                       verdicts={vid: v.verdict for vid, v in result.validation.items()},
                       judge={vid: {k: s["score"] for k, s in v.task_fit.get("scores", {}).items()}
                              for vid, v in result.validation.items()},
                       claims=len(result.aem.claims), rejected=len(result.aem.rejected_claims),
                       usage=result.usage.get("total", {}))
        except UsageLimitReached as exc:  # stop (or wait) and resume this same run later from the cache
            if not args.wait:
                print(f"{exc}. Progress is saved; run the same command again after the reset.", flush=True)
                return 3
            pause = max(60, (exc.resets_at or time.time() + 3600) - time.time() + 60)
            resume = datetime.fromtimestamp(time.time() + pause).strftime("%H:%M")
            print(f"{exc}. Waiting until about {resume}, then continuing {run_id}.", flush=True)
            time.sleep(pause)
            continue
        except Exception as exc:  # one failing case must not stop the set; the error is recorded
            row.update(error=str(exc)[:500], trace=traceback.format_exc(limit=3))
        summary.write(json.dumps(row) + "\n")
        summary.flush()
        print(json.dumps({k: v for k, v in row.items() if k != "trace"}), flush=True)
        pending.pop(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
