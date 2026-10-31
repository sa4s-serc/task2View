# UML use case diagram: municipal problem reporting application

**Takeaway:** citizens report problems and follow them, including notifications; municipal operators review received reports, update their status from that list, and monitor activity; both register and log in.
**Stakeholder:** software analyst. **Detail level:** overview (as given): 2 actors, 6 use cases inside the application boundary, domain wording.
Files: `view.puml`, `view.png`, `inventory.json` (evidence for every element and relation). The previous version is in `v1/`.

## Concern
- **Main user types:** Citizen and Municipal operator, as separated by the role guards in `UserDashboardGUI` (e.g. lines 450, 479, 509, 539, 569).
- **Goals per user:** Citizen: create a report, view own reports, history and notifications. Operator: review received reports (details, internal notes), update status, monitor activity trends. Both: register and log in.
- **How functionalities relate:**
  - «extend»: "Update report status" extends "Review received reports". A status update is always started from the received-reports list (`UserDashboardGUI.java:569-575`, `ReceivedReportsGUI.java:1105-1122`).
  - Notification link: a note ties the status update to the citizen's "View own reports, history and notifications" (`NotificationController.java:22-46`, `SubmittedReportsGUI.java:239-260`).
  - Login precondition: a note says every use case except "Register and log in" needs a logged-in user. No include arrows were drawn, to keep the overview readable.

## Omitted on purpose
Separate use cases for report details/history and internal notes (merged into the two list use cases), a generalised "User" actor, notification sending as its own use case, entities, persistence, GUI windows.

## Assumptions
- Registration and login are offered to both roles on the home page (`HomePageGUI.java:119-128`). Whether registration lets users choose their role was not checked in detail. The reviewer cites a role choice at `UserRegistrationGUI.java:112-113`; I did not verify that.

## Revision after review (v1 -> v2)
Changes: added the system boundary; added the «extend» relation; renamed the citizen use case to include notifications; removed "(citizen is notified)" from the status update name and put it in a note; added the login-precondition note. The earlier README said the budget was why relations were missing; that was wrong, relations add no elements, and they are now drawn.
Not changed: no reviewer point was contradicted by the code (I checked `UserDashboardGUI.java:575` and `ReceivedReportsGUI.java:1105-1122`).

## Check result
- `puml-check`: 2 `edge-through-node` warnings remain (the notification note's dashed link passes over the login note). Two alternative layouts gave 3 warnings each, so I kept this one. Rendered and viewed.
- `check_inventory.py --level overview`: 1 issue, "9 elements, budget 8". The 9th element is the system boundary rectangle, which the reviewer asked for. The skill's budget is "≤ 8 use cases", and there are 6, so I kept the boundary. No unbacked items, 8 relations.
