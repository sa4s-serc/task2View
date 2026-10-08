"""Write an ADR-006 run to disk (output package, design 03 §8; research plan §7)."""

from __future__ import annotations

import json
from pathlib import Path

from task2view.agents.run_v2 import RunV2Result


def _dump(path: Path, data) -> None:
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    elif isinstance(data, list):
        data = [d.model_dump(mode="json") if hasattr(d, "model_dump") else d for d in data]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_run_v2(result: RunV2Result, out: str | Path) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _dump(out / "repository_card.json", result.card)
    (out / "repository_card.txt").write_text(_card_text(result), encoding="utf-8")
    _dump(out / "stakeholder_profile.json", result.profile)
    _dump(out / "view_plan.json", result.plan)
    _dump(out / "architectural_questions.json", result.questions)
    _dump(out / "investigation_plan.json", result.tasks)
    _dump(out / "evidence_model.json", result.aem)
    _dump(out / "reconciliation.json", {vid: d.model_dump(mode="json") for vid, d in result.decisions.items()})
    _dump(out / "viewset.json", result.viewset)
    _dump(out / "validation_report.json", {vid: v.model_dump(mode="json") for vid, v in result.validation.items()})
    for view in result.viewset.views:
        vdir = out / view.id
        vdir.mkdir(exist_ok=True)
        _dump(vdir / "view.json", view)
        for render in result.renders.get(view.id, []):
            name = f"view.{render.language}.{render.extension}" if render.language != "plantuml" else f"view.{render.extension}"
            (vdir / name).write_text(render.source, encoding="utf-8")
    (out / "traceability.md").write_text(_traceability(result), encoding="utf-8")
    (out / "README.md").write_text(_readme(result), encoding="utf-8")
    (out / "run.log").write_text("\n".join(result.log) + "\n", encoding="utf-8")
    return out


def _card_text(result: RunV2Result) -> str:
    from task2view.phase0.card import render_card

    return render_card(result.card) + "\n"


def _traceability(result: RunV2Result) -> str:
    lines = ["# Traceability", ""]
    for view in result.viewset.views:
        lines += [f"## {view.id} — {view.viewpoint_name}", "", "| Element | Files | Symbols |", "|---|---|---|"]
        for row in view.traceability:
            lines.append(f"| {row.name} | {', '.join(row.files) or '—'} | {', '.join(row.symbols[:6]) or '—'} |")
        lines.append("")
    return "\n".join(lines)


def _readme(result: RunV2Result) -> str:
    p, plan = result.profile, result.plan
    lines = [
        f"# Task2View run — {result.card.name}", "",
        f"**Goal:** {result.goal}", "",
        f"- Role: {p.role or p.role_label or 'unknown'}; target: {p.target or 'whole system'}; detail level: {p.detail_level}",
        f"- Needs (primary): {', '.join(plan.needs) or 'none'}; secondary: {', '.join(plan.secondary_needs) or 'none'}",
        f"- Generator model: {result.llm}; judge model: {result.judge_llm or 'none'}",
        f"- Repository signals: {', '.join(sorted(result.card.signals))}", "",
        "## Views", "",
        "| View | Viewpoint | Decision | Verdict | Elements | Notation |", "|---|---|---|---|---|---|",
    ]
    for view in result.viewset.views:
        d, v = result.decisions[view.id], result.validation[view.id]
        lines.append(f"| {view.id} | {view.viewpoint_name} ({view.vb_ref}) | {d.decision} | {v.verdict} | "
                     f"{len(view.content_elements())} | {v.notation.get('language')}"
                     f"{' (approximated)' if v.notation.get('approximated') else ''} |")
    lines += ["", "## Rationale", ""]
    lines += [f"- {pv.viewpoint_id}: {pv.rationale}" for pv in plan.views]
    gaps = result.viewset.declared_gaps + [f"need not covered: {n}" for n in plan.uncovered_needs] + \
        [f"secondary need not shown: {n}" for n in plan.secondary_not_shown]
    lines += ["", "## Limitations and declared gaps", ""]
    lines += [f"- {g}" for g in gaps] or ["- none"]
    for view in result.viewset.views:
        lines += [f"- {view.id}: {lim}" for lim in view.limitations + view.gaps]
    lines += ["", "## Evidence", "",
              f"- {len(result.aem.claims)} verified claims, {len(result.aem.rejected_claims)} rejected; "
              f"{len(result.aem.elements)} model elements; {len(result.aem.relations)} relations; "
              f"{len(result.aem.scenarios)} scenarios", ""]
    return "\n".join(lines)
