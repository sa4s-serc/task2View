"""Redraw every view of a saved run as UML 2.5.1 (ADR-008), with no model call.

Structural views come from the run's architecture.json (parts and arrows); the other views from view.json
(the projected view). Each view gets view.puml and view.png (when plantuml is installed).

    .venv/bin/python scripts/rerender_uml.py --run ../experiments/adr7-run-2026-10-13 --out ../experiments/adr7-uml-2026-10-21
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from task2view.contracts.architecture import ArchView
from task2view.contracts.views import ArchitectureView
from task2view.phase7.notations import get_renderer
from task2view.phase7.uml_arch import render_arch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    summary = []
    for goal_dir in sorted(p for p in args.run.iterdir() if (p / "stakeholder_profile.json").exists()):
        system = json.loads((goal_dir / "repository_card.json").read_text())["name"]
        for vdir in sorted(goal_dir.glob("V*")):
            view = ArchitectureView.model_validate_json((vdir / "view.json").read_text())
            if (vdir / "architecture.json").exists():
                source = render_arch(ArchView.model_validate_json((vdir / "architecture.json").read_text()), system,
                                     view.viewpoint_id)
            else:
                source = get_renderer("plantuml").render(view).source
            out = args.out / goal_dir.name / vdir.name
            out.mkdir(parents=True, exist_ok=True)
            (out / "view.puml").write_text(source, encoding="utf-8")
            if shutil.which("plantuml"):
                subprocess.run(["plantuml", "-tpng", str(out / "view.puml")], check=False, capture_output=True)
            summary.append({"goal": goal_dir.name, "view": vdir.name, "model_kind": view.model_kind,
                            "compiled": (out / "view.png").exists()})
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for r in summary:
        print(f"{r['goal']:11} {r['view']:18} {r['model_kind']:14}{'' if r['compiled'] else '  NOT COMPILED'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
