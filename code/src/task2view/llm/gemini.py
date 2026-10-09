"""Google AI Studio (Gemini) adapter.

Get a key at https://aistudio.google.com/apikey and export GEMINI_API_KEY.
No billing account is required for the free-tier Flash models.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from task2view.contracts.models import PipelineError
from task2view.llm.base import JSON_INSTRUCTION, LLMClient, Usage
from task2view.llm.registry import register_provider

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


@register_provider("gemini", default_model=DEFAULT_MODEL)
class GeminiClient(LLMClient):
    provider = "gemini"

    def complete_text(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        parts = [p for p in (system, JSON_INSTRUCTION if json_mode else None) if p]
        text = "\n\n".join([*parts, prompt]) if parts else prompt
        usage: dict = {}
        out = _generate(self.model, text, json_mime=json_mode, usage_out=usage)
        cached = int(usage.get("cachedContentTokenCount", 0) or 0)
        self.last_usage = Usage(input_tokens=int(usage.get("promptTokenCount", 0) or 0) - cached,
                                output_tokens=int(usage.get("candidatesTokenCount", 0) or 0)
                                + int(usage.get("thoughtsTokenCount", 0) or 0),
                                cache_read_tokens=cached)
        return out


def api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    if not key.strip():
        raise PipelineError(
            "GEMINI_API_KEY is not set. Create a free key at "
            "https://aistudio.google.com/apikey and export GEMINI_API_KEY=..."
        )
    return key.strip()


def _generate(model: str, prompt: str, *, json_mime: bool, usage_out: dict, timeout: int = 180) -> str:
    """One model only, so results always name the model that produced them."""
    key = api_key()
    for use_json_mime in (True, False) if json_mime else (False,):
        try:
            payload = _post(model, prompt, key, timeout, use_json_mime=use_json_mime)
        except urllib.error.HTTPError as exc:
            if exc.code == 400 and use_json_mime:  # model without JSON mode: retry as plain text
                continue
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise PipelineError(f"Gemini request failed ({model}: HTTP {exc.code}) {detail}") from exc
        except urllib.error.URLError as exc:
            raise PipelineError(f"Gemini request failed: {exc}") from exc
        usage_out.update(payload.get("usageMetadata") or {})
        return _first_text(payload)
    raise PipelineError(f"Gemini request failed ({model}): JSON mode rejected")


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
