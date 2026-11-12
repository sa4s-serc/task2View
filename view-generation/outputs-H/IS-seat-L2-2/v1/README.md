# Seat booking: UML package diagram (balanced)

**Takeaway:** a booking passes from three entry packages through the Library facade into the Reservation manager, which relies on the Seat assignment strategy, the Registries and the Reservation and seat model. A new booking rule most likely changes the blue packages.

Stakeholder: developer changing the booking rules. Detail level: balanced (given), meaning the packages involved in booking and their dependencies, without classes. A detailed level would show the individual rule methods (`Seat.isAvailable`, `Student.hasActiveOrConfirmedReservationForDateAndSlot`, `StudyRoom.isOpenOnDate`).

Names and styling match the component view IS-seat-L2 (`check_consistency.py`: consistent).

## How the view answers the concern
- **Main components:** the packages in three layers: Entry points, Booking logic, Domain and persistence.
- **Responsibilities:** each package's responsibility is in `inventory.json`; the names say the role, and the legend gives the change role.
- **Interactions:** labelled dependency arrows read top to bottom: entry packages call the facade, the facade delegates to the managers, the managers use the registries and the model, and the registries store data via persistence.
- **Change impact:** blue = likely changed (Reservation manager, Seat assignment strategy, model, Registries). Plain = may be affected (facade signatures, Room availability manager, Notification manager, entry packages). Grey = Persistence, unaffected unless the stored data changes.

Evidence and the member code of each package are in `inventory.json`. `check_inventory.py --level balanced --graph`: 0 issues (notes only). `check_view.py`: clean.

## Omitted on purpose
DTOs, user management and factories, the email gateway, UI helper classes, the Librarian (librarian screens do not book seats), and the interfaces of the component view. Undrawn dependencies: the model is used by the room manager, notification manager and strategy (55, 16 and 6 code dependencies). This is deliberate, because entities flow through nearly every package and drawing them would clutter the view.

## Assumptions
The three grouping packages (Entry points, Booking logic, Domain and persistence) are layers I chose. They have no code members, so the graph does not check them.

## Check result
puml-check: 2 layout warnings remain (an edge crossing the group title and a same-rank label), reduced from 6 by lengthening three edges. Rendered to `view.png` and not visually reviewed.
