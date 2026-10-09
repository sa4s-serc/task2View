"""Compare judge scores with people.

Two modes:

--labels  expert_labels.yaml (problems / praise coded from free-text comments). Descriptive only:
          per theme, the judge's lowest score on outputs the expert flagged vs praised. The rubric
          was derived from these comments, so this cannot validate the judge.
--ratings ratings.csv from make_rating_sheet.py, filled in by one or more raters (1-5 per theme).
          Quadratic-weighted Cohen's kappa per theme, judge vs each rater and rater vs rater,
          with a 95% bootstrap interval. A theme may become a gate only when judge-human kappa
          is close to human-human kappa (ADR-006: soft until validated).

    .venv/bin/python scripts/judge_agreement.py --labels ../experiments/pilot-2026-09/review/expert_labels.yaml
    .venv/bin/python scripts/judge_agreement.py --ratings ratings.csv --key rating_key.csv --judge judge_summary.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

import yaml

from task2view.phase8.judge import THEMES

LEVELS = range(1, 6)


def weighted_kappa(a: list[int], b: list[int]) -> float | None:
    """Quadratic-weighted Cohen's kappa on the 1-5 scale; None when undefined (fewer than 2 items or no spread)."""
    n = len(a)
    if n < 2:
        return None
    observed = sum((x - y) ** 2 for x, y in zip(a, b)) / n
    expected = sum((x - y) ** 2 for x in a for y in b) / (n * n)
    return None if expected == 0 else 1 - observed / expected


def bootstrap(a: list[int], b: list[int], reps: int = 2000, seed: int = 7) -> tuple[float, float] | None:
    rng = random.Random(seed)
    values = []
    for _ in range(reps):
        idx = [rng.randrange(len(a)) for _ in a]
        k = weighted_kappa([a[i] for i in idx], [b[i] for i in idx])
        if k is not None:
            values.append(k)
    if len(values) < reps / 2:
        return None
    values.sort()
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


def _judge_scores(run_dir: Path) -> dict[str, int]:
    """Lowest judge score per theme over the run's views (a problem in any view counts)."""
    path = run_dir / "judge.json"
    if not path.exists():
        return {}
    low: dict[str, int] = {}
    for report in json.loads(path.read_text()).values():
        for theme, s in (report.get("scores") or {}).items():
            if isinstance(s.get("score"), int):
                low[theme] = min(low.get(theme, 5), s["score"])
    return low


def from_labels(labels_file: Path) -> list[str]:
    doc = yaml.safe_load(labels_file.read_text())
    root = labels_file.parent.parent
    groups: dict[str, dict[str, list[int]]] = {t: {"flagged": [], "praised": []} for t in THEMES}
    missing = []
    for e in doc["entries"]:
        scores = _judge_scores(root / e["run_dir"])
        if not scores:
            missing.append(e["run_dir"])
            continue
        for theme in THEMES:
            if theme in scores:
                for group in ("problems", "praised"):
                    if theme in e.get(group, []):
                        groups[theme]["flagged" if group == "problems" else "praised"].append(scores[theme])
    lines = [f"rater {doc.get('rater')}, rubric {doc.get('rubric')}; descriptive only (themes came from these comments)",
             "theme | flagged: n, mean judge score, share scored <=3 | praised: n, mean, share scored >=4"]
    for theme, g in groups.items():
        f, p = g["flagged"], g["praised"]
        fl = f"{len(f)}, {sum(f) / len(f):.2f}, {sum(s <= 3 for s in f) / len(f):.0%}" if f else "0"
        pr = f"{len(p)}, {sum(p) / len(p):.2f}, {sum(s >= 4 for s in p) / len(p):.0%}" if p else "0"
        lines.append(f"{theme} | {fl} | {pr}")
    if missing:
        lines.append(f"no judge.json (run scripts/judge_outputs.py first) for {len(missing)} entries: {', '.join(missing[:3])} …")
    return lines


def from_ratings(ratings: Path, key: Path, judge_csv: Path) -> list[str]:
    item_of = {r["item"]: (r["condition"], r["run_id"], r["view"]) for r in csv.DictReader(key.open())}
    judge = {(r["condition"], r["run_id"], r["view"]): r for r in csv.DictReader(judge_csv.open())}
    by_rater: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)  # rater -> item -> theme -> score
    for r in csv.DictReader(ratings.open()):
        by_rater[r["rater"]][r["item"]] = {t: int(r[t]) for t in THEMES if (r.get(t) or "").strip().isdigit()}
    raters = sorted(by_rater)
    lines = ["theme | pair | n | weighted kappa | 95% bootstrap interval"]
    for theme in THEMES:
        pairs = [(x, "judge") for x in raters] + [(x, y) for i, x in enumerate(raters) for y in raters[i + 1:]]
        for x, y in pairs:
            a, b = [], []
            for item, scores in by_rater[x].items():
                other = (judge.get(item_of.get(item), {}).get(f"score_{theme}") if y == "judge"
                         else by_rater[y].get(item, {}).get(theme))
                if theme in scores and str(other or "").strip().isdigit():
                    a.append(scores[theme])
                    b.append(int(other))
            k = weighted_kappa(a, b)
            ci = bootstrap(a, b) if k is not None else None
            lines.append(f"{theme} | {x} vs {y} | {len(a)} | {'n/a' if k is None else f'{k:.2f}'} | "
                         + (f"[{ci[0]:.2f}, {ci[1]:.2f}]" if ci else "n/a"))
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--ratings", type=Path)
    parser.add_argument("--key", type=Path, help="rating_key.csv from make_rating_sheet.py")
    parser.add_argument("--judge", type=Path, help="judge_summary.csv from judge_outputs.py")
    args = parser.parse_args()
    if args.labels:
        print("\n".join(from_labels(args.labels)))
    if args.ratings:
        if not (args.key and args.judge):
            parser.error("--ratings needs --key and --judge")
        print("\n".join(from_ratings(args.ratings, args.key, args.judge)))
    if not (args.labels or args.ratings):
        parser.error("give --labels or --ratings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
