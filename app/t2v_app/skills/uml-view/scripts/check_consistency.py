#!/usr/bin/env python3
"""check_consistency: do the views of one task agree on their shared elements? (42010 cl. 5, correspondences)

    python3 -I .claude/skills/uml-view/scripts/check_consistency.py view-out/A/inventory.json view-out/B/inventory.json ...

Two elements in different views that stand for mostly the same code (Jaccard >= 0.5 on their member specs, or the
same single member) should carry the same name; one name in two views should stand for overlapping code.
Elements without members are compared by name only. Exit 0 when consistent, 1 otherwise. Stdlib only.
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path


def elements(path: Path) -> list[dict]:
    inv = json.loads(path.read_text(encoding="utf-8"))
    return [{"view": path.parent.name, "name": (e.get("name") or e.get("id") or "").strip(),
             "members": {m.strip() for m in e.get("members", []) if isinstance(m, str)}}
            for e in inv.get("elements", [])]


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    views = [elements(Path(p)) for p in sys.argv[1:]]
    issues = []
    for va, vb in combinations(views, 2):
        for a in va:
            for b in vb:
                if not a["members"] or not b["members"]:
                    continue
                j = len(a["members"] & b["members"]) / len(a["members"] | b["members"])
                same_name = a["name"].lower() == b["name"].lower()
                if j >= 0.5 and not same_name:
                    issues.append(f"name: '{a['name']}' ({a['view']}) and '{b['name']}' ({b['view']}) stand for the "
                                  f"same code ({j:.0%} of members shared); use one name")
                elif same_name and j == 0:
                    issues.append(f"meaning: '{a['name']}' stands for different code in {a['view']} and {b['view']}; "
                                  "rename one or align their members")
    for i in issues:
        print(i)
    print("consistent" if not issues else f"{len(issues)} issue(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
