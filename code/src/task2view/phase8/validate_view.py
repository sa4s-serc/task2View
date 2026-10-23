"""Phase 8 — two checks per view, by rules (no model judges a view):

1 compiles       the PlantUML source compiles (when plantuml is installed) and the model kind is the viewpoint's
2 true to code   every mark is an evidence-model entry (or a part of entries) with at least inferred
                 support, keeps its name and appears once; a part lists member classes that exist in the code;
                 every message is a recovered interaction

Verdict: fail on any error; pass_with_limitations when the view declares gaps or limitations; else pass.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, Field

from task2view.contracts.aem import EvidenceModel
from task2view.contracts.card import RepositoryCard
from task2view.contracts.views import ArchitectureView, RenderResult
from task2view.knowledge.catalog import Catalog

_COMPILERS = {"plantuml": (["plantuml", "-checkonly"], ".puml")}


class ViewValidation(BaseModel):
    view_id: str
    verdict: str
    notation: dict = Field(default_factory=dict)
    faithfulness: list[dict] = Field(default_factory=list)
    errors: int = 0


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


def validate_view(view: ArchitectureView, render: RenderResult, aem: EvidenceModel, card: RepositoryCard,
                  catalog: Catalog, *, compile_enabled: bool = True) -> ViewValidation:
    vp = catalog.viewpoint(view.viewpoint_id)
    notation = compile_check(render, enabled=compile_enabled)
    notation.update({"language": render.language, "model_kind_matches": view.model_kind == vp.model_kind})
    faith = _faithfulness(view, aem, card)
    errors = [f for f in faith if f["severity"] == "error"]
    if notation["status"] == "fail" or not notation["model_kind_matches"]:
        errors.append({"severity": "error", "message": "the diagram does not compile or is not the viewpoint's kind"})
    verdict = "fail" if errors else "pass_with_limitations" if view.gaps or view.limitations else "pass"
    return ViewValidation(view_id=view.id, verdict=verdict, notation=notation, faithfulness=faith, errors=len(errors))
