# UML use case diagram: municipal problem reporting application

Files: `view.puml` (source), `view.png` (render), `inventory.json` (evidence for every element and relation). The first version is in `v1/`; the reviewer's critique is in `critique-1.json`.

**Takeaway.** Any user registers and logs in. Citizens report problems and follow their reports and notifications. Municipal operators review received reports, update status, annotate and monitor activity.

**Stakeholder:** software analyst. **Detail level:** overview, because the perspective is what the whole system offers. Wording is domain terms only, with no technology names.

## How the view answers the concern
- **Main types of users.** "User" is the base actor, the person before login. Citizen and Municipal operator specialise it by generalisation. They match the persisted roles (`Entity/User.java:18` with its Citizen and MunicipalOperator subtypes, role chosen at `UserRegistrationGUI.java:183`). The dashboard shows each role only its own functions (`UserDashboardGUI.java:316-352`).
- **Goals of each user.**
  - User (so also Citizen and Operator): register and log in.
  - Citizen: report a problem; review my submitted reports; view notifications on my report.
  - Operator: review received reports; update report status; add an internal note; monitor activity trends.
- **How the functions relate.**
  - "View report details and status history" «extend»s both review use cases. The condition, shown in a note, is that a report is selected (`SubmittedReportsGUI.java:154-168`, `ReceivedReportsGUI.java:244-258`).
  - "View notifications on my report" «extend»s the details use case. It is an option in the details dialog (`SubmittedReportsGUI.java:236-262`), fed by `NotificationController.sendNotificationToCitizen`.
  - "Add internal note" «extend»s "Review received reports" (`ReceivedReportsGUI.java:790`).
  - "Update report status" is a top-level operator goal with its own dashboard entry (`UserDashboardGUI.java:575`), so it has no «extend».

## What changed from v1 and why
Changes made because the reviewer's points held in the code:
- «include» became «extend» for details, since details are shown only on request.
- The Visitor actor became "User" with generalisation, and the explanatory note was removed.
- Added the citizen goal "View notifications on my report".
- Renamed "Update report status and notify citizen" to "Update report status" and dropped its «extend». The notification is a system-side result: `NotificationController.verifyNotifiableStatus` sends it only for notifiable statuses. The citizen sees it through "View notifications".

Reviewer points not applied:
- None rejected. The suggestion to attach the "report selected" condition to the extend relations is done with one shared note, not per-arrow constraints, to keep the diagram readable.

## Omitted on purpose
- Logout and dashboard navigation (navigation, not a goal).
- Persistence and entity classes (internal).
- Viewing the report image and viewing history as separate goals (they are options within the details dialog).

## Assumptions
- "User" as the base actor reads "anyone who may log in". The unauthenticated state is not modelled as a separate actor.
- Operators also see the details dialog (`ReceivedReportsGUI.java:244-258`). They do not get the citizen's notifications option, so that extend is tied to the citizen path only.

## Check results
- `puml-check`: WARN, one `edge-through-text` plus one crossing. The Citizen–"Review my submitted reports" line passes through the system boundary label. One reordering attempt did not reduce it, so I kept the readable layout.
- `check_inventory.py`: no unbacked items and all relations match. It reports one issue, the budget: 13 elements against 8. The script counts the 3 actors and the system boundary as elements. The view now has 9 use cases, one over the skill's 8-use-case budget. The extra one is the citizen's "View notifications", which the reviewer asked for. I merged register and login already, and any further merge would hide a goal. This is a deliberate overrun, not a fix pending.
