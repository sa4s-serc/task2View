"""Phase 1: from a stakeholder's request to the ISO/IEC/IEEE 42010:2022 inputs of one or more views.

For each case of inputs.yaml:
  1. prefill   the agent pre-fills the fixed questions (elicit/questions.yaml) from the request
  2. answers   the stakeholder confirms or corrects them in one round: a person at the terminal (--ask), or a
               simulated stakeholder (default) that knows only the case's long request text (original_request
               when there is one, else request); the agent sees only `request`
  3. proposal  the agent proposes the fewest views that cover the concerns: one viewpoint per view from
               elicit/viewpoints.yaml, and any other viewpoint that answers a concern about as well ("also")
  4. record    a task gets several views (case, case-2, ...) only when its concerns need different viewpoints;
               the "also" viewpoints are not drawn, only noted as alternatives. Views with the same viewpoint
               are merged. One 42010 input record per view in inputs-elicited.yaml

    cd Task2View/code && .venv/bin/python ../experiments/view-generation-2026-10/elicit.py [--only CASE] [--ask] [--redo]

The hand-made inputs.yaml stays the reference: the hand-made viewpoint is printed next to the proposed ones.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
EL = HERE / "elicit"
OUT = HERE / "elicited"
WORK = Path.home() / "t2v-subjects" / "view-generation" / "elicit"
AGENT_MODEL = "claude-sonnet-5-5"
STAKEHOLDER_MODEL = "claude-opus-5-5"


def ask_model(prompt: str, model: str) -> dict:
    """One headless call with no tools; returns the JSON object in the reply."""
    WORK.mkdir(parents=True, exist_ok=True)
    run = subprocess.run(["claude", "-p", prompt, "--model", model, "--output-format", "json"], cwd=WORK,
                         capture_output=True, text=True, env={**__import__("os").environ,
                                                              "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"})
    text = json.loads(run.stdout).get("result", "")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON in reply: {text[:300]}")
    return json.loads(m.group(0))


def questions_text(qs: list[dict]) -> str:
    lines = []
    for q in qs:
        lines.append(f"- {q['id']} ({q['term']}): {q['explain']} {q['ask']}")
        for k, v in (q.get("options") or {}).items():
            lines.append(f"    {k}: {v}")
    return "\n".join(lines)


def ask_person(qs: list[dict], prefill: dict) -> dict:
    """The fixed questions at the terminal, each with its explanation and the pre-filled answer."""
    answers = dict(prefill)
    for q in qs:
        print(f"\n{q['term']}: {q['explain']}\n{q['ask']}")
        for k, v in (q.get("options") or {}).items():
            print(f"  {k}: {v}")
        if q["id"] == "aspects":
            answers["aspects"] = {}
            for concern in answers["concerns"]:
                pre = ", ".join(prefill.get("aspects", {}).get(concern, [])) or "not stated"
                got = input(f"  '{concern}' [{pre}]: ").strip()
                answers["aspects"][concern] = [a.strip() for a in got.split(",")] if got else pre.split(", ")
            continue
        pre = prefill.get(q["id"])
        shown = "; ".join(pre) if isinstance(pre, list) else pre
        got = input(f"[{shown}] (Enter keeps it{'; separate items with ;' if q['answer'] == 'list' else ''}): ").strip()
        if got:
            answers[q["id"]] = [s.strip() for s in got.split(";")] if q["answer"] == "list" else got
    return answers


def expand(views: list[dict]) -> list[dict]:
    """One view per chosen viewpoint (same viewpoint merged); "also" viewpoints are kept only as alternatives."""
    out: dict[str, dict] = {}
    for v in views:
        w = out.setdefault(v["viewpoint"], {"viewpoint": v["viewpoint"], "concern": v["concern"],
                                            "concern_details": [], "reasons": [], "alternatives": []})
        w["concern_details"] += [d for d in v["concern_details"] if d not in w["concern_details"]]
        w["reasons"].append(v.get("reason"))
        w["alternatives"] += [a for a in v.get("also", []) if a not in w["alternatives"]]
    return list(out.values())


def records(case: str, c: dict, answers: dict, views: list[dict], vps: dict) -> dict:
    """One 42010 input record per proposed view, in the shape of inputs.yaml."""
    out = {}
    for i, v in enumerate(views, 1):
        vp = vps[v["viewpoint"]]
        out[case if i == 1 else f"{case}-{i}"] = {
            "request": c["request"],
            "entity_of_interest": c["entity_of_interest"],
            "stakeholder": answers.get("stakeholder"),
            "perspective": {"description": answers.get("perspective"),
                            "detail_level": answers.get("detail_level") if answers.get("detail_level") in
                            ("overview", "balanced", "detailed") else "balanced"},
            "concern": v["concern"],
            "concern_details": v["concern_details"],
            "aspect": vp["aspect"],
            "viewpoint": v["viewpoint"],
            "model_kind": vp["model_kind"],
            "elicitation": {"reasons": v["reasons"], "alternatives": v["alternatives"], "views_for_request": len(views),
                            "detail_level_stated": answers.get("detail_level") in ("overview", "balanced", "detailed")},
        }
    return out



def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only")
    ap.add_argument("--ask", action="store_true", help="ask a person at the terminal instead of the simulated one")
    ap.add_argument("--redo", action="store_true", help="redo the model calls even if their results exist")
    args = ap.parse_args()
    sheet = yaml.safe_load((HERE / "inputs.yaml").read_text())
    qs = yaml.safe_load((EL / "questions.yaml").read_text())["questions"]
    vps = yaml.safe_load((EL / "viewpoints.yaml").read_text())["viewpoints"]
    vp_text = "\n".join(f"- {k}: {v['model_kind']}; shows {v['shows']}; frames aspects {', '.join(v['frames'])}"
                        for k, v in vps.items())
    elicited = {}
    for case, c in sheet["cases"].items():
        if args.only and case != args.only:
            continue
        d = OUT / case
        d.mkdir(parents=True, exist_ok=True)
        entity = sheet["entities_of_interest"][c["entity_of_interest"]]["description"]

        def step(name: str, make):
            f = d / f"{name}.json"
            if f.exists() and not args.redo:
                return json.loads(f.read_text())
            got = make()
            f.write_text(json.dumps(got, indent=2), encoding="utf-8")
            return got

        prefill = step("prefill", lambda: ask_model((EL / "prefill.txt").read_text().format(
            entity=entity, request=c["request"], questions=questions_text(qs)), AGENT_MODEL))
        answers = step("answers", lambda: ask_person(qs, prefill) if args.ask else ask_model(
            (EL / "stakeholder.txt").read_text().format(
                entity=entity, knowledge=c.get("original_request") or c["request"], questions=questions_text(qs),
                prefill=json.dumps(prefill, indent=2)), STAKEHOLDER_MODEL))
        proposal = step("proposal", lambda: ask_model((EL / "propose.txt").read_text().format(
            entity=entity, request=c["request"], answers=json.dumps(answers, indent=2), viewpoints=vp_text),
            AGENT_MODEL))
        for v in proposal["views"]:
            v["also"] = [a for a in v.get("also", []) if a.get("viewpoint") in vps]
        views = expand([v for v in proposal["views"] if v.get("viewpoint") in vps])
        elicited.update(records(case, c, answers, views, vps))
        print(f"{case}: " + " + ".join(v["viewpoint"] + "".join(f" (or {a['viewpoint']})" for a in v["alternatives"])
                                       for v in views)
              + f"   hand-made: {c['viewpoint']}", flush=True)
    target = HERE / "inputs-elicited.yaml"
    old = yaml.safe_load(target.read_text()) if target.exists() and args.only else {}
    cases = {**(old or {}).get("cases", {}), **elicited}
    target.write_text("# Written by elicit.py (Phase 1); do not edit by hand.\n"
                      + yaml.safe_dump({"entities_of_interest": sheet["entities_of_interest"], "cases": cases},
                                       sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
