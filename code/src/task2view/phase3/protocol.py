"""Phase 3 Scoper protocol. Implementations share this contract."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from task2view.contracts.models import CleanedCorpus, RepositoryScope, ViewSpecification


@runtime_checkable
class Scoper(Protocol):
    name: str
    requires: set[str]

    def scope(
        self,
        view_spec: ViewSpecification,
        repo_root: str,
        budget: int,
        corpus: CleanedCorpus | None = None,
        graph: Any | None = None,
    ) -> RepositoryScope: ...


SCOPERS: dict[str, type] = {}


def register_scoper(cls: type) -> type:
    SCOPERS[cls.name] = cls
    return cls


def get_scoper(name: str) -> Scoper:
    try:
        return SCOPERS[name]()
    except KeyError as exc:
        raise KeyError(f"Unknown scoper {name!r}. Registered: {sorted(SCOPERS)}") from exc
