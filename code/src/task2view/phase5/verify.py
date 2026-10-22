"""Mechanical verification of Phase 5 claims (no model call; design 02 §5.2).

A claim enters the Architecture Evidence Model only if at least one of its
citations checks out:
- the cited file exists and is not a UML model or binary,
- the first cited line exists,
- the excerpt occurs in the file (whitespace-insensitive) within the cited
  lines, give or take a small slack,
- a cited or claimed symbol exists in the repository card.

A relation's ends must each be a symbol in the repository card or a non-code element (actor, use case,
node, artifact, datastore, …) whose own element claim was verified earlier in the run (``register``):
relations between such elements, e.g. an actor and a use case, have no code symbol at either end. Next to a
non-code end, a name that is also a class (actor "Citizen", entity class Citizen) means the non-code element.

Support is then decided here, not by the agent:
- observed:   a code citation shows it: an element is cited in the file that declares
              it; a relation is backed by a graph edge in its direction, or the
              excerpt names the target as a word
- inferred:   cited, but not in that way
Observed means the cited code exists where the claim says; it does not prove the
claim's wording (responsibilities are the agent's reading of that code).
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


def _number(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_list(value) -> list:
    return value if isinstance(value, list) else [value] if value else []


class SymbolIndex:
    def __init__(self, card: RepositoryCard):
        self.card = card
        self.suffix: dict[str, set[str]] = {}
        for sid in card.symbols:
            parts = sid.split(".")
            for i in range(len(parts)):
                self.suffix.setdefault(".".join(parts[i:]), set()).add(sid)

    def resolve(self, ref: str | None, files: set[str] = frozenset()) -> str | None:
        """A symbol id for an id, a dotted suffix, or ``Type.member`` when the type has that member.
        An ambiguous name resolves only if exactly one candidate is declared in one of ``files``."""
        if not ref:
            return None
        ref = ref.strip().split("(", 1)[0]
        if ref in self.card.symbols:
            return ref
        candidates = self.suffix.get(ref) or set()
        if len(candidates) > 1:
            candidates = {c for c in candidates if self.card.symbols[c].file in files}
        if len(candidates) == 1:
            return next(iter(candidates))
        head, _, member = ref.rpartition(".")
        owner = self.resolve(head, files) if head else None
        if owner is not None and member in self._members(owner):
            return owner
        return None

    def _members(self, sid: str) -> set[str]:
        s = self.card.symbols[sid]
        return {m.name for m in s.methods} | {f.name for f in s.fields} | set(s.enum_constants)


class ClaimVerifier:
    def __init__(self, card: RepositoryCard, *, slack: int = 3, min_confidence: float = 0.0):
        self.card = card
        self.index = SymbolIndex(card)
        self.classes = {f.path: f.file_class for f in card.files}
        self.slack = slack
        self.min_confidence = min_confidence
        self._cache: dict[str, list[str]] = {}
        self.edges: set[tuple[str, str]] = {(e.source, e.target) for e in card.edges if e.kind in _RELATION_EDGE_KINDS}
        self.non_code: dict[str, str] = {}  # normalised name -> name of a verified non-code element

    def register(self, claim: Claim) -> None:
        """Remember a verified non-code element, so relations may end at it."""
        if claim.kind == "element" and claim.symbol is None and (claim.element_kind or "") in _NON_CODE_KINDS and claim.name:
            self.non_code[_norm(claim.name).lower()] = claim.name.strip()

    def _end(self, ref: str | None, files: set[str]) -> str | None:
        """A relation end: a repository symbol, else a verified non-code element (by name)."""
        sid = self.index.resolve(ref, files)
        if sid is not None or not ref:
            return sid
        return self.non_code.get(_norm(str(ref)).lower())

    def verify(self, raw: dict, *, claim_id: str, task_id: str, question_ids: list[str]) -> tuple[Claim | None, str]:
        kind = raw.get("kind")
        if kind not in {"element", "relation", "interaction", "state", "transition"}:
            return None, f"unknown claim kind {kind!r}"
        refs, problems = [], []
        for ev in _as_list(raw.get("evidence")):
            ok, reason = self._check_ref(ev)
            if ok:
                refs.append(EvidenceRef(file=ev["file"], symbol=self.index.resolve(ev.get("symbol"), {ev["file"]}) or ev.get("symbol"),
                                        lines=list(ev.get("lines") or [])[:2], excerpt=str(ev.get("excerpt") or "")))
            else:
                problems.append(reason)
        if not refs:
            return None, "no citation checks out: " + ("; ".join(problems) or "no evidence given")

        claim = Claim(
            id=claim_id, task=task_id, kind=kind,
            # the questions this claim answers (of the task's); all of them when the agent did not say
            question_ids=[q for q in _as_list(raw.get("answers")) if q in question_ids] or question_ids,
            element_kind=raw.get("element_kind"), name=raw.get("name"),
            responsibilities=[str(r).strip() for r in _as_list(raw.get("responsibilities")) if str(r).strip()],
            attributes=[a for a in _as_list(raw.get("attributes")) if isinstance(a, dict) and a.get("name")],
            source=raw.get("source"), target=raw.get("target"), relation=raw.get("relation"), label=raw.get("label"),
            order=int(raw["order"]) if str(raw.get("order", "")).strip().isdigit() else None,
            scenario=raw.get("scenario"), condition=raw.get("condition") or None,
            evidence=refs, confidence=max(0.0, min(1.0, _number(raw.get("confidence"), 0.5))),
        )
        if kind == "element":
            files = {r.file for r in refs}
            non_code = (claim.element_kind or "") in _NON_CODE_KINDS
            # a non-code element (an actor "Customer") is not the class that shares its name
            claim.symbol = self.index.resolve(raw.get("symbol"), files) or (
                None if non_code else self.index.resolve(raw.get("name"), files))
            if claim.symbol is None and (claim.element_kind or "") not in _NON_CODE_KINDS:
                return None, f"element {raw.get('name')!r} is not a symbol in the repository"
        if kind in {"relation", "interaction"}:
            files = {r.file for r in refs}
            src, tgt = self._end(claim.source, files), self._end(claim.target, files)
            # an actor named like a class (actor "Citizen", entity class Citizen): next to a non-code end
            # (a use case, a node), the name means the non-code element
            for end, other in (("source", tgt), ("target", src)):
                name = self.non_code.get(_norm(str(getattr(claim, end) or "")).lower())
                if name and other in self.non_code.values():
                    src, tgt = (name, tgt) if end == "source" else (src, name)
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
        path = str(ev["file"]).removeprefix("./")
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
        if not re.search(r"\w{3}", excerpt):
            return False, f"{path}: excerpt too short to locate"
        lo, hi = (1, len(lines))
        if span:
            lo = max(1, span[0] - self.slack)
            hi = min(len(lines), (span[1] if len(span) > 1 else span[0]) + self.slack)
        window = _norm("\n".join(lines[lo - 1:hi]))
        if excerpt not in window:
            return False, f"{path}: excerpt not found at lines {span or 'any'}"
        sym = ev.get("symbol")
        if sym and self.index.resolve(sym, {path}) is None:
            return False, f"{path}: symbol {sym!r} not in the repository"
        return True, ""

    def _support(self, claim: Claim) -> str:
        classes = {self.classes.get(r.file) for r in claim.evidence}
        if classes <= {"docs"}:
            return "documented"
        if claim.kind in {"relation", "interaction"}:
            src, tgt = claim.source, claim.target
            if (src, tgt) in self.edges:
                return "observed"
            names = [n for n in ((tgt or "").rsplit(".", 1)[-1], re.split(r"[(\s]", claim.label or "", maxsplit=1)[0])
                     if len(n) > 2]
            if any(re.search(rf"\b{re.escape(n)}\b", r.excerpt) for n in names for r in claim.evidence):
                return "observed"
            return "inferred"
        if claim.symbol and claim.symbol in self.card.symbols:  # an element is observed only where it is declared
            return "observed" if self.card.symbols[claim.symbol].file in {r.file for r in claim.evidence} else "inferred"
        return "observed"

    def _lines(self, path: str) -> list[str]:
        if path not in self._cache:
            try:
                self._cache[path] = (Path(self.card.root) / path).read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                self._cache[path] = []
        return self._cache[path]
