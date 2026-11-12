#!/usr/bin/env python3
"""check_view: notation and readability checks on a view's PlantUML source that a reader would otherwise catch.

    python3 -I .claude/skills/uml-view/scripts/check_view.py view-out/<case>/view.puml

Checks (each is a general rule, not tied to one system):
  boundary   use case diagram: every use case is inside a system boundary (rectangle/package), actors outside
             (UML 2.5.1 cl. 18: the subject of a use case)
  codes      labels use plain words: no invented codes or numbering such as IP1, UC3, C2 that need a legend
  styling    the styling stereotypes <<accent>>, <<alert>>, <<muted>> are hidden, so they are not printed as text
  style      one shared style for every view (the plantuml-diagrams house style): Helvetica, no text below 12 pt,
             colours only from the house palette (colour carries meaning, with a legend)
On the rendered diagram (needs plantuml on PATH; skipped otherwise):
  fit        readable on one screen: scaled to 1600 px wide, no text smaller than 9 px. Group or split the view
             rather than shrinking it (no element count is imposed)
  flow       one reading direction: at most a quarter of the arrows run against the main direction
             (top to bottom, or left to right); replies and callbacks are the exception, so draw them dashed
  grouping   component, package and deployment views: 10 or more boxes side by side with no container are
             nested in their layer, subsystem or node instead of listed flat
Grounding: Purchase 1997 (crossings, then bends, hurt reading most); Moody 2009, Physics of Notations
(complexity management, cognitive integration, colour only for meaning); Störrle 2014/2017 (UML layout quality
affects comprehension, more so as diagrams grow).

Exit 0 when clean, 1 when an issue is found. Stdlib only.
"""
from __future__ import annotations

import math
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://www.w3.org/2000/svg}"
FIT_WIDTH, MIN_PX = 1600, 9.0
# the colours of the plantuml-diagrams house style and its templates
HOUSE = {"#475569", "#64748B", "#CBD5E1", "#F8FAFC", "#B91C1C", "#FFF7E0", "#FEE2E2", "#F1F5F9", "#B45309", "#7F1D1D",
         "#1F2937", "#1E3A8A", "#1D4ED8", "#D55E00", "#94A3B8", "#FFF7ED", "#FEF2F2", "#F5F3FF", "#F0FDF4", "#C2410C",
         "#6D28D9", "#15803D", "#FFFFFF", "#000000", "#WHITE", "#BLACK", "#TRANSPARENT"}

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
    for m in re.finditer(r"(?i)fontsize\s+(\d+)", src):
        if int(m.group(1)) < 12:
            issues.append(f"style: FontSize {m.group(1)} is below 12; keep the house style sizes")
    for m in re.finditer(r"(?i)(?:fontname|defaultfontname)\s+\"?([A-Za-z ]+?)\"?\s*(?:;|$|\})", src, re.M):
        if m.group(1).strip().lower() != "helvetica":
            issues.append(f"style: font {m.group(1).strip()}; use the house font Helvetica in every view")
    used = {c.upper() for c in re.findall(r"#(?:[0-9A-Fa-f]{6}|[A-Za-z]+)\b", src)}
    odd = sorted(c for c in used if c not in HOUSE and not re.fullmatch(r"#[0-9A-F]{3}", c))
    if odd:
        issues.append(f"style: colours outside the house palette ({', '.join(odd[:5])}); use <<accent>>, <<alert>> "
                      "or <<muted>> with a legend, or no colour")
    return issues


def rendered(src_path: Path) -> list[str]:
    """Checks on the rendered SVG: fit, flow, grouping."""
    if not shutil.which("plantuml"):
        return []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_src = Path(tmp) / "v.puml"
        tmp_src.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
        subprocess.run(["plantuml", "-tsvg", str(tmp_src)], capture_output=True)
        svg = Path(tmp) / "v.svg"
        if not svg.exists():
            return ["render: plantuml produced no SVG"]
        root = ET.parse(svg).getroot()
    vb = [float(v) for v in (root.get("viewBox") or "0 0 0 0").split()]
    width = vb[2] or float(re.sub(r"[^\d.]", "", root.get("width", "0")) or 0)
    dtype = root.get("data-diagram-type", "")
    issues = []
    sizes = [float(t.get("font-size")) for t in root.iter(f"{NS}text") if t.get("font-size") and (t.text or "").strip()]
    scale = min(1.0, FIT_WIDTH / width) if width else 1.0
    if sizes and min(sizes) * scale < MIN_PX:
        issues.append(f"fit: {width:.0f} px wide; on a {FIT_WIDTH} px screen its text shrinks to "
                      f"{min(sizes) * scale:.1f} px. Group elements into containers, shorten labels, or split the "
                      "view by concern; do not drop what the concern needs")
    if dtype != "SEQUENCE":
        dirs = []
        for g in root.iter(f"{NS}g"):
            if g.get("class") != "link":
                continue
            head = next((p for p in g.iter(f"{NS}polygon")), None)
            path = next((p for p in g.iter(f"{NS}path")), None)
            if head is None or path is None:
                continue
            hv = [float(v) for v in re.findall(r"-?[\d.]+", head.get("points", ""))]
            pv = [float(v) for v in re.findall(r"-?[\d.]+", path.get("d", ""))]
            if len(hv) < 4 or len(pv) < 4:
                continue
            hx, hy = sum(hv[0::2]) / len(hv[0::2]), sum(hv[1::2]) / len(hv[1::2])
            pts = list(zip(pv[0::2], pv[1::2]))
            sx, sy = max(pts, key=lambda p: math.hypot(p[0] - hx, p[1] - hy))
            dx, dy = hx - sx, hy - sy
            if math.hypot(dx, dy) > 20:
                dirs.append((dx, dy))
        if len(dirs) >= 4:
            down = sum(1 for dx, dy in dirs if abs(dy) >= abs(dx) and dy > 0)
            up = sum(1 for dx, dy in dirs if abs(dy) >= abs(dx) and dy < 0)
            right = sum(1 for dx, dy in dirs if abs(dx) > abs(dy) and dx > 0)
            left = sum(1 for dx, dy in dirs if abs(dx) > abs(dy) and dx < 0)
            main, against = max(((down, up, "top to bottom"), (up, down, "bottom to top"),
                                 (right, left, "left to right"), (left, right, "right to left")))[0:3:2], None
            against = {"top to bottom": up, "bottom to top": down, "left to right": left, "right to left": right}[main[1]]
            if against > len(dirs) / 4:
                issues.append(f"flow: {against} of {len(dirs)} arrows run against the main direction ({main[1]}); "
                              "declare elements in reading order (users first, data last) and point dependencies "
                              "the same way; draw replies and callbacks dashed")
    if dtype in ("DESCRIPTION", "COMPONENT", "DEPLOYMENT", ""):
        boxes, clusters = [], []
        for g in root.iter(f"{NS}g"):
            kind = g.get("class")
            r = next((e for e in g if e.tag in (f"{NS}rect", f"{NS}path", f"{NS}polygon")), None)
            if kind not in ("entity", "cluster") or r is None:
                continue
            if r.tag == f"{NS}rect":
                x, y = float(r.get("x", 0)), float(r.get("y", 0))
                b = (x, y, x + float(r.get("width", 0)), y + float(r.get("height", 0)))
            else:
                v = [float(t) for t in re.findall(r"-?[\d.]+", r.get("points", "") or r.get("d", ""))]
                if len(v) < 4:
                    continue
                b = (min(v[0::2]), min(v[1::2]), max(v[0::2]), max(v[1::2]))
            (clusters if kind == "cluster" else boxes).append(b)
        inside = lambda b: any(c[0] <= b[0] and c[1] <= b[1] and c[2] >= b[2] and c[3] >= b[3] for c in clusters)
        flat = [b for b in boxes if not inside(b) and (b[2] - b[0]) > 40]
        if len(flat) >= 10 and not clusters:
            issues.append(f"grouping: {len(flat)} boxes side by side with no container; nest them in their layer, "
                          "subsystem or node so the reader sees the structure first")
    return issues


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    issues = check(Path(sys.argv[1]).read_text(encoding="utf-8")) + rendered(Path(sys.argv[1]))
    for i in issues:
        print(i)
    print("clean" if not issues else f"{len(issues)} issue(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
