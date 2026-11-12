# Seat booking: UML package diagram (balanced), revision 1

**Takeaway:** a booking passes from three entry packages through the Library facade into the Reservation manager, which runs the booking flow and relies on the Seat assignment strategy, the Registries and the Reservation and seat model. The rule predicates live in the model and registries, so a new booking rule mostly changes those two packages plus the Reservation manager.

Stakeholder: developer changing the booking rules. Detail level: balanced (given): packages involved in booking, their dependencies and a short note each, no classes. A detailed level would show the individual rule methods and their call order. Names match the component view IS-seat-L2 (`check_consistency.py`: consistent). The earlier version is in `v1/`.

## How the view answers the concern
- **Main components:** the packages in four groups (Entry points, Booking logic, Booking data, Domain and persistence).
- **Responsibilities:** each package carries a note with its responsibility. The Reservation manager note says the booking flow runs in `makeReservation`. The model note lists the rule predicates (`Seat.isAvailable`, `Area.getAvailableSeats`, one booking per slot in `Student`, `StudyRoom.isOpenOnDate`), and the Registries note names `ReservationRegistry.occupiesSlot`.
- **Interactions:** labelled dependency arrows, top to bottom: entry points call the facade, the facade delegates to the managers, the managers use the registries, the model and the strategy, and the registries store data.
- **Change impact:** each note ends with an "Impact:" line giving the reason. Notes replace the colour and custom stereotypes of v1.

## Changes after the review
- Added the Booking DTOs package, used by the screens, the REST API, the facade and the Reservation manager.
- Added the dependencies from the Room availability manager and from the Seat assignment strategy to the model. The Room availability manager note says it shows availability with the same predicates, so it is likely affected.
- Responsibility and impact notes replace colour, hidden stereotypes and the legend.
- Package names are the readable names. The notes now sit inside each package so the tab shows the name.

## Kept from v1 (reviewer point not taken)
The reviewer suggested packages named after the real Java packages, with the single classes as members. I kept the names of the component view IS-seat-L2, because the same code must keep the same name across views. Library facade, Reservation manager and Reservation scheduler are single classes (`LibraryFacade`, `ReservationManager`, `NotificationScheduler`). The inventory `members` records which code each stands for.

## Omitted on purpose
UI helpers, user management and factories, the email gateway, the Librarian, the interfaces of the component view, and the Notification manager's 16 dependencies on the model. The Observer link from model to notifications is shown as the Notification manager's dependency on the registries only; the observer interface is a component-view element.

## Check result
`check_inventory.py --level balanced --graph`: 0 issues (notes only). `check_view.py`: clean. `check_consistency.py`: consistent. `puml-check`: layout warnings remain (edge through the "Domain and persistence" group title, labels on container borders, bundled edges). The diagram has 22 edges and the PNG is tall (2966x3531). I viewed the PNG and it is readable, but I did not reduce the layout warnings further.
