# Traceability

## V1-deployment — Deployment

| Element | Files | Symbols |
|---|---|---|
| MySQL Server 127.0.0.1:3306 | src/main/resources/META-INF/persistence.xml | — |
| reports_db | src/main/resources/META-INF/persistence.xml | — |
| Desktop GUI Client | src/main/java/Boundary/HomePageGUI.java | — |
| Hibernate JPA persistence unit Municipal_Report_Management_System | src/main/resources/META-INF/persistence.xml | — |
| municipal-report-management.jar | pom.xml | — |

## V2-uses — Uses

| Element | Files | Symbols |
|---|---|---|
| Report desktop screens | src/main/java/Boundary/ActivityMonitoringGUI.java, src/main/java/Boundary/InternalNoteGUI.java, src/main/java/Boundary/ReceivedReportsGUI.java, src/main/java/Boundary/ReportCreationGUI.java, src/main/java/Boundary/ReportStatusUpdateGUI.java, src/main/java/Boundary/SubmittedReportsGUI.java, src/main/java/Boundary/UserDashboardGUI.java | Boundary.ReportCreationGUI, Boundary.ActivityMonitoringGUI, Boundary.ReceivedReportsGUI, Boundary.ReportStatusUpdateGUI, Boundary.SubmittedReportsGUI, Boundary.InternalNoteGUI |
| Report handling services | src/main/java/Control/ReportCreationController.java, src/main/java/Control/SystemServicesController.java, src/main/java/Entity/ReportService.java, src/main/java/Entity/UserService.java | Entity.ReportService, Control.SystemServicesController, Entity.UserService, Control.ReportCreationController |
| Report domain entities | src/main/java/Entity/Assigned.java, src/main/java/Entity/Citizen.java, src/main/java/Entity/Credentials.java, src/main/java/Entity/InProgress.java, src/main/java/Entity/InternalNote.java, src/main/java/Entity/Location.java, src/main/java/Entity/MunicipalOperator.java, src/main/java/Entity/Notification.java, src/main/java/Entity/Report.java, src/main/java/Entity/ReportStatus.java, src/main/java/Entity/Resolved.java, src/main/java/Entity/StatusUpdate.java, src/main/java/Entity/Submitted.java, src/main/java/Entity/User.java | Entity.Report, Entity.User, Entity.Notification, Entity.MunicipalOperator, Entity.StatusUpdate, Entity.InternalNote |
| Report database access | src/main/java/Database/JpaUtil.java, src/main/java/Database/PersistenceService.java | Database.PersistenceService, Database.JpaUtil |
| MySQL database | src/main/resources/META-INF/persistence.xml | — |
