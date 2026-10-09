"""Make a blind rating sheet for human raters from the outputs of all conditions.

Every view gets an anonymous item id; its diagram source is copied to <out>/items/<item>.puml
and items are shuffled within each goal, so a rater cannot tell the condition. The key that maps
items back to (condition, run id, view) is written separately. Raters fill one row per item with
1-5 per rubric theme and, when the goal set lists expected facts, how many of them the view shows.

    .venv/bin/python scripts/make_rating_sheet.py --runs ../experiments/<name>/outputs --goals goals.yaml \
        --out ../experiments/<name>/rating --rater <name>
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from judge_outputs import _views  # noqa: E402  (same view ids as the judge)

from task2view.phase8.judge import RUBRIC_VERSION, THEMES  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--goals", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--rater", default="", help="pre-fills the rater column")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    cases = yaml.safe_load(args.goals.read_text())["cases"]
    by_case: dict[str, list[tuple]] = {}
    for condition in sorted(p for p in args.runs.iterdir() if p.is_dir()):
        for run in sorted(p for p in condition.iterdir() if p.is_dir()):
            case = run.name.split("@")[0]
            if case in cases:
                for view, source, _ in _views(run):
                    by_case.setdefault(case, []).append((condition.name, run.name, view.id, source))
    rng = random.Random(args.seed)
    (args.out / "items").mkdir(parents=True, exist_ok=True)
    sheet, key, n = [], [], 0
    for case in sorted(by_case):
        views = by_case[case]
        rng.shuffle(views)
        for condition, run_id, view_id, source in views:
            n += 1
            item = f"I{n:03d}"
            (args.out / "items" / f"{item}.puml").write_text(source, encoding="utf-8")
            expected = cases[case].get("expected") or []
            sheet.append({"item": item, "rater": args.rater, "case": case, "goal": cases[case]["goal"],
                          "expected_facts": len(expected), "facts_shown": "", **{t: "" for t in THEMES}, "notes": ""})
            key.append({"item": item, "condition": condition, "run_id": run_id, "view": view_id})
    for name, rows in (("rating_sheet.csv", sheet), ("rating_key.csv", key)):
        if rows:
            with (args.out / name).open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
    print(f"{n} items for rubric {RUBRIC_VERSION}; give raters rating_sheet.csv and items/, keep rating_key.csv apart")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
