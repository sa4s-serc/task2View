"""LLM providers shared by the phase agents and the extractors.

``generate_json(prompt, model=spec)`` dispatches to the adapter named by the
``provider:model`` spec (registry.py). Importing this package registers every
adapter; SDKs are imported only when an adapter is instantiated.
"""

from task2view.llm.registry import default_spec, generate_json, get_client, parse_spec, providers
from task2view.llm import claude, gemini, openai_compat  # noqa: F401  (register adapters)

__all__ = ["default_spec", "generate_json", "get_client", "parse_spec", "providers"]
