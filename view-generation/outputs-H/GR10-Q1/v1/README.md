# Layered package view: municipal report management application

**Takeaway:** the application is a four-layer stack (Presentation → Application → Domain → Persistence) in which dependencies run downward only; screens never touch persistence, and only the domain services reach the database.

Stakeholder: software architect reviewing the structure before planning evolution. Detail level: **overview** (as given). A balanced level would add the individual screens, controllers and entity classes.

## How it answers the concern
- **Components and responsibilities:** five packages, each with a name matching the code: Boundary (Swing screens), Control (one controller per use case plus a system services facade), Domain services (`Entity.ReportService`, `Entity.UserService`), Domain entities (the other `Entity` classes, JPA-mapped), Database (`PersistenceService`, `JpaUtil` over JPA/Hibernate to MySQL). Responsibilities are in `inventory.json`.
- **Layers/subsystems:** the four enclosing packages. The `Entity` code package is split into two parts, services and entities, because it holds both.
- **Dependencies:** screens → controllers → domain services → database. Controllers and screens also depend directly on domain entities (screens only for report categories).
- **Separation:** user-facing code is only in Boundary, application logic in Control, domain model in the entities, and persistence only in Database, reached via the domain services. The Boundary → Control path is the dependency the code shows most (37 edges in the graph).

Evidence and the member mapping are in `inventory.json`. `check_inventory.py --level overview --graph .claude/repo-graph.json`: 0 issues (one note: layer packages have no members, so their relations are not checked against the graph). `check_view.py`: clean. `puml-check`: no warnings (info notes about edges crossing sibling packages only).

## Omitted
Individual classes, GUI forms, enums and state classes; the MySQL server (an external system, not a module); framework glue.

## Assumptions
- The `Entity` package's two service classes are treated as a domain services part, though in the code they live beside the entities. Their database dependency is what makes them the persistence gateway.
- Dependencies are static, from the graph; no run-time wiring was checked.
