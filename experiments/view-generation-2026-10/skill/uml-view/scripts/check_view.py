#!/usr/bin/env python3
"""check_view: notation and readability checks on a view's PlantUML source that a reader would otherwise catch.

    python3 -I .claude/skills/uml-view/scripts/check_view.py view-out/<case>/view.puml

Checks (each is a general rule, not tied to one system):
  boundary   use case diagram: every use case is inside a system boundary (rectangle/package), actors outside
             (UML 2.5.1 cl. 18: the subject of a use case)
  codes      labels use plain words: no invented codes or numbering such as IP1, UC3, C2 that need a legend
  styling    the styling stereotypes <<accent>>, <<alert>>, <<muted>> are hidden, so they are not printed as text

Exit 0 when clean, 1 when an issue is found. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CODE = re.compile(r"\b[A-Z]{1,4}\d{1,3}\b")
STYLING = ("accent", "alert", "muted")
# words that legitimately end in digits in architecture views
ALLOWED = {"S3", "EC2", "IPV4", "IPV6", "HTTP2", "H2", "UTF8", "SHA256", "SHA1", "MD5", "AES256", "OAUTH2", "JDK17",
           "JDK21", "JDK11", "JDK8", "ES6", "HTML5", "CSS3", "UML2", "BCRYPT"}


def labels(line: str) -> list[str]:
    """Text a reader sees on a line: quoted names and the part after ':' on relations/messages."""
    out = re.findall(r'"([^"]*)"', line)
    if ":" in line and re.search(r"(-+>|<-+|\.\.>|<\.\.|--|\.\.)", line):
        out.append(line.split(":", 1)[1])
    return out


def check(src: str) -> list[str]:
    issues = []
    lines = src.splitlines()
    body = [l.strip() for l in lines if l.strip() and not l.strip().startswith("'")]
    uc = re.compile(r"^(usecase\b|\([^)]+\)\s+as\b)")
    is_use_case = any(uc.match(l) for l in body)
    if is_use_case:
        depth = 0
        for l in body:
            if uc.match(l) and depth == 0:
                issues.append(f"boundary: use case outside a system boundary: {l[:60]}")
            depth += l.count("{") - l.count("}")
        if not any(re.match(r"^(rectangle|package)\b.*\{", l) for l in body):
            issues.append("boundary: no system boundary; put the use cases in rectangle \"<system name>\" { ... }")
    in_note = False
    for n, raw in enumerate(lines, 1):
        l = raw.strip()
        if re.match(r"^(note|legend)\b", l) and not re.search(r"\bnote\b.*:|\{", l):
            in_note = True
        if in_note:
            if re.match(r"^end ?(note|legend)\b", l):
                in_note = False
            continue
        for text in labels(l):
            for code in CODE.findall(text):
                if code.upper() not in ALLOWED:
                    issues.append(f"codes: line {n}: '{code}' is a code a reader cannot read without a legend; "
                                  "use plain words")
    for s in STYLING:
        if re.search(rf"<<\s*{s}\s*>>", src) and not re.search(rf"hide\s+<<\s*{s}\s*>>\s+stereotype", src):
            issues.append(f"styling: <<{s}>> is used but not hidden; add 'hide <<{s}>> stereotype'")
    return issues


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    issues = check(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for i in issues:
        print(i)
    print("clean" if not issues else f"{len(issues)} issue(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
