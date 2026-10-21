"""Check PlantUML diagrams against UML 2.5.1 (ADR-008, phase8/uml_check.py), whoever drew them.

Finds every .puml under the given folders, infers each diagram's UML type (frame heading, else its primary
symbols), and reports non-UML symbols (errors), symbols or paths of another diagram type and non-standard
stereotypes (warnings), and a missing frame heading. Writes a CSV when --csv is given. No model call.

    .venv/bin/python scripts/check_uml.py ../experiments/pilot-2026-10/outputs/plain-agent --csv plain.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

from task2view.phase8.uml_check import check_uml


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folders", nargs="+", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()
    rows = []
    for folder in args.folders:
        for path in sorted(folder.rglob("*.puml")):
            findings, metrics = check_uml(path.read_text(encoding="utf-8", errors="replace"))
            errors = [f["message"] for f in findings if f["severity"] == "error"]
            warnings = [f["message"] for f in findings if f["severity"] == "warning"]
            rows.append({"file": str(path), "uml_diagram": metrics["uml_diagram"] or "not UML",
                         "errors": len(errors), "warnings": len(warnings),
                         "first_error": errors[0] if errors else "", "first_warning": warnings[0] if warnings else ""})
    for r in rows:
        print(f"{r['uml_diagram']:14} E{r['errors']:<3} W{r['warnings']:<3} {r['file']}"
              + (f"\n    {r['first_error'][:120]}" if r["first_error"] else ""))
    kinds = Counter(r["uml_diagram"] for r in rows)
    print(f"\n{len(rows)} diagrams; {sum(r['errors'] > 0 for r in rows)} with errors; "
          f"{sum(r['errors'] == 0 and r['warnings'] > 0 for r in rows)} with warnings only; types: {dict(kinds)}")
    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["file"])
            writer.writeheader()
            writer.writerows(rows)
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
