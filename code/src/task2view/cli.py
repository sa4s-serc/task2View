"""task2view command line: run the pipeline, or inspect one stage of it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from task2view.contracts.models import PipelineError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task2view",
                                     description="Stakeholder goal + repository -> validated architecture views.")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the pipeline and write the run package")
    run.add_argument("--code", required=True, help="Repository path")
    run.add_argument("--goal", required=True, help="Stakeholder goal, verbatim")
    run.add_argument("--out", required=True, help="Output directory")
    run.add_argument("--llm", help="provider:model for every phase (default: TASK2VIEW_LLM, else gemini)")
    run.add_argument("--interactive", action="store_true",
                     help="Ask the request's clarification questions (scope, granularity, behaviour) in the terminal")
    run.add_argument("--notations", default="plantuml", help="Comma-separated notations to write for every view")
    run.add_argument("--max-views", type=int, default=3)
    run.add_argument("--evidence", choices=["agent", "retrieval"], default="agent",
                     help="Phase 5: tool-loop agents, or one call over retrieved seed code (baseline)")
    run.add_argument("--no-compile-check", action="store_true", help="Skip compiling diagrams in Phase 8 layer 1")
    run.add_argument("--images", default="", help="Also render images, e.g. svg,png (local compilers; see compile)")
    run.add_argument("--kroki-url", help="Allow rendering through this Kroki server when no local compiler exists")

    card = sub.add_parser("card", help="Phase 0 repository card")
    card.add_argument("--code", required=True)
    card.add_argument("--json", action="store_true", help="Print the full card as JSON")

    select = sub.add_parser("select-views", help="Phase 1 + viewpoint selection for a goal (no evidence collection)")
    select.add_argument("--goal", required=True)
    select.add_argument("--code", help="Repository: add the signals the Phase 0 card computes")
    select.add_argument("--signals", default="", help="Extra comma-separated repository signals")
    select.add_argument("--llm")
    select.add_argument("--max-views", type=int, default=3)

    sub.add_parser("plugins", help="List notations and LLM providers")

    compile_cmd = sub.add_parser("compile", help="Render the diagram sources of a run directory to images")
    compile_cmd.add_argument("--run-dir", required=True)
    compile_cmd.add_argument("--formats", default="svg,png")
    compile_cmd.add_argument("--kroki-url", help="Allow rendering through this Kroki server when no local compiler exists")
    return parser


def _run(args) -> dict:
    from task2view.agents.run_v2 import run_v2
    from task2view.agents.write_v2 import write_run_v2
    from task2view.phase7.compile import compile_run_dir, parse_formats

    notations = [n.strip() for n in args.notations.split(",") if n.strip()]
    result = run_v2(args.goal, args.code, llm=args.llm, max_views=args.max_views, ask=_ask if args.interactive else None,
                    languages=notations, compile_enabled=not args.no_compile_check, evidence_mode=args.evidence)
    out = write_run_v2(result, args.out)
    images = compile_run_dir(out, formats=parse_formats(args.images), kroki_url=args.kroki_url) if args.images else None
    return {
        "out": str(out.resolve()),
        "generator": result.llm,
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


def _ask(question: str, options, default: str) -> str:
    answer = input(f"{question} [{'/'.join(options)}] (default: {default}): ").strip().lower()
    return answer or default


def _select(args) -> dict:
    from task2view.agents.runtime import AgentRuntime
    from task2view.knowledge.catalog import load_catalog
    from task2view.phase1.needs import extract_needs
    from task2view.phase3.selection import RepoFacts, select_views

    catalog = load_catalog()
    signals = {s.strip() for s in args.signals.split(",") if s.strip()}
    unknown = sorted(signals - set(catalog.signals))
    if unknown:
        raise PipelineError(f"unknown signals {unknown}; known: {sorted(catalog.signals)}")
    if args.code:
        from task2view.phase0.card import build_card

        signals |= set(build_card(args.code).signals)
    profile = extract_needs(args.goal, AgentRuntime(model=args.llm), catalog=catalog)
    plan = select_views(profile.selection_input(), catalog, RepoFacts(signals=signals), max_views=args.max_views)
    return {"profile": profile.model_dump(), "plan": plan.model_dump()}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "run":
            print(json.dumps(_run(args), indent=2))
        elif args.command == "card":
            from task2view.phase0.card import build_card, render_card

            card = build_card(args.code)
            print(card.model_dump_json(indent=2) if args.json else render_card(card))
        elif args.command == "select-views":
            print(json.dumps(_select(args), indent=2))
        elif args.command == "plugins":
            from task2view.llm import providers
            from task2view.phase7.notations import renderers

            print(json.dumps({"notations": sorted(renderers()),
                              "llm_providers": [f"{n}:{m or '<model>'}" for n, m in providers().items()]}, indent=2))
        elif args.command == "compile":
            from task2view.phase7.compile import compile_run_dir, parse_formats

            report = compile_run_dir(Path(args.run_dir), formats=parse_formats(args.formats), kroki_url=args.kroki_url)
            print(json.dumps(report, indent=2))
            return 0 if report["status"] != "fail" else 2
    except (PipelineError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
