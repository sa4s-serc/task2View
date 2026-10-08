"""Token budget helper. tiktoken is optional; char/4 is the fallback."""

from __future__ import annotations

from pathlib import Path


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


def file_tokens(repo_root: str | Path, relative: str) -> int:
    path = Path(repo_root) / relative
    try:
        return estimate_tokens(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return 0
