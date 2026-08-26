# ADR-004 — Filesystem graph, directory groups, config-selected plug-ins

- **Status:** accepted (D2 superseded by [ADR-005](ADR-005-correspondence-and-published-grain.md))
- **Date:** 2026-08-24
- **Supersedes:** [ADR-003](ADR-003-structure-grounding.md) D1 grouping and D4 as *core* behaviour
- **Extends:** [ADR-002](ADR-002-sota-plugins.md) (plug-in catalogs remain)
- **Superseded in part by:** [ADR-005](ADR-005-correspondence-and-published-grain.md) (directory groups are not the published architecture; grain is viewpoint-keyed)

## Context

ADR-003 grounded views in a **javalang** type graph and regrouped by BCED-style layers. That fixed some GR10 runs and broke the claim that Task2View is language-neutral. Architecture also varies per repository: Boundary/Control/Entity is one possible layout, not the default ontology.

ISO/IEC/IEEE 42010 already separates identifying stakeholders/concerns, selecting a catalog viewpoint, and constructing a view of the system of interest. Diagram notation is a model-kind language, not a fixed PlantUML choice.

## Decision

### D1. ArchitectureGraph is filesystem-shaped

Nodes are kept files (stem keys, path aliases). `layer` is the **parent directory name**. Uses/calls come from import-like lines and identifier mentions that resolve to other kept files. No language AST in the core.

### D2. `apply_facts` regroups by directory *(superseded)*

ADR-004 grouped selected elements by parent directory. That published folder names (`Boundary` / `Control` / `Entity`) as the architecture. [ADR-005](ADR-005-correspondence-and-published-grain.md) keeps the filesystem graph (D1) but projects with **viewpoint grain**: component names stay, type edges only when `unit` is type, context is actors + system, no folder-lift.

### D3. 42010 artefacts are first-class

A run records stakeholder (catalog id), concerns/QAs (catalog ids), optional environment, viewpoint id, view, and **unanswered concerns** as declared gaps. Viewpoint ids are never invented.

### D4. Model-kind language follows goal then viewpoint

`choose_language`: explicit CLI/config or a registered language named in the goal, then viewpoint `default_diagram_language`, then formality × preference matrix.

### D5. Scoper / extractor / notation stay catalogs, now YAML-selectable

`--config pipeline.yaml` sets `scoper`, `extractor`, `diagram_language`. CLI flags override. Every extractor still emits a `ViewModel`. `apply_facts`, critic, adapter, and gate always run after it.

## Consequences

- Java is one corpus among others; a Python (or mixed) repo gets directory groups and import edges without javalang.
- GR10 directories named Entity/Boundary/Control still appear as group names because those **are** the directories, not because BCED is hardcoded.
- Ablations remain configuration, not forks.
