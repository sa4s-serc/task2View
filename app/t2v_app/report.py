"""The result of a job: out/README.md with the request, the 42010 inputs and every view; out/inputs.yaml."""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path

import yaml

from .phase1 import VIEWPOINTS

CHECKS = {"inventory-check.txt": "Evidence and relations (inventory against the code and the graph)",
          "view-check.txt": "Notation and readability",
          "consistency-check.txt": "Same names across this request's views"}


def write_inputs(out: Path, records: list[dict]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "inputs.yaml").write_text(
        "# ISO/IEC/IEEE 42010:2022 inputs of each view, as confirmed by the stakeholder.\n"
        + yaml.safe_dump({"views": records}, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")


def inputs_rows(record: dict) -> list[tuple[str, str]]:
    p = record["perspective"]
    return [("Entity of interest", record["entity_of_interest"]),
            ("Part of the system in focus", record.get("focus", "")),
            ("Stakeholder", record["stakeholder"]),
            ("Stakeholder perspective", p["description"]),
            ("Detail level", p["detail_level"]),
            ("Concern", record["concern"]),
            ("Concern details", "; ".join(record["concern_details"])),
            ("Aspect", record["aspect"]),
            ("Viewpoint", record["viewpoint"]),
            ("Model kind", record["model_kind"])]


def checks(view_dir: Path) -> list[dict]:
    """Each check that ran on the view: its label, whether it passed, and its output."""
    out = []
    for name, label in CHECKS.items():
        if (view_dir / name).exists():
            verdict, _, text = (view_dir / name).read_text(encoding="utf-8", errors="replace").partition("\n")
            out.append({"label": label, "file": name, "text": text.strip(), "passed": verdict == "passed"})
    return out


def review(view_dir: Path) -> dict:
    """The critic's verdict on the version that was kept."""
    try:
        loop = json.loads((view_dir / "loop.json").read_text())
        kept = json.loads((view_dir / f"critique-{2 if loop.get('kept') == 'v2' else 1}.json").read_text())
    except (OSError, ValueError):
        return {}
    return {"revised": loop.get("revised", False), "kept": loop.get("kept"), "verdict": kept.get("verdict"),
            "level": kept.get("level"), "concern_details": kept.get("concern_details", []),
            "open": kept.get("fixes", []) if kept.get("verdict") == "revise" else []}


def takeaway(view_dir: Path) -> str:
    """The one-sentence answer the view's README opens with, if it has one."""
    try:
        found = re.search(r"\*\*Takeaway:?\*\*:?\s*(.+)", (view_dir / "README.md").read_text(encoding="utf-8"))
    except OSError:
        return ""
    return found.group(1).strip() if found else ""


def _demote(markdown: str) -> str:
    """Push the headings of a view's README two levels down, so they sit under the view's heading."""
    return "\n".join("##" + line if line.startswith("#") else line for line in markdown.splitlines())


def write_readme(out: Path, request: str, records: list[dict]) -> None:
    first = records[0]
    lines = ["# Architecture views", "", "**Request:** " + request, "",
             f"**System:** {first['entity_of_interest']}  ", f"**In focus:** {first.get('focus', '')}  ",
             f"**Stakeholder:** {first['stakeholder']}  ",
             f"**Perspective:** {first['perspective']['description']}", ""]
    if first["clarifications"]:
        lines += ["**Clarifications from the stakeholder:**", *[f"- {c}" for c in first["clarifications"]], ""]
    for n, record in enumerate(records, 1):
        folder = out / record["id"]
        lines += [f"## View {n}: {record['model_kind']} ({record['concern']})", "",
                  f"![View {n}]({record['id']}/view.png)", "",
                  "| ISO/IEC/IEEE 42010 input | Value |", "|---|---|",
                  *[f"| {k} | {str(v).replace('|', '/')} |" for k, v in inputs_rows(record)], ""]
        for reason in record["elicitation"]["reasons"]:
            lines += [f"Why this viewpoint: {reason}", ""]
        for a in record["elicitation"]["alternatives"]:
            lines += [f"Also plausible, not drawn: {VIEWPOINTS[a['viewpoint']]['model_kind']}. {a.get('reason', '')}", ""]
        if (folder / "README.md").exists():
            lines += [_demote((folder / "README.md").read_text(encoding="utf-8", errors="replace")), ""]
        lines += ["### Checks", ""]
        lines += [f"- {c['label']}: {'passed' if c['passed'] else 'issues, see ' + record['id'] + '/' + c['file']}"
                  for c in checks(folder)]
        r = review(folder)
        if r:
            lines.append(f"- Independent review: {r['verdict']}, detail level {r['level']}"
                         + (" (after one revision)" if r["revised"] and r["kept"] == "v2" else ""))
            lines += [f"  - still open: {f}" for f in r["open"]]
        lines += ["", f"Files: `{record['id']}/view.puml` (source), `view.png`, `inventory.json` (each element with "
                  "its evidence in the code), `README.md`.", ""]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")


def zip_bytes(out: Path) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(out.rglob("*")):
            if path.is_file():
                z.write(path, Path("architecture-views") / path.relative_to(out))
    buffer.seek(0)
    return buffer
