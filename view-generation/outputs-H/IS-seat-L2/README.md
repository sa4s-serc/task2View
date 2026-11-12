# Seat booking: component view (UML component diagram, balanced), revision 1

**Takeaway:** every seat booking goes through the Library facade to the Reservation manager, but the booking rules are spread over the manager, the Seat assignment strategy and the model checks, so a new rule most likely changes those, with knock-on effects on the other components.

Stakeholder: developer changing the booking rules. Detail level: balanced (given). A detailed level would add the manager's validation steps (`ReservationManager.java:65-102`) and the registry queries. The first version is in `v1/`.

## How the view answers the concern
- **Main components:** three entry points (desktop screens, REST API, scheduler), Library facade, Reservation manager, Room availability manager, Notification manager, Seat assignment strategy, Registries, Reservation and seat model, Persistence (JPA, MySQL).
- **Responsibilities:** each component box now carries its responsibility under its name. Rules live in three places: the Reservation manager (flow), the model (seat availability `Seat.java:45`, one booking per slot `Student.java:42`, opening days `StudyRoom.java:141`) and the Registries (shared occupancy rule `ReservationRegistry.occupiesSlot`, line 120).
- **Interactions:** entry points call the facade; the facade delegates; the Reservation manager uses the Seat selection interface, creates the reservation, saves it through the Registries and notifies. The model queries the Registries and notifies through the Reservation observer interface; the Room availability manager cancels and saves reservations and notifies on room deletion (`StudyRoomManager.java:158-180`).
- **Change impact:** marked in the diagram. Blue fill: likely changed (Reservation manager, Seat assignment strategy, model, Registries). Plain: may be affected (facade signature and the screens/REST API that pass request data, Room availability manager, Notification manager). Grey: persistence. Hidden coupling: `occupiesSlot` and the model availability checks are also used by the availability display, room deletion and statistics (`ReservationRegistry.java:67,92`, `StudyRoomManager.java:172`), so a rule placed there changes all of them. Tests: `MakeReservationTest`, `CancelReservationTest`, `PerformCheckInTest`, `ManageReservationEndTest`.

## What changed after the review (v1 to now)
- Added model to Registries, model to Reservation observer to Notification manager, Room availability manager to Notification manager, and widened the room manager's registry edge to "reads, cancels bookings".
- Merged Persistence manager, JPA and the database into one element, so JPA is no longer provided by the database or both provided and required; dropped the non-standard «external».
- Added responsibilities in the boxes, a change-impact legend and highlighting.
- Corrected the desktop screens' evidence (`ReservationSummary.java:100`, `StudentDashboard.java:125,140`).
- Student is linked to the screens by an association instead of «use».
- Removed the Librarian: the librarian's screens only create rooms and monitor (`LibrarianDashboard.java:82`, `CreateRoom.java:242`) and do not book seats. The entity includes librarians, but this booking view does not need them.
- Kept: the Seat selection and Facade operations interfaces (Seat selection is the extension point for seat-choice rules). The email port (`NotificationService`) stays omitted as below balanced level.

## Checks
- `inventory.json` (evidence per element/relation): `check_inventory.py --level balanced --graph .claude/repo-graph.json` reports 0 issues (8 notes: undrawn dependencies and unchecked interfaces/actor). `check_view.py`: clean.
- `puml-check`: 2 warnings (an edge touches the "Domain and persistence" title tab; the label "saves status" sits on a group border). Lengthening the edges raised the count, so I kept this version. v1 had 2 warnings too.
- Omitted: DTOs, user management and factories, email adapter, Swing helper classes, Librarian, entity dependencies of the room manager, notification manager and strategy.

## Assumptions
- Room availability manager is its own component because it computes what users see and cancels bookings on room deletion.
- The REST API caller is not drawn: the code shows no client.
