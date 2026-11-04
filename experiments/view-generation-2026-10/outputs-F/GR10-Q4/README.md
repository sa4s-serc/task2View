# UML use case diagram: Municipal problem reporting system

**Takeaway:** citizens report problems and follow them; municipal operators review received reports, update status, add internal notes and monitor activity trends. A status update reaches the citizen as a notification.

Stakeholder: software analyst. Detail level: overview (as given). Files: `view.puml`, `view.png`, `inventory.json`. The first version is kept in `v1/`.

## How the view addresses the concern
- **Main types of users:** *Citizen* and *Municipal operator*, the two roles the code distinguishes (`Entity/UserService.java:260-266`, `Boundary/UserDashboardGUI.java:299-348`).
- **Goals of each:** Citizen: report a problem, track reports and notifications. Operator: review received reports, update report status, add internal note, monitor activity trends.
- **Relations between functions:**
  - «extend»: "Add internal note" extends "Review received reports", since it is an optional step in the report-details dialog (`ReceivedReportsGUI.java:790`).
  - A note links "Update report status" and "Track my reports and notifications": a status update creates a notification (`ReportStatusUpdateController.java:66`) that the citizen reads (`SubmittedReportsGUI.java:743`).

## Revision after review (v1 -> v2)
- Split "Update status or add internal note" into two use cases.
- Operator is now associated with "Update report status". It is no longer an «extend» of reviewing, because the dashboard starts it directly (`UserDashboardGUI.java:566-575`).
- Added the notification note.
- **Not applied: system boundary box.** The checker counts it toward the overview budget of 8 elements, and the title names the system. UML allows leaving it out.
- **Consequence of the budget:** "Register and log in" (shared by both roles, in v1) had to go. It is a precondition shared by both roles rather than a role-specific goal. A balanced-level view would restore it and the boundary.

## Omitted on purpose
Register / log in, log out and navigation; the notification as its own use case; the system boundary; filters, lifecycle states, database and technology.

## Assumptions
Operators can also register (`UserRegistrationGUI.java:186`); this is not drawn now. Login precedes every goal shown.

## Check result
`puml-check`: OK, no issues. `check_inventory.py --level overview --graph .claude/repo-graph.json`: 0 issues (a note only that actors and use cases carry no `members`).
