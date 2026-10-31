# Persisted data of the municipal report system (UML class diagram)

**Takeaway:** the database stores users (Citizen and MunicipalOperator, single table), reports with embedded location and a status name, and three child tables (status updates, internal notes, notifications). All reads and writes go through `ReportService` and `UserService` to `PersistenceService`.

**Stakeholder:** database engineer, about to change report management. **Detail:** detailed, for the persistence area only (12 classes), with domain and technology terms (JPA, single table, cascade).

## How the view answers the concern
- **Main entities and relationships:** the classes `User`, `Citizen`, `MunicipalOperator`, `Report`, `StatusUpdate`, `InternalNote`, `Notification`, with multiplicities taken from the JPA mappings. `Location` and `Credentials` are embedded columns, not tables.
- **Information persisted across a report's life:** `Report` (current status name, editable flag, operator once assigned), `StatusUpdate` (history of each change), `InternalNote`, `Notification` (message and notified status for the citizen).
- **How the listed concepts relate:**
  - Users: `Report` belongs to a `Citizen` and may have a `MunicipalOperator`.
  - Locations: embedded in `Report`.
  - Categories: an enum attribute of `Report`, stored as text (shown as an attribute and a note).
  - States: `currentStatusName` text. The state objects are not persisted.
  - State changes: `StatusUpdate`.
  - Notes: `InternalNote`, written by an operator.
  - Notifications: addressed to a `Citizen` and tied to a `Report`.
- **Dependent parts of the application:** `ReportService`, `UserService` and `PersistenceService` (red). Notes on the services name the controllers that use them. The Boundary (GUI) classes reach the data only through the controllers.

`inventory.json` holds the evidence. `check_inventory.py`: 0 issues, 0 unbacked items.

## Omitted on purpose
Controller and GUI classes (named in notes only), `ReportStatus` and its four state classes (not persisted), `JpaUtil`, a separate `ReportCategory` box, getters and setters.

## Assumptions
- Report states are `submitted`, `assigned`, `in progress`, `resolved` as handled in `Report.rebuildCurrentStatus`. No status table exists.
- The `ReportCategory` enum is stored by name (`@Enumerated(STRING)`).
- Column lengths come from annotations. `hbm2ddl=update` generates the schema, so there are no migration scripts (persistence.xml).
- The `Notification` associations carry no cascade or lazy setting.
- The reported controller usage is derived from fields of type `ReportService` and `UserService`.

## Check result
`puml-check` on the final version: 4 warnings (aspect ratio of 1.2 against 16:9, and a crowded "0..1"/"1" label pair near MunicipalOperator, which I made less crowded but did not remove). No tiny text and no overlapping labels otherwise. The image was viewed. The diagram is tall rather than slide-shaped. Splitting it would separate the entities from their dependents.
