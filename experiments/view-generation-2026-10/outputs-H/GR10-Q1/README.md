# Package view: municipal report management application (revision 1)

**Takeaway:** the code is four flat packages, Boundary, Control, Entity and Database, that depend downward in that order. Entity mixes domain classes with persistence mapping, so the domain is not independent of persistence.

Stakeholder: software architect reviewing the structure before planning evolution. Detail level: **overview** (as given). A balanced level would add the facade and controllers, the screens, and the entity classes. The previous version is in `v1/`.

## How it answers the concern
- **Components and responsibilities:** each package box names its layer role and responsibility: Boundary (presentation, Swing screens), Control (application, use-case controllers), Entity (domain, entities and services), Database (persistence, JPA access). A note on Boundary records that the SystemServicesController facade is the entry point of seven of ten screens, that the login screen uses its own controller, and that two screens call no controller. The facade is in the note, not a box, since it is a class and the view is at package level.
- **Layers/subsystems:** the layer role is in each package name. The four packages are the real code namespaces; layers are not drawn as owning packages.
- **Dependencies:** Boundary → Control; Boundary → Entity (only the `ReportCategory` enum); Control → Entity (the services and the `ReportCategory` enum); Entity → Database; Entity and Database → the external JPA API (`jakarta.persistence`).
- **Separation:** the note on Entity says that its classes carry JPA annotations, that its services call Database directly, and that layers exchange `Map` data instead of domain objects. This shows where the separation is weaker than the layer names suggest.

`inventory.json` has the evidence and members. `check_inventory.py --level overview --graph .claude/repo-graph.json`: 0 issues (one note: the external JPA API has no members to check). `check_view.py`: clean. `puml-check`: OK, no warnings.

## Changes from the reviewer's critique (details in `v1/`)
- Removed the four layer wrapper packages and the Entity split into two packages; the code has one `Entity` namespace.
- Relabelled Control → Entity as "calls services, enum". The reviewer is right that controllers do not create or update entity objects. The Control → Entity edge stays because the code shows it: controllers import `ReportService`, `UserService` and, in `ReportCreationController`, `ReportCategory`. Both Entity services and the enum sit in the same package.
- Added the JPA API as an external package, with Entity → JPA and Database → JPA dependencies, and a note on the facade and on `Map` data.
- Dependency labels are plain verbs; no keyword stereotypes are used.

## Omitted
Individual classes, GUI forms, enums, the MySQL server and framework glue.

## Assumptions
- Dependencies are static, from the graph and imports; run-time wiring was not checked.
- The seven-of-ten facade count comes from grepping `Boundary` for `SystemServicesController`; I did not trace every call.
