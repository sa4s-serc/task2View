"""Phase 1: from the stakeholder's request to the ISO/IEC/IEEE 42010:2022 inputs of one or more views.

  1. prefill   the agent fills in every field from the request and the repository summary, says where it is
               unsure, and may add up to MAX_EXTRA_QUESTIONS questions of its own
  2. propose   the agent proposes the fewest views that cover the concerns, one viewpoint per view; other
               viewpoints that would do about as well are noted as alternatives, not drawn
  3. confirm   if the agent was unsure of anything, the stakeholder sees all fields and the proposed views on
               one page and corrects them; after a correction the views are proposed again
  4. records   one 42010 input record per view
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from . import claude, config

QUESTIONS = yaml.safe_load((config.PACKAGE / "data" / "questions.yaml").read_text())["questions"]
VIEWPOINTS = yaml.safe_load((config.PACKAGE / "data" / "viewpoints.yaml").read_text())["viewpoints"]
ASPECTS = QUESTIONS["aspects"]["options"]
NOT_STATED = "not stated"
FIELDS = ("entity", "focus", "stakeholder", "perspective", "detail_level", "concerns")


def _prompt(name: str) -> str:
    return (config.PACKAGE / "prompts" / name).read_text()


def _questions_text() -> str:
    lines = []
    for qid, q in QUESTIONS.items():
        lines.append(f"- {qid} ({q['term']}): {q['explain']} {q['ask']}")
        lines += [f"    {k}: {v}" for k, v in (q.get("options") or {}).items()]
    return "\n".join(lines)


def _text(value) -> str:
    """A pre-filled answer as form text; "not stated" becomes an empty field."""
    value = str(value or "").strip()
    return "" if value.lower() == NOT_STATED else value


def prefill(request: str, summary: str, workdir: Path) -> dict:
    got = claude.ask_json(_prompt("prefill.txt").format(
        max_extra=config.MAX_EXTRA_QUESTIONS, summary=summary, request=request, questions=_questions_text()),
        config.GENERATOR_MODEL, workdir)
    concerns = [c for c in map(_text, got.get("concerns") or []) if c]
    aspects = got.get("aspects") if isinstance(got.get("aspects"), dict) else {}
    unsure = got.get("unsure") if isinstance(got.get("unsure"), dict) else {}
    extra = [q for q in got.get("extra_questions") or [] if isinstance(q, dict) and _text(q.get("question"))]
    return {
        "entity": _text(got.get("entity")),
        "focus": _text(got.get("focus")),
        "stakeholder": _text(got.get("stakeholder")),
        "perspective": _text(got.get("perspective")),
        "detail_level": got.get("detail_level") if got.get("detail_level") in config.DETAIL_LEVELS else "",
        "concerns": [{"text": c, "aspects": [a for a in aspects.get(c) or [] if a in ASPECTS]} for c in concerns],
        "unsure": {k: _text(v) for k, v in unsure.items() if k in FIELDS},
        "extra_questions": [{"question": _text(q["question"]), "why": _text(q.get("why")),
                             "options": [str(o) for o in (q.get("options") or [])][:4]}
                            for q in extra[:config.MAX_EXTRA_QUESTIONS]],
    }


def as_answers(prefilled: dict) -> dict:
    """The agent's own values, in the shape of the stakeholder's answers."""
    return {**{k: prefilled[k] for k in FIELDS}, "extra": [], "notes": ""}


def needs_stakeholder(prefilled: dict) -> bool:
    """True if the agent is unsure of something; otherwise the views are drawn without asking."""
    return bool(prefilled["unsure"] or prefilled["extra_questions"] or missing(as_answers(prefilled)))


def answers_from_form(form, prefilled: dict) -> dict:
    """The stakeholder's answers as submitted. `form` is the posted form (a werkzeug MultiDict)."""
    concerns = []
    for i in sorted({int(k.split("-")[1]) for k in form if k.startswith("concern-") and k.split("-")[1].isdigit()}):
        text = form.get(f"concern-{i}", "").strip()
        if text:
            concerns.append({"text": text, "aspects": [a for a in form.getlist(f"aspects-{i}") if a in ASPECTS]})
    extra = []
    for i, q in enumerate(prefilled["extra_questions"]):
        answer = form.get(f"extra-{i}-text", "").strip() or form.get(f"extra-{i}", "").strip()
        if answer:
            extra.append({"question": q["question"], "answer": answer})
    return {
        "entity": form.get("entity", "").strip(),
        "focus": form.get("focus", "").strip(),
        "stakeholder": form.get("stakeholder", "").strip(),
        "perspective": form.get("perspective", "").strip(),
        "detail_level": form.get("detail_level") if form.get("detail_level") in config.DETAIL_LEVELS else "",
        "concerns": concerns,
        "extra": extra,
        "notes": form.get("notes", "").strip(),
    }


def changed(answers: dict, prefilled: dict) -> bool:
    """True if the stakeholder corrected or added anything; the views are then proposed again."""
    plain = lambda a: {**a, "concerns": [(c["text"], sorted(c["aspects"])) for c in a["concerns"]]}
    return plain(answers) != plain(as_answers(prefilled))


def missing(answers: dict) -> list[str]:
    """What the stakeholder still has to fill in before views can be proposed."""
    need = {"entity": "the system", "focus": "the part of the system to focus on", "stakeholder": "your role",
            "perspective": "what you will use the view for"}
    out = [label for key, label in need.items() if not answers[key]]
    return out + ([] if answers["concerns"] else ["at least one question the view should answer"])


def propose(request: str, answers: dict, workdir: Path) -> list[dict]:
    """The views to draw: one per chosen viewpoint, each with the viewpoints noted as alternatives."""
    stated = {
        "stakeholder": answers["stakeholder"], "perspective": answers["perspective"],
        "concerns": [c["text"] for c in answers["concerns"]],
        "detail_level": answers["detail_level"] or config.DEFAULT_DETAIL_LEVEL,
        "aspects": {c["text"]: c["aspects"] for c in answers["concerns"]},
        "extra": answers["extra"], "notes": answers["notes"],
    }
    listed = "\n".join(f"- {k}: {v['model_kind']}; shows {v['shows']}; frames aspects {', '.join(v['frames'])}"
                       for k, v in VIEWPOINTS.items())
    got = claude.ask_json(_prompt("propose.txt").format(
        entity=answers["entity"], focus=answers["focus"], request=request, answers=json.dumps(stated, indent=2),
        viewpoints=listed),
        config.GENERATOR_MODEL, workdir)
    views: dict[str, dict] = {}
    for v in got.get("views") or []:
        if not isinstance(v, dict) or v.get("viewpoint") not in VIEWPOINTS:
            continue
        w = views.setdefault(v["viewpoint"], {"viewpoint": v["viewpoint"], "concern": str(v.get("concern", "")),
                                              "concern_details": [], "reasons": [], "alternatives": []})
        w["concern_details"] += [d for d in v.get("concern_details") or [] if d not in w["concern_details"]]
        w["reasons"] += [v["reason"]] if v.get("reason") else []
        w["alternatives"] += [a for a in v.get("also") or [] if isinstance(a, dict)
                              and a.get("viewpoint") in VIEWPOINTS and a not in w["alternatives"]]
    if not views:
        raise claude.ClaudeError("No view was proposed for this request")
    return list(views.values())


def records(request: str, answers: dict, views: list[dict]) -> list[dict]:
    """One 42010 input record per view; `id` names the view's folder."""
    out = []
    for i, v in enumerate(views, 1):
        viewpoint = VIEWPOINTS[v["viewpoint"]]
        out.append({
            "id": f"view-{i}",
            "request": request,
            "entity_of_interest": answers["entity"],
            "focus": answers["focus"],
            "stakeholder": answers["stakeholder"],
            "perspective": {"description": answers["perspective"],
                            "detail_level": answers["detail_level"] or config.DEFAULT_DETAIL_LEVEL},
            "concern": v["concern"],
            "concern_details": v["concern_details"],
            "aspect": viewpoint["aspect"],
            "viewpoint": v["viewpoint"],
            "model_kind": viewpoint["model_kind"],
            "clarifications": clarifications(answers),
            "elicitation": {"reasons": v["reasons"], "alternatives": v["alternatives"]},
        })
    return out


def clarifications(answers: dict) -> list[str]:
    """What the stakeholder said beyond the five fixed questions."""
    out = [f"{e['question']} {e['answer']}" for e in answers["extra"]]
    return out + ([answers["notes"]] if answers["notes"] else [])
