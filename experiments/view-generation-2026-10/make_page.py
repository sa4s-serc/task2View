"""Build index.html: for each case, its 42010:2022 inputs next to the generated view and README, for human judgement.

    python3 make_page.py
"""

from __future__ import annotations

import collections
import html
import json
import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
FIELDS = ["stakeholder", "perspective", "concern", "aspect", "viewpoint", "model_kind"]
CONDITIONS = {"outputs": "A: agent", "outputs-B": "B: + skill and feedback loop", "outputs-C": "C: + memory",
              "outputs-D": "D: revised skill + separate critic",
              "outputs-E": "E: D + detail level given in the perspective",
              "outputs-F": "F: E + static dependency graph",
              "outputs-G": "G: F + component views from a checked model, tighter critic"}


def esc(s: object) -> str:
    return html.escape(str(s))


def case_html(case: str, c: dict, entities: dict) -> str:
    out = HERE / "outputs" / case
    rows = [f"<tr><th>entity of interest</th><td>{esc(entities[c['entity_of_interest']]['description'])}</td></tr>"]
    for f in FIELDS:
        value = c[f]
        if isinstance(value, dict):  # perspective: description and detail level
            value = f"{value['description']} (detail level: {value['detail_level']})"
        rows.append(f"<tr><th>{f.replace('_', ' ')}</th><td>{esc(value)}</td></tr>")
        if f == "concern":
            items = "".join(f"<li>{esc(d)}</li>" for d in c.get("concern_details", []))
            rows.append(f"<tr><th>concern details</th><td><ul>{items}</ul></td></tr>")
    original = (f"<details><summary>original long request</summary><p>{esc(c['original_request'])}</p></details>"
                if c.get("original_request") else "")
    columns = "".join(condition_html(case, d, label) for d, label in CONDITIONS.items() if (HERE / d / case).exists())
    return f"""<section id="{case}">
<h2>{case}</h2>
<p class="request">“{esc(c['request'])}”</p>{original}
<details open><summary>Inputs (hand-made, used by A to G)</summary><table>{''.join(rows)}</table></details>
<div class="cols">{columns}</div>{h_html(case)}</section>"""


def phase1_html(task: str) -> str:
    """Phase 1 for one task: the agent's pre-filled answers, the stakeholder's confirmed or corrected ones, the
    proposed views."""
    d = HERE / "elicited" / task
    if not (d / "answers.json").exists():
        return ""
    pre, ans, prop = (json.loads((d / f"{n}.json").read_text()) for n in ("prefill", "answers", "proposal"))
    show = lambda v: ("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in v) + "</ul>") if isinstance(v, list) else esc(v)
    rows = []
    for key, label in [("stakeholder", "stakeholder"), ("perspective", "perspective"), ("concerns", "concerns"),
                       ("detail_level", "detail level")]:
        same = pre.get(key) == ans.get(key)
        rows.append(f"<tr><th>{label}</th><td>{show(pre.get(key))}</td><td>{show(ans.get(key))}"
                    f"{'' if same else ' <b class=changed>(corrected)</b>'}</td></tr>")
    asp = lambda a: "<ul>" + "".join(f"<li>{esc(c)}: <b>{esc(', '.join(x))}</b></li>" for c, x in a.items()) + "</ul>"
    same = pre.get("aspects") == ans.get("aspects")
    rows.append(f"<tr><th>aspects per concern</th><td>{asp(pre.get('aspects', {}))}</td><td>"
                f"{asp(ans.get('aspects', {}))}{'' if same else ' <b class=changed>(corrected)</b>'}</td></tr>")
    views = "".join(
        f"<li><b>{esc(v['viewpoint'])}</b> for “{esc(v['concern'])}”: {esc(v.get('reason', ''))}"
        + "".join(f"<br><i>also plausible, not drawn: {esc(a['viewpoint'])}</i> ({esc(a.get('reason', ''))})"
                  for a in v.get("also", [])) + "</li>" for v in prop.get("views", []))
    return f"""<details open><summary>Phase 1 inputs (H): generated from the request, not hand-made</summary>
<table class="p1"><tr><th></th><th>1. agent pre-fill (from the short request)</th>
<th>2. stakeholder's answer (simulated, knows the long request)</th></tr>{''.join(rows)}</table>
<p><b>3. proposed views</b></p><ul>{views}</ul></details>"""


def h_html(task: str) -> str:
    """Condition H: the views Phase 1 proposed for this task, each with its elicited inputs."""
    f = HERE / "inputs-elicited.yaml"
    if not f.exists():
        return ""
    views = {k: v for k, v in yaml.safe_load(f.read_text())["cases"].items()
             if re.sub(r"-\d+$", "", k) == task and (HERE / "outputs-H" / k / "view.png").exists()}
    if not views:
        return ""
    blocks = []
    for k, v in views.items():
        out = HERE / "outputs-H" / k
        details = "".join(f"<li>{esc(d)}</li>" for d in v.get("concern_details", []))
        el = v.get("elicitation", {})
        why = esc("; ".join(r for r in el.get("reasons", []) if r))
        read = lambda n: esc((out / n).read_text().strip().splitlines()[-1]) if (out / n).exists() else "not run"
        alt = "".join(f'<p class="check">also plausible, not drawn: {esc(a["viewpoint"])} ({esc(a.get("reason") or "")})</p>'
                      for a in el.get("alternatives", []))
        readme = esc((out / "README.md").read_text()) if (out / "README.md").exists() else "(none)"
        blocks.append(f"""<div><h3>H view: {esc(v['viewpoint'])} ({esc(v['model_kind'])})</h3>
<a href="outputs-H/{k}/view.png"><img src="outputs-H/{k}/view.png" alt="{k}"></a>
<p class="check">answers: <ul class="check">{details}</ul></p><p class="check">why this viewpoint: {why}</p>{alt}
<p class="check">detail level {esc(v['perspective']['detail_level'])}; readability and notation check: {read('view-check.txt')};
names across this task's views: {read('consistency-check.txt') if len(views) > 1 else 'one view'}</p>{critic_html('outputs-H', k)}
<details><summary>README</summary><pre>{readme}</pre></details>
<p class="links"><a href="outputs-H/{k}/view.puml">view.puml</a> · <a href="outputs-H/{k}/prompt.txt">prompt</a></p></div>""")
    return (f"<h3 class=\"hrow\">H: {len(views)} view(s) from the elicited inputs (Phase 1)</h3>{phase1_html(task)}"
            f"<div class=\"cols\">{''.join(blocks)}</div>")


def measures(out: Path) -> dict | None:
    try:
        d = json.loads((out / "check.json").read_text())
    except (OSError, ValueError):
        return None
    counts = d.get("counts", {})
    issues = len(d.get("issues", []))
    nodes = counts.get("nodes", 0)
    return {"issues": issues, "nodes": nodes, "edges": counts.get("edges", 0),
            "per_node": issues / nodes if nodes else None,
            "kinds": collections.Counter(i["kind"] for i in d.get("issues", []))}


def checks(out: Path) -> str:
    m = measures(out)
    if not m:
        return "layout check: not run"
    per = f", {m['per_node']:.2f} per node" if m["per_node"] is not None else ""
    kinds = ", ".join(f"{k} {n}" for k, n in m["kinds"].most_common())
    return (f"{m['nodes']} nodes, {m['edges']} edges; layout issues {m['issues']}{per}"
            + (f" ({kinds})" if kinds else ""))


def critic_html(d: str, case: str) -> str:
    out = HERE / d / case
    try:
        loop = json.loads((out / "loop.json").read_text())
    except (OSError, ValueError):
        return ""
    rows = []
    for n in (1, 2):
        try:
            cr = json.loads((out / f"critique-{n}.json").read_text())
        except (OSError, ValueError):
            continue
        answered = ", ".join(x.get("answered", "?") for x in cr.get("concern_details", []))
        if "findings" in cr:  # condition G: findings marked blocking or minor, no overall verdict
            sev = [f.get("severity") for f in cr["findings"]]
            rows.append(f"<li>review {n}: {sev.count('blocking')} blocking ({esc(loop.get(f'blocking_{n}'))} checked), "
                        f"{sev.count('minor')} minor; level {esc(cr.get('level'))}; concern details {esc(answered)} "
                        f"(<a href=\"{d}/{case}/critique-{n}.json\">critique</a>)</li>")
            continue
        rows.append(f"<li>review {n}: {esc(cr.get('verdict'))}; level {esc(cr.get('level'))}; "
                    f"concern details {esc(answered)} (<a href=\"{d}/{case}/critique-{n}.json\">critique</a>)</li>")
    first = f' · <a href="{d}/{case}/v1/view.png">first version</a>' if loop.get("revised") else ""
    return f"<p class=\"check\">critic loop: kept {esc(loop.get('kept'))}{first}</p><ul class=\"check\">{''.join(rows)}</ul>"


def condition_html(case: str, d: str, label: str) -> str:
    out = HERE / d / case
    readme = esc((out / "README.md").read_text()) if (out / "README.md").exists() else "(none)"
    view = (f'<a href="{d}/{case}/view.png"><img src="{d}/{case}/view.png" alt="{case} {label}"></a>'
            if (out / "view.png").exists() else "<p>(no image)</p>")
    return f"""<div><h3>{esc(label)}</h3>{view}<p class="check">{esc(checks(out))}</p>{critic_html(d, case)}
<details><summary>README</summary><pre>{readme}</pre></details>
<p class="links"><a href="{d}/{case}/view.puml">view.puml</a> · <a href="{d}/{case}/prompt.txt">prompt</a></p></div>"""


def main() -> None:
    sheet = yaml.safe_load((HERE / "inputs.yaml").read_text())
    cases = sheet["cases"]
    nav = " · ".join(f'<a href="#{k}">{k}</a>' for k in cases)
    body = "\n".join(case_html(k, c, sheet["entities_of_interest"]) for k, c in cases.items())
    (HERE / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>View generation from 42010 inputs</title>
<style>
body{{font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1300px;padding:16px;color:#222;background:#fff}}
h2{{margin-top:2.5em;border-top:1px solid #ddd;padding-top:1em}} .request{{font-style:italic}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px;align-items:start}}
.check{{font-size:13px;color:#555}}
table{{border-collapse:collapse;width:100%}} th,td{{text-align:left;vertical-align:top;padding:4px 6px;border-bottom:1px solid #eee}}
th{{width:9em;color:#555;font-weight:600}} ul{{margin:0;padding-left:1.1em}}
img{{max-width:100%;border:1px solid #ddd}} pre{{white-space:pre-wrap;font-size:13px;background:#f6f6f6;padding:8px}}
.changed{{color:#B91C1C}} .p1 th{{width:auto}} .p1 td{{width:42%}}
.hrow{{margin-top:1.5em;padding-top:.8em;border-top:2px solid #1D4ED8;color:#1D4ED8}}
nav{{position:sticky;top:0;background:#fff;padding:6px 0;border-bottom:1px solid #ddd}}
</style></head><body>
<h1>View generation from 42010:2022 inputs</h1>
<p>Central question: given the entity of interest, stakeholder, perspective, concern, aspect and viewpoint / model kind,
can a view be generated that addresses the concern? The architecture is not given; one agent (Claude Sonnet 5.5)
derives it from the repository and writes one view. Conditions side by side: A the agent alone; B with the uml-view
skill and its render, check and look loop; C as B plus a notes file per repository kept across cases; D with the
revised skill (checked inventory, examples, no self-review) and a separate critic on a different model, one
revision, better version kept; E as D with the detail level given in the stakeholder perspective instead of
chosen by the agent; F as E with a static dependency graph of the repository, which the agent queries to find the
concern's code and against which the drawn relations are checked; G as F with component views built from a checked UML component model (components meet through provided and required interfaces; the PlantUML is generated), no element budget, and a tighter critic whose blocking findings must cite code and which only triggers a revision when a checked blocking finding remains. Layout issues are counted by puml-check, which
B to F also used while working, so they favour those conditions; per node normalises for size. The judgement is
the blind rating.</p>
<h2 id="design-h">The new design (condition H): elicited inputs, several views per task</h2>
<p><img src="docs/architecture-H.png" alt="View generation in two phases, condition H"></p>
<ol>
<li><b>Phase 1, the ISO 42010 inputs.</b> The agent pre-fills five fixed questions from the request (role, purpose,
concerns, detail level, and for each concern what the stakeholder needs to see); each question explains its 42010
term. The stakeholder confirms or corrects them in one round (here a simulated stakeholder that knows only the
request's long text). The agent then proposes the views: one viewpoint per view from six viewpoints whose content
can be recovered from code (use case, module, component, data model, interaction, deployment); every concern is
covered, and every plausible viewpoint becomes a view, so a task may get several views.</li>
<li><b>Phase 2, one run per view</b>, in order within a task: F's generator, checks and critic, plus the reviewer's
rules (one viewpoint per view, use-case system boundary, plain words instead of codes such as "IP5", styling
stereotypes hidden), readability checks on the rendered view (house style, fits a 1600 px screen, one reading
direction, grouping), and the same names for the same code across a task's views. No element budget.</li>
</ol>
<p>H appears below A to G in each case, with the inputs elicited for each view.</p>
<h2 id="pipeline">The previous design (condition F)</h2>
<p><img src="docs/architecture.png" alt="View generation pipeline, condition F"></p>
<ol>
<li><b>Request and repository.</b> The request gives the ISO 42010 inputs: stakeholder, perspective with the detail
level, concern with its details, aspect, viewpoint and model kind.</li>
<li><b>Prepare</b> (no LLM): a fresh copy of the repository without its existing UML models, plus the skills.</li>
<li><b>Static graph</b> (no LLM, tree-sitter): classes and dependencies with file:line, entry points, persisted
entities, deployment files.</li>
<li><b>Generator agent</b> (Sonnet 5.5, uml-view skill): finds the concern's code with the graph and by reading code;
groups it into elements at the given detail level; writes the inventory (elements, relations, evidence, members);
draws PlantUML.</li>
<li><b>Checks</b> (scripts, no LLM): evidence lines exist, diagram matches inventory, element budget for the level,
arrows backed by the graph, layout. The agent fixes what they report and checks again.</li>
<li><b>Critic agent</b> (Opus 5.5, fresh session): are the concern details answered, is the level right, is it
supported by the code, is the UML correct. Its critique goes back to the generator for one revision.</li>
<li><b>Keep the better version</b> by the critic's score: view.png / view.puml, inventory.json, README.md.</li>
</ol>
<p>No memory is kept across cases: every case starts from a fresh copy and a fresh session.</p>
<nav>{nav}</nav>
{body}
</body></html>""", encoding="utf-8")


if __name__ == "__main__":
    main()
