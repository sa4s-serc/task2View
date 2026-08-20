"""Google AI Studio (Gemini) client for the student free tier.

Get a key at https://aistudio.google.com/apikey and export GEMINI_API_KEY.
No billing account is required for the free-tier Flash models.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from task2view.contracts.models import PipelineError

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
FALLBACK_MODELS = [
    DEFAULT_MODEL,
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]


def api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    if not key.strip():
        raise PipelineError(
            "GEMINI_API_KEY is not set. Create a free key at "
            "https://aistudio.google.com/apikey and export GEMINI_API_KEY=..."
        )
    return key.strip()


def generate_json(prompt: str, *, model: str | None = None, timeout: int = 180) -> dict:
    text = generate_text(prompt, model=model, timeout=timeout, json_mime=True)
    parsed = _parse_json(text)
    return parsed


def generate_text(
    prompt: str,
    *,
    model: str | None = None,
    timeout: int = 180,
    json_mime: bool = False,
) -> str:
    key = api_key()
    tried: list[str] = []
    models: list[str] = [model] if model else []
    for candidate in FALLBACK_MODELS:
        if candidate and candidate not in models:
            models.append(candidate)
    last_error = "no model attempted"
    mime_order = (True, False) if json_mime else (False,)
    for name in models:
        tried.append(name)
        for use_json_mime in mime_order:
            try:
                payload = _post(name, prompt, key, timeout, use_json_mime=use_json_mime)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                last_error = f"{name}: HTTP {exc.code} {detail}"
                if exc.code in {404, 400} and use_json_mime:
                    continue
                if exc.code in {404, 400}:
                    break
                raise PipelineError(f"Gemini request failed ({name}: HTTP {exc.code})") from exc
            except urllib.error.URLError as exc:
                raise PipelineError(f"Gemini request failed: {exc}") from exc
            return _first_text(payload)
    raise PipelineError(
        f"Gemini models failed ({', '.join(tried)}). Last error: {last_error}"
    )


def _post(name: str, prompt: str, key: str, timeout: int, *, use_json_mime: bool) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent"
    config: dict = {"temperature": 0.2}
    if use_json_mime:
        config["responseMimeType"] = "application/json"
    body = json.dumps(
        {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": config,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": key,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _first_text(payload: dict) -> str:
    cands = payload.get("candidates") or []
    if not cands:
        raise PipelineError(f"Gemini returned no candidates: {payload}")
    parts = (((cands[0] or {}).get("content") or {}).get("parts")) or []
    return "".join(p.get("text", "") for p in parts)


def _parse_json(text: str) -> dict:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[: -3]
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < 0:
        raise PipelineError("Gemini did not return JSON")
    return json.loads(raw[start : end + 1])
