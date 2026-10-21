"""Diagram renderers for View format v2 (ADR-008: PlantUML UML only). Every module in this package is imported, which registers its renderer."""

import importlib
import pkgutil

from task2view.phase7.notations.base import MODEL_KINDS, NATIVE, get_renderer, renderers

for _module in pkgutil.iter_modules(__path__):
    if _module.name != "base":
        importlib.import_module(f"{__name__}.{_module.name}")

__all__ = ["MODEL_KINDS", "NATIVE", "get_renderer", "renderers"]
