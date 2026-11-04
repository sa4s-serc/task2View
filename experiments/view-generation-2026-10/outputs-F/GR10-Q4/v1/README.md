# UML use case diagram: Municipal problem reporting system

**Takeaway:** citizens register, log in, report problems and follow them; municipal operators review received reports, update their status or add internal notes, and monitor activity trends.

Stakeholder: software analyst. Detail level: overview (as given). Files: `view.puml`, `view.png`, `inventory.json` (evidence per element and relation).

## How the view addresses the concern
- **Main types of users:** two actors, *Citizen* and *Municipal operator*. The code distinguishes them by user class (`Entity/UserService.java:260-266`) and by the role-dependent dashboard (`Boundary/UserDashboardGUI.java:299-348`).
- **Goals each can achieve:** the associations show who does what. Both: register and log in. Citizen: report a problem, track reports and notifications. Operator: review received reports, update status or add internal note, monitor activity trends.
- **How functionalities relate:** "Update status or add internal note" is an «extend» of "Review received reports". Both are launched from the received-reports screen (`ReceivedReportsGUI.java:790`, `:1122`).

## Omitted on purpose
Log out and navigation; the automatic status-change notification (shown inside "Track my reports and notifications"); the system boundary box and separate Register / Log in / Add note use cases (merged to stay within the 8-element budget); the database and technology.

## Assumptions
Operators can also register (the registration form offers the role, `UserRegistrationGUI.java:186`). Login is a prerequisite for every other goal; it is not drawn as a relation, to keep the view readable.

## Check result
`puml-check`: OK, no issues. `check_inventory.py --level overview --graph .claude/repo-graph.json`: 0 issues (a note only that use cases and actors carry no `members`).
During the work, the first version had 11 elements, over the budget of 8. I merged use cases and dropped the boundary box.
