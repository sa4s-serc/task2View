"""ADR-007 step 1 check: build the architectural view of a saved Task2View run, without new evidence.

Reads the run's repository card, evidence model and stakeholder profile, applies the abstraction
step, renders a UML component diagram (and a PNG when plantuml is installed) and writes the view as JSON with
its readability counts. No model call.

    .venv/bin/python scripts/abstract_saved_run.py --run ../experiments/pilot-2026-10/outputs/task2view/IS-seat-L1 \
        --out ../experiments/pilot-2026-10/adr7/IS-seat-L1
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from task2view.contracts.aem import EvidenceModel
from task2view.contracts.card import RepositoryCard
from task2view.phase5.abstract import abstract_view
from task2view.phase7.uml_arch import readability, render_arch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    card = RepositoryCard.model_validate_json((args.run / "repository_card.json").read_text())
    aem = EvidenceModel.model_validate_json((args.run / "evidence_model.json").read_text())
    profile = json.loads((args.run / "stakeholder_profile.json").read_text())
    target = profile.get("target") or ""
    view = abstract_view(card, aem, target=target,
                         title=f"{target[:1].upper() + target[1:] if target else 'System'}: parts involved and how they interact")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "view.puml").write_text(render_arch(view, card.name, "client-server"), encoding="utf-8")
    counts = readability(view)
    (args.out / "view.json").write_text(json.dumps({"view": view.model_dump(), "readability": counts}, indent=2))
    if shutil.which("plantuml"):
        subprocess.run(["plantuml", "-tpng", str(args.out / "view.puml")], check=False, capture_output=True)
    print(json.dumps(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
