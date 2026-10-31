# UML use case diagram: municipal problem reporting application

Files: `view.puml` (source), `view.png` (render), `inventory.json` (evidence for every element and relation).

**Takeaway.** Visitors register and log in; citizens report problems and follow their reports; municipal operators review received reports, update their status, annotate them and monitor activity.

**Stakeholder:** software analyst. **Detail level:** overview, because the perspective is what the whole system offers. Wording is domain terms only, with no technology names.

## How the view answers the concern
- **Main types of users.** Three actors: Visitor (not logged in), Citizen and Municipal operator. The code has two persisted roles, Citizen and MunicipalOperator, which the user picks at registration (`UserRegistrationGUI.java:183`). The dashboard shows each role only its own functions (`UserDashboardGUI.java:316-352`). The controllers also check the role. "Visitor" is our name for the unauthenticated home-page user.
- **Goals of each user.** Each actor is linked to the use cases it can start:
  - Visitor: register and log in.
  - Citizen: report a problem; review my submitted reports.
  - Operator: review received reports; update report status and notify the citizen; add an internal note; monitor activity trends.
- **How the functions relate.**
  - Both review use cases «include» "View report details and status history" (`SubmittedReportsGUI.java:164`, `ReceivedReportsGUI.java:254`).
  - "Update report status" and "Add internal note" «extend» "Review received reports", because both are launched from that screen (`ReceivedReportsGUI.java:1122`, `:790`).

## Omitted on purpose
- Logout and dashboard navigation (navigation, not a goal).
- Persistence and entity classes (internal).
- Report categories and statuses (data, not functions).
- The citizen notification is folded into "Update report status and notify citizen". It has no entry point of its own: it is triggered by the status update.

## Assumptions
- Registration and login are merged into one use case to stay within 8 use cases.
- The «extend» relations are inferred from which screen opens which: `ReceivedReportsGUI` constructs `InternalNoteGUI` and `ReportStatusUpdateGUI`.
- Whether an operator can view details of a report from the status-update screen is not drawn, because that screen only calls `displayReportDetails` to show data (`ReportStatusUpdateGUI.java:450`).

## Check results
- `puml-check`: OK, no errors (the last run reports 1 edge crossing, between the Citizen–"Review my submitted reports" line and the system boundary).
- `check_inventory.py`: evidence, elements and relations are all consistent. It reports one issue, the budget: 12 elements against 8. The script counts actors and the system boundary as elements. The view has exactly 8 use cases, which is what the skill's use case budget names. I did not cut further, since fewer than 8 use cases would drop a user goal.
