"""Phase 8 — validation of a view (ADR-006 D3, revised by ADR-007 D4).

The three judging questions: "true to the code?" and "readable?" are checked here by rules;
"right view?" is for people (the stakeholder confirms the spec; the expert rates in studies).

1 notation       the diagram source compiles (local tool when available) and the
                 model kind is the viewpoint's
2 constraints    the viewpoint's named constraints (phase8/constraints.py)
3 faithfulness   every mark is an AEM entry (or a projection group / fold of AEM
                 entries) with at least inferred support, keeps its AEM name, and
                 appears once; a part (ADR-007) lists members that exist in the code
4 coverage       every assigned question is covered (Phase 6 table); a view with
                 questions draws at least one relation or interaction (not decomposition
                 or use-case views, which show containment)
5 readability    for abstracted views: labels, crossings, box text, title and legend, and
                 conformance to the view spec (phase8/readability.py)

Verdict: fail on any error; pass_with_limitations when gaps, limitations, partial
coverage or warnings remain; else pass. `repair_marks` lists the element/relation ids
whose removal would clear the layer 2-3 errors. No LLM judges the view.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from collections import Counter

from pydantic import BaseModel, Field

from task2view.contracts.aem import EvidenceModel
from task2view.contracts.card import RepositoryCard
from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.knowledge.catalog import Catalog
from task2view.phase6.decide import QuestionCoverage
from task2view.phase8.constraints import check_constraints
from task2view.phase8.readability import check as check_readability

_COMPILERS = {
    "plantuml": (["plantuml", "-checkonly"], ".puml"),
    "c4plantuml": (["plantuml", "-checkonly"], ".puml"),
    "graphviz": (["dot", "-Tsvg", "-o", "/dev/null"], ".dot"),
}


class ViewValidation(BaseModel):
    view_id: str
    verdict: str
    notation: dict = Field(default_factory=dict)
    constraints: list[dict] = Field(default_factory=list)
    faithfulness: list[dict] = Field(default_factory=list)
    coverage: list[dict] = Field(default_factory=list)
    readability: list[dict] = Field(default_factory=list)  # ADR-007: readable? and matches its spec?
    metrics: dict = Field(default_factory=dict)
    errors: int = 0
    warnings: int = 0
    repair_marks: list[str] = Field(default_factory=list)


def compile_check(render: RenderResult, *, enabled: bool = True) -> dict:
    spec = _COMPILERS.get(render.language)
    if not enabled or spec is None or shutil.which(spec[0][0]) is None:
        return {"status": "not-compiled", "reason": "no local compiler for this language" if enabled else "disabled"}
    cmd, suffix = spec
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"view{suffix}"
        src.write_text(render.source, encoding="utf-8")
        try:
            proc = subprocess.run([*cmd, str(src)], capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"status": "not-compiled", "reason": str(exc)[:200]}
    if proc.returncode == 0:
        return {"status": "pass"}
    return {"status": "fail", "reason": (proc.stdout + proc.stderr).strip()[:500]}


def _faithfulness(view: ArchitectureView, aem: EvidenceModel, card: RepositoryCard) -> list[dict]:
    out = []
    files = {f.path for f in card.files}
    seen_symbols: dict[str, str] = {}
    for dup in sorted(i for i, n in Counter(e.id for e in view.elements).items() if n > 1):
        out.append({"mark": dup, "severity": "error", "message": "element drawn more than once"})
    for e in view.content_elements():
        if e.id.startswith("fold:"):
            missing = [m for m in e.realized_by if m not in aem.elements]
            if missing:
                out.append({"mark": e.id, "severity": "error", "message": f"folded element lists unknown members {missing}"})
            continue
        if e.id.startswith("part:"):  # ADR-007 part: true to the code when every member exists
            missing = [m for m in e.realized_by if m not in card.symbols and m not in files]
            if missing or not e.realized_by:
                out.append({"mark": e.id, "severity": "error",
                            "message": f"{e.name}: members not in the repository {missing[:3]}" if missing else f"{e.name} has no members"})
            for sym in e.realized_by:
                if sym in seen_symbols and seen_symbols[sym] != e.id:
                    out.append({"mark": e.id, "severity": "error", "message": f"{sym} belongs to two parts"})
                seen_symbols[sym] = e.id
            continue
        el = aem.elements.get(e.id)
        if el is None and e.kind == "system":  # the analysed system itself (context view)
            continue
        if el is None:
            out.append({"mark": e.id, "severity": "error", "message": f"{e.name} is not in the evidence model"})
            continue
        if el.support == "weak":
            out.append({"mark": e.id, "severity": "error", "message": f"{e.name} is only weakly supported"})
        if e.name != el.name:
            out.append({"mark": e.id, "severity": "error", "message": f"renamed: {el.name!r} drawn as {e.name!r}"})
        for sym in el.realized_by if e.kind != "state" else []:  # an enum's states share its symbol
            if sym in seen_symbols and seen_symbols[sym] != e.id:
                out.append({"mark": e.id, "severity": "error",
                            "message": f"symbol {sym} is drawn by two elements ({seen_symbols[sym]}, {e.id})"})
            seen_symbols[sym] = e.id
    steps = {(st.source, st.target, st.message) for s in aem.scenarios.values() for st in s.steps}
    for i in view.interactions:
        if (i.source, i.target, i.message) not in steps:
            out.append({"mark": view.id, "severity": "error", "message": f"message {i.order} is not a recovered interaction"})
    return out


def validate_view(
    view: ArchitectureView,
    render: RenderResult,
    aem: EvidenceModel,
    card: RepositoryCard,
    catalog: Catalog,
    coverage: list[QuestionCoverage],
    *,
    compile_enabled: bool = True,
    arch=None,
    spec=None,
) -> ViewValidation:
    """``arch`` and ``spec``: the abstraction-step view and the view spec, for the readability checks."""
    vp = catalog.viewpoint(view.viewpoint_id)
    notation = compile_check(render, enabled=compile_enabled)
    notation.update({"language": render.language, "approximated": render.approximated,
                     "model_kind_matches": view.model_kind == vp.model_kind})
    constraints = check_constraints(view, vp, aem, card, catalog.constraints)
    faith = _faithfulness(view, aem, card)
    cov = [c.model_dump() for c in coverage]
    coverage_errors = []
    readable, metrics = check_readability(arch, render.source, viewpoint_id=vp.id, spec=spec) if arch is not None else ([], {})
    if coverage and len(view.content_elements()) >= 2 and view.model_kind not in {"table", "uml-state"} \
            and vp.id not in {"decomposition", "use-case"} and not view.relations and not view.interactions:
        coverage_errors.append({"severity": "error", "message": "the view has questions to answer but draws no relation"})

    errors = [f for f in constraints + faith + coverage_errors + readable if f["severity"] == "error"]
    if notation["status"] == "fail" or not notation["model_kind_matches"]:
        errors.append({"severity": "error", "message": "notation layer failed"})
    warnings = [f for f in constraints + readable if f["severity"] == "warning"]
    limited = bool(view.gaps or view.limitations or warnings or any(c.status != "supported" for c in coverage))
    verdict = "fail" if errors else "pass_with_limitations" if limited else "pass"
    repair = sorted({f["mark"] for f in constraints + faith if f["severity"] == "error" and f["mark"] != view.id})
    return ViewValidation(
        view_id=view.id, verdict=verdict, notation=notation, constraints=constraints, faithfulness=faith,
        coverage=cov + coverage_errors, readability=readable, metrics=metrics,
        errors=len(errors), warnings=len(warnings), repair_marks=repair,
    )
