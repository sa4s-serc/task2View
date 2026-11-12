# Use case view: municipal problem reporting and management

**Takeaway:** Citizens report problems and follow them; municipal operators review, update and annotate those reports and monitor activity.
**Stakeholder:** business analyst. **Detail level:** overview (given), so only user goals are drawn.

## How the concern is answered
- *Main user types*: two actors, Citizen and Municipal operator, the two roles the dashboard code distinguishes (`UserDashboardGUI.java`).
- *Goals per type*: each actor is linked to the goals it starts. Both roles register (the registration form offers Citizen and Municipal Operator), log in, and open report details. The citizen also reports a problem and follows their own reports. The operator also reviews received reports, updates status, adds internal notes and monitors trends.
- *Relations between functions*: «extend» links show two optional steps on viewing report details: reading status notifications (the "View Notifications" button, citizen side) and adding an internal note (operator side). Updating status «include»s viewing report details. A note ties the operator's status update to the citizen's notification, which is the cross-actor relation.

Evidence is in `inventory.json`. `check_inventory.py --level overview --graph .claude/repo-graph.json`: 0 issues (1 note, because use cases and actors have no code members). `check_view.py`: clean. `puml-check`: OK, 0 crossings. `view.png` was rendered from `view.puml`.

## Omitted
Screens, controllers, entities, the database, report categories and filters. A component or class view would show those.

## Assumptions
- Status-change notifications are created automatically when an operator updates a report (NotificationController.java:46); the note states this rather than drawing a link between use cases.

## Revision 1 (reviewer critique)
Previous version is in `v1/`. Changes: operator now registers; both actors are linked to "View report details"; notifications changed from «include» of "Follow my reports" to «extend» of "View report details"; the «extend» from "Update report status" to "Review received reports" was removed; a note was added for the status-update-to-notification link. All reviewer points were confirmed in the code, so none were rejected. Checks after the revision: puml-check OK (0 crossings, info only: 16 edges is busy), check_inventory.py 0 issues, check_view.py clean.
