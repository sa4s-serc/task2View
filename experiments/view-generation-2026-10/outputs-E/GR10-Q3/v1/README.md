# UML class diagram: persisted report data (GR10-Q3)

**Takeaway:** every report lives in `reports`, owned by a Citizen and optionally assigned to a MunicipalOperator, and accumulates StatusUpdate, InternalNote and Notification rows. Location and Credentials are embedded columns, and the state objects are not stored.

**Stakeholder:** database engineer, before changing report management. **Detail level:** detailed (given), 14 classes. Wording is technical (JPA, table and column names).

## How the view addresses the concern
- **Main entities and relations:** `User` (single table `users`, role discriminator, subclasses Citizen and MunicipalOperator, embedded Credentials), `Report`, `StatusUpdate`, `InternalNote` and `Notification`, with FK columns and multiplicities.
- **Lifecycle information:** on creation a Report stores its data and `currentStatusName` = submitted. Each status change appends a StatusUpdate (date, new status, operator) and rewrites `current_status` and `citizen_editable`. Notes are appended by operators. A Notification is stored only for the assigned and resolved statuses.
- **Relations among users, reports, locations, categories, states, state changes, notes and notifications:**
  - Location is embedded in Report (same table).
  - Category is an enum stored as a string.
  - State is the string `current_status`. `ReportStatus` and its implementations are rebuilt on load and not stored.
  - State changes, notes and notifications are child rows of Report.
- **Dependents:** `ReportService`, `UserService` and `PersistenceService` (all JPA access). A note records that the controllers instantiate the two services and the GUIs reach them via the controllers. Controllers and GUIs are not drawn individually; a component view would show them.

`inventory.json` holds the elements, relations and file:line evidence. `check_inventory.py --level detailed`: 0 issues.
`puml-check`: renders, 3 minor warnings remaining (multiplicity labels close to edges), no overlaps of class boxes. Layout not further tuned.

## Omitted
The four state classes, controllers, GUIs and `JpaUtil` (see `inventory.json`).

## Assumptions
- Table and column names come from the JPA annotations. No SQL schema exists, and `hibernate.hbm2ddl.auto=update` generates it.
- Citizen and operator foreign keys are modelled as in the annotations. Notification uses the field name `destinatario`, shown as recipient.
- `persistence.xml` lists no `Credentials`, `Location` or enum classes. They are embeddables or columns and need no registration.
