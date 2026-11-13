"""Collect exported jobs ("Export for sharing" zips) into one folder with an overview page and two tables.

    t2v-collect EXPORT.zip [EXPORT.zip ...] --out results/

Writes results/<job id>/ (each export unpacked), results/index.html (every job: request, confirmed fields,
views, checks, review, feedback, ratings, time and cost), results/jobs.csv and results/ratings.csv.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import zipfile
from datetime import datetime
from pathlib import Path

from .pipeline import JOB_ID, RATING_CRITERIA
from .report import checks, review, takeaway


def unpack(export: Path, out: Path) -> list[Path]:
    """Unpack one export; only the job folders it names are written, nothing outside `out`."""
    jobs = set()
    with zipfile.ZipFile(export) as z:
        for member in z.infolist():
            parts = Path(member.filename).parts
            if not parts or not JOB_ID.fullmatch(parts[0]) or ".." in parts or member.is_dir():
                continue
            target = out.joinpath(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(member))
            jobs.add(out / parts[0])
    return sorted(jobs)


def agent_usage(job: Path) -> dict:
    """Time and estimated cost of every Claude Code call of a job, from the result events in its logs."""
    seconds, cost, calls = 0.0, 0.0, 0
    results = []
    for log in (job / "logs").glob("*.jsonl"):
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict) and event.get("type") == "result":
                results.append(event)
    for call in (job / "calls").glob("*.json"):
        results.append(json.loads(call.read_text()).get("reply") or {})
    for r in results:
        calls += 1
        seconds += (r.get("duration_ms") or 0) / 1000
        cost += r.get("total_cost_usd") or 0
    return {"calls": calls, "agent_minutes": round(seconds / 60, 1), "estimated_cost_usd": round(cost, 2)}


def wall_minutes(job: Path) -> float:
    try:
        times = [datetime.fromisoformat(json.loads(l)["time"])
                 for l in (job / "timeline.jsonl").read_text().splitlines() if l.strip()]
    except (OSError, ValueError, KeyError):
        return 0.0
    return round((max(times) - min(times)).total_seconds() / 60, 1) if times else 0.0


def asked(job: Path) -> bool:
    """True if the stakeholder saw the confirmation page (the agent was unsure of something)."""
    try:
        return any(json.loads(l).get("state") == "confirm" for l in (job / "timeline.jsonl").read_text().splitlines())
    except (OSError, ValueError):
        return False


def page(rows: list[dict]) -> str:
    e = lambda x: html.escape(str(x if x is not None else ""))
    parts = ["<!doctype html><meta charset='utf-8'><title>Task2View results</title><style>",
             "body{font:15px/1.5 Helvetica,Arial,sans-serif;max-width:1100px;margin:auto;padding:16px;color:#1f2937}",
             "section{border-top:2px solid #cbd5e1;margin-top:32px;padding-top:8px}img{max-width:100%;border:1px solid #cbd5e1}",
             "table{border-collapse:collapse;width:100%}td,th{border:1px solid #cbd5e1;padding:4px 8px;text-align:left;",
             "vertical-align:top}th{width:230px;background:#f8fafc}.hint{color:#64748b}</style>",
             f"<h1>Task2View results</h1><p class='hint'>{len(rows)} jobs. Ratings: 1 = poor, 5 = very good.</p>"]
    for row in rows:
        s, job = row["state"], row["dir"]
        a = s.get("answers") or {}
        parts.append(f"<section><h2>{e(s['id'])}: {e(s.get('source', {}).get('name'))}</h2>"
                     f"<p><strong>Request:</strong> {e(s['request'])}</p>"
                     f"<p class='hint'>State {e(s['state'])} · confirmation page shown: {'yes' if row['asked'] else 'no'}"
                     f" · {row['wall_minutes']} min in all · {row['calls']} agent calls, {row['agent_minutes']} agent min,"
                     f" about ${row['estimated_cost_usd']} (estimate by Claude Code)</p>")
        prefill = s.get("prefill") or {}
        if prefill.get("unsure") or prefill.get("extra_questions"):
            parts.append("<p><strong>The agent asked:</strong></p><ul>")
            parts += [f"<li>{e(k)}: {e(q)}</li>" for k, q in (prefill.get("unsure") or {}).items()]
            parts += [f"<li>{e(q['question'])}</li>" for q in prefill.get("extra_questions") or []]
            parts.append("</ul>")
        if a:
            parts.append("<details><summary>Confirmed fields</summary><table>")
            for k in ("entity", "focus", "stakeholder", "perspective", "detail_level"):
                parts.append(f"<tr><th>{e(k)}</th><td>{e(a.get(k))}</td></tr>")
            parts.append(f"<tr><th>concerns</th><td>{'<br>'.join(e(c['text']) + ' <span class=hint>(' + e(', '.join(c['aspects'])) + ')</span>' for c in a.get('concerns', []))}</td></tr>")
            for x in a.get("extra") or []:
                parts.append(f"<tr><th>{e(x['question'])}</th><td>{e(x['answer'])}</td></tr>")
            if a.get("notes"):
                parts.append(f"<tr><th>notes</th><td>{e(a['notes'])}</td></tr>")
            parts.append("</table></details>")
        for r in s.get("records") or []:
            view = job / "out" / r["id"]
            rv, ratings = review(view), (s.get("ratings") or {}).get(r["id"]) or []
            parts.append(f"<h3>{e(r['id'])}: {e(r['model_kind'])} <span class='hint'>{e(r['concern'])}</span></h3>")
            if (view / "view.png").exists():
                parts.append(f"<img src='{e(s['id'])}/out/{e(r['id'])}/view.png' alt='{e(r['id'])}'>")
            parts.append(f"<p>{e(takeaway(view))}</p><p class='hint'>Checks: "
                         + ", ".join(f"{e(c['label'])} {'passed' if c['passed'] else 'issues'}" for c in checks(view))
                         + f" · review: {e(rv.get('verdict'))}, kept {e(rv.get('kept'))}</p>")
            for f in [f for f in s.get("feedback") or [] if f["view"] == r["id"]]:
                parts.append(f"<p><strong>Feedback:</strong> {e(f['text'])}</p>")
            for rating in ratings:
                scores = ", ".join(f"{e(RATING_CRITERIA[k])} {v}" for k, v in rating["scores"].items())
                parts.append(f"<p><strong>Rating</strong> <span class='hint'>{e(rating['time'])}, after "
                             f"{rating['after_feedback_rounds']} feedback rounds</span>: {scores}. {e(rating['comment'])}</p>")
        parts.append("</section>")
    return "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("exports", nargs="+", type=Path, help="exported zip files")
    parser.add_argument("--out", type=Path, default=Path("task2view-results"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for export in args.exports:
        unpack(export, args.out)

    rows = []
    for job in sorted(p for p in args.out.iterdir() if JOB_ID.fullmatch(p.name) and (p / "job.json").exists()):
        state = json.loads((job / "job.json").read_text())
        rows.append({"dir": job, "state": state, "asked": asked(job), "wall_minutes": wall_minutes(job),
                     **agent_usage(job)})

    with (args.out / "jobs.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["job", "repository", "request", "state", "confirmation_shown", "views", "feedback_rounds",
                    "wall_minutes", "agent_calls", "agent_minutes", "estimated_cost_usd"])
        for r in rows:
            s = r["state"]
            w.writerow([s["id"], s.get("source", {}).get("name"), s["request"], s["state"], r["asked"],
                        "; ".join(f"{v['id']} {v['model_kind']}" for v in s.get("records") or []),
                        len(s.get("feedback") or []), r["wall_minutes"], r["calls"], r["agent_minutes"],
                        r["estimated_cost_usd"]])
    with (args.out / "ratings.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["job", "view", "model_kind", "time", "after_feedback_rounds", *RATING_CRITERIA, "comment"])
        for r in rows:
            s = r["state"]
            kinds = {v["id"]: v["model_kind"] for v in s.get("records") or []}
            for view, ratings in (s.get("ratings") or {}).items():
                for x in ratings:
                    w.writerow([s["id"], view, kinds.get(view), x["time"], x["after_feedback_rounds"],
                                *(x["scores"].get(k, "") for k in RATING_CRITERIA), x["comment"]])
    (args.out / "index.html").write_text(page(rows), encoding="utf-8")
    print(f"{len(rows)} jobs in {args.out}/: index.html, jobs.csv, ratings.csv")


if __name__ == "__main__":
    main()
