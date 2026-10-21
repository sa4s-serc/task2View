"""Download the OMG UML 2.5.1 specification (formal/17-12-05) for reading the clauses that
knowledge/data/uml/uml-2.5.1.yaml cites. It is saved outside version control (default: ~/.cache/task2view),
since the repository keeps only our summary of the rules with their clause numbers.

    .venv/bin/python scripts/fetch_uml_spec.py
"""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

URL = "https://www.omg.org/spec/UML/2.5.1/PDF"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path.home() / ".cache" / "task2view" / "UML-2.5.1.pdf")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL, timeout=120) as response:
        args.out.write_bytes(response.read())
    print(f"saved {args.out} ({args.out.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
