# Data model view: persisted entities of the municipal report system

**Viewpoint / model kind:** data model, UML class diagram. **Stakeholder:** database engineer. **Detail level:** detailed (given), drawn for the persistence area only.

**Takeaway:** every report row (`reports`) owns its state-change history, internal notes and an embedded location, points to a citizen and an optional operator, and is the target of citizen notifications; all access goes through `ReportService`/`UserService` -> `PersistenceService` (JPA/Hibernate, MySQL `reports_db`).

Files: `view.puml`, `view.png`, `inventory.json` (elements, relations, `file:line` evidence).

## How the view answers the concern
- **Main entities and relationships:** the tables `users` (single table, `role` discriminator: Citizen / MunicipalOperator), `reports`, `status_updates`, `internal_notes`, `notifications`, with key attributes, ids and multiplicities. Credentials and Location are embedded columns, not tables.
- **Persisted through a report's lifecycle:** creation stores `Report` (+ location, category, image, `current_status`, `citizen_editable`); each state change appends a `StatusUpdate` (date, new status, operator) and updates `current_status`; operators add `InternalNote`s; notifiable states create a `Notification` for the citizen. `ReportStatus` (Submitted/Assigned/InProgress/Resolved) is not persisted: only the state name string is.
- **Relations among users, reports, locations, categories, states, state changes, notes, notifications:** composition for embedded/owned parts (cascade ALL, orphanRemoval on notes and updates), associations for foreign keys (`citizen_id`, `operator_id`, `report_id`), a dependency for the category enum (stored as string).
- **Dependent application parts:** `PersistenceService` <- `UserService`, `ReportService` <- Control package (10 controllers) <- Boundary package (GUI screens). Only the two services touch the database.

## Omitted on purpose
Individual controllers/GUIs (grouped), `JpaUtil`, state-class internals, DTO-mapping helpers, and per-consumer edges to `ReportCategory` and from `UserService` to the user subtypes (listed in `inventory.json` under `omitted`).

## Assumptions
- Table/column names come from JPA annotations; `hbm2ddl.auto=update` means there are no migration scripts, the schema is derived from the entities. Whether the live database matches is unknown.
- `Credentials` and `Location` are not listed in `persistence.xml` but are embeddables of persisted entities.
- Status and category are stored as plain strings with no foreign-key lookup table.

## Check result
- `check_inventory.py --level detailed --graph .claude/repo-graph.json`: 0 issues (5 notes about undrawn dependencies, all listed as omitted).
- `puml-check`: renders; 4 cosmetic warnings left (two detached labels, two bundled edges); the layout is wide (about 2:1).
