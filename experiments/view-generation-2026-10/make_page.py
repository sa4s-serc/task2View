"""Build index.html: for each case, its 42010:2022 inputs next to the generated view and README, for human judgement.

    python3 make_page.py
"""

from __future__ import annotations

import collections
import html
import json
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
<details open><summary>Inputs</summary><table>{''.join(rows)}</table></details>
<div class="cols">{columns}</div></section>"""


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
concern's code and against which the drawn relations are checked. Layout issues are counted by puml-check, which
B to F also used while working, so they favour those conditions; per node normalises for size. The judgement is
the blind rating.</p>
<h2 id="pipeline">The current design (condition F)</h2>
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
