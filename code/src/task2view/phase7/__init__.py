"""Phase 7. One view-generation agent, then a notation adapter writes the diagram text."""

from task2view.phase7 import render as _render  # noqa: F401
from task2view.phase7.compile import compile_diagram, compile_file, compile_run_dir, parse_formats
from task2view.phase7.protocol import ADAPTERS, NotationAdapter, get_adapter, register_adapter

__all__ = [
    "ADAPTERS",
    "NotationAdapter",
    "compile_diagram",
    "compile_file",
    "compile_run_dir",
    "get_adapter",
    "parse_formats",
    "register_adapter",
]
