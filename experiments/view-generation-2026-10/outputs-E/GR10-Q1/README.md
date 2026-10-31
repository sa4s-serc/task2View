# UML component diagram: Municipal Report Management System, whole system

**Takeaway:** the Swing desktop application is a layered system (UI → controllers → domain services → persistence → MySQL). Domain entities are used by the services and mapped by the persistence layer.
**Stakeholder:** software architect. **Detail level:** overview, as given in the perspective. 6 components, 7 dependencies.

Files: `view.puml`, `view.png`, `inventory.json` (elements, relations, `file:line` evidence). The previous version is in `v1/`.

## How the view addresses the concern
- **Components and responsibilities:** each box names the component, its layer and a one-line responsibility.
- **Layers/subsystems:** the layer is stated in every box (Presentation = `Boundary`, Application = `Control`, Domain = `Entity`, Persistence = `Database`) and the chain reads top to bottom.
- **Main dependencies:** UML dashed dependencies point from dependent to dependency. They show UI → controllers → services → persistence → database, plus services → entities and persistence → entities.
- **Separation and collaboration:** a note says UI and controllers exchange `Map<String,Object>` data, not entities. `SystemServicesController` is the facade, and only login bypasses it. The UI reaches past the controllers only for the `ReportCategory` enum, drawn as its own dependency; the controllers' use of the same enum is stated in the note.

## Changes after review (critique-1)
- Solid arrows became dashed dependencies.
- Added the UI → entities (`ReportCategory`) dependency.
- The persistence → entities link is relabelled "ORM mapping". The code confirms it is not an import: `PersistenceService` imports no `Entity` class and the link comes from `persistence.xml`.
- Removed the `<<muted>>` stereotype from the database. Box texts are now name plus a one-line responsibility with the layer.
- The note states that Domain Services and Domain Entities are a logical split of package `Entity`.

## Not taken from the review, and why
- **Layer packages:** drawn once, then removed. Four packages plus six components gave 10 elements, over the overview budget of 7, and the packages crossed several edges. Layers are in the box text and the note instead.
- **Provided interface on the facade:** an interface element would add a seventh node for little gain at overview level. It is stated in the note.
- **Controller → entities edge:** also in the note only, because the edge crossed layers in the render.

## Omitted on purpose
Individual screens and use-case controllers (merged), state classes, enums other than `ReportCategory`, Credentials, Location, tests.

## Assumptions
- "Domain Services" is a logical component. `ReportService` and `UserService` are in package `Entity`.
- The notification and login controllers are folded into "Application Controllers".

A detailed level would add the individual controllers and screens and the report state hierarchy.

## Check result
`puml-check`: OK, 6 nodes, 7 edges, 1 crossing, 0 issues. `check_inventory.py --level overview`: 0 issues, 0 unbacked items. During the revision, a version with layer packages produced edge-through-container warnings and exceeded the budget; I reverted to the version without packages.
