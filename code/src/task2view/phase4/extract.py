"""Phase 4a — extract a notation-neutral view model. LLM + repository graph."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from task2view.contracts.models import (
    ALLOWED_ELEMENT_KINDS,
    ALLOWED_GROUP_KINDS,
    ALLOWED_RELATION_KINDS,
    Evidence,
    PipelineError,
    RepositoryScope,
    ViewElement,
    ViewGroup,
    ViewModel,
    ViewRelation,
    ViewSpecification,
    canonical_element_kind,
    canonical_relation_kind,
)
from task2view.phase3.graph import RepositoryGraph
from task2view.phase4.gemini import DEFAULT_MODEL, generate_json

EXTRACT_PROMPT = """You extract an architecture view from source code. Output JSON only.

Rules:
- Use ONLY the provided files and the repository graph. Do not invent types.
- Every non-external element must have evidence.file and evidence.symbol that exist in the files.
- support is "observed" if a file excerpt shows it, otherwise "inferred".
- Prefer the types named in the graph listing. Actors, datastores, and external systems may be external.
- Keep the view at the requested granularity. Do not dump every class if granularity is component_or_service_level.
- Answer each required_information id or list it in unanswered.
- Put each non-external element in the group that matches the parent directory of evidence.file. Do not invent layer names.
- Include a relation for every uses/calls edge among selected files that the graph listing shows.

Return this shape:
{{
  "elements": [{{"id":"E1","name":"...","kind":"component|module|actor|datastore|external_system","role":"...","external":false,
    "evidence":{{"file":"relative/path","symbol":"Name","excerpt":"..."}},
    "support":"observed"}}],
  "relations": [{{"id":"R1","from":"E1","to":"E2","kind":"uses|calls|dataflow|contains|deploys|transition",
    "label":"methodName","order":1,
    "evidence":{{"file":"...","symbol":"...","excerpt":"..."}},
    "support":"observed"}}],
  "groups": [{{"id":"G1","name":"directory-name","kind":"package|layer|boundary","contains":["E1"]}}],
  "unanswered": ["RI-6"],
  "notes": []
}}

view_type: {view_type}
granularity: {granularity}
purpose: {purpose}
required_information:
{required}

FILE/DIRECTORY GRAPH (kept files; parent directory in [dir]; import-like uses edges; scoped files first):
{graph}

SOURCE FILES:
{files}
"""


def _pack_files(repo_root: str, scope: RepositoryScope, per_file: int = 12_000) -> str:
    """Include every scoped path. Truncate a file if huge; never drop later files."""
    root = Path(repo_root)
    chunks: list[str] = []
    truncated: list[str] = []
    unread: list[str] = []
    for cand in scope.candidate_areas:
        path = root / cand.path
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            unread.append(cand.path)
            chunks.append(f"### FILE: {cand.path}\n/* unreadable */\n")
            continue
        if len(text) > per_file:
            text = text[:per_file] + "\n/* truncated */\n"
            truncated.append(cand.path)
        chunks.append(f"### FILE: {cand.path}\n{text}\n")
    header = (
        f"PACKED {len(scope.candidate_areas)} scoped files; omitted=0; "
        f"truncated={len(truncated)}; unread={len(unread)}\n"
    )
    if truncated:
        header += "truncated_paths: " + ", ".join(truncated) + "\n"
    if unread:
        header += "unread_paths: " + ", ".join(unread) + "\n"
    return header + "\n".join(chunks)


def _as_element(raw: dict, idx: int) -> ViewElement:
    ev = raw.get("evidence") or {}
    kind = canonical_element_kind(str(raw.get("kind") or "component"))
    return ViewElement(
        id=str(raw.get("id") or f"E{idx}"),
        name=str(raw.get("name") or "").strip(),
        kind=kind,
        role=raw.get("role"),
        external=bool(raw.get("external")),
        evidence=Evidence(
            file=ev.get("file"),
            symbol=ev.get("symbol"),
            excerpt=ev.get("excerpt"),
        )
        if ev
        else None,
        support="inferred" if raw.get("support") == "inferred" else "observed",
    )


def _as_relation(raw: dict, idx: int) -> ViewRelation:
    ev = raw.get("evidence") or {}
    kind = canonical_relation_kind(str(raw.get("kind") or "uses"))
    return ViewRelation(
        id=str(raw.get("id") or f"R{idx}"),
        frm=str(raw.get("from") or raw.get("frm") or ""),
        to=str(raw.get("to") or ""),
        kind=kind,
        label=raw.get("label"),
        order=raw.get("order"),
        evidence=Evidence(
            file=ev.get("file"),
            symbol=ev.get("symbol"),
            excerpt=ev.get("excerpt"),
        )
        if ev
        else None,
        support="inferred" if raw.get("support") == "inferred" else "observed",
    )


def _as_group(raw: dict, idx: int) -> ViewGroup:
    kind = str(raw.get("kind") or "layer")
    if kind not in ALLOWED_GROUP_KINDS:
        kind = "layer"
    return ViewGroup(
        id=str(raw.get("id") or f"G{idx}"),
        name=str(raw.get("name") or ""),
        kind=kind,
        contains=[str(x) for x in (raw.get("contains") or raw.get("contains") or [])],
    )


def _el_key(el: ViewElement) -> str:
    return f"{el.kind}:{el.name.casefold().strip()}"


def merge_samples(samples: list[ViewModel], request_id: str, view_spec: ViewSpecification) -> ViewModel:
    n = max(1, len(samples))
    el_votes: dict[str, list[ViewElement]] = defaultdict(list)
    rel_votes: dict[tuple, list[ViewRelation]] = defaultdict(list)
    group_members: dict[str, set[str]] = defaultdict(set)
    group_meta: dict[str, ViewGroup] = {}
    unanswered: dict[str, int] = defaultdict(int)
    notes: list[str] = []
    for vm in samples:
        for el in vm.elements:
            if el.name:
                el_votes[_el_key(el)].append(el)
        id_to_name = {el.id: el.name for el in vm.elements}
        for rel in vm.relations:
            frm = id_to_name.get(rel.frm, rel.frm)
            to = id_to_name.get(rel.to, rel.to)
            rel_votes[(frm.casefold(), to.casefold(), rel.kind, (rel.label or "").casefold())].append(rel)
        for g in vm.groups:
            group_meta.setdefault(g.name, g)
            for eid in g.contains:
                if eid in id_to_name:
                    group_members[g.name].add(id_to_name[eid])
        for u in vm.unanswered:
            unanswered[u] += 1
        notes.extend(vm.notes)

    elements: list[ViewElement] = []
    name_to_id: dict[str, str] = {}
    for i, (_key, votes) in enumerate(sorted(el_votes.items()), start=1):
        best = votes[0]
        eid = f"E{i}"
        best.id = eid
        best.agreement = len(votes) / n
        elements.append(best)
        name_to_id[best.name.casefold()] = eid

    rebuilt: list[ViewRelation] = []
    for i, (key, votes) in enumerate(sorted(rel_votes.items()), start=1):
        frm_n, to_n, kind, _label = key
        best = votes[0]
        frm_id = name_to_id.get(frm_n)
        to_id = name_to_id.get(to_n)
        if not frm_id or not to_id:
            continue
        rebuilt.append(
            ViewRelation(
                id=f"R{i}",
                frm=frm_id,
                to=to_id,
                kind=kind,
                label=best.label,
                order=best.order,
                evidence=best.evidence,
                support=best.support,
                agreement=len(votes) / n,
            )
        )

    remapped_groups: list[ViewGroup] = []
    for i, (gname, names) in enumerate(group_members.items(), start=1):
        meta = group_meta[gname]
        contains = [name_to_id[n.casefold()] for n in names if n.casefold() in name_to_id]
        if contains:
            remapped_groups.append(
                ViewGroup(id=f"G{i}", name=gname, kind=meta.kind, contains=contains)
            )

    return ViewModel(
        request_id=request_id,
        view_type=view_spec.selected_view.view_type,
        granularity=view_spec.selected_view.granularity,
        groups=remapped_groups,
        elements=elements,
        relations=rebuilt,
        unanswered=[k for k, c in unanswered.items() if c >= max(1, n // 2)],
        notes=list(dict.fromkeys(notes)),
    )


def _model_from_dict(raw: dict, request_id: str, view_spec: ViewSpecification) -> ViewModel:
    elements = [_as_element(x, i) for i, x in enumerate(raw.get("elements") or [], start=1)]
    id_ok = {e.id for e in elements}
    relations = []
    for i, x in enumerate(raw.get("relations") or [], start=1):
        rel = _as_relation(x, i)
        if rel.frm in id_ok and rel.to in id_ok:
            relations.append(rel)
    groups = [_as_group(x, i) for i, x in enumerate(raw.get("groups") or [], start=1)]
    return ViewModel(
        request_id=request_id,
        view_type=view_spec.selected_view.view_type,
        granularity=view_spec.selected_view.granularity,
        groups=groups,
        elements=elements,
        relations=relations,
        unanswered=[str(x) for x in raw.get("unanswered") or []],
        notes=[str(x) for x in raw.get("notes") or []],
    )


def extract_view(
    view_spec: ViewSpecification,
    scope: RepositoryScope,
    graph: RepositoryGraph,
    repo_root: str,
    *,
    model: str | None = None,
    samples: int = 1,
    generate=generate_json,
    prompt_template: str = EXTRACT_PROMPT,
) -> ViewModel:
    if not scope.candidate_areas:
        raise PipelineError("scope is empty; cannot extract a view")
    required = "\n".join(f"- {i.id}: {i.need}" for i in view_spec.required_information)
    prefer: list[str] = []
    for cand in scope.candidate_areas:
        prefer.extend(graph.path_to_types.get(cand.path, []))
    prompt = prompt_template.format(
        view_type=view_spec.selected_view.view_type,
        granularity=view_spec.selected_view.granularity,
        purpose=view_spec.selected_view.purpose,
        required=required,
        graph=graph.summary(prefer=prefer),
        files=_pack_files(repo_root, scope),
    )
    built: list[ViewModel] = []
    for _ in range(max(1, samples)):
        raw = generate(prompt, model=model or DEFAULT_MODEL)
        if isinstance(raw, dict):
            raw = {k: v for k, v in raw.items() if not str(k).startswith("_")}
        built.append(_model_from_dict(raw, view_spec.request_id, view_spec))
    return merge_samples(built, view_spec.request_id, view_spec)

