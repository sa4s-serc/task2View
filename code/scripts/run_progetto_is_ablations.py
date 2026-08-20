"""Ablation grid for the three Progetto-IS developer goals.

Interprets each goal once (agents 1–3), then runs every scoper × extractor
and emits every registered notation from the resulting view model.
Resumable: a cell with view_model.json is skipped.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from task2view.agents.orchestrate import _normalized, _view_spec
from task2view.agents.phase1_interpret import interpret_stakeholder_task
from task2view.agents.phase2_questions import derive_questions
from task2view.agents.phase3_viewpoint import plan_viewpoints
from task2view.agents.runtime import AgentRuntime
from task2view.contracts.models import (
    CleanedCorpus,
    NormalizedRequest,
    PipelineError,
    UserRequest,
    ViewSpecification,
)
from task2view.knowledge.loader import load_knowledge
from task2view.phase0.clean import clean_repository
from task2view.phase1.intake import new_request_id
from task2view.phase3 import SCOPERS, get_scoper
from task2view.phase3.graph import build_graph
from task2view.phase4 import ADAPTERS, EXTRACTORS, get_adapter, get_extractor
from task2view.phase4.gemini import generate_json
from task2view.phase4.validate import validate_view, write_diagram
from task2view.pipeline import DIAGRAM_EXT, PipelineResult, write_json, write_result

REPO = (
    ROOT.parents[1]
    / "data_points"
    / "Progetto-IS-main-English"
)

GOALS = [
    (
        "G1-short",
        "I am a software developer. I need to modify the seat booking functionality "
        "and understand the main system components involved and how they interact.",
    ),
    (
        "G2-rules",
        "I am a software developer. I need to modify the seat booking functionality "
        "to introduce new booking rules. Before changing the code, I need to understand "
        "the main components involved in this functionality, their responsibilities, "
        "and how they interact with each other. I also want to identify which parts of "
        "the system may be affected by the modification.",
    ),
    (
        "G3-detailed",
        "I am a software developer. I need to modify the seat booking functionality "
        "to introduce new booking rules. Before making changes to the code, I need to "
        "understand the high-level architecture supporting this functionality. I want "
        "to identify the main components involved in the booking process, their "
        "responsibilities, and the interactions and dependencies among them. In "
        "particular, I need to understand which components are responsible for handling "
        "booking requests, checking seat availability, applying booking rules, managing "
        "and storing reservations, and interacting with external services such as the "
        "notification service. This understanding will help me identify which parts of "
        "the system need to be modified and which other components may be affected by "
        "the changes.",
    ),
]

SCOPER_ORDER = [
    "composite",
    "graph1",
    "locagent",
    "pagerank",
    "central",
    "layer",
    "dataflow",
    "grep",
    "lexical",
    "full",
]
EXTRACTOR_ORDER = ["gemini", "archagent", "ciao"]


def _retrying_generate(prompt: str, *, model=None):
    last: Exception | None = None
    for attempt in range(10):
        try:
            return generate_json(prompt, model=model)
        except PipelineError as exc:
            last = exc
            text = str(exc)
            retryable = any(tok in text for tok in ("HTTP 429", "HTTP 503", "HTTP 500", "RESOURCE_EXHAUSTED"))
            if not retryable:
                raise
            wait = min(90, 15 * (2 ** attempt))
            print(f"  rate-limited ({exc}); sleeping {wait}s", flush=True)
            time.sleep(wait)
    raise last or PipelineError("Gemini retries exhausted")


def _dump(model) -> dict:
    return model.model_dump(mode="json", by_alias=True)


def load_prepared(shared: Path) -> PipelineResult:
    corpus = CleanedCorpus.model_validate_json((shared / "cleaned_corpus.json").read_text())
    request = NormalizedRequest.model_validate_json((shared / "normalized_request.json").read_text())
    spec = ViewSpecification.model_validate_json((shared / "view_specification.json").read_text())
    graph = build_graph(request.repository.location, corpus)
    extras = {}
    for name in (
        "stakeholder_task_profile.json",
        "architectural_questions.json",
        "viewpoint_plan.json",
    ):
        path = shared / name
        if path.exists():
            extras[name] = json.loads(path.read_text())
    return PipelineResult(
        corpus=corpus,
        request=request,
        spec=spec,
        graph=graph,
        scope=get_scoper("composite").scope(
            spec,
            request.repository.location,
            request.preferences.scope_token_budget,
            corpus=corpus,
            graph=graph,
        ),
        extras=extras,
    )


def prepare_goal(goal_id: str, goal: str, out_root: Path) -> PipelineResult:
    shared = out_root / goal_id / "_shared"
    if (shared / "viewpoint_plan.json").exists() and (shared / "view_specification.json").exists():
        print("  reusing cached agents 1–3", flush=True)
        return load_prepared(shared)
    raw = UserRequest(code=str(REPO), goal=goal, request_id=goal_id, skip_extract=True)
    knowledge = load_knowledge()
    raw.request_id = raw.request_id or new_request_id()
    runtime = AgentRuntime(generate=_retrying_generate, model=raw.gemini_model)
    corpus = clean_repository(raw.code or "", request_id=raw.request_id)
    profile = interpret_stakeholder_task(raw.goal or "", runtime, knowledge=knowledge)
    request = _normalized(raw, profile, knowledge, corpus)
    questions = derive_questions(profile, runtime, knowledge=knowledge)
    viewpoint_plan = plan_viewpoints(
        profile,
        questions,
        runtime,
        knowledge=knowledge,
        max_views=raw.max_views,
        preferred_language=raw.diagram_language,
    )
    active = next((v for v in viewpoint_plan.views if not v.deferred), None)
    if active is None:
        raise PipelineError("no active view in the viewpoint plan")
    spec = _view_spec(request, profile, questions, active, knowledge)
    repo = request.repository.location
    graph = build_graph(repo, corpus)
    extras = {
        "stakeholder_task_profile.json": profile.model_dump(mode="json"),
        "architectural_questions.json": questions.model_dump(mode="json"),
        "viewpoint_plan.json": viewpoint_plan.model_dump(mode="json"),
    }
    result = PipelineResult(
        corpus=corpus,
        request=request,
        spec=spec,
        graph=graph,
        scope=get_scoper("composite").scope(
            spec, repo, request.preferences.scope_token_budget, corpus=corpus, graph=graph
        ),
        extras=extras,
    )
    write_result(shared, result)
    write_json(shared / "goal.json", {"id": goal_id, "goal": goal})
    return result


def emit_all_notations(cell: Path, result: PipelineResult) -> dict[str, str]:
    assert result.view_model is not None
    notations_dir = cell / "notations"
    notations_dir.mkdir(parents=True, exist_ok=True)
    syntax: dict[str, str] = {}
    for name in sorted(ADAPTERS):
        adapter = get_adapter(name)
        source = adapter.emit(result.view_model)
        ext = DIAGRAM_EXT.get(name, "txt")
        write_diagram(notations_dir / f"{name}.{ext}", source)
        _, report = validate_view(
            result.view_model,
            result.spec,
            result.scope,
            result.graph,
            source,
            name,
        )
        syntax[name] = report.syntax.get("status", "unknown")
    return syntax


def run_cell(prepared: PipelineResult, scoper_name: str, extractor_name: str, cell: Path) -> dict:
    if (cell / "view_model.json").exists():
        return {"status": "skipped", "reason": "already complete"}
    repo = prepared.request.repository.location
    started = time.time()
    try:
        scope = get_scoper(scoper_name).scope(
            prepared.spec,
            repo,
            prepared.request.preferences.scope_token_budget,
            corpus=prepared.corpus,
            graph=prepared.graph,
        )
        if not scope.candidate_areas:
            raise PipelineError(f"scope strategy {scoper_name!r} selected no files")
        extractor = get_extractor(extractor_name)
        view_model = extractor.extract(
            prepared.spec,
            scope,
            prepared.graph,
            repo,
            generate=_retrying_generate,
        )
        notation = prepared.spec.selected_view.diagram_language
        adapter = get_adapter(notation)
        source = adapter.emit(view_model)
        cleaned, report = validate_view(
            view_model, prepared.spec, scope, prepared.graph, source, notation
        )
        result = PipelineResult(
            corpus=prepared.corpus,
            request=prepared.request,
            spec=prepared.spec,
            graph=prepared.graph,
            scope=scope,
            view_model=cleaned,
            diagram_source=adapter.emit(cleaned),
            validation=report,
            extras=prepared.extras,
        )
        write_result(cell, result)
        notation_syntax = emit_all_notations(cell, result)
        row = {
            "status": "ok",
            "seconds": round(time.time() - started, 1),
            "scope_files": len(scope.candidate_areas),
            "elements": len(cleaned.elements),
            "relations": len(cleaned.relations),
            "unanswered": list(cleaned.unanswered or []),
            "verdict": report.verdict,
            "viewpoint": prepared.spec.selected_view.viewpoint_id,
            "view_type": prepared.spec.selected_view.view_type,
            "notation_syntax": notation_syntax,
            "element_names": [e.name for e in cleaned.elements],
        }
        write_json(cell / "ablation_cell.json", row)
        return row
    except Exception as exc:
        row = {
            "status": "error",
            "seconds": round(time.time() - started, 1),
            "error": str(exc),
            "trace": traceback.format_exc()[-2000:],
        }
        write_json(cell / "ablation_cell.json", row)
        return row


def main() -> int:
    if not REPO.is_dir():
        print(f"error: repo not found: {REPO}", file=sys.stderr)
        return 2
    out_root = ROOT / "runs" / "ablations-progetto-is"
    out_root.mkdir(parents=True, exist_ok=True)
    scopers = [s for s in SCOPER_ORDER if s in SCOPERS]
    extractors = [e for e in EXTRACTOR_ORDER if e in EXTRACTORS]
    print(
        f"repo={REPO}\n"
        f"scopers={scopers}\n"
        f"extractors={extractors}\n"
        f"notations={sorted(ADAPTERS)}\n"
        f"cells={len(GOALS) * len(scopers) * len(extractors)}",
        flush=True,
    )
    summary: list[dict] = []
    log_path = out_root / "summary.jsonl"
    for goal_id, goal in GOALS:
        print(f"\n=== {goal_id}: agents 1–3 ===", flush=True)
        prepared = prepare_goal(goal_id, goal, out_root)
        print(
            f"  viewpoint={prepared.spec.selected_view.viewpoint_id} "
            f"view={prepared.spec.selected_view.view_type} "
            f"lang={prepared.spec.selected_view.diagram_language}",
            flush=True,
        )
        for scoper_name in scopers:
            for extractor_name in extractors:
                cell_id = f"{scoper_name}-{extractor_name}"
                cell = out_root / goal_id / cell_id
                cell.mkdir(parents=True, exist_ok=True)
                print(f"  {goal_id}/{cell_id} ...", flush=True)
                row = run_cell(prepared, scoper_name, extractor_name, cell)
                row.update(
                    {
                        "goal_id": goal_id,
                        "scoper": scoper_name,
                        "extractor": extractor_name,
                        "cell": str(cell),
                    }
                )
                summary.append(row)
                with log_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row) + "\n")
                print(f"    -> {row.get('status')} elements={row.get('elements')} verdict={row.get('verdict')}", flush=True)
                if row.get("status") != "skipped":
                    time.sleep(2)
    write_json(out_root / "summary.json", {"runs": summary, "repo": str(REPO)})
    ok = sum(1 for r in summary if r.get("status") == "ok")
    skipped = sum(1 for r in summary if r.get("status") == "skipped")
    err = sum(1 for r in summary if r.get("status") == "error")
    print(f"\nDone. ok={ok} skipped={skipped} error={err} out={out_root}", flush=True)
    return 0 if err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
