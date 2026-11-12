# Persisted data model of the municipal report system (UML class diagram, balanced)

**Takeaway:** a report is the central persisted entity; it belongs to one citizen, optionally to one operator, embeds its location and category, and owns its status history and internal notes, while notifications reference it and its citizen.

Stakeholder: database engineer. Detail level: balanced (as given): the entities with their key columns and relations, no code-level members.

## How the view answers the concern
- **Main entities:** User (Citizen and MunicipalOperator, one `users` table with a `role` discriminator), Report, StatusUpdate, InternalNote, Notification; Credentials and Location are embedded columns, ReportCategory is a string-stored enum.
- **Relations:** Report → Citizen (mandatory) and → MunicipalOperator (optional); Report composes StatusUpdate and InternalNote (cascade all, orphan removal); StatusUpdate and InternalNote → MunicipalOperator; Notification → Report and → Citizen.
- **States:** ReportStatusValue lists the stored strings shared by `Report.currentStatus`, `StatusUpdate.newStatus` and `Notification.notifiedStatus` (the last limited to assigned and resolved, per `Notification.isStatusNotifiable`).
- **Lifecycle data:** report fields and current status string (`submitted`, `assigned`, `in_progress`, `resolved`), one StatusUpdate per change (date, new status, operator), InternalNotes (text, date, operator), Notifications (date, message, notified status). The status classes are not persisted.
- **Dependents:** named in a note on the view, not drawn (a component view would show them). From the code: `PersistenceService` (JPA via `JpaUtil`, MySQL `reports_db`, `persistence.xml`) is used only by `ReportService` and `UserService`, which the controllers and GUIs call.

Evidence: `inventory.json`. `check_inventory.py --level balanced --graph`: 0 issues. `check_view.py`: clean. `puml-check`: remaining warnings are layout-only (one edge passing over a node, one label offset).

## Omitted
Status classes, service/controller/GUI classes, `PersistenceService`/`JpaUtil` (other viewpoints), the unused Credentials listing in `persistence.xml` (embeddable).

## Assumptions
Column types are Java types from the annotations, no schema script exists. Cardinalities come from `@ManyToOne` and `nullable`. Notifications are not cascaded from Report. A detailed level would add table names, indexes and fetch rules.

## Revision 1 (after reviewer critique; previous version in `v1/`)
- Added the status value domain (ReportStatusValue) and typed the three status columns with it; notifications limited to assigned and resolved.
- Added multiplicities `[0..1]` on `reportDate` and `attachedImage`; legend says unmarked attributes are mandatory.
- Replaced the lifecycle note: status order, one StatusUpdate per change, operator required first (`Report.java:202,369`), `citizenEditable` true only while submitted (`Report.java:391-431`), notifications not cascaded so they block report deletion.
- Removed the Report to ReportCategory dependency (category stays a typed attribute) and the blue emphasis styling; `<<embeddable>>` became «dataType» with a legend entry; the Location note now sits on Location.
- Added a note naming the dependents (ReportService, UserService via PersistenceService/JpaUtil).
- Kept: the composition diamonds. They match `cascade = ALL, orphanRemoval` for status updates and notes; the legend limits the claim to those two and the lifecycle note states the notification restriction.
- Result: `check_inventory.py` 0 issues (two undrawn notes are the removed category edge, listed under omitted); `check_view.py` clean; `puml-check` 4 layout warnings (labels near edges, bundled edges at Notification), down in shape from ratio 2.0 to 1.5.
