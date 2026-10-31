# Use case view - Municipal Report Management System

**Viewpoint / model kind:** use case, UML use case diagram (`view.puml`). **Aspect:** functional.

## What it shows
The functionalities the desktop application offers, grouped by the actors that use them, and the relations among the functionalities. Derived from `Boundary/UserDashboardGUI` (role-dependent buttons), `Boundary/HomePageGUI`, the `Control/*Controller` classes (role checks via `UserService`) and `Boundary/ReceivedReportsGUI` / `SubmittedReportsGUI`.

## How it addresses the concern
- **Main types of users:** *Visitor* (not logged in; home page offers Register and Log in), and its two specializations *Citizen* and *Municipal Operator*. The dashboard shows different functions per role, and controllers reject the wrong role (e.g. "Only citizens can create reports", "Only an operator can update the status").
- **Goals of each user:**
  - Visitor: register, log in.
  - Citizen: create a report, view own submitted reports (with details/history and notifications), log out.
  - Operator: view received reports (filter them, add internal notes), update report status (Submitted -> Assigned -> In Progress -> Resolved), monitor activity trends, log out.
- **Relations between functionalities:** `include` for behaviour always performed (viewing either report list shows report details/history; a status update always triggers the notification step, which sends a citizen notification only when the new status is notifiable); `extend` for optional behaviour (filtering and adding internal notes from the received-reports list; reading notifications from a report's details).

## Notes
- Login/registration are shown for the Visitor; Citizen and Operator inherit them. Log out is available to both roles.
- Status update and internal notes are reached through the received-reports list in the code, hence the relations modelled on that use case.
