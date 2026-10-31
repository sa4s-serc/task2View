# Component view: seat booking and its dependencies

**Takeaway:** a booking request flows from three entry points through `Library Facade` into `Reservation Manager`, which holds the booking rules (validation, seat selection) and delegates to the reservation domain, the registries and notifications. A new rule changes `Reservation Manager` first. It may also change the domain rules, `Seat Assignment Strategy` and the entry points' error handling.

Stakeholder: software developer about to add booking rules. Detail level: **detailed** for the booking area only (13 components, within the ≤20 budget). Wording uses technology names, since the reader is an engineer.

## How the concern is answered
- **Components and responsibilities**: each box is named for its role. Responsibilities are in the inventory below.
- **Interaction**: the labelled arrows show who calls whom. Flow runs top to bottom: entry points → facade → managers → domain/registries → persistence → MySQL.
- **Affected parts**: blue marks the places for new rules. Light red marks domain classes that already hold booking constraints. Everything downstream of `Reservation Manager` (registries, persistence) is affected only if a rule needs new data. Notification Manager is affected only if a rule adds a message.

## Inventory (element → evidence, `JavaProject/src/main/java/it/unina/reservations/`)
| Element | Responsibility | Evidence |
|---|---|---|
| Swing Booking Wizard | Desktop UI; submits the reservation | `boundary/Swing/ReservationSummary.java:100`, `DateAndRoomSelection.java:214`, `TimeSlotSelection.java:87` |
| REST Controllers | `POST /api/reservations/create`, cancel, check-in; room/slot/detail queries. `RestExceptionHandler` turns rule violations into HTTP 400 | `boundary/SpringBoot/ReservationController.java:21-49`, `StudyRoomController.java:44-65`, `RestExceptionHandler.java:19` |
| Notification Scheduler | Every minute runs end-of-reservation handling and reminders | `boundary/NotificationScheduler.java:15-29` |
| Library Facade | Single entry that delegates to the managers | `controller/LibraryFacade.java:117,81-102` |
| Reservation Manager | Booking rules: room/area/slot/seat checks, one reservation per student per slot, seat selection, save, notify; also cancel, check-in, expiry | `controller/ReservationManager.java:65-197,357-401` |
| Seat Assignment Strategy | Picks the seat when none is chosen (first available) | `controller/strategy/AssignmentStrategy.java:10`, `FirstAvailableAssignment.java:15`; used at `ReservationManager.java:400` |
| Study Room Manager | Room, slot and seat availability queries for the booking screens | `controller/StudyRoomManager.java:196-289` |
| Notification Manager | Observer of `Reservation`; sends emails | `controller/NotificationManager.java:14-47`, `ReservationManager.java:120` |
| Reservation Domain | `Reservation`, its state classes, `Seat`, `Area` and `Student`. Holds the 6-hour cancellation window, the 10-minute check-in tolerance and seat/student occupancy checks | `entity/Reservation.java:19,156-164`, `Seat.java:44`, `Area.java:49`, `Student.java:42` |
| Registries | Reservation, StudyRoom and User lookup and save | `entity/ReservationRegistry.java:33-123`, `ReservationManager.java:28-30` |
| Persistence Manager | JPA/Hibernate access | `database/PersistenceManager.java`, `ReservationRegistry.java:20` |
| MySQL database | Stores the data | `resources/META-INF/persistence.xml:21` |
| Email Adapter | Implements `NotificationService`; sends through `ExternalEmailGateway` | `boundary/NotificationServiceAdapter.java:12-20`, `NotificationConfiguration.java:17` |

## Omitted on purpose
DTOs, the user and room management paths (`UserManager`, factories, `StudyRoomManager` create/delete), the Swing screens other than the booking ones, the reminder path from facade to Notification Manager, and the reservation state classes as separate boxes. This keeps the view on the booking path.

## Assumptions / unconfirmed
- The static web pages in `resources/static` were not shown to call the reservation API (no `/api/` match), so no web client is drawn.
- `SeatSelection.java` was not checked for how it obtains seat data, so its edge is not drawn.
- `NotificationScheduler` is shown calling the facade for the end-of-slot job only; the reminder path is omitted.
- The state classes are inside Reservation Domain.

## Check result
Final `puml-check`: 3 warnings, no text overlaps, 13 nodes, 15 edges. They are `aspect` (the diagram is tall, 0.80 ratio, because it is layered), and two edges that pass through package areas (`facade→roommgr`, `roommgr→dom`) plus bundled edges at Study Room Manager. The image review found a visible `«accent»`-style stereotype label, which is not a UML standard stereotype; I replaced it with inline colours and the legend. The first render was too wide and was switched to top-to-bottom. The facade→Notification Manager edge was dropped because it was off the booking path.
