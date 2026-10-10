# Traceability

## V1-data-model

| Element | Files | Symbols |
|---|---|---|
| User | src/main/java/Entity/User.java | Entity.User |
| Citizen | src/main/java/Entity/Citizen.java | Entity.Citizen |
| MunicipalOperator | src/main/java/Entity/MunicipalOperator.java | Entity.MunicipalOperator |
| Credentials | src/main/java/Entity/Credentials.java | Entity.Credentials |
| Report | src/main/java/Entity/Report.java | Entity.Report |
| Location | src/main/java/Entity/Location.java | Entity.Location |
| ReportCategory | src/main/java/Entity/ReportCategory.java | Entity.ReportCategory |
| StatusUpdate | src/main/java/Entity/StatusUpdate.java<br>src/main/java/Entity/Report.java | Entity.StatusUpdate |
| InternalNote | src/main/java/Entity/InternalNote.java | Entity.InternalNote |
| Notification | src/main/java/Entity/Notification.java<br>src/main/java/Entity/ReportService.java | Entity.Notification |

## V2-uses

| Element | Files | Symbols |
|---|---|---|
| JpaUtil | src/main/java/Database/JpaUtil.java | Database.JpaUtil |
| PersistenceService | src/main/java/Database/PersistenceService.java | Database.PersistenceService |
| UserService | src/main/java/Entity/UserService.java | Entity.UserService |
| ReportService | src/main/java/Entity/ReportService.java | Entity.ReportService |
| UserRegistrationController | src/main/java/Control/UserRegistrationController.java | Control.UserRegistrationController |
| UserLoginController | src/main/java/Control/UserLoginController.java | Control.UserLoginController |
| ReportCreationController | src/main/java/Control/ReportCreationController.java | Control.ReportCreationController |
| ReportReviewController | src/main/java/Control/ReportReviewController.java | Control.ReportReviewController |
| ReportDetailsController | src/main/java/Control/ReportDetailsController.java | Control.ReportDetailsController |
| ReportStatusUpdateController | src/main/java/Control/ReportStatusUpdateController.java | Control.ReportStatusUpdateController |
| NotificationController | src/main/java/Control/NotificationController.java | Control.NotificationController |
| InternalNoteController | src/main/java/Control/InternalNoteController.java | Control.InternalNoteController |
| ActivityMonitoringController | src/main/java/Control/ActivityMonitoringController.java | Control.ActivityMonitoringController |
