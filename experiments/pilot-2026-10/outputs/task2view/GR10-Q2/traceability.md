# Traceability

## V1-deployment — Deployment

| Element | Files | Symbols |
|---|---|---|
| reports_db | src/main/java/Database/PersistenceService.java, src/main/resources/META-INF/persistence.xml | — |
| Hibernate JPA persistence unit Municipal_Report_Management_System | src/main/resources/META-INF/persistence.xml | — |
| municipal-report-management.jar | pom.xml | — |
| Municipal_Report_Management_System | src/main/resources/META-INF/persistence.xml | — |
| Hibernate | src/main/resources/META-INF/persistence.xml | — |
| hbm2ddl update schema generation | src/main/resources/META-INF/persistence.xml | — |
| Municipal_Report_Management_System | src/main/java/Database/JpaUtil.java | — |

## V2-cnc-generic — Component-and-Connector

| Element | Files | Symbols |
|---|---|---|
| Persistence | src/main/java/Database/JpaUtil.java, src/main/java/Database/PersistenceService.java | Database.PersistenceService, Database.JpaUtil |
| Application | src/main/java/Control/ActivityMonitoringController.java, src/main/java/Control/InternalNoteController.java, src/main/java/Control/ReportCreationController.java, src/main/java/Control/ReportDetailsController.java, src/main/java/Control/ReportReviewController.java, src/main/java/Control/ReportStatusUpdateController.java, src/main/java/Control/SystemServicesController.java, src/main/java/Control/UserRegistrationController.java | Control.SystemServicesController, Control.UserRegistrationController, Control.ReportCreationController, Control.ReportReviewController, Control.ReportDetailsController, Control.ReportStatusUpdateController |
| Domain | src/main/java/Entity/InternalNote.java, src/main/java/Entity/Notification.java, src/main/java/Entity/Report.java, src/main/java/Entity/ReportService.java, src/main/java/Entity/StatusUpdate.java, src/main/java/Entity/User.java | Entity.ReportService, Entity.Report, Entity.InternalNote, Entity.Notification, Entity.StatusUpdate, Entity.User |
| Presentation | src/main/java/Boundary/HomePageGUI.java | Boundary.HomePageGUI |
