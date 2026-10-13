# Traceability

## V1-decomposition — Decomposition

| Element | Files | Symbols |
|---|---|---|
| Report management desktop screens | src/main/java/Boundary/ActivityMonitoringGUI.java, src/main/java/Boundary/InternalNoteGUI.java, src/main/java/Boundary/ReceivedReportsGUI.java, src/main/java/Boundary/ReportCreationGUI.java, src/main/java/Boundary/ReportStatusUpdateGUI.java, src/main/java/Boundary/SubmittedReportsGUI.java, src/main/java/Boundary/UserDashboardGUI.java | Boundary.UserDashboardGUI, Boundary.ReportCreationGUI, Boundary.ActivityMonitoringGUI, Boundary.ReceivedReportsGUI, Boundary.ReportStatusUpdateGUI, Boundary.SubmittedReportsGUI |
| Use case controllers | src/main/java/Control/ReportCreationController.java, src/main/java/Control/SystemServicesController.java, src/main/java/Control/UserRegistrationController.java | Control.SystemServicesController, Control.ReportCreationController, Control.UserRegistrationController |
| Report and user services | src/main/java/Entity/ReportService.java, src/main/java/Entity/UserService.java | Entity.ReportService, Entity.UserService |
| Municipal report entities | src/main/java/Entity/Assigned.java, src/main/java/Entity/Citizen.java, src/main/java/Entity/Credentials.java, src/main/java/Entity/InProgress.java, src/main/java/Entity/InternalNote.java, src/main/java/Entity/Location.java, src/main/java/Entity/MunicipalOperator.java, src/main/java/Entity/Notification.java, src/main/java/Entity/Report.java, src/main/java/Entity/ReportStatus.java, src/main/java/Entity/Resolved.java, src/main/java/Entity/StatusUpdate.java, src/main/java/Entity/Submitted.java, src/main/java/Entity/User.java | Entity.Report, Entity.Notification, Entity.MunicipalOperator, Entity.StatusUpdate, Entity.InternalNote, Entity.User |
| Report data storage | src/main/java/Database/JpaUtil.java, src/main/java/Database/PersistenceService.java | Database.PersistenceService, Database.JpaUtil |
| MySQL database | src/main/resources/META-INF/persistence.xml | — |

## V2-cnc-generic — Component-and-Connector

| Element | Files | Symbols |
|---|---|---|
| Report management desktop screens | src/main/java/Boundary/ActivityMonitoringGUI.java, src/main/java/Boundary/InternalNoteGUI.java, src/main/java/Boundary/ReceivedReportsGUI.java, src/main/java/Boundary/ReportCreationGUI.java, src/main/java/Boundary/ReportStatusUpdateGUI.java, src/main/java/Boundary/SubmittedReportsGUI.java, src/main/java/Boundary/UserDashboardGUI.java | Boundary.UserDashboardGUI, Boundary.ReportCreationGUI, Boundary.ActivityMonitoringGUI, Boundary.ReceivedReportsGUI, Boundary.ReportStatusUpdateGUI, Boundary.SubmittedReportsGUI |
| Use case controllers | src/main/java/Control/ReportCreationController.java, src/main/java/Control/SystemServicesController.java, src/main/java/Control/UserRegistrationController.java | Control.SystemServicesController, Control.ReportCreationController, Control.UserRegistrationController |
| Report and user services | src/main/java/Entity/ReportService.java, src/main/java/Entity/UserService.java | Entity.ReportService, Entity.UserService |
| Municipal report entities | src/main/java/Entity/Assigned.java, src/main/java/Entity/Citizen.java, src/main/java/Entity/Credentials.java, src/main/java/Entity/InProgress.java, src/main/java/Entity/InternalNote.java, src/main/java/Entity/Location.java, src/main/java/Entity/MunicipalOperator.java, src/main/java/Entity/Notification.java, src/main/java/Entity/Report.java, src/main/java/Entity/ReportStatus.java, src/main/java/Entity/Resolved.java, src/main/java/Entity/StatusUpdate.java, src/main/java/Entity/Submitted.java, src/main/java/Entity/User.java | Entity.Report, Entity.Notification, Entity.MunicipalOperator, Entity.StatusUpdate, Entity.InternalNote, Entity.User |
| Report data storage | src/main/java/Database/JpaUtil.java, src/main/java/Database/PersistenceService.java | Database.PersistenceService, Database.JpaUtil |
| MySQL database | src/main/resources/META-INF/persistence.xml | — |
