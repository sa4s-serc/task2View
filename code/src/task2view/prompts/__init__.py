"""Prompt templates for the model calls of the ADR-006 pipeline.

Each prompt is a Markdown file in this folder:

    ---                      front matter for humans (purpose, inputs, output, how it is checked);
    id: phase1_interpret     never sent to the model
    ...
    ---
    # Task2View — Phase 1: ...    the prompt body, sent to the model
    ... {{placeholder}} ...

Placeholders are ``{{name}}``. Single braces are left alone, so JSON examples in a
prompt read exactly as the model will see them. Rendering fails if a placeholder
is missing or unknown, so a prompt and its caller cannot drift apart silently.
See README.md in this folder for the shared vocabulary.
"""

from __future__ import annotations

import re
from functools import lru_cache
from importlib import resources

import yaml

_PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


class Prompt:
    def __init__(self, prompt_id: str, meta: dict, body: str):
        self.id = prompt_id
        self.meta = meta
        self.body = body

    @property
    def placeholders(self) -> set[str]:
        return set(_PLACEHOLDER.findall(self.body))

    def render(self, **values: str) -> str:
        missing = self.placeholders - set(values)
        unknown = set(values) - self.placeholders
        if missing or unknown:
            raise KeyError(f"prompt {self.id}: missing {sorted(missing)}, unknown {sorted(unknown)}")
        return _PLACEHOLDER.sub(lambda m: str(values[m.group(1)]), self.body)


@lru_cache(maxsize=None)
def load_prompt(prompt_id: str) -> Prompt:
    text = resources.files("task2view.prompts").joinpath(f"{prompt_id}.md").read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"prompt {prompt_id}: missing front matter")
    _, front, body = text.split("---\n", 2)
    meta = yaml.safe_load(front) or {}
    if meta.get("id") != prompt_id:
        raise ValueError(f"prompt {prompt_id}: front matter id is {meta.get('id')!r}")
    return Prompt(prompt_id, meta, body.strip() + "\n")


def prompt_ids() -> list[str]:
    root = resources.files("task2view.prompts")
    return sorted(p.name[:-3] for p in root.iterdir() if p.name.endswith(".md") and p.name != "README.md")
