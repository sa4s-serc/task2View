# Traceability

## V1-data-model — Data Model

| Element | Files | Symbols |
|---|---|---|
| InternalNote | src/main/java/Entity/InternalNote.java | Entity.InternalNote |
| Notification | src/main/java/Entity/Notification.java | Entity.Notification |
| Report | src/main/java/Entity/Report.java | Entity.Report |
| Location | src/main/java/Entity/Location.java | Entity.Location |
| User | src/main/java/Entity/User.java | Entity.User |
| StatusUpdate | src/main/java/Entity/StatusUpdate.java | Entity.StatusUpdate |
| Credentials | src/main/java/Entity/Credentials.java | Entity.Credentials |
| Citizen | src/main/java/Entity/Citizen.java | Entity.Citizen |
| MunicipalOperator | src/main/java/Entity/MunicipalOperator.java | Entity.MunicipalOperator |

## V2-uses — Uses

| Element | Files | Symbols |
|---|---|---|
| Report handling screens | src/main/java/Boundary/InternalNoteGUI.java, src/main/java/Boundary/ReceivedReportsGUI.java, src/main/java/Boundary/ReportCreationGUI.java, src/main/java/Boundary/ReportStatusUpdateGUI.java | Boundary.ReportCreationGUI, Boundary.ReceivedReportsGUI, Boundary.ReportStatusUpdateGUI, Boundary.InternalNoteGUI |
| Report and user services | src/main/java/Entity/ReportService.java, src/main/java/Entity/UserService.java | Entity.ReportService, Entity.UserService |
| Report data model | src/main/java/Entity/Assigned.java, src/main/java/Entity/Citizen.java, src/main/java/Entity/Credentials.java, src/main/java/Entity/InProgress.java, src/main/java/Entity/InternalNote.java, src/main/java/Entity/Location.java, src/main/java/Entity/MunicipalOperator.java, src/main/java/Entity/Notification.java, src/main/java/Entity/Report.java, src/main/java/Entity/ReportStatus.java, src/main/java/Entity/Resolved.java, src/main/java/Entity/StatusUpdate.java, src/main/java/Entity/Submitted.java, src/main/java/Entity/User.java | Entity.Report, Entity.Notification, Entity.MunicipalOperator, Entity.StatusUpdate, Entity.InternalNote, Entity.User |
| Report storage access | src/main/java/Database/JpaUtil.java, src/main/java/Database/PersistenceService.java | Database.PersistenceService, Database.JpaUtil |
| MySQL database | src/main/resources/META-INF/persistence.xml | — |
