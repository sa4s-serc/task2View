# Data model view – persistence of municipal reports (UML class diagram)

**Takeaway:** every report is one row in `reports` (with location and category inline) owned by a citizen and optionally assigned to an operator; its lifecycle is persisted as child rows (status updates, internal notes) plus notifications, and only `ReportService`/`UserService` (via `PersistenceService`) touch them.

Stakeholder: database engineer, about to change report management. Detail level: *detailed* for the persistence area only (12 classes, within the ≤15 budget); technology names (JPA, Hibernate, MySQL) are used.

## How the view answers the concern
- **Main entities and relations:** the persistent classes `User` (Citizen / MunicipalOperator, single table `users`, discriminator `role`), `Report`, `StatusUpdate`, `InternalNote`, `Notification`, with multiplicities on every foreign key.
- **Lifecycle information:** `Report.currentStatusName` + `citizenEditable` (current state), `StatusUpdate` (history: date, new status, operator), `InternalNote` (text, date, operator), `Notification` (date, message, notified status, recipient). Status values are in the note on `Report`.
- **Users, locations, categories, states:** users = `User` hierarchy + embedded `Credentials`; location = embedded `Location` (columns in `reports`); category = enum `ReportCategory` stored as string column (values in note); states = text column, not a table (the state objects are rebuilt on load and not persisted).
- **Dependent parts:** `UserService`, `ReportService` and `PersistenceService` are shown with the entities they use. The note records that Control classes call the services and GUIs reach them only through Control (the Control/Boundary classes are not drawn, to stay one abstraction level).

## Inventory (evidence)
| Element | Evidence |
|---|---|
| User, Citizen, MunicipalOperator, Credentials | `src/main/java/Entity/User.java:20-67`, `Citizen.java:9-10`, `MunicipalOperator.java:9-10`, `Credentials.java:9-16` |
| Report, Location | `Report.java:29-112`, `Location.java:9-25` |
| ReportCategory | `ReportCategory.java:6-12`, `Report.java:49-51` |
| StatusUpdate | `StatusUpdate.java:20-53`; created `Report.java:367-382` |
| InternalNote | `InternalNote.java:20-53`; created `Report.java:224-242` |
| Notification | `Notification.java:19-53`; saved `ReportService.java:398` |
| ReportService / UserService | `Entity/ReportService.java`, `Entity/UserService.java` (`persistenceService.*` calls) |
| PersistenceService, store | `Database/PersistenceService.java:24,51,116,177`, `META-INF/persistence.xml` |
| Callers | `Control/*Controller.java` create the services; `Boundary/*GUI.java` use `SystemServicesController` |

## Omitted on purpose
State classes (`Submitted`, `Assigned`, `InProgress`, `Resolved`, `ReportStatus`: not persisted), Control and Boundary classes, getters/validation, individual service methods.

## Assumptions
- `Notification` has no inverse collection in `Report` and no cascade; it is persisted separately by `ReportService`.
- Table names come from `@Table`; Location/Credentials columns are embedded, so no separate tables. `Notification.destinatario` is shown as `recipient`.
- Dependency labels (reads/creates) summarise `ReportService` calls; `UserService` also uses `Citizen`/`MunicipalOperator` lookups through `User`.
- `<<persistent>>`/`<<embeddable>>` are not UML standard stereotypes; they are declared as a profile in the legend.

## Check result
Final `puml-check`: 3 warnings (two edge labels near a line, two crowded multiplicity ends at `MunicipalOperator`); first render had 13. Image review: moved the enum into a note and fixed a mis-rendered attribute; a variant with extra ranks was worse (13 warnings) and was reverted.
