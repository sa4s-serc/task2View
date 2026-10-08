"""Mechanical verification of Phase 5 claims (no model call; design 02 §5.2).

A claim enters the Architecture Evidence Model only if at least one of its
citations checks out:
- the cited file exists and is not a UML model or binary,
- the cited lines exist,
- the excerpt occurs in the file (whitespace-insensitive) within the cited
  lines, give or take a small slack,
- a cited or claimed symbol exists in the repository card.

Support is then decided here, not by the agent:
- observed:   a code citation shows it (a relation is also backed by a graph
              edge between the two symbols, or the excerpt names the target)
- inferred:   cited, but the relation is not visible in the graph or excerpt
- documented: backed only by documentation files
- weak:       confidence below the configured floor
"""

from __future__ import annotations

import re
from pathlib import Path

from task2view.contracts.aem import Claim, EvidenceRef
from task2view.contracts.card import RepositoryCard

_NON_CODE_KINDS = {"actor", "use_case", "node", "execution_env", "artifact", "datastore", "external_system", "system",
                   "state", "team", "person", "decision_record", "requirement", "tier", "event_bus", "connector"}
_RELATION_EDGE_KINDS = {"calls", "field", "instantiates", "param", "returns", "extends", "implements", "annotated", "imports"}


def _norm(text: str) -> str:
    return " ".join(text.split())


class SymbolIndex:
    def __init__(self, card: RepositoryCard):
        self.card = card
        self.suffix: dict[str, set[str]] = {}
        for sid in card.symbols:
            parts = sid.split(".")
            for i in range(len(parts)):
                self.suffix.setdefault(".".join(parts[i:]), set()).add(sid)

    def resolve(self, ref: str | None) -> str | None:
        if not ref:
            return None
        ref = ref.strip()
        if ref in self.card.symbols:
            return ref
        candidates = self.suffix.get(ref) or set()
        if len(candidates) == 1:
            return next(iter(candidates))
        head = ref.rsplit(".", 1)[0] if "." in ref else None  # "Type.method" -> Type
        if head:
            return self.resolve(head) if head != ref else None
        return None


class ClaimVerifier:
    def __init__(self, card: RepositoryCard, *, slack: int = 3, min_confidence: float = 0.0):
        self.card = card
        self.index = SymbolIndex(card)
        self.classes = {f.path: f.file_class for f in card.files}
        self.slack = slack
        self.min_confidence = min_confidence
        self._cache: dict[str, list[str]] = {}
        self.edges: set[tuple[str, str]] = {(e.source, e.target) for e in card.edges if e.kind in _RELATION_EDGE_KINDS}

    def verify(self, raw: dict, *, claim_id: str, task_id: str, question_ids: list[str]) -> tuple[Claim | None, str]:
        kind = raw.get("kind")
        if kind not in {"element", "relation", "interaction", "state", "transition"}:
            return None, f"unknown claim kind {kind!r}"
        refs, problems = [], []
        for ev in raw.get("evidence") or []:
            ok, reason = self._check_ref(ev)
            if ok:
                refs.append(EvidenceRef(file=ev["file"], symbol=self.index.resolve(ev.get("symbol")) or ev.get("symbol"),
                                        lines=list(ev.get("lines") or [])[:2], excerpt=str(ev.get("excerpt") or "")))
            else:
                problems.append(reason)
        if not refs:
            return None, "no citation checks out: " + ("; ".join(problems) or "no evidence given")

        claim = Claim(
            id=claim_id, task=task_id, kind=kind, question_ids=question_ids,
            element_kind=raw.get("element_kind"), name=raw.get("name"),
            responsibilities=[str(r).strip() for r in raw.get("responsibilities") or [] if str(r).strip()],
            attributes=[a for a in raw.get("attributes") or [] if isinstance(a, dict) and a.get("name")],
            source=raw.get("source"), target=raw.get("target"), relation=raw.get("relation"), label=raw.get("label"),
            order=raw.get("order") if isinstance(raw.get("order"), int) else None,
            scenario=raw.get("scenario"), condition=raw.get("condition") or None,
            evidence=refs, confidence=max(0.0, min(1.0, float(raw.get("confidence") or 0.5))),
        )
        if kind == "element":
            claim.symbol = self.index.resolve(raw.get("symbol")) or self.index.resolve(raw.get("name"))
            if claim.symbol is None and (claim.element_kind or "") not in _NON_CODE_KINDS:
                return None, f"element {raw.get('name')!r} is not a symbol in the repository"
        if kind in {"relation", "interaction"}:
            src, tgt = self.index.resolve(claim.source), self.index.resolve(claim.target)
            if tgt is None or (src is None and kind == "relation"):
                return None, f"{kind} endpoint not in the repository: {claim.source!r} -> {claim.target!r}"
            claim.source, claim.target = src or claim.source, tgt
        claim.support = self._support(claim)
        if claim.support == "inferred":
            claim.confidence = min(claim.confidence, 0.7)
        if claim.confidence < self.min_confidence:
            claim.support = "weak"
        return claim, ""

    def _check_ref(self, ev) -> tuple[bool, str]:
        if not isinstance(ev, dict) or not ev.get("file"):
            return False, "citation without file"
        path = str(ev["file"]).lstrip("./")
        cls = self.classes.get(path)
        if cls is None:
            return False, f"{path}: not in the repository"
        if cls in {"model", "binary"}:
            return False, f"{path}: {cls} files are not evidence"
        ev["file"] = path
        lines = self._lines(path)
        excerpt = _norm(str(ev.get("excerpt") or ""))
        span = ev.get("lines") or []
        if span and (not isinstance(span, list) or not all(isinstance(x, int) for x in span[:2])):
            return False, f"{path}: lines must be [start, end]"
        if span and (span[0] < 1 or span[0] > len(lines)):
            return False, f"{path}: line {span[0]} does not exist"
        if not excerpt:
            return False, f"{path}: empty excerpt"
        lo, hi = (1, len(lines))
        if span:
            lo = max(1, span[0] - self.slack)
            hi = min(len(lines), (span[1] if len(span) > 1 else span[0]) + self.slack)
        window = _norm("\n".join(lines[lo - 1:hi]))
        if excerpt not in window:
            return False, f"{path}: excerpt not found at lines {span or 'any'}"
        sym = ev.get("symbol")
        if sym and self.index.resolve(sym) is None:
            return False, f"{path}: symbol {sym!r} not in the repository"
        return True, ""

    def _support(self, claim: Claim) -> str:
        classes = {self.classes.get(r.file) for r in claim.evidence}
        if classes <= {"docs"}:
            return "documented"
        if claim.kind in {"relation", "interaction"}:
            src, tgt = claim.source, claim.target
            if (src, tgt) in self.edges or (tgt, src) in self.edges and claim.kind == "relation":
                return "observed"
            target_name = (tgt or "").rsplit(".", 1)[-1]
            method = re.split(r"[(\s]", claim.label or "", maxsplit=1)[0]
            if any(target_name and target_name in r.excerpt or method and len(method) > 2 and method in r.excerpt
                   for r in claim.evidence):
                return "observed"
            return "inferred"
        return "observed"

    def _lines(self, path: str) -> list[str]:
        if path not in self._cache:
            try:
                self._cache[path] = (Path(self.card.root) / path).read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                self._cache[path] = []
        return self._cache[path]
