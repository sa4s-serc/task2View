"""Build rating.html: per case, the views of every condition in a shuffled order with no condition names, and
rating fields for each. Ratings stay in the browser and download as JSON; blind-key.json maps the shown
numbers back to conditions.

    python3 make_blind.py
"""

from __future__ import annotations

import base64
import html
import json
import random
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CONDITIONS = {"outputs": "A", "outputs-B": "B", "outputs-C": "C", "outputs-D": "D"}
CRITERIA = [("concern", "Answers the concern"), ("level", "Right level of detail for this stakeholder"),
            ("correct", "Correct for the code and correct UML"), ("readable", "Easy to read")]


def esc(s: object) -> str:
    return html.escape(str(s))


def main() -> None:
    sheet = yaml.safe_load((HERE / "inputs.yaml").read_text())
    rng = random.Random(20261031)
    key, sections = {}, []
    for case, c in sheet["cases"].items():
        views = [(cond, HERE / d / case / "view.png") for d, cond in CONDITIONS.items()
                 if (HERE / d / case / "view.png").exists()]
        rng.shuffle(views)
        key[case] = {str(i + 1): cond for i, (cond, _) in enumerate(views)}
        details = "".join(f"<li>{esc(d)}</li>" for d in c.get("concern_details", []))
        cards = []
        for i, (_, png) in enumerate(views, 1):
            img = base64.b64encode(png.read_bytes()).decode()
            fields = "".join(
                f'<label>{esc(label)} <select data-case="{case}" data-view="{i}" data-c="{k}">'
                f'<option value=""></option>' + "".join(f"<option>{n}</option>" for n in range(1, 6)) +
                "</select></label>" for k, label in CRITERIA)
            cards.append(f'<div class="card"><h3>View {i}</h3><img src="data:image/png;base64,{img}" alt="view {i}">'
                         f'<div class="fields">{fields}<textarea data-case="{case}" data-view="{i}" data-c="comment" '
                         f'placeholder="comment"></textarea></div></div>')
        sections.append(f"""<section id="{case}"><h2>{case}</h2><p class="request">“{esc(c['request'])}”</p>
<p>Stakeholder: <b>{esc(c['stakeholder'])}</b> · perspective: {esc(c['perspective']['description'] if isinstance(c['perspective'], dict) else c['perspective'])} · model kind: {esc(c['model_kind'])}</p>
<ul>{details}</ul><div class="cards">{''.join(cards)}</div></section>""")
    (HERE / "blind-key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    nav = " · ".join(f'<a href="#{k}">{k}</a>' for k in sheet["cases"])
    (HERE / "rating.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Blind view rating</title>
<style>
body{{font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1400px;padding:16px;color:#222;background:#fff}}
h2{{margin-top:2.5em;border-top:1px solid #ddd;padding-top:1em}} .request{{font-style:italic}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px;align-items:start}}
.card img{{max-width:100%;border:1px solid #ddd}} .fields label{{display:flex;justify-content:space-between;gap:8px;font-size:14px;margin:4px 0}}
textarea{{width:100%;min-height:3em;box-sizing:border-box}}
nav{{position:sticky;top:0;background:#fff;padding:6px 0;border-bottom:1px solid #ddd}}
</style></head><body>
<h1>Blind rating of generated views</h1>
<p>For each request the views are shown in a random order without saying how they were made. Rate each from 1 (poor)
to 5 (very good). Ratings are kept in this browser; press <b>Download ratings</b> when done and send the file.</p>
<p><button id="dl">Download ratings</button> <span id="n"></span></p>
<nav>{nav}</nav>
{''.join(sections)}
<script>
const K = "blind-ratings-v1";
let r = {{}};
try {{ r = JSON.parse(localStorage.getItem(K) || "{{}}"); }} catch (e) {{}}
const fields = document.querySelectorAll("[data-case]");
const id = el => el.dataset.case + "|" + el.dataset.view + "|" + el.dataset.c;
const count = () => document.getElementById("n").textContent =
  Object.values(r).filter(v => v !== "").length + " answers saved";
fields.forEach(el => {{
  if (r[id(el)] !== undefined) el.value = r[id(el)];
  el.addEventListener("change", () => {{
    r[id(el)] = el.value;
    try {{ localStorage.setItem(K, JSON.stringify(r)); }} catch (e) {{}}
    count();
  }});
}});
count();
document.getElementById("dl").onclick = () => {{
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(r, null, 2)], {{type: "application/json"}}));
  a.download = "ratings.json"; a.click();
}};
</script></body></html>""", encoding="utf-8")


if __name__ == "__main__":
    main()
