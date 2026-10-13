"""Redraw the structural views of a saved run in the notation chosen for their viewpoint and reader
(ADR-007 D1/D3, knowledge/data/vb/notations.yaml). No model call: the parts and arrows are the run's
architecture.json; other views (sequence, data model, deployment, use case) are copied unchanged.

    .venv/bin/python scripts/rerender_notation.py --run ../experiments/adr7-run-2026-10-13 \
        --out ../experiments/adr7-notation-2026-10-13
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from task2view.contracts.architecture import ArchView
from task2view.knowledge.catalog import load_catalog
from task2view.phase1.needs import ViewSpec
from task2view.phase7.arch_notations import choose_notation, language_of, render_arch
from task2view.phase8.readability import check


def _png(src: Path) -> None:
    if src.suffix == ".dot" and shutil.which("dot"):
        subprocess.run(["dot", "-Tpng", "-Gdpi=110", "-o", str(src.with_suffix(".png")), str(src)], check=False)
    elif src.suffix == ".puml" and shutil.which("plantuml"):
        subprocess.run(["plantuml", "-tpng", str(src)], check=False, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    roles = load_catalog().roles
    summary = []
    for goal_dir in sorted(p for p in args.run.iterdir() if (p / "stakeholder_profile.json").exists()):
        profile = json.loads((goal_dir / "stakeholder_profile.json").read_text())
        spec = ViewSpec(**profile.get("spec", {}))
        role = roles.get(profile.get("role") or "")
        audience = role.audience if role else "technical"
        system = json.loads((goal_dir / "repository_card.json").read_text())["name"]
        for vdir in sorted(goal_dir.glob("V*")):
            out = args.out / goal_dir.name / vdir.name
            out.mkdir(parents=True, exist_ok=True)
            vp_id = json.loads((vdir / "view.json").read_text())["viewpoint_id"]
            row = {"goal": goal_dir.name, "view": vdir.name, "viewpoint": vp_id, "role": profile.get("role"),
                   "audience": audience}
            if not (vdir / "architecture.json").exists():
                for f in vdir.glob("view.*"):
                    shutil.copy(f, out / f.name)
                row["notation"] = "unchanged (UML projection)"
                summary.append(row)
                continue
            arch = ArchView.model_validate_json((vdir / "architecture.json").read_text())
            notation = choose_notation(vp_id, audience, spec.notation)
            source = render_arch(arch, system, notation)
            src = out / ("view.dot" if language_of(notation) == "graphviz" else "view.puml")
            src.write_text(source, encoding="utf-8")
            _png(src)
            shutil.copy(vdir / "view.png", out / "before_c4.png") if (vdir / "view.png").exists() else None
            findings, _ = check(arch, source, viewpoint_id=vp_id, spec=spec, notation=notation)
            row |= {"notation": notation, "readability": [f["message"] for f in findings]}
            summary.append(row)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for r in summary:
        print(f"{r['goal']:11} {r['view']:18} {r['audience']:9} {r['notation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
