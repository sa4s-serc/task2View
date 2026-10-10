# Task2View — GR10-Q4 (municipal-report-management)

**Goal:** I am a business analyst. I need to understand at a high level how a system for reporting and managing problems in a municipal area is expected to work. I know that the application should allow people to report issues in the territory and support the municipality in managing them, but I do not yet know the specific user roles or the functionalities available to each of them. I need to identify the main types of users that interact with the system, the main goals they can achieve through it, and how the different functionalities are related to each other.

- **Role:** business analyst (`business-analyst`) — **Target:** whole system — **Detail level:** overview
- **Primary need:** actors-goals — **Secondary needs:** none
- **Produced by:** Claude Sonnet 5.5 (single agent + task2view skill)

## Views
| View | Viewpoint | Decision | Verdict | Elements | Notation |
|---|---|---|---|---|---|
| V1-use-case | Use Case (8.3.1) | confirm | pass_with_limitations | 5 (+ system boundary) | plantuml |

## Rationale
The goal asks who uses the system and what they can achieve, with how the functionalities relate. That is the actors-goals need, framed only by the Use Case viewpoint, so one view suffices.

## What the system does (from the evidence model)
Two user types, set at registration (UserRegistrationGUI offers "Citizen" and "Municipal Operator") and applied at login by role:
- **Citizen** — createReport, reviewReportsSubmitted, displayReportDetails (own reports only), registerUser, login.
- **MunicipalOperator** — reviewReportsReceived, displayReportDetails (any report), updateReportStatus, addInternalNote, monitorActivityTrends, registerUser, login.

Relations between functionalities: updateReportStatus and addInternalNote are launched from the received-reports screen (`extend` reviewReportsReceived); reviewing reports (submitted or received) includes displayReportDetails; sendNotificationToCitizen extends updateReportStatus and only happens for notifiable statuses. A report moves Submitted -> Assigned -> InProgress -> Resolved, one step per status update; a Resolved report cannot change.

## Limitations and declared gaps
- Overview cap of 5 elements: the diagram draws createReport, reviewReportsReceived, updateReportStatus. Not drawn (overflow): reviewReportsSubmitted, displayReportDetails, addInternalNote, monitorActivityTrends, registerUser, verifyCredentialsLogin, sendNotificationToCitizen. All are in `evidence_model.json`.
- Use-case names are the facade/controller method names, because the code has no other names for them.
- Actor-use case associations and extend/include relations are `inferred` (role checks, dashboard and screen navigation, not direct calls between the named elements); confidence capped at 0.7.
- Task-fit validation is `not-run` (a different model must judge).
- usage.json not written: this tool reports no token or cost totals.
- No declared evidence gaps; no uncovered needs.

## Evidence counts
Claims verified: 32; rejected: 0; elements in model: 20; relations: 19; scenarios: 1.
