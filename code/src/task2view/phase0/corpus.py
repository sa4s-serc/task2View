"""Classify every repository file (code, test, build, deploy, config, schema, web, docs, model, binary, other)."""

from __future__ import annotations

import fnmatch
from functools import lru_cache
from importlib import resources
from pathlib import Path

import yaml

from task2view.contracts.card import SourceFile


@lru_cache(maxsize=1)
def corpus_rules() -> dict:
    path = resources.files("task2view.knowledge.data").joinpath("vb", "corpus.yaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _matches(rule: dict, rel: str, name: str, ext: str, dirs: set[str], languages: dict) -> bool:
    if rule.get("language_extensions") and ext in languages:
        return True
    if ext and ext in {e.lower() for e in rule.get("extensions", [])}:
        return True
    lname = name.lower()
    if any(fnmatch.fnmatch(lname, pattern.lower()) for pattern in rule.get("names", [])):
        return True
    if dirs & {p.lower() for p in rule.get("paths", [])}:
        return True
    return not any(k in rule for k in ("extensions", "names", "paths", "language_extensions"))


def classify(rel: str, rules: dict | None = None) -> tuple[str, str | None]:
    rules = rules or corpus_rules()
    path = Path(rel)
    name = path.name
    ext = path.suffix.lower().lstrip(".")
    dirs = {p.lower() for p in path.parts[:-1]}
    languages = rules["languages"]
    language = languages.get(ext)
    for rule in rules["classes"]:
        if _matches(rule, rel, name, ext, dirs, languages):
            cls = rule["class"]
            if cls == "test" and language is None:
                continue  # test-folder data files keep their own class
            return cls, language if cls in {"code", "test", "web"} else None
    return "other", None


def scan(root: Path) -> list[tuple[Path, SourceFile]]:
    rules = corpus_rules()
    skip = {d.lower() for d in rules["skip_directories"]}
    out: list[tuple[Path, SourceFile]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if {p.lower() for p in rel_parts[:-1]} & skip:
            continue
        rel = "/".join(rel_parts)
        cls, language = classify(rel, rules)
        try:
            lines = path.read_bytes().count(b"\n") + 1 if cls not in {"binary", "model"} else 0
        except OSError:
            lines = 0
        out.append((path, SourceFile(path=rel, file_class=cls, language=language, lines=lines)))
    return out
