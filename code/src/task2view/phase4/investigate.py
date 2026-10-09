"""Phase 4 — investigation plan: what to look for, where to start (ADR-006 D2; design 02 §4).

One task per (view, subject), or per (view, need) when the view has no subjects.
Starting points are suggested deterministically from the repository card
(symbol and method names, entry points, graph neighbours), each with its origin.
The planning agent may pick different starting points, but only ones that exist
in the card. Starting points are not a boundary: Phase 5 agents can read any
file of the task's evidence classes.
"""

from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache
from importlib import resources

import yaml

from task2view.agents.runtime import AgentRuntime
from task2view.contracts.models import PipelineError
from task2view.contracts.aem import InvestigationTask, Question, Seeds
from task2view.contracts.card import RepositoryCard
from task2view.knowledge.catalog import Catalog
from task2view.phase3.selection import ViewPlan
from task2view.prompts import load_prompt

_STOP = {"the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "with", "by", "from", "as", "is", "are", "be",
         "this", "that", "these", "those", "it", "its", "which", "what", "how", "when", "where", "who", "their", "them",
         "they", "such", "system", "functionality", "feature", "data", "main", "new", "other", "each", "all", "any"}


@lru_cache(maxsize=1)
def pipeline_config() -> dict:
    path = resources.files("task2view.knowledge.data").joinpath("vb", "pipeline.yaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def tokens(text: str) -> set[str]:
    """Lower-case words from free text or identifiers (camelCase and snake_case split), plurals normalised."""
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", text)
    out = set()
    for w in words:
        w = w.lower()
        if len(w) < 3 or w in _STOP:
            continue
        if w.endswith("ies") and len(w) > 4:
            w = w[:-3] + "y"
        elif w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            w = w[:-1]
        out.add(w)
    return out


def related(a: str, b: str) -> bool:
    """Same word up to inflection: equal, or a shared prefix of >= 3 letters covering all but 2 of the shorter word."""
    if a == b:
        return True
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n >= 3 and n >= min(len(a), len(b)) - 2


def overlap(want: set[str], have: set[str]) -> int:
    return sum(1 for w in want if any(related(w, h) for h in have))


def suggest_seeds(card: RepositoryCard, about: str, *, limit: int, neighbours: int) -> list[tuple[str, str]]:
    """(symbol id, origin) suggestions ranked by identifier overlap with the subject; no file-path matching."""
    want = tokens(about)
    if not want:
        return []
    scores: Counter = Counter()
    origin: dict[str, str] = {}
    for sid, s in card.symbols.items():
        if s.is_test or s.kind == "module" and s.language == "java":
            continue
        name_hits = overlap(want, tokens(s.name))
        method_hits = overlap(want, set().union(*(tokens(m.name) for m in s.methods))) if s.methods else 0
        score = 2 * name_hits + method_hits
        if score:
            scores[sid] = score
            origin[sid] = "symbol-name" if name_hits else "method-name"
    for e in card.entry_points:
        if overlap(want, tokens(e.detail)) and e.symbol in card.symbols:
            scores[e.symbol] += 2
            origin.setdefault(e.symbol, f"entry-point:{e.kind}")
    ranked = [sid for sid, _ in scores.most_common(limit)]
    out = [(sid, origin[sid]) for sid in ranked]
    graph_out: dict[str, Counter] = {}
    for e in card.edges:
        if e.source in ranked[:3] and e.kind in {"calls", "field", "instantiates"}:
            graph_out.setdefault(e.source, Counter())[e.target] += 1
    extra = Counter()
    for counts in graph_out.values():
        extra.update(counts)
    for sid, _ in extra.most_common():
        if len([o for o in out if o[1] == "graph-neighbour"]) >= neighbours:
            break
        if sid not in ranked and not card.symbols[sid].is_test:
            out.append((sid, "graph-neighbour"))
    return out


def _plan_reply(runtime: AgentRuntime, prompt: str, purpose: str) -> dict:
    """Seed choice is optional: on a failed or malformed reply the code's own suggestions stand."""
    try:
        return runtime.complete_json(prompt, purpose=purpose)
    except PipelineError:
        return {}


def _strings(value) -> list[str]:
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def plan_investigation(
    plan: ViewPlan,
    questions: list[Question],
    card: RepositoryCard,
    catalog: Catalog,
    *,
    target: str = "",
    runtime: AgentRuntime | None = None,
    card_text: str = "",
) -> list[InvestigationTask]:
    cfg = pipeline_config()["investigation"]
    known_paths = {f.path for f in card.files} | {f.path.rsplit("/", 1)[0] for f in card.files if "/" in f.path}
    tasks: list[InvestigationTask] = []
    for view_questions in _by_view(questions):
        vid, vp = view_questions[0].view_id, catalog.viewpoint(view_questions[0].viewpoint_id)
        detail = next(v.detail_level for v in plan.views if v.viewpoint_id == vp.id)
        groups = _group(view_questions, cfg["max_tasks_per_view"])
        for group in groups:
            first = group[0]
            about = " ".join(filter(None, [first.subject, target, catalog.needs[first.need].description]))
            suggestions = suggest_seeds(card, " ".join(filter(None, [first.subject, target])) or about,
                                        limit=cfg["seed_symbols_per_task"], neighbours=cfg["neighbour_suggestions"])
            seeds = Seeds(symbols=[s for s, _ in suggestions], classes=list(vp.evidence_classes))
            goal = f"Collect evidence for: {'; '.join(q.text for q in group)}"
            suggested_by = sorted({o for _, o in suggestions}) or ["none"]
            if runtime is not None:
                raw = _plan_reply(runtime, load_prompt("phase4_investigate").render(
                    card=card_text, viewpoint=f"{vp.name} ({vp.vb_ref})",
                    elements=", ".join(vp.element_kinds), relations=", ".join(vp.relation_kinds),
                    questions="\n".join(f"- {q.id}: {q.text}" for q in group),
                    suggestions="\n".join(f"- {s} ({o})" for s, o in suggestions) or "- none",
                    limit=cfg["seed_symbols_per_task"],
                ), f"phase4:{vid}:task{len(tasks) + 1}")
                picked = [s for s in _strings(raw.get("symbols")) if s in card.symbols]
                paths = [p for p in _strings(raw.get("paths")) if p in known_paths]
                if picked or paths:
                    seeds = Seeds(symbols=picked[: cfg["seed_symbols_per_task"]], paths=paths, classes=seeds.classes)
                    suggested_by = sorted(set(suggested_by) | {"planning-agent"})
                goal = str(raw.get("goal") or goal)
            tasks.append(InvestigationTask(
                id=f"IT{len(tasks) + 1}", view_id=vid, viewpoint_id=vp.id,
                question_ids=[q.id for q in group], need=first.need, subject=first.subject, goal=goal,
                seeds=seeds, expect_elements=list(vp.element_kinds), expect_relations=list(vp.relation_kinds),
                budget_steps=int(cfg["budget_steps"][detail]), suggested_by=suggested_by,
            ))
    return tasks


def _by_view(questions: list[Question]) -> list[list[Question]]:
    out: dict[str, list[Question]] = {}
    for q in questions:
        out.setdefault(q.view_id, []).append(q)
    return list(out.values())


def _group(questions: list[Question], cap: int) -> list[list[Question]]:
    """One group per subject (or per need without subject); merge the overflow into the last group."""
    groups: dict[str, list[Question]] = {}
    for q in questions:
        groups.setdefault(q.subject or f"need:{q.need}", []).append(q)
    ordered = list(groups.values())
    if len(ordered) > cap:
        ordered = ordered[: cap - 1] + [[q for g in ordered[cap - 1:] for q in g]]
    return ordered
