from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from task2view.contracts.models import PipelineError, UserRequest
from task2view.phase7.compile import compile_file, compile_run_dir, parse_formats
from task2view.pipeline import run_pipeline, write_result


def _plugin_names() -> dict[str, list[str]]:
    from task2view.llm import providers
    from task2view.phase4 import SCOPERS
    from task2view.phase5 import EXTRACTORS
    from task2view.phase7 import ADAPTERS

    return {
        "scopers": sorted(SCOPERS),
        "extractors": sorted(EXTRACTORS),
        "notations": sorted(ADAPTERS),
        "llm_providers": [f"{name}:{model or '<model>'}" for name, model in providers().items()],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task2view",
        description="Task2View: two inputs — a code repository and a stakeholder goal.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the pipeline: goal + repository -> validated architecture views")
    run.add_argument("--code", "--repo", dest="code", required=True, help="Path to the source repository")
    run.add_argument("--engine", choices=["v2", "legacy"], default="v2",
                     help="v2: ADR-006 pipeline (default). legacy: the pre-ADR-006 single-view pipeline")
    run.add_argument("--judge-llm", help="v2: provider:model for the task-fit judge (Phase 8 layer 5); "
                                         "use a different model from --llm. Omit to skip the judge")
    run.add_argument("--notations", help="v2: comma-separated notations to write for every view "
                                         "(default: --diagram-language, else plantuml)")
    run.add_argument("--no-compile-check", action="store_true",
                     help="v2: skip compiling diagram source in Phase 8 layer 1")
    run.add_argument(
        "--goal",
        help="Stakeholder goal statement, e.g. 'As a tester, I need to understand how registration works.'",
    )
    run.add_argument("--stakeholder", help="Role override if the goal does not name one")
    run.add_argument("--task", help="Task text if --goal is omitted; requires --stakeholder")
    run.add_argument("--out", required=True, help="Output directory for artifacts")
    run.add_argument("--request-id")
    run.add_argument(
        "--config",
        help="YAML run profile selecting scoper/extractor/diagram_language (CLI flags override)",
    )
    run.add_argument(
        "--diagram-language",
        default=None,
        help="Notation adapter: plantuml, mermaid, d2, c4plantuml, structurizr, graphviz, nomnoml, excalidraw, bpmn",
    )
    run.add_argument("--max-views", type=int, default=None, help="v2 default 3 (ADR-006); legacy default 1")
    run.add_argument("--scope-token-budget", type=int, default=120_000)
    run.add_argument(
        "--scope-strategy",
        default=None,
        help=(
            "Phase 4 scoper plug-in: composite (default), graph1, locagent, central, "
            "pagerank, layer, grep, lexical, dataflow, full"
        ),
    )
    run.add_argument(
        "--extract-backend",
        default=None,
        help="Phase 5 extractor plug-in: packed (default), archagent, ciao",
    )
    run.add_argument(
        "--llm",
        "--model",
        dest="llm",
        help=(
            "LLM as provider:model, e.g. anthropic:claude-opus-5-5, gemini:gemini-2.5-flash, "
            "openai:<model>, ollama:<model>, vllm:<model>, openrouter:<model> "
            "(default: TASK2VIEW_LLM, else gemini)"
        ),
    )
    run.add_argument(
        "--samples",
        type=int,
        default=1,
        help="Extractor samples for agreement (use 1 on the free tier)",
    )
    run.add_argument(
        "--skip-extract",
        action="store_true",
        help="Stop after scoping (no extractor / diagram)",
    )
    run.add_argument(
        "--skip-critic",
        action="store_true",
        help="Skip the completeness critic (package regrouping still runs)",
    )
    run.add_argument(
        "--extract-workers",
        type=int,
        default=2,
        help="Unused on the default path",
    )
    run.add_argument(
        "--render-formats",
        default="svg,png,jpeg",
        help="Compiled image formats written next to the diagram source (default: svg,png,jpeg)",
    )
    run.add_argument(
        "--skip-render",
        action="store_true",
        help="Write diagram source only; do not compile SVG/PNG/JPEG",
    )
    run.add_argument(
        "--kroki-url",
        help="Kroki base URL (default: KROKI_URL or https://kroki.io)",
    )

    compile_cmd = sub.add_parser(
        "compile",
        help="Compile diagram source to SVG/PNG/JPEG (Kroki, with local fallbacks)",
    )
    compile_cmd.add_argument("--source", help="Path to a .puml / .mmd / .d2 / .dot / ... file")
    compile_cmd.add_argument("--run-dir", help="Existing pipeline output directory")
    compile_cmd.add_argument("--notation", help="Override inferred diagram language")
    compile_cmd.add_argument("--out", help="Directory for images (defaults to the source directory)")
    compile_cmd.add_argument("--formats", default="svg,png,jpeg")
    compile_cmd.add_argument(
        "--all-notations",
        action="store_true",
        help="With --run-dir, also compile every file in notations/",
    )
    compile_cmd.add_argument("--kroki-url")

    plugins = sub.add_parser("plugins", help="List registered scopers, extractors, and notations")
    plugins.set_defaults(command="plugins")

    card_cmd = sub.add_parser("card", help="Phase 0 repository card: typed files, symbols, graph, facts, signals")
    card_cmd.set_defaults(command="card")
    card_cmd.add_argument("--code", required=True, help="Local repository path")
    card_cmd.add_argument("--json", action="store_true", help="Print the full card as JSON instead of the summary")
    card_cmd.add_argument("--out", help="Also write the full card JSON here")

    select = sub.add_parser(
        "select-views",
        help="ADR-006 Phase 1 + covering selection: which V&B views a goal needs (no repository read)",
    )
    select.set_defaults(command="select-views")
    select.add_argument("--goal", required=True)
    select.add_argument("--llm", help="provider:model for Phase 1 (default: TASK2VIEW_LLM, else gemini)")
    select.add_argument(
        "--signals",
        default="",
        help="Comma-separated repository signals (e.g. rest-api,layered,persisted-data); "
        "the Phase 0 card will compute these",
    )
    select.add_argument("--code", help="Repository path: add the signals the Phase 0 card computes")
    select.add_argument("--max-views", type=int, default=3)
    return parser


def _run_v2(args: argparse.Namespace) -> int:
    from task2view.agents.run_v2 import run_v2
    from task2view.agents.write_v2 import write_run_v2

    if not args.goal:
        print("error: --goal is required", file=sys.stderr)
        return 2
    notations = [n.strip() for n in (args.notations or args.diagram_language or "plantuml").split(",") if n.strip()]
    result = run_v2(args.goal, args.code, llm=args.llm, judge_llm=args.judge_llm, max_views=args.max_views or 3,
                    languages=notations, compile_enabled=not args.no_compile_check)
    out = write_run_v2(result, args.out)
    images = []
    if not args.skip_render:
        for view in result.viewset.views:
            for render in result.renders.get(view.id, []):
                name = f"view.{render.language}.{render.extension}" if render.language != "plantuml" else f"view.{render.extension}"
                try:
                    report = compile_file(out / view.id / name, out / view.id, notation=render.language,
                                          formats=parse_formats(args.render_formats), kroki_url=args.kroki_url)
                    images += report.get("files", []) if isinstance(report, dict) else []
                except (PipelineError, ValueError, OSError) as exc:
                    images.append(f"{view.id}/{name}: not rendered ({exc})")
    summary = {
        "out": str(out.resolve()),
        "generator": result.llm,
        "judge": result.judge_llm,
        "views": [{"id": v.id, "viewpoint": v.viewpoint_id, "decision": result.decisions[v.id].decision,
                   "verdict": result.validation[v.id].verdict, "elements": len(v.content_elements())}
                  for v in result.viewset.views],
        "uncovered_needs": result.viewset.uncovered_needs,
        "declared_gaps": result.viewset.declared_gaps,
        "claims": len(result.aem.claims),
        "rejected_claims": len(result.aem.rejected_claims),
        "usage": result.usage.get("total", {}),
        "images": images,
    }
    print(json.dumps(summary, indent=2))
    return 0


def _run_card(args: argparse.Namespace) -> int:
    from task2view.phase0.card import build_card, render_card

    card = build_card(args.code)
    payload = card.model_dump_json(indent=2)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    print(payload if args.json else render_card(card))
    return 0


def _run_select_views(args: argparse.Namespace) -> int:
    from task2view.agents.runtime import AgentRuntime
    from task2view.knowledge.catalog import load_catalog
    from task2view.phase1.needs import extract_needs
    from task2view.phase3.selection import RepoFacts, select_views

    catalog = load_catalog()
    signals = {s.strip() for s in args.signals.split(",") if s.strip()}
    if args.code:
        from task2view.phase0.card import build_card

        signals |= set(build_card(args.code).signals)
    unknown = sorted(signals - set(catalog.signals))
    if unknown:
        print(f"error: unknown signals {unknown}; known: {sorted(catalog.signals)}", file=sys.stderr)
        return 2
    profile = extract_needs(args.goal, AgentRuntime(model=args.llm), catalog=catalog)
    plan = select_views(profile.selection_input(), catalog, RepoFacts(signals=signals), max_views=args.max_views)
    print(json.dumps({"profile": profile.model_dump(), "plan": plan.model_dump()}, indent=2))
    return 0


def _run_compile(args: argparse.Namespace) -> int:
    formats = parse_formats(args.formats)
    if args.run_dir:
        report = compile_run_dir(
            Path(args.run_dir),
            formats=formats,
            all_notations=args.all_notations,
            kroki_url=args.kroki_url,
        )
        print(json.dumps(report, indent=2))
        return 0 if report.get("status") != "fail" else 2
    if not args.source:
        print("error: compile needs --source or --run-dir", file=sys.stderr)
        return 2
    src = Path(args.source)
    out = Path(args.out) if args.out else src.parent
    report = compile_file(
        src,
        out,
        notation=args.notation,
        formats=formats,
        kroki_url=args.kroki_url,
    )
    print(json.dumps(report, indent=2))
    return 0 if report.get("status") != "fail" else 2


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "plugins":
        print(json.dumps(_plugin_names(), indent=2))
        return 0
    if args.command == "card":
        try:
            return _run_card(args)
        except PipelineError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if args.command == "select-views":
        try:
            return _run_select_views(args)
        except PipelineError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if args.command == "compile":
        try:
            return _run_compile(args)
        except (PipelineError, ValueError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if args.engine == "v2":
        try:
            return _run_v2(args)
        except (PipelineError, ValueError, KeyError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if args.max_views is None:
        args.max_views = 1
    try:
        raw = UserRequest(
            code=args.code,
            goal=args.goal,
            stakeholder=args.stakeholder,
            task=args.task,
            request_id=args.request_id,
            diagram_language=args.diagram_language,
            max_views=args.max_views,
            scope_token_budget=args.scope_token_budget,
            scope_strategy=args.scope_strategy,
            extract_backend=args.extract_backend,
            llm=args.llm,
            samples=args.samples,
            skip_extract=args.skip_extract,
            skip_critic=args.skip_critic,
            extract_workers=args.extract_workers,
            config=args.config,
        )
        if raw.config:
            from task2view.config import apply_pipeline_config, load_pipeline_config

            raw = apply_pipeline_config(raw, load_pipeline_config(raw.config))
            if args.scope_strategy:
                raw.scope_strategy = args.scope_strategy
            if args.extract_backend:
                raw.extract_backend = args.extract_backend
            if args.diagram_language:
                raw.diagram_language = args.diagram_language
        result = run_pipeline(raw)
        out = Path(args.out)
        render_formats = [] if args.skip_render or args.skip_extract else parse_formats(args.render_formats)
        write_result(out, result, render_formats=render_formats or None, kroki_url=args.kroki_url)
    except (PipelineError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    summary = {
        "request_id": result.request.request_id,
        "code": result.request.repository.location,
        "files_kept": result.corpus.counts["kept"],
        "files_dropped": result.corpus.counts["dropped"],
        "languages": result.corpus.counts.get("languages", {}),
        "role": result.request.stakeholder.role,
        "viewpoint": result.spec.selected_view.viewpoint_id,
        "view_type": result.spec.selected_view.view_type,
        "diagram_language": result.spec.selected_view.diagram_language,
        "scope_strategy": result.scope.scope_strategy,
        "extract_backend": raw.extract_backend,
        "scope_files": len(result.scope.candidate_areas),
        "graph_nodes": result.scope.graph.get("nodes"),
        "out": str(out.resolve()),
    }
    if result.view_model is not None:
        summary["elements"] = len(result.view_model.elements)
        summary["relations"] = len(result.view_model.relations)
    if result.validation is not None:
        summary["verdict"] = result.validation.verdict
    report_path = out / "render_report.json"
    if report_path.exists():
        summary["render"] = json.loads(report_path.read_text()).get("status")
        summary["images"] = json.loads(report_path.read_text()).get("files")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
