"""ADR-007: structural views come from the abstraction step (phase5/abstract.py), not from class-level
projection. This module turns an ArchView into the common view format, so Phase 6, Phase 8, the run
package and the other notations handle it like any other view; the main diagram is C4-PlantUML."""

from __future__ import annotations

from task2view.contracts.architecture import ArchView
from task2view.contracts.card import RepositoryCard
from task2view.contracts.views import ArchitectureView, RenderResult, TraceRow, ViewElement, ViewRelation
from task2view.knowledge.catalog import Viewpoint
from task2view.phase7.c4 import _text, render_c4

# Viewpoints drawn as parts and connectors. Style views with their own element kinds (pipes and
# filters, publish-subscribe, peer-to-peer, aspects, concurrency) and the context view keep projection.
ABSTRACTED = {"decomposition", "uses", "layered", "cnc-generic", "client-server", "multi-tier", "shared-data", "soa"}
_KINDS = {"database": ["datastore"], "web_client": ["client", "component", "module"], "ui": ["client", "component", "module"],
          "api": ["interface", "server", "service", "component", "module"]}


def _kind(role: str, vp: Viewpoint) -> str:
    for kind in _KINDS.get(role, []) + ["component", "service", "module", "tier"]:
        if kind in vp.element_kinds:
            return kind
    return vp.element_kinds[0]


def to_architecture_view(arch: ArchView, base: ArchitectureView, vp: Viewpoint, card: RepositoryCard) -> ArchitectureView:
    view = base.model_copy(update={"elements": [], "relations": [], "interactions": [], "fragments": [],
                                   "traceability": [], "overflow": [], "gaps": list(base.gaps),
                                   "limitations": [f"not drawn: {o}" for o in arch.omitted] + arch.notes})
    rel_kind = next((k for k in ("uses", "request-reply", "allowed-to-use", "attachment", "reads", "is-part-of")
                     if k in vp.relation_kinds), vp.relation_kinds[0])
    for p in arch.parts:
        view.elements.append(ViewElement(id=f"part:{p.id}", kind=_kind(p.role, vp), name=p.name, stereotype=p.role,
                                         technology=p.technology, responsibilities=[_text(p).replace("\\n", "; ")],
                                         realized_by=p.members + p.files))
        files = sorted({card.symbols[m].file for m in p.members if m in card.symbols} | set(p.files))
        view.traceability.append(TraceRow(element=f"part:{p.id}", name=p.name, files=files, symbols=p.members))
    for c in arch.connectors:
        view.relations.append(ViewRelation(id=f"conn:{c.source}:{c.target}", kind=rel_kind, source=f"part:{c.source}",
                                           target=f"part:{c.target}", label=c.label, protocol=c.protocol,
                                           against_layering=c.against_layering))
    return view


def render_abstracted(arch: ArchView, view: ArchitectureView, system: str) -> RenderResult:
    return RenderResult(language="plantuml", model_kind=view.model_kind, source=render_c4(arch, system), extension="puml")
