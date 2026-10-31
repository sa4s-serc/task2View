# Data model view: persisted entities of the municipal report system

**Takeaway:** every report is one row in `reports` linked to the citizen who filed it, with its location and category stored inline and its history in child rows (status updates, internal notes, notifications). All access goes through `ReportService` and `UserService`.

**Stakeholder:** database engineer, about to change the persistence layer. **Detail:** balanced (14 classes: 11 persisted types plus 3 persistence-access classes), with attributes shown because the change is to the schema. Technology names (JPA table and column terms) are used because the audience is engineering.

## How the view answers the concern
- **Main entities and relationships:** the seven JPA entities in `persistence.xml:14-20` and their associations. `Credentials` and `Location` are embedded columns, not tables. `ReportCategory` is an enum stored as a string.
- **Users, reports, locations, categories:** `User` is a single table with a `role` discriminator, with `Citizen` and `MunicipalOperator` as subclasses. `Report` points to the citizen who reported it and the optional assigned operator. `Location` is embedded in `Report` and `ReportCategory` is its `category` attribute.
- **States and state changes:** the current state is the string `currentStatusName` on `Report`. Each change is a `StatusUpdate` row (date, new status, operator), composed by `Report` with cascade and orphan removal. The state objects (`Submitted`, `Assigned`, `InProgress`, `Resolved`) are `@Transient`, so they are not stored.
- **Internal notes and notifications:** `InternalNote` holds text, date and author operator, and is composed by `Report`. `Notification` holds date, message and notified status, and points to the report and the citizen recipient. It is not cascaded from `Report`.
- **Lifecycle information persisted:** the creation attributes on `Report`, then `StatusUpdate`, `InternalNote` and `Notification` rows added over time.
- **Dependents:** `ReportService` and `UserService` use `PersistenceService`, which uses `JpaUtil`. Only these services access the entities. The 9 Control classes reach persistence through them (the 10th, `SystemServicesController`, is a facade).

## Inventory (element: evidence)
- `User`: Entity/User.java:20-33 (single table, discriminator `role`: :22-27)
- `Credentials`: Credentials.java:9-16; embedded in User.java:47
- `Citizen`: Citizen.java:9-11; `MunicipalOperator`: MunicipalOperator.java:9-11
- `Report`: Report.java:29-113 (citizen :87-89, operator :94-96, notes :101-107, updates :112-113, category :49-51, status string :69-70, `@Transient` status :75-76, `Location` embedded :56-57)
- `Location`: Location.java:9-25. `ReportCategory`: ReportCategory.java:8-12
- `StatusUpdate`: StatusUpdate.java:20-54. `InternalNote`: InternalNote.java:20-54
- `Notification`: Notification.java:19-54 (citizen :48-50, report :52-54)
- `ReportService` use of Report, Notification, InternalNote and StatusUpdate: ReportService.java:113, 200, 213, 248, 398
- `UserService` use of User: UserService.java:89, 123
- Both services use `PersistenceService`: ReportService.java:21, UserService.java:20
- Persistence unit and entity list: persistence.xml:10-20

## Omitted on purpose
- The status state classes and the `ReportStatus` interface (not persisted).
- The 9 Control classes and the Swing GUI classes (shown only as a note).
- `JpaUtil`, constructors, getters and private helper methods.
- Edges from `ReportService` to `StatusUpdate`, `InternalNote` and `User` (written in a note and merged into the `Report` edge).

## Assumptions
- Foreign-key column names come from `@JoinColumn`, but the real database schema (`hbm2ddl update`, persistence.xml:35-36) was not inspected.
- Statuses are free strings, so the only status values known are the constants in Report.java:33-36 (no database constraint is visible).
- Table names appear in a note rather than as stereotypes, to stay within standard UML.

## Check result
Final `puml-check`: 4 warnings (edge-through-text and edge-through-node on long cross-row edges, bundled edges); the first run had 10. Aspect ratio is 1.85 against a target of 1.78, with no tiny text. Image review: the layout was restacked into rows and the view was kept at the better, less wide version. Rendered with PlantUML to `view.png`.
