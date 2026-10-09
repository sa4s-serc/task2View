"""How much do repeated runs of the same goal agree? (LLM output varies even at temperature 0.)

For each condition and goal with at least two runs (<case>@<k>), compares every pair of runs:
- viewpoints: whether the runs chose the same set of views;
- elements:   Jaccard overlap of element names per viewpoint;
- relations:  Jaccard overlap of (source, kind, target) names per viewpoint.
Needs runs that wrote V*/view.json (pipeline and skill conditions).

    .venv/bin/python scripts/run_stability.py --runs ../experiments/<name>/outputs
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path


def _jaccard(a: set, b: set) -> float:
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def _load(run: Path) -> dict[str, tuple[set, set]]:
    views = {}
    for vfile in sorted(run.glob("V*/view.json")):
        v = json.loads(vfile.read_text())
        names = {e["id"]: e["name"] for e in v.get("elements", [])}
        elements = {e["name"] for e in v.get("elements", []) if not e.get("group")}
        relations = {(names.get(r["source"]), r["kind"], names.get(r["target"])) for r in v.get("relations", [])}
        relations |= {(names.get(i["source"]), "message", names.get(i["target"])) for i in v.get("interactions", [])}
        views[v["viewpoint_id"]] = (elements, relations)
    return views


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", required=True, type=Path)
    args = parser.parse_args()
    print("condition | case | runs | same viewpoints | element Jaccard | relation Jaccard")
    for condition in sorted(p for p in args.runs.iterdir() if p.is_dir()):
        groups: dict[str, list[dict]] = {}
        for run in sorted(p for p in condition.iterdir() if p.is_dir()):
            loaded = _load(run)
            if loaded:
                groups.setdefault(run.name.split("@")[0], []).append(loaded)
        for case, runs in sorted(groups.items()):
            if len(runs) < 2:
                continue
            same, el, rel = [], [], []
            for a, b in combinations(runs, 2):
                same.append(set(a) == set(b))
                for vp in set(a) & set(b):
                    el.append(_jaccard(a[vp][0], b[vp][0]))
                    rel.append(_jaccard(a[vp][1], b[vp][1]))
            mean = lambda xs: f"{sum(xs) / len(xs):.2f}" if xs else "n/a"  # noqa: E731
            print(f"{condition.name} | {case} | {len(runs)} | {sum(same)}/{len(same)} | {mean(el)} | {mean(rel)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
