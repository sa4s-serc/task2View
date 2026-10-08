"""Gemini client shared by the phase agents and the extractor."""

from task2view.llm.gemini import DEFAULT_MODEL, generate_json

__all__ = ["DEFAULT_MODEL", "generate_json"]
