# UML component diagram: seat booking (study-room reservation application)

**Takeaway:** a booking enters through the Swing client or REST API, passes `LibraryFacade` to `ReservationManager`, which holds the booking rules and orchestrates availability, seat selection, persistence and notification. New rules belong in `ReservationManager`.
**Stakeholder:** software developer about to add booking rules. **Detail level:** balanced (as given), so only the booking path is drawn at component level (12 components, 14 relations). Files: `view.puml`, `view.png`, `inventory.json`.

## How the view addresses the concern
- **Handling booking requests:** Swing client and REST API (`POST /api/reservations/create`) call `LibraryFacade`, which delegates to `ReservationManager`.
- **Checking seat availability:** `ReservationManager` checks it against the Room and seat model (`Area.getAvailableSeats`, `Seat.isAvailable`) and rejects a seat that is no longer free.
- **Applying booking rules:** `ReservationManager` (highlighted, with a note): student, room, area and slot resolution, one active or confirmed booking per student and slot, seat-in-area check, synchronized section. Automatic seat choice is pluggable via the Seat assignment strategy (`FirstAvailableAssignment`).
- **Managing and storing reservations:** `ReservationManager` creates the Reservation (state model) and saves it through the Registries, then PersistenceManager (JPA/Hibernate) and the MySQL database.
- **External services / notifications:** `Reservation` state changes notify `NotificationManager` (Observer), which calls the `NotificationService` interface implemented by the email adapter (a stub gateway returning 200). The scheduler also calls the facade for reservation expiry and reminders.
- **What to modify / what is affected:** modify `ReservationManager` (and the strategy or the model for rules about seats or reservation state). Affected: the facade and both boundaries if the request shape changes, the registries and persistence if rules need new queries or fields, and `NotificationManager` if rules add new states or messages.

## Omitted on purpose
DTOs, `UserManager`, `StudyRoomManager`, factories, cancel, check-in and monitoring flows. The student and librarian actors were dropped to stay within the 12-component budget; the two client boundaries are their entry points. Undrawn dependencies: NotificationManager to registries and ReservationManager, registries to the Reservation and room models, Reservation to room model, strategy to Seat, Swing start-up to notification wiring. These are secondary entity references or start-up wiring. A detailed view of `ReservationManager` would show its internal steps.

## Assumptions
- Components group several classes (see `members` in the inventory); "Registries" and "Notification boundary" are groupings I chose.
- The email gateway is a stub in code; no real external service is called.
- The scheduler/wiring to NotificationManager edge reflects `NotificationConfiguration` injecting the adapter.

## Check results
- `puml-check`: renders, 12 nodes, no warnings (one info about edge count). Direction is top-to-bottom, chosen over left-to-right because it gave a better aspect ratio.
- `check_inventory.py --level balanced --graph .claude/repo-graph.json`: 0 issues; 8 notes (the undrawn dependencies listed above, and the database not being in the graph).
