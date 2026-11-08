# Use case view: Municipal report management system

**Takeaway:** citizens report problems and follow them; municipal operators review received reports, update their status (which notifies the citizen), annotate them and monitor activity trends.

Stakeholder: software analyst. Detail level: overview (given). Files: `view.puml`, `view.png`, `inventory.json`.

## How the view addresses the concern
- **Main types of users:** actors *Citizen* and *Municipal operator*, both specializing *User*. The dashboard shows different functions per role (`Boundary/UserDashboardGUI.java:322-346`) and the controllers refuse the other role.
- **Goals of each user:** Citizen: submit a problem report, review own submitted reports. Operator: review received reports, update report status, add internal note, monitor activity trends. Any user: register an account, log in.
- **How functionalities relate:** `«include»` from both review use cases to *View report details and history*, and from *Update report status* to *Notify citizen of status change*.

## Omitted on purpose
Log out, window navigation, persistence/entities, report categories and fields (below overview level). `.claude/repo-graph.json` is empty, so graph-backed dependency checks had nothing to compare against.

## Assumptions
- *Add internal note* is reached from the received-reports list; the include/extend link to it was left undrawn.
- The code stores a notification for the citizen, but I found no screen where citizens read it; the use case is drawn as the system-side effect, with no actor association (unconfirmed).

## Check result
- puml-check: 1 advisory warning (aspect ratio 1.28 vs 1.78); no overlaps or edge-through-text.
- check_inventory.py (--level overview, with graph): 0 issues, 1 note (use case elements have no code members, so they are not graph-checked).
