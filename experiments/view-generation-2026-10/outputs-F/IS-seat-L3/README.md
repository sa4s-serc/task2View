# UML component diagram: seat booking (study-room reservation application)

**Takeaway:** a booking enters through the client boundaries (Swing, REST) and `LibraryFacade`, and `ReservationManager` applies the booking rules. It reads seat availability from the stored reservations (via the model and registries), saves the reservation, and notifies through the `NotificationService` interface. New rules belong in `ReservationManager`, and the availability lists in `StudyRoomManager` must agree with them.
**Stakeholder:** software developer about to add booking rules. **Detail level:** balanced, as given (12 elements, 14 relations). Files: `view.puml`, `view.png`, `inventory.json`; the first version is in `v1/`.

## How the view addresses the concern
- **Handling booking requests:** Client boundaries to `LibraryFacade`, which delegates to `ReservationManager`. Pre-booking availability queries go to `StudyRoomManager`.
- **Checking seat availability:** `ReservationManager` checks the room, seat and reservation model (`Seat.isAvailable`). The model reads stored reservations through the registries, so the check depends on persisted data. `StudyRoomManager` computes the availability lists shown before booking.
- **Applying booking rules:** `ReservationManager` (blue) with a note listing the rule kinds: room active and open on weekdays, seat belongs to the area, one active or confirmed booking per student, date and slot, seat free, default seat through the `AssignmentStrategy` interface (`FirstAvailableAssignment`).
- **Managing and storing reservations:** model (Reservation and states), then registries and persistence, then the MySQL database.
- **External services:** `NotificationManager` (Observer) requires the `NotificationService` interface, realised by the Email adapter, which calls the external email gateway (a stub in code). The gateway and the database are drawn grey, outside the application.
- **Modify / affected:** the blue box is the place to change. A note lists the likely-affected components: clients and facade (request shape), `StudyRoomManager`, the registries, `NotificationManager`.

## Revision after review (critique-1)
Done: added `StudyRoomManager`; added the model-to-registries dependency (`Seat.java:45`); separated the external email gateway from the adapter and showed `NotificationService` and `AssignmentStrategy` as interfaces; made all relations dashed dependencies; corrected the rules note (per student, not per slot; room and seat-in-area rules); dropped the scheduler and the facade-to-`NotificationManager` reminder edge; added the affected-components note.
Not done as asked:
- The system boundary box is not drawn. With it the view has 13 or more elements, over the balanced budget of 12 (`check_inventory.py` flags it). Grey fill and a legend mark the external elements instead.
- `FirstAvailableAssignment` is not a separate box. It is named in the interface label to stay within budget, so the interface is shown without a drawn realizing component.
- Swing and REST are merged into one "Client boundaries" element for the same reason.
- Dashed arrows carry no «use» stereotype.

## Omitted on purpose
Scheduler and `NotificationConfiguration` (reminders and expiry, and start-up wiring), DTOs, `UserManager`, factories, cancel, check-in and monitoring flows, and the student and librarian actors. Undrawn dependencies: `NotificationManager` to the registries and `ReservationManager`, registries to the Reservation model, model to the strategy, Swing start-up wiring. These are secondary entity references or wiring.

## Assumptions
- Members of grouped elements are listed in `inventory.json`.
- The email gateway stands for the external service although the code only contains a stub.

## Check results
- `puml-check`: renders, 12 nodes, no crossings. It still warns about edges running near two notes and the interface labels. I judged these cosmetic after viewing the PNG; I did not fix them.
- `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues; the remaining notes are undrawn dependencies (listed above) and the database having no members.
