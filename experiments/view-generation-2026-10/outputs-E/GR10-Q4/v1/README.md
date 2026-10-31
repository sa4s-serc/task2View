# UML use case diagram: municipal problem reporting application

**Takeaway:** citizens report problems and follow them; municipal operators review, update and monitor them; both register and log in.
**Stakeholder:** software analyst. **Detail level:** overview (as given): 8 elements (2 actors, 6 use cases), domain wording.
Files: `view.puml`, `view.png`, `inventory.json` (evidence for every element and relation).

## Concern
- **Main user types:** Citizen and Municipal operator. The code separates the two roles in `UserDashboardGUI` (e.g. "Only citizens can create reports", "Only municipal operators can ...") and in the controllers.
- **Goals per user:** Citizen: create a report, view own reports and their history. Operator: review received reports (details, internal notes), update status (the citizen is notified), monitor activity trends. Both: register and log in.
- **How functionalities relate:** only partly answered. The view shows which goals share an actor and the shared entry point (register and log in). It does not draw include/extend. In the code, both report lists open the report details/history, and internal notes are added from the details of a received report. A balanced use case view would show this as «include»/«extend» with "View report details and history" and "Add internal note" as separate use cases.

## Omitted on purpose
A generalised "User" actor (both roles link to "Register and log in" directly), separate details/internal-note use cases (merged into the list use cases), notification sending (folded into status update), entities, persistence, GUI windows. `check_inventory.py` counts actors and use cases together against the budget of 8, which forced these cuts.

## Assumptions
- Registration and login are offered to both roles via the home page (`HomePageGUI.java:119-128`). Whether registration lets users choose their role was not checked in detail.

## Check result
`puml-check`: OK, 0 issues (one info line on aspect ratio, fits slot unscaled). `check_inventory.py --level overview`: 0 issues, 8 elements, 7 relations, exit 0. The first version (3 actors, 8 use cases, include/extend) failed the budget and was reduced as described. No independent reviewer was run.
