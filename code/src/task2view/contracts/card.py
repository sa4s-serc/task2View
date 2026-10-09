"""Phase 0 repository card (ADR-006 D2; design 02 §3).

Deterministic facts about a repository: typed files, a symbol table, a directed
dependency graph from code only, entry points, persisted entities, deployment and
build units, layers, and the repository signals the viewpoint catalog uses.
Every signal carries the evidence that raised it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

FileClass = Literal["code", "test", "build", "deploy", "config", "schema", "web", "docs", "model", "binary", "other"]
EdgeKind = Literal["imports", "extends", "implements", "field", "param", "returns", "instantiates", "calls", "annotated"]


class SourceFile(BaseModel):
    path: str
    file_class: FileClass
    language: str | None = None
    lines: int = 0
    parsed: bool = False


class Field_(BaseModel):
    name: str
    type: str | None = None
    annotations: list[str] = Field(default_factory=list)
    static: bool = False
    line: int = 0


class Method(BaseModel):
    name: str
    start_line: int
    end_line: int
    params: list[str] = Field(default_factory=list)
    returns: str | None = None
    annotations: list[str] = Field(default_factory=list)
    calls: list[str] = Field(default_factory=list)  # "<symbol id>.<method>" of resolved internal calls


class Symbol(BaseModel):
    id: str  # fully qualified (java: package.Type, python: package.module or package.module.Class)
    name: str
    kind: Literal["class", "interface", "enum", "record", "annotation", "module", "function"]
    file: str
    start_line: int
    end_line: int
    language: str
    package: str = ""
    layer: str | None = None
    is_test: bool = False
    annotations: list[str] = Field(default_factory=list)
    extends: list[str] = Field(default_factory=list)  # names as written
    implements: list[str] = Field(default_factory=list)
    fields: list[Field_] = Field(default_factory=list)
    methods: list[Method] = Field(default_factory=list)
    enum_constants: list[str] = Field(default_factory=list)


class Edge(BaseModel):
    source: str
    target: str
    kind: EdgeKind
    file: str
    line: int
    detail: str = ""  # method name for calls, field name for fields


class EntryPoint(BaseModel):
    kind: Literal["main", "http-route", "gui", "scheduled", "listener", "cli"]
    symbol: str
    file: str
    line: int
    detail: str = ""  # route, schedule, event


class EntityField(BaseModel):
    name: str
    type: str | None = None
    key: bool = False
    relation: str | None = None  # many-to-one, one-to-many, embedded, ...
    target: str | None = None  # internal symbol id for relations
    foreign_key: str | None = None  # join column name


class Entity(BaseModel):
    symbol: str | None = None  # None for schema-only tables
    name: str
    table: str | None = None
    source: Literal["orm", "schema"]
    file: str
    fields: list[EntityField] = Field(default_factory=list)


class DeployUnit(BaseModel):
    kind: Literal["dockerfile", "compose-service", "k8s", "persistence-unit", "app-config", "ci", "other"]
    name: str
    file: str
    details: dict[str, str | list[str]] = Field(default_factory=dict)


class BuildUnit(BaseModel):
    tool: str
    file: str
    name: str = ""
    packaging: str = ""
    dependencies: list[str] = Field(default_factory=list)


class RepositoryCard(BaseModel):
    root: str
    name: str
    languages: dict[str, int] = Field(default_factory=dict)  # language -> code files
    files: list[SourceFile] = Field(default_factory=list)
    symbols: dict[str, Symbol] = Field(default_factory=dict)
    edges: list[Edge] = Field(default_factory=list)
    entry_points: list[EntryPoint] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    deploy: list[DeployUnit] = Field(default_factory=list)
    build: list[BuildUnit] = Field(default_factory=list)
    layers: dict[str, list[str]] = Field(default_factory=dict)  # layer id -> packages/directories
    signals: dict[str, list[str]] = Field(default_factory=dict)  # signal -> evidence
    notes: list[str] = Field(default_factory=list)

    def by_simple_name(self, name: str) -> list[Symbol]:
        return [s for s in self.symbols.values() if s.name == name]
