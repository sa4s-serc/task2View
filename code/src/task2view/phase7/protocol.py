"""Phase 7 notation adapter. Each adapter turns a view model into diagram text."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from task2view.contracts.models import ViewModel


@runtime_checkable
class NotationAdapter(Protocol):
    id: str
    supports: set[str]
    formats: set[str]

    def emit(self, view_model: ViewModel) -> str:
        ...


ADAPTERS: dict[str, type[NotationAdapter]] = {}


def register_adapter(cls: type[NotationAdapter]) -> type[NotationAdapter]:
    ADAPTERS[cls.id] = cls
    return cls


def get_adapter(name: str) -> NotationAdapter:
    try:
        return ADAPTERS[name]()
    except KeyError as exc:
        raise KeyError(f"Unknown notation adapter {name!r}. Registered: {sorted(ADAPTERS)}") from exc
