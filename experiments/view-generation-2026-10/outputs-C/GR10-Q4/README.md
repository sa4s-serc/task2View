# Use case view: Municipal Issue Reporting System

**Takeaway:** the system lets any user register and log in, citizens report and follow municipal problems, and municipal operators review, process and monitor them.
**Stakeholder:** software analyst. **Detail level:** overview (whole system, domain wording, no technology names).
Files: `view.puml` (source), `view.png` (render).

## How the view answers the concern
- **Main types of users:** actors `Citizen` and `Municipal Operator`, both specializing the abstract `User` (Entity `User`, `Citizen`, `MunicipalOperator`).
- **Goals of each:** Citizen: Create report, View submitted reports. Operator: View received reports, Update report status, Add internal note, Monitor activity trends. Both (through `User`): Register account, Log in.
- **How functionalities relate:** «extend» from View report details to the two report lists (opened optionally from a selected row); «include» from Update report status and Add internal note to View received reports (the operator picks a report in that list first), and from Update report status to View report details (the status screen loads the details).

## Inventory (element -> evidence)
| Element | Evidence |
|---|---|
| User / Citizen / Municipal Operator | `Entity/User.java:28`, `Citizen.java:11`, `MunicipalOperator.java:11` |
| Register account (role chosen in a combo box) | `Boundary/UserRegistrationGUI.java:214`, `:32`; `Control/UserRegistrationController.java:55-64`; `Control/SystemServicesController.java:registerUser` |
| Log in | `Boundary/HomePageGUI.java:110`, `Boundary/UserLoginGUI.java`, `Control/UserLoginController.java:49` |
| Create report (citizen only) | `Boundary/UserDashboardGUI.java:447`, `Control/ReportCreationController.java:155` |
| View submitted reports (citizen only) | `UserDashboardGUI.java:476`, `Control/ReportReviewController.java:34` |
| View received reports (operator only, with filters) | `UserDashboardGUI.java:506`, `Control/ReportReviewController.java:53`, `Boundary/ReceivedReportsGUI.java:117,176` |
| View report details | `ReceivedReportsGUI.java:254`, `SubmittedReportsGUI.java:164`, `ReportStatusUpdateGUI.java:450`, `Control/ReportDetailsController.java:42-49` |
| Update report status (operator only) | `UserDashboardGUI.java:566` (opens `ReceivedReportsGUI(..., true)` :575), `Control/ReportStatusUpdateController.java:40` |
| Add internal note (operator only) | `ReceivedReportsGUI.java:790`, `Control/InternalNoteController.java:56` |
| Monitor activity trends (operator only) | `UserDashboardGUI.java:536`, `Control/ActivityMonitoringController.java:38` |

## Omitted on purpose
Log out and Back to dashboard (navigation); filter/clear-filter and image attachment (parts of other use cases); the citizen notification sent when a status changes (`Control/ReportStatusUpdateController.java:104` -> `NotificationController`) is an internal effect of Update report status, not a separate user goal. The view has 9 use cases, one over the budget of 8, because two actor groups share the system; dropping one would lose a goal.

## Assumptions
- The generalization from `User` to the two roles is drawn from the entity classes; the login and registration screens are reachable without a role.
- «include»/«extend» are inferred from the screen navigation, not from an explicit feature model.

## Check result
Final `puml-check`: 1 warning (a Citizen edge passes through the system boundary title). An alternative layout removed it but added 5 edge crossings, so the first version was kept. The image review found no overlapping labels.
