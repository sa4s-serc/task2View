"""Phase 5. Per-task evidence extraction, merged into one evidence model."""

from task2view.phase5 import extractors as _extractors  # noqa: F401
from task2view.phase5.extractors import EXTRACTORS, Extractor, get_extractor, register_extractor

__all__ = ["EXTRACTORS", "Extractor", "get_extractor", "register_extractor"]
