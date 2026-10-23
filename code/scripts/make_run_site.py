"""Make a static website that walks through each run of a goal set, stage by stage: the request, then
every stage's input, what it did (and, for model calls, the prompt and the reply), and its output,
down to the UML view. No model call.

    .venv/bin/python scripts/make_run_site.py --runs ../experiments/simple-requests-2026-10/task2view-simple \
        --out ../experiments/simple-requests-2026-10/site

Open <out>/index.html. Each run's raw files are copied to <out>/<case>/files/ and linked from its page.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
from pathlib import Path

CSS = """
:root{--bg:#fbfaf7;--fg:#1f1f1e;--mut:#5f5e5a;--line:#d8d6cf;--card:#fff;--soft:#f1efe8;--llm:#e6f1fb;--llmfg:#0c447c;
--code:#e1f5ee;--codefg:#085041;--bad:#fcebeb;--badfg:#791f1f;--accent:#185fa5}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1b1b1a;--fg:#ececea;--mut:#a8a69e;--line:#3d3d3a;
--card:#232321;--soft:#2c2c2a;--llm:#10263b;--llmfg:#b5d4f4;--code:#0c3a2c;--codefg:#9fe1cb;--bad:#3a1515;--badfg:#f7c1c1;--accent:#85b7eb}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,Helvetica,Arial,sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}a{color:var(--accent)}h1{font-size:24px;margin:8px 0}
.req{font-size:18px;background:var(--card);border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:8px;padding:12px 16px}
.mut{color:var(--mut)}.step{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:14px 0}
.sh{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.n{background:var(--fg);color:var(--bg);border-radius:50%;width:28px;height:28px;
display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex:none}.sh h2{font-size:18px;margin:0}
.b{font-size:12px;border-radius:4px;padding:2px 8px}.b.llm{background:var(--llm);color:var(--llmfg)}.b.code{background:var(--code);color:var(--codefg)}
.what{margin:6px 0 10px}.io{display:grid;grid-template-columns:90px 1fr;gap:4px 12px;margin:8px 0}.io>b{color:var(--mut);font-weight:600}
table{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0}th,td{border:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
th{background:var(--soft)}.wrap{overflow-x:auto}details{margin:6px 0}summary{cursor:pointer;color:var(--accent)}
pre{background:var(--soft);border-radius:6px;padding:10px;overflow:auto;max-height:420px;font-size:12px;white-space:pre-wrap;word-break:break-word}
.rej td{background:var(--bad);color:var(--badfg)}.img{background:#fff;border:1px solid var(--line);border-radius:8px;padding:8px}
.img img{max-width:100%;display:block}.arrow{text-align:center;color:var(--mut);font-size:20px;line-height:1}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}.cards a{text-decoration:none;color:inherit}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px}.card img{width:100%;max-height:180px;object-fit:contain;background:#fff}
nav{font-size:14px;margin-bottom:6px}.chips span{display:inline-block;background:var(--soft);border-radius:12px;padding:1px 8px;margin:2px;font-size:12px}
"""


def e(x) -> str:
    return html.escape(str(x))


def load(run: Path, name: str, default=None):
    p = run / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def calls(run: Path, prefix: str) -> list[dict]:
    p = run / "model_calls.jsonl"
    if not p.exists():
        return []
    rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [c for c in rows if c["purpose"].startswith(prefix)]


def pre(text, summary: str) -> str:
    return f"<details><summary>{e(summary)}</summary><pre>{e(text)}</pre></details>"


def jpre(obj, summary: str) -> str:
    return pre(json.dumps(obj, indent=2, ensure_ascii=False), summary)


def step(n, title, kind, what, inp, out, body="", files=()) -> str:
    badge = f'<span class="b {"llm" if "model" in kind else "code"}">{e(kind)}</span>'
    links = " · ".join(f'<a href="files/{f}">{f}</a>' for f in files)
    return (f'<section class="step" id="s{n}"><div class="sh"><span class="n">{n}</span><h2>{e(title)}</h2>{badge}</div>'
            f'<p class="what">{what}</p><div class="io"><b>Input</b><div>{inp}</div><b>Output</b><div>{out}</div></div>'
            f'{body}{f"<p class=mut>Raw files: {links}</p>" if links else ""}</section><div class="arrow">▼</div>')


def table(headers, rows, cls=None) -> str:
    head = "".join(f"<th>{e(h)}</th>" for h in headers)
    body = "".join(f'<tr{f" class={cls(r)}" if cls and cls(r) else ""}>' + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
                   for r in rows)
    return f'<div class="wrap"><table><tr>{head}</tr>{body}</table></div>'


def cite(ev: list[dict]) -> str:
    return "<br>".join(f"{e(r['file'].rsplit('/', 1)[-1])}:{e('-'.join(map(str, r.get('lines') or [])))}" for r in ev[:2])


def model_calls_block(cs: list[dict], label: str) -> str:
    if not cs:
        return ""
    out = []
    for i, c in enumerate(cs, 1):
        tag = f"{label} {i}" if len(cs) > 1 else label
        out.append(pre(c["prompt"], f"{tag}: prompt sent to the model ({len(c['prompt']):,} characters)"))
        out.append(jpre(c["reply"], f"{tag}: the model's reply"))
    return "".join(out)


def _model(run: Path) -> str:
    log = (run / "run.log").read_text(encoding="utf-8") if (run / "run.log").exists() else ""
    return next((line.split(": ", 1)[1] for line in log.splitlines() if line.startswith("generator: ")), "")


def page(run: Path, case: str, goals: dict) -> str:
    profile, plan = load(run, "stakeholder_profile.json", {}), load(run, "view_plan.json", {})
    questions, tasks = load(run, "architectural_questions.json", []), load(run, "investigation_plan.json", [])
    aem, card = load(run, "evidence_model.json", {}), load(run, "repository_card.json", {})
    validation, usage = load(run, "validation_report.json", {}), load(run, "usage.json", {})
    vdir = next(iter(sorted(run.glob("V*"))), None)
    view = load(vdir, "view.json", {}) if vdir else {}
    arch = load(vdir, "architecture.json") if vdir else None
    goal = profile.get("goal") or goals.get(case, {}).get("goal", "")
    parts = [f'<nav><a href="../index.html">← all examples</a></nav><h1>{e(case)}</h1>',
             f'<p class="mut">System: {e(card.get("name", ""))} · model: {e(_model(run))} · the model replies are those '
             f'of the original run, replayed</p>']

    # 0 request
    parts.append(f'<section class="step"><div class="sh"><span class="n">0</span><h2>The request (input)</h2></div>'
                 f'<p class="req">{e(goal)}</p></section><div class="arrow">▼</div>')

    # 1 repository card
    sig = "".join(f"<span>{e(s)}</span>" for s in sorted(card.get("signals", {})))
    parts.append(step(1, "Phase 0 · Repository card", "code, no model",
        "Parses the whole repository once with tree-sitter: classes, dependencies, entry points, entities, database "
        "and deployment facts.", "the repository folder",
        f'{len(card.get("files", []))} files · {len(card.get("symbols", {}))} classes · {len(card.get("edges", []))} '
        f'code dependencies · {len(card.get("entry_points", []))} entry points · {len(card.get("entities", []))} entities'
        f'<div class="chips">{sig}</div>',
        pre((run / "repository_card.txt").read_text(encoding="utf-8") if (run / "repository_card.txt").exists() else "",
            "The repository card as the model sees it"), ["repository_card.txt", "repository_card.json"]))

    # 2 read the request
    needs = table(["need", "primary?", "quoted from the request"],
                  [[e(n["need"]), e(n.get("salience", "")), f"“{e(n.get('evidence', ''))}”"] for n in profile.get("needs", [])])
    spec = profile.get("spec", {})
    clar = "".join(f"<li>asked: {e(c['question'])} → <b>{e(c.get('answer') or c['default'])}</b>"
                   f"{'' if c.get('answer') else ' (default used)'}</li>" for c in profile.get("clarifications", []))
    parts.append(step(2, "Phase 1 · Read the request", "model, 1 call",
        "The model reads the request and returns who is asking, what they need (each need must quote the request; "
        "code drops any that doesn't), the target and the level of detail. Code then sets the view spec.",
        "the request + the catalogue of needs and roles",
        f'role <b>{e(profile.get("role") or "—")}</b> ({e(profile.get("role_label", ""))}) · target '
        f'<b>{e(profile.get("target") or "whole system")}</b> · detail <b>{e(profile.get("detail_level", ""))}</b> · '
        f'spec: {e(spec.get("scope"))} scope, {e(spec.get("granularity"))} granularity, {e(spec.get("behaviour"))}'
        + needs + (f"<ul>{clar}</ul>" if clar else ""),
        model_calls_block(calls(run, "phase1"), "Phase 1 call"), ["stakeholder_profile.json"]))

    # 3 choose the view
    pv = plan.get("views", [])
    chosen = (f'<b>{e(pv[0]["viewpoint_id"])}</b> ({e(pv[0]["model_kind"])}) — {e(pv[0].get("rationale", ""))}'
              if pv else "no view")
    unc = ", ".join(plan.get("uncovered_needs", [])) or "none"
    parts.append(step(3, "Phase 3 · Choose the view", "code, no model",
        "Picks the one Views &amp; Beyond viewpoint (drawable as a UML diagram) that best covers the primary needs.",
        "the needs + the repository's signals", f"{chosen}<br>needs not covered: {e(unc)}"
        + ("".join(f"<br><span class=mut>{e(x)}</span>" for x in plan.get("notes", []))), "", ["view_plan.json"]))

    # 4 questions
    parts.append(step(4, "Phase 2 · Questions for the view", "code, no model",
        "Writes the question(s) the view must answer, from the viewpoint's template and the target.",
        "the chosen view + the needs", "<ul>" + "".join(f"<li><b>{e(q['id'])}</b>: {e(q['text'])}</li>" for q in questions) + "</ul>",
        "", ["architectural_questions.json"]))

    # 5 investigation plan
    trows = [[e(t["id"]), e(t["goal"]), "<br>".join(e(s.rsplit(".", 1)[-1]) for s in t["seeds"]["symbols"][:8]),
              e(t.get("budget_steps", ""))] for t in tasks]
    parts.append(step(5, "Phase 4 · Investigation plan", "model, 1 call",
        "The model is shown the repository card and the questions and suggests where in the code to start looking.",
        "the questions + the repository card",
        table(["task", "goal for the evidence agent", "starting classes", "step budget"], trows),
        model_calls_block(calls(run, "phase4"), "Phase 4 call"), ["investigation_plan.json"]))

    # 6 evidence agent
    turns = calls(run, "phase5:")
    trow = []
    for i, c in enumerate(turns, 1):
        r = c["reply"]
        if "final" in r:
            fin = r["final"].get("claims", r["final"]) if isinstance(r["final"], dict) else r["final"]
            trow.append([str(i), "<b>final answer</b>", f"{len(fin)} claims"])
        else:
            args = r.get("args", {})
            what = args.get("paths") or args.get("path") or args.get("id") or args.get("pattern") or args
            trow.append([str(i), e(r.get("tool", "?")), e(", ".join(p.rsplit('/', 1)[-1] for p in what) if isinstance(what, list) else what)])
    parts.append(step(6, "Phase 5 · Evidence agent reads the code", f"model, {len(turns)} turns with tools",
        "An agent with read-only tools (read, search, symbol, neighbours) reads the code and ends with claims, each "
        "citing file, lines and the exact code.", "the task + the repository card + the tools",
        table(["turn", "what the agent did", "on"], trow),
        model_calls_block(turns, "Turn"), ["model_calls.jsonl"]))

    # 7 verification
    claims = list(aem.get("claims", {}).values())
    crow = [[e(c["id"]), e(c["kind"]), e(c.get("name") or f'{c.get("source")} → {c.get("target")}'
             + (f' : {c.get("label")}' if c.get("label") else "")), e("; ".join(c.get("responsibilities", [])[:2])),
             cite(c.get("evidence", [])), e(c.get("support", ""))] for c in claims]
    rrow = [["—", e(r["claim"].get("kind", "")), e(r["claim"].get("name") or f'{r["claim"].get("source")} → {r["claim"].get("target")}'),
             e(r["reason"]), "", "rejected"] for r in aem.get("rejected_claims", [])]
    parts.append(step(7, "Verify every claim against the code", "code, no model",
        "Each citation is checked: the file exists, the lines exist, the quoted code is really there, the symbol "
        "exists. Claims that fail are rejected and never drawn.", f"{len(claims) + len(rrow)} claims from the agent",
        f"{len(claims)} accepted · {len(rrow)} rejected" + table(["id", "kind", "claim", "responsibility / reason", "cited", "support"],
                                                                crow + rrow, cls=lambda r: "rej" if r[-1] == "rejected" else None),
        "", ["evidence_model.json"]))

    # 8 evidence model
    els = list(aem.get("elements", {}).values())
    rels = list(aem.get("relations", {}).values())
    scen = list(aem.get("scenarios", {}).values())
    el_rows = [[e(x["kind"]), e(x["name"]), e(x.get("layer") or ""), e("; ".join(r["text"] for r in x.get("responsibilities", [])[:1]))] for x in els]
    names = {x["id"]: x["name"] for x in els}
    rel_rows = [[e(names.get(r["source"], r["source"])), e(r["kind"]), e(names.get(r["target"], r["target"])), e(r.get("label") or "")] for r in rels]
    steps_html = "".join(f"<li>{e(names.get(s['source'], s['source']))} → {e(names.get(s['target'], s['target']))}: {e(s['message'])}</li>"
                         for sc in scen for s in sc["steps"])
    parts.append(step(8, "Evidence model", "code, no model",
        "The accepted claims and the code facts are merged into one model: elements, relations and ordered scenarios.",
        "accepted claims + repository card",
        f"{len(els)} elements · {len(rels)} relations · {len(scen)} scenario(s)",
        "<details><summary>Elements</summary>" + table(["kind", "name", "layer", "responsibility"], el_rows) + "</details>"
        + "<details><summary>Relations</summary>" + table(["from", "kind", "to", "label"], rel_rows) + "</details>"
        + (f"<details><summary>Scenario steps</summary><ol>{steps_html}</ol></details>" if steps_html else ""),
        ["evidence_model.json"]))

    n = 9
    if arch:  # structural views: abstraction into parts
        prow = [[e(p["name"]), e(p["role"]), e(p.get("description", "")), e(", ".join(m.rsplit(".", 1)[-1] for m in p.get("members", [])[:6])
                 + (" …" if len(p.get("members", [])) > 6 else ""))] for p in arch["parts"]]
        pn = {p["id"]: p["name"] for p in arch["parts"]}
        conn = [[e(pn.get(c["source"], c["source"])), e(c["label"]), e(pn.get(c["target"], c["target"])), e(c.get("protocol", "")),
                 e(c.get("weight", "")), "yes" if c.get("against_layering") else ""] for c in arch["connectors"]]
        parts.append(step(n, "Abstraction · classes into parts", "code + 1 naming call",
            "Classes are grouped by architectural role into parts; arrows are lifted from the code dependencies between "
            "the parts' classes. One model call names and describes the parts; code checks the names.",
            "the evidence model + the code dependencies",
            table(["part", "role", "what it does", "classes"], prow)
            + (table(["from", "arrow", "to", "protocol", "code deps", "against layering"], conn) if conn else "<p class=mut>no arrows (containment only)</p>"),
            model_calls_block(calls(run, "phase5c"), "Naming call"), [f"{vdir.name}/architecture.json"]))
        n += 1

    # draw
    img = f"{vdir.name}/view.png" if vdir and (vdir / "view.png").exists() else None
    src = (vdir / "view.puml").read_text(encoding="utf-8") if vdir and (vdir / "view.puml").exists() else ""
    lim = "".join(f"<li>{e(x)}</li>" for x in view.get("limitations", []) + view.get("gaps", []))
    parts.append(step(n, "Phase 7 · Draw the UML view", "code, no model",
        f"The view is drawn as a UML {e(view.get('model_kind', '').replace('uml-', ''))} diagram in PlantUML, from the "
        + ("parts above." if arch else "evidence model (projection: the most relevant elements, up to the cap)."),
        "the parts / the evidence model", (f'<div class="img"><a href="files/{img}"><img src="files/{img}" alt="the view"></a></div>' if img else "")
        + (f"<p>Limitations noted:</p><ul>{lim}</ul>" if lim else ""),
        pre(src, "PlantUML source"), [f"{vdir.name}/view.puml", f"{vdir.name}/view.json"] if vdir else []))
    n += 1

    # check
    v = next(iter(validation.values()), {})
    find = "".join(f"<li>{e(f.get('message'))}</li>" for f in v.get("faithfulness", []))
    parts.append(step(n, "Phase 8 · Check", "code, no model",
        "Two rules: the diagram compiles, and every mark is backed by verified code.", "the drawn view + the evidence model",
        f'verdict <b>{e(v.get("verdict", "—"))}</b> · compiles: {e(v.get("notation", {}).get("status", "—"))}'
        + (f"<ul>{find}</ul>" if find else " · no faithfulness problems"), "", ["validation_report.json", "traceability.md"]).rsplit('<div class="arrow">', 1)[0])

    rp = usage.get("replayed", {})
    parts.append(f'<p class="mut">Model calls in the original run: {e(rp.get("calls", usage.get("total", {}).get("calls", "")))}; '
                 f'cost ${rp.get("cost_usd", usage.get("total", {}).get("cost_usd", 0)):.2f}. '
                 f'<a href="files/README.md">Run README</a> · <a href="files/run.log">run.log</a></p>')
    return doc(f"{case} · Task2View walkthrough", "".join(parts))


def doc(title: str, body: str) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{e(title)}</title><style>{CSS}</style></head><body><main>{body}</main></body></html>")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--goals", type=Path, help="goal set (for request text when a run lacks it)")
    args = parser.parse_args()
    goals = {}
    if args.goals and args.goals.exists():
        import yaml
        goals = yaml.safe_load(args.goals.read_text())["cases"]
    args.out.mkdir(parents=True, exist_ok=True)
    cards = []
    for run in sorted(p for p in args.runs.iterdir() if (p / "stakeholder_profile.json").exists()):
        case = run.name
        files = args.out / case / "files"
        if files.exists():
            shutil.rmtree(files)
        shutil.copytree(run, files, ignore=shutil.ignore_patterns(".llm-cache"))
        for puml in files.glob("V*/view.puml"):
            if not puml.with_suffix(".png").exists() and shutil.which("plantuml"):
                subprocess.run(["plantuml", "-tpng", str(puml)], check=False, capture_output=True)
        # pages read from the copy, so the images rendered there are found
        (args.out / case / "index.html").write_text(page(files, case, goals), encoding="utf-8")
        prof = load(files, "stakeholder_profile.json", {})
        vdir = next(iter(sorted(files.glob("V*"))), None)
        img = f'<img src="{case}/files/{vdir.name}/view.png" alt="">' if vdir and (vdir / "view.png").exists() else ""
        cards.append(f'<a href="{case}/index.html"><div class="card"><b>{e(case)}</b> · {e(vdir.name[3:] if vdir else "no view")}'
                     f'<p class="mut">{e(prof.get("goal", ""))}</p>{img}</div></a>')
    body = ("<h1>Task2View walkthroughs</h1><p class=mut>One page per request: the request, then every stage in order "
            "(input, what it did, output; for model calls the prompt and the reply), down to the UML view.</p>"
            f'<div class="cards">{"".join(cards)}</div>')
    (args.out / "index.html").write_text(doc("Task2View walkthroughs", body), encoding="utf-8")
    print(f"wrote {args.out / 'index.html'} ({len(cards)} examples)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
