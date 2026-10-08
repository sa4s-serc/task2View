"""Phase 5. Extract a notation-neutral view model from the scoped files and the graph."""

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
from task2view.phase4.graph import RepositoryGraph
from task2view.llm import generate_json

_VIEWTYPE_VIEWPOINT = {
    "context_view": "context",
    "class_view": "code-mapping",
    "deployment_view": "allocation-deployment",
}


def ciao_grounding_rules(viewpoint_id: str | None = None, view_type: str | None = None) -> str:
    """CIAO mapping rules for this viewpoint. Empty when the viewpoint is unknown."""
    from importlib.resources import files
    import json

    try:
        raw = files("task2view.knowledge.data").joinpath("ciao_prompt.json").read_text(encoding="utf-8")
        doc = json.loads(raw)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return ""
    vid = (viewpoint_id or "").strip() or _VIEWTYPE_VIEWPOINT.get(view_type or "", "")
    block = (doc.get("viewpoints") or {}).get(vid)
    if not isinstance(block, dict):
        return ""
    title = block.get("title") or vid
    lines = [
        f"CIAO mapping_rules for {vid} ({title}). One view; ViewModel JSON only.",
    ]
    guidelines = doc.get("global_guidelines") or {}
    objective = guidelines.get("objective")
    if isinstance(objective, str) and objective.strip():
        lines.append(objective.strip())
    for key in ("coverage", "naming", "grounding"):
        for item in guidelines.get(key) or []:
            lines.append(f"- {item}")
    for rule in block.get("mapping_rules") or []:
        lines.append(f"- {rule}")
    for forbidden in block.get("forbidden_inferences") or []:
        lines.append(f"- do not infer: {forbidden}")
    return "\n".join(lines)

EXTRACT_PROMPT = """You extract an architecture view from source code. Output JSON only.

Follow this catalog grain. Do not invent a different diagram kind.
{grain}

Shared grounding:
- Use ONLY the scoped SOURCE FILES and the scoped file graph below. Do not invent types or files.
- Publish the smallest model that answers the ANALYSIS PLAN. Do not
  draw one box per scoped file. A file that no task names is not a box.
- evidence.file must be a path in SOURCE FILES. evidence.symbol is optional and must be
  a groundable file stem when present.
- If grain unit is type, published names may be those file stems. Otherwise name boxes
  by responsibility; ground each to one stem. Never rename a responsibility box to a
  folder, package, or [dir] value.
- Never name a box Boundary, Entity, DTO, Controller, Database, or a Java package.
- Actors, datastores, and external systems may be external.
- Do not try to answer DECLARED GAPS in this view. List them in unanswered if asked.
- support is "observed" if a file excerpt shows it, otherwise "inferred".
- Answer each required_information id or list it in unanswered.

Return this shape:
{{
  "elements": [{{"id":"E1","name":"...","kind":"component|module|actor|datastore|external_system|class","role":"...","external":false,
    "evidence":{{"file":"relative/path","symbol":"Name","excerpt":"..."}},
    "support":"observed"}}],
  "relations": [{{"id":"R1","from":"E1","to":"E2","kind":"uses|calls|dataflow|contains|deploys|transition",
    "label":"methodName","order":1,
    "evidence":{{"file":"...","symbol":"...","excerpt":"..."}},
    "support":"observed"}}],
  "groups": [],
  "unanswered": ["RI-6"],
  "notes": []
}}

view_type: {view_type}
viewpoint_id: {viewpoint_id}
granularity: {granularity}
purpose: {purpose}

ANALYSIS PLAN (answer these tasks from the files they name):
{plan}

QUESTIONS this view must answer:
{questions}

required_information:
{required}

DECLARED GAPS (other viewpoints; do not add boxes to cover these):
{gaps}

GROUNDABLE FILE STEMS (evidence only; not a list of boxes to draw):
{allowed}

SCOPED FILE GRAPH (scoped files only; [dir] is the parent directory, not a box):
{graph}

SOURCE FILES:
{files}

{ciao_grounding}
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


def _plan_text(analysis_plan) -> str:
    if analysis_plan is None or not getattr(analysis_plan, "analysis_tasks", None):
        return "(none. Answer the questions from the scoped files.)"
    lines = [
        f"goal: {analysis_plan.analysis_goal}",
        f"viewpoint: {analysis_plan.target_view}",
        f"granularity: {analysis_plan.target_granularity}",
        "constraints: " + ("; ".join(analysis_plan.constraints or []) or "(none)"),
    ]
    for task in analysis_plan.analysis_tasks:
        lines.append(
            f"- {task.id} answers {', '.join(task.addresses) or '?'}: {task.goal}"
        )
        lines.append("  starting points: " + ", ".join(task.starting_points) or "(none)")
        lines.append("  files: " + ", ".join(task.candidate_locations) or "(none)")
        lines.append("  evidence: " + "; ".join(task.expected_evidence) or "(none)")
    return "\n".join(lines)


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
    analysis_plan=None,
) -> ViewModel:
    from task2view.knowledge.loader import load_knowledge

    if not scope.candidate_areas:
        raise PipelineError("scope is empty; cannot extract a view")
    required = "\n".join(f"- {i.id}: {i.need}" for i in view_spec.required_information)
    questions = "\n".join(
        f"- {q.id}: {q.text}" for q in (view_spec.architectural_questions or [])
    ) or "(none; answer required_information only)"
    gaps = ", ".join(view_spec.unanswered_concerns or view_spec.declared_gaps or []) or "(none)"
    prefer: list[str] = []
    scoped_paths = {cand.path for cand in scope.candidate_areas}
    for cand in scope.candidate_areas:
        prefer.extend(graph.path_to_types.get(cand.path, []))
    kb = load_knowledge()
    prompt = prompt_template.format(
        view_type=view_spec.selected_view.view_type,
        viewpoint_id=view_spec.selected_view.viewpoint_id or "",
        grain=kb.grain_prompt(
            view_spec.selected_view.viewpoint_id,
            view_spec.selected_view.view_type,
        ),
        granularity=view_spec.selected_view.granularity,
        purpose=view_spec.selected_view.purpose,
        plan=_plan_text(analysis_plan),
        questions=questions,
        required=required,
        gaps=gaps,
        graph=graph.summary(prefer=prefer, only_paths=scoped_paths),
        allowed=", ".join(dict.fromkeys(prefer)) or "(none in scope)",
        files=_pack_files(repo_root, scope),
        ciao_grounding=ciao_grounding_rules(
            view_spec.selected_view.viewpoint_id,
            view_spec.selected_view.view_type,
        ),
    )
    built: list[ViewModel] = []
    for _ in range(max(1, samples)):
        raw = generate(prompt, model=model)
        if isinstance(raw, dict):
            raw = {k: v for k, v in raw.items() if not str(k).startswith("_")}
        built.append(_model_from_dict(raw, view_spec.request_id, view_spec))
    return merge_samples(built, view_spec.request_id, view_spec)

