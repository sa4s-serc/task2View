"""LLM providers: one adapter per provider, chosen by a ``provider:model`` spec (registry.py).

Importing this package registers every adapter; SDKs are imported only when an adapter is instantiated.
"""

from task2view.llm import claude, gemini, openai_compat  # noqa: F401  (register adapters)
from task2view.llm.registry import get_client, parse_spec, providers

__all__ = ["get_client", "parse_spec", "providers"]
