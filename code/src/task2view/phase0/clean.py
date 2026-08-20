"""Phase 0 — keep only source files. Deterministic; no model call."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from task2view.contracts.models import CleanedCorpus, CleanedFile, DroppedFile, PipelineError
from task2view.contracts.validate import validate_artifact
from task2view.knowledge.loader import KnowledgeBase, load_knowledge

SKIP_DIR_ALWAYS = {".git", ".hg", ".svn"}


def _is_binary(path: Path, sample: int = 8192) -> bool:
    try:
        chunk = path.read_bytes()[:sample]
    except OSError:
        return True
    return b"\0" in chunk


def clean_repository(
    repo: str | Path,
    *,
    request_id: str,
    knowledge: KnowledgeBase | None = None,
) -> CleanedCorpus:
    knowledge = knowledge or load_knowledge()
    root = Path(repo).expanduser().resolve()
    if not root.is_dir():
        raise PipelineError(f"Repository path is not a directory: {root}")

    rules = knowledge.corpus_rules
    source_ext = {str(k).lower().lstrip("."): str(v) for k, v in rules["source_extensions"].items()}
    skip_ext = {str(e).lower().lstrip(".") for e in rules.get("skip_extensions", [])}
    skip_dirs = {str(d).lower() for d in rules.get("skip_directories", [])} | SKIP_DIR_ALWAYS
    max_bytes = int(rules.get("max_file_bytes", 1_048_576))

    kept: list[CleanedFile] = []
    dropped: list[DroppedFile] = []

    for path in root.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(root).as_posix()
        parts_l = {p.lower() for p in path.relative_to(root).parts[:-1]}
        if parts_l & skip_dirs:
            dropped.append(DroppedFile(path=rel, reason="skip_directory"))
            continue
        ext = path.suffix.lower().lstrip(".")
        if not ext:
            dropped.append(DroppedFile(path=rel, reason="no_extension"))
            continue
        if ext in skip_ext:
            dropped.append(DroppedFile(path=rel, reason="non_code_extension"))
            continue
        if ext not in source_ext:
            dropped.append(DroppedFile(path=rel, reason="unknown_extension"))
            continue
        try:
            size = path.stat().st_size
        except OSError:
            dropped.append(DroppedFile(path=rel, reason="unreadable"))
            continue
        if size > max_bytes:
            dropped.append(DroppedFile(path=rel, reason="too_large"))
            continue
        if size == 0:
            dropped.append(DroppedFile(path=rel, reason="empty"))
            continue
        if _is_binary(path):
            dropped.append(DroppedFile(path=rel, reason="binary"))
            continue
        kept.append(
            CleanedFile(
                path=rel,
                language=source_ext[ext],
                bytes=size,
                reason="source_extension",
            )
        )

    kept.sort(key=lambda item: item.path)
    dropped.sort(key=lambda item: item.path)
    languages = dict(Counter(item.language for item in kept))
    corpus = CleanedCorpus(
        request_id=request_id,
        repository=str(root),
        kept=kept,
        dropped=dropped,
        counts={"kept": len(kept), "dropped": len(dropped), "languages": languages},
    )
    if not kept:
        raise PipelineError(f"No source files found under {root}")
    validate_artifact("cleaned_corpus", corpus)
    return corpus
