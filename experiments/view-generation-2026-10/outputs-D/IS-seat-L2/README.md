# Seat booking: UML component diagram (revision 1)

**Takeaway:** a booking goes UI → REST → `LibraryFacade` → `ReservationManager`, which applies its rules through the room, seat, student and reservation parts of the domain model and the registries. `AssignmentStrategy` and `Observer` are the pluggable seams.

Stakeholder: software developer about to add booking rules. Detail: **detailed** (15 components and interfaces plus the application boundary), because the developer is about to change this area. The previous version is in `v1/`.

## How the concern is answered
- **Components and responsibilities:** every box carries its role. The old merged domain box is split into the rule-bearing parts: `StudyRoom, TimeSlot` (active, open on date, schedule), `Seat, Area` (seat free), `Student` (one booking per date and slot), and `Reservation + states`. `ReservationManager` lists its rule steps (`resolveRoom`, `resolveTimeSlot`, `validateSeatInArea`, `createAndSave`).
- **Interactions:** relations are dashed «use» dependencies from caller to callee. `AssignmentStrategy` and `Observer` are interfaces (realised by `FirstAvailableAssignment` and `NotificationManager`). The notification path now runs through the `Observer` interface. The wizard's room and slot queries (`/api/rooms`, `StudyRoomManager`) are drawn next to the booking path.
- **Affected parts:** blue marks edit points and ripple targets, and the note names them in the model as well. `ReservationRegistry.occupiesSlot` (inside "Registries + JPA persistence") is marked. `StudyRoomManager` is marked because it reuses `Area.getAvailableSeats` for the free-seat counts the UIs show. The note says `ReservationRequestDTO`, `ReservationController`, Swing `ReservationSummary` and `reservation.html` change only if a rule needs new input, and that `MakeReservationTest` needs updating.

`inventory.json` holds elements, relations and evidence. `check_inventory.py`: 0 issues (16 elements including the boundary).

## Changes made after the review
Split the domain box, dropped `NotificationScheduler`, `NotificationServiceAdapter` and MySQL, merged persistence into the registries box, added interfaces and the `Observer` path, switched to dashed dependencies, added the system boundary, and added the availability ripple and test/DTO note.

## Reviewer points not followed
- **`NotificationScheduler` "not safe to call unaffected":** I dropped the scheduler as outside the booking flow. This is a cut, not a rebuttal: a rule about reservation lifetime or state would also touch `manageReservationEnd`, which moves reservations out of ACTIVE/CONFIRMED and so changes what `occupiesSlot` counts. See Omitted.
- **Colour stereotypes:** I kept `<<accent>>` for emphasis (the skill's allowed styling stereotype, hidden in the render) but the note now states the affected parts in text.
- **`NotificationService` interface and the email adapter:** not drawn. `NotificationManager` depends on the `NotificationService` interface, with `NotificationServiceAdapter` injected at startup in `NotificationConfiguration`. This is peripheral to booking rules.

## Omitted on purpose
`NotificationScheduler`, `NotificationServiceAdapter`, MySQL, DTOs, `UserManager`, factories, `RestExceptionHandler`, and the cancel, check-in and monitoring flows. Outside the booking path or external.

## Assumptions
- Persistence (`PersistenceManager`, `JpaUtil`) is merged into the registries box.
- `ReservationManager` attaches `NotificationManager` as an observer (`ReservationManager.notifyReservation`). The view draws it through the `Observer` interface.

## Check result
`puml-check`: renders, 1 crossing, two warnings: tiny text (7.3 px when scaled to 1200 px wide) and one edge label crossed by its own edge. Dropping the «use» prefixes made it worse (three warnings), so I reverted. Ratio 1.72 against the 16:9 target. v1 had two warnings and a tall 0.99 ratio, so this version is wider but denser.
