# Use case view: Municipal report management application

**Takeaway:** a Citizen can register, log in, create reports and follow their own reports; a Municipal Operator can review all received reports, advance their status (with a citizen notification), add internal notes and monitor activity trends.

- Stakeholder: software analyst. Detail level: overview, 8 use cases (budget ≤ 8), domain wording, no technology names.
- Files: `view.puml`, `view.png` (`out/` holds the checker/renderer output).

## How the view addresses the concern
| Concern | Where in the view |
|---|---|
| Main types of users | Actors Citizen and Municipal Operator, both specializing the abstract actor User (`Entity/User.java:28`, `Citizen.java:11`, `MunicipalOperator.java:11`). |
| Goals of each | Citizen: create report, review submitted reports. Operator: review received reports, update status, add internal note, monitor trends. Both: register, log in. |
| Relations between functionalities | «include»: update status needs the received-reports review (the update button opens the received-reports screen, `UserDashboardGUI.java:575`). «extend»: internal note is opened from a report's details in that review (`ReceivedReportsGUI.java:790`). Generalization of actors. |

## Inventory (element → evidence)
- Register account → `HomePageGUI.java:49`, `UserRegistrationController.java:23`
- Log in → `HomePageGUI.java:52`, `UserLoginController.java:24`
- Create report → `UserDashboardGUI.java:100`, citizen only (`:321`), `ReportCreationController.java:146`
- Review submitted reports → `UserDashboardGUI.java:101`, `ReportReviewController.java:28`
- Review received reports (filter by category and status) → `UserDashboardGUI.java:102`, `ReceivedReportsGUI.java:411`, `ReportReviewController.java:44`
- Update report status → `UserDashboardGUI.java:103`, `ReportStatusUpdateController.java:27` (operator only)
- Citizen notification (note on Update report status) → `NotificationController.java:22,46`
- Add internal note → `InternalNoteController.java:25` (operator only)
- Monitor activity trends → `UserDashboardGUI.java:104`, `ActivityMonitoringController.java:28` (operator only)

## Omitted on purpose
Log out, report details/history screens (folded into the two review use cases), the three monitoring variants (general, in progress, area summary), and the notification as its own use case (it is automatic).

## Assumptions
- "User" is an abstract actor drawn from the entity hierarchy. Registration and login are available before a role exists, so the actor owning them is the generalization.
- The login and registration screens are reachable without authentication (`HomePageGUI`).

## Check result
Final `puml-check`: 2 warnings (aspect 2.6:1, too wide; one edge from Operator passing through the system boundary title), 1 crossing. The first layout (left to right) had 2 warnings too, but was too tall (1.19:1) and had the same title crossing. Two attempts to remove the title crossing (an edge direction hint and a note move) increased crossings (3 to 4, then 1 to 5), so I reverted to the best version. Image review: all inventory items are drawn, and no labels overlap.
