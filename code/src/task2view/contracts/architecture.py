"""ADR-007 architectural view: named parts that keep their member classes, and connectors lifted from code."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Part(BaseModel):
    id: str
    name: str
    role: str  # ui, api, job, service, integration, domain, data_access, database, web_client
    technology: str = ""
    description: str = ""
    members: list[str] = Field(default_factory=list)  # symbol ids: the verification handle
    files: list[str] = Field(default_factory=list)  # for parts without classes (web pages, deploy facts)


class Connector(BaseModel):
    source: str
    target: str
    label: str  # intent, never a method name
    protocol: str = ""
    weight: int = 0  # code dependencies between the members behind this arrow
    against_layering: bool = False
    evidence: list[str] = Field(default_factory=list)


class ArchView(BaseModel):
    title: str
    parts: list[Part] = Field(default_factory=list)
    connectors: list[Connector] = Field(default_factory=list)
    omitted: list[str] = Field(default_factory=list)  # relations not drawn, with the reason
    notes: list[str] = Field(default_factory=list)

    def part(self, pid: str) -> Part:
        return next(p for p in self.parts if p.id == pid)
