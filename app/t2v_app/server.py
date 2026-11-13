"""The web pages. The server listens on this machine only (127.0.0.1)."""

from __future__ import annotations

import secrets
import shutil

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, send_from_directory, url_for
from markdown_it import MarkdownIt

from . import config, phase1, pipeline, report
from .repo import GITHUB_URL, SUPPORTED_LANGUAGES

REQUIRED = {"claude": "Claude Code, installed and logged in", "git": "git, to fetch GitHub repositories",
            "plantuml": "PlantUML, to render the views", "dot": "Graphviz, used by PlantUML",
            "java": "Java, used by PlantUML"}
STAGES = {"drawing": "Draw from the code", "reviewing": "Independent review", "revising": "Revise if needed",
          "reviewing the revision": "Review the revision", "checking": "Check against the code"}
SERVED = {".png": "image/png"}      # every other result file is sent as plain text, never as a web page

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_BYTES
TOKEN = secrets.token_urlsafe(32)   # sent with every form of this tool, so that other web pages cannot post to it
markdown = MarkdownIt("commonmark", {"html": False}).enable("table")


@app.before_request
def only_this_machine():
    if request.host not in (f"127.0.0.1:{config.T2V_PORT}", f"localhost:{config.T2V_PORT}"):
        abort(403)
    if request.method == "POST" and not secrets.compare_digest(request.form.get("token", ""), TOKEN):
        abort(403)


@app.after_request
def headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; style-src 'self'; " \
                                                  "script-src 'self'; connect-src 'self'; form-action 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.context_processor
def common():
    return {"token": TOKEN}


def job_or_404(job_id: str) -> pipeline.Job:
    try:
        job = pipeline.Job(job_id)
        job.read()
        return job
    except KeyError:
        abort(404)


def home_page(error: str = "", status: int = 200):
    missing = [what for tool, what in REQUIRED.items() if not shutil.which(tool)]
    return render_template("home.html", jobs=pipeline.all_jobs(), missing=missing, error=error,
                           form=request.form, languages=sorted(SUPPORTED_LANGUAGES)), status


@app.get("/")
def home():
    return home_page()


@app.post("/jobs")
def new_job():
    text = request.form.get("request", "").strip()
    url = request.form.get("repo_url", "").strip()
    upload = request.files.get("repo_zip")
    has_zip = bool(upload and upload.filename)
    if not text:
        return home_page("Write what you need the view for.", 400)
    if bool(url) == has_zip:
        return home_page("Give the repository either as a zip file or as a GitHub URL.", 400)
    if url and not GITHUB_URL.fullmatch(url):
        return home_page("The URL must look like https://github.com/<owner>/<repository> (public).", 400)
    source = {"kind": "github", "url": url, "name": url.rstrip("/").removesuffix(".git").split("/")[-1]} if url \
        else {"kind": "zip", "name": upload.filename.rsplit("/", 1)[-1][:100]}
    job = pipeline.create(text, source)
    if has_zip:
        upload.save(job.upload)
    pipeline.start(job, "prepare")
    return redirect(url_for("job_page", job_id=job.id))


@app.get("/jobs/<job_id>")
def job_page(job_id: str, error: str = "", answers: dict | None = None):
    job = job_or_404(job_id)
    state = job.read()
    progress = state.get("progress") or {}
    views = []
    for record in state.get("records") or state.get("proposed") or []:
        view = {"record": record, "inputs": report.inputs_rows(record), "step": progress.get(record["id"], "waiting")}
        if view["step"] == "done":
            folder = job.out / record["id"]
            readme = folder / "README.md"
            view.update(
                checks=report.checks(folder), review=report.review(folder),
                takeaway=markdown.renderInline(report.takeaway(folder)),
                readme=markdown.render(readme.read_text(encoding="utf-8", errors="replace")) if readme.exists()
                else "",
                files=sorted(p.name for p in folder.iterdir() if p.is_file()))
        views.append(view)
    return render_template("job.html", job=state, views=views, error=error, stages=STAGES,
                           answers=answers or state.get("answers") or state.get("prefill"),
                           questions=phase1.QUESTIONS, aspects=phase1.ASPECTS, viewpoints=phase1.VIEWPOINTS,
                           levels=phase1.QUESTIONS["detail_level"]["options"])


@app.get("/jobs/<job_id>/version")
def job_version(job_id: str):
    return jsonify(version=job_or_404(job_id).read()["version"])


@app.post("/jobs/<job_id>/answers")
def answer(job_id: str):
    job = job_or_404(job_id)
    state = job.read()
    if state["state"] != "confirm":
        return redirect(url_for("job_page", job_id=job_id))
    answers = phase1.answers_from_form(request.form, state["prefill"])
    todo = phase1.missing(answers)
    if todo:
        return job_page(job_id, error="Please fill in: " + ", ".join(todo) + ".", answers=answers), 400
    pipeline.confirm(job, answers)
    return redirect(url_for("job_page", job_id=job_id))


@app.post("/jobs/<job_id>/retry")
def retry(job_id: str):
    pipeline.retry(job_or_404(job_id))
    return redirect(url_for("job_page", job_id=job_id))


@app.get("/jobs/<job_id>/files/<path:name>")
def job_file(job_id: str, name: str):
    kind = SERVED.get("." + name.rsplit(".", 1)[-1].lower(), "text/plain; charset=utf-8")
    return send_from_directory(job_or_404(job_id).out, name, mimetype=kind)


@app.get("/jobs/<job_id>/download")
def download(job_id: str):
    job = job_or_404(job_id)
    if job.read()["state"] != "done":
        abort(404)
    return send_file(report.zip_bytes(job.out), mimetype="application/zip", as_attachment=True,
                     download_name=f"architecture-views-{job.id}.zip")


def main() -> None:
    config.T2V_HOME.mkdir(parents=True, exist_ok=True)
    pipeline.mark_interrupted()
    print(f"Task2View is running at http://127.0.0.1:{config.T2V_PORT}  (jobs are kept in {config.T2V_HOME})")
    app.run(host="127.0.0.1", port=config.T2V_PORT, threaded=True)


if __name__ == "__main__":
    main()
