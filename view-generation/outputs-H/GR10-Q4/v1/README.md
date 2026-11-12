# Use case view: municipal problem reporting and management

**Takeaway:** Citizens report problems and follow them; municipal operators review, update and annotate those reports and monitor activity.
**Stakeholder:** business analyst. **Detail level:** overview (given), so only user goals are drawn.

## How the concern is answered
- *Main user types*: two actors, Citizen and Municipal operator, the two roles the dashboard code distinguishes (`UserDashboardGUI.java`).
- *Goals per type*: each actor is linked to the goals it can reach. Registration, login, reporting and following reports belong to the citizen. Reviewing received reports, updating status, adding internal notes and monitoring trends belong to the operator. Login is shared.
- *Relations between functions*: «include» links show that following reports covers reading status notifications, and that updating status includes viewing report details. «extend» links show adding an internal note as an optional step on report details, and updating status as an optional step from the list of received reports.

Evidence is in `inventory.json`. `check_inventory.py --level overview --graph .claude/repo-graph.json`: 0 issues (1 note, because use cases and actors have no code members). `check_view.py`: clean. `puml-check`: OK, 0 crossings. `view.png` was rendered from `view.puml`.

## Omitted
Screens, controllers, entities, the database, report categories and filters. A component or class view would show those.

## Assumptions
- Registration is drawn for the citizen only; the code's registration form may also allow operators (unconfirmed).
- Status-change notifications are sent automatically to the citizen. This is shown as a citizen goal, not an operator one.
- The «extend» from "Update report status" to "Review received reports" reflects that the dashboard opens the same list in status-update mode.
