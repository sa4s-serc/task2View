# UML class diagram: persisted report data (GR10-Q3)

**Takeaway (revision 2; v1 kept in `v1/`):** every report lives in `reports`, owned by a Citizen and optionally assigned to a MunicipalOperator, and accumulates StatusUpdate, InternalNote and Notification rows. Location and Credentials are embedded columns, and the state objects are not stored.

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
`puml-check`: renders with 5 warnings (a label on a node, two edges passing over a node, one edge label on its own line, two end labels close together). v1 had 3 warnings but lacked the content below. Direction was changed to left-to-right, which fixed an aspect ratio of 2.6.

## Revision after review (critique-1.json)
Changed:
- Status vocabulary, the `citizenEditable` rule, the "StatusUpdate needs an assigned operator" rule and the code-only notification restriction are in a note on Report. `notifiedStatus` no longer shows `{assigned | resolved}` as if it were a schema constraint.
- ReportService now depends on StatusUpdate, InternalNote, User and MunicipalOperator.
- FK column names are on the association labels. Discriminator values are on Citizen and MunicipalOperator. `role` is no longer a User attribute.
- Lengths added to Location and `category`. DATE/TIMESTAMP marked on the date fields.
- Report..>ReportCategory and Report..>ReportStatus dependencies became directed associations. The "embeds" labels became role names, and embedded parts have multiplicity 1.
- The styling stereotypes were replaced by plain colour.

Kept as they were:
- Association role names are in the labels, not at the ends, because end labels overlapped when I tried them.
- The `category` attribute stays alongside its association to the enum. The enum is a drawn class, and the association gives its stored-as-string link.
- Controllers and GUIs stay in a note, because they are callers, not persisted data.

## Omitted
The four state classes, controllers, GUIs and `JpaUtil` (see `inventory.json`).

## Assumptions
- Table and column names come from the JPA annotations. No SQL schema exists, and `hibernate.hbm2ddl.auto=update` generates it.
- Notification's recipient field is `destinatario` in the code and is drawn under that name.
- `persistence.xml` lists no `Credentials`, `Location` or enum classes. They are embeddables or columns and need no registration.
