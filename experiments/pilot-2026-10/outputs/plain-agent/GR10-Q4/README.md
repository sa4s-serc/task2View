# Architecture views for the Municipal Issue Reporting System (business analyst audience)

Both views are derived from the code (`Boundary/UserDashboardGUI`, `Control/*Controller`, `Entity/*`).

## view-1.puml - Actors, goals and functionalities (use case view)
Shows the two user roles chosen at registration (Citizen, Municipal Operator; plus the not-yet-signed-in visitor), the goals each can achieve, and the relations between functionalities (details are reused by report lists, notes are added from details, status updates trigger notifications). Role separation comes from the dashboard (`configureDashboardCitizen/Operator`) and the role checks in the controllers (`verifyUserCitizen`, `isMunicipalOperator`). It answers: who uses the system, for what, and what depends on what.

## view-2.puml - Report lifecycle across roles (activity view)
Shows how the functionalities chain together over a report's life: citizen creates it (Submitted), operator reviews, optionally annotates, and advances it Submitted -> Assigned -> In Progress -> Resolved; citizens are notified only on Assigned and Resolved (`isStatusNotifiable`); a resolved report is closed. Monitoring is an operator aggregate over all reports. It answers how the features relate in time and which role acts at each step.

Notes: the code advances status one step per update (no operator choice of target status); some validation rules in report creation are hard-coded sample values.
