# Seat booking: UML component diagram (overview)

**Takeaway:** a seat booking enters through the Swing wizard or the REST API, goes through the single Library facade to the Reservation manager (with the Study room manager for room, slot and seat availability), and is stored through the registries and Persistence in MySQL. The Reservation manager also notifies observers.

Stakeholder: software developer about to modify seat booking. Detail level: **overview**, as given. A balanced level would add the interfaces of the booking path, such as the assignment strategy and the reservation state classes.

## Concern
- **Main components involved:** the diagram shows the two entry points (Swing booking wizard, Reservation REST API), Library facade, Reservation manager (includes the seat assignment strategy), Study room manager, Domain model and registries, Persistence, Notification and the MySQL database.
- **How they interact:** the dependencies point from caller to callee through the interfaces (Library use-case API, Reservation operations, Room and seat availability, Registries, Persistence manager). The only plain dependency is "notifies observers" (Reservation manager to Notification). This is a structural view of the control flow; it does not show call order.

Files: `view.puml` and `view.png` (generated from `model.json`), `inventory.json` (elements, relations and evidence).

## Omitted on purpose
DTOs; user management and factories; Notification scheduler and Launcher. Three dependencies are not drawn: Notification to the domain registries (26 code dependencies), and Library facade and Study room manager to Notification (not on the booking path).

## Assumptions
- The Student and Librarian actors are drawn using the Library use-case API. In the code they reach it through the Swing wizard or the REST API, so the actor-to-API arrows are shortened.
- Library facade and Study room manager are each a single class, so the checker notes them as fine-grained components. I kept them because the facade is the single entry point and the Study room manager is the second manager the booking depends on.

## Check result
- `component_model.py build`: 0 errors, 5 notes.
- `puml-check`: 5 warnings, none fixed. Four are interface labels placed close to their node, and one is an edge crossing the "Reservation operations" label. I did not edit the generated source.
- `check_inventory.py --level overview --graph .claude/repo-graph.json`: exit 0, 0 issues, 4 notes (the undrawn dependencies above and the elements without members: database, actors).
