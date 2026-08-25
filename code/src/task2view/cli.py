from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from task2view.contracts.models import PipelineError, UserRequest
from task2view.phase4.compile import compile_file, compile_run_dir, parse_formats
from task2view.pipeline import run_pipeline, write_result


def _plugin_names() -> dict[str, list[str]]:
    from task2view.phase3 import SCOPERS
    from task2view.phase4 import ADAPTERS, EXTRACTORS

    return {
        "scopers": sorted(SCOPERS),
        "extractors": sorted(EXTRACTORS),
        "notations": sorted(ADAPTERS),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task2view",
        description="Task2View: two inputs — a code repository and a stakeholder goal.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Clean the repo, then run interpretation through view generation")
    run.add_argument("--code", "--repo", dest="code", required=True, help="Path to the source repository")
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
    run.add_argument("--max-views", type=int, default=1)
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
        help="Phase 5 extractor plug-in: gemini (default), archagent, ciao",
    )
    run.add_argument(
        "--model",
        dest="gemini_model",
        help="Gemini model id (default: GEMINI_MODEL or gemini-2.5-flash)",
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
        "--legacy",
        action="store_true",
        help="Regex Phase 1–2 instead of interpretation/question/viewpoint agents",
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
    return parser


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
    if args.command == "compile":
        try:
            return _run_compile(args)
        except (PipelineError, ValueError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
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
            gemini_model=args.gemini_model,
            samples=args.samples,
            skip_extract=args.skip_extract,
            skip_critic=args.skip_critic,
            legacy=args.legacy,
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
