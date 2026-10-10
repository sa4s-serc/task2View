# Traceability

## V1-decomposition — Decomposition

| Element | Files | Symbols |
|---|---|---|
| PersistenceService | src/main/java/Database/PersistenceService.java | Database.PersistenceService |
| UserLoginGUI | src/main/java/Boundary/UserLoginGUI.java | Boundary.UserLoginGUI |
| UserService | src/main/java/Entity/UserService.java | Entity.UserService |
| SystemServicesController | src/main/java/Control/SystemServicesController.java | Control.SystemServicesController |
| UserRegistrationController | src/main/java/Control/UserRegistrationController.java | Control.UserRegistrationController |
| JpaUtil | src/main/java/Database/JpaUtil.java | Database.JpaUtil |
| ReportCreationController | src/main/java/Control/ReportCreationController.java | Control.ReportCreationController |
| UserLoginController | src/main/java/Control/UserLoginController.java | Control.UserLoginController |
| UserDashboardGUI | src/main/java/Boundary/UserDashboardGUI.java | Boundary.UserDashboardGUI |
| ReportService | src/main/java/Entity/ReportService.java | Entity.ReportService |
| ReportCreationGUI | src/main/java/Boundary/ReportCreationGUI.java | Boundary.ReportCreationGUI |
| ActivityMonitoringGUI | src/main/java/Boundary/ActivityMonitoringGUI.java | Boundary.ActivityMonitoringGUI |
| ReceivedReportsGUI | src/main/java/Boundary/ReceivedReportsGUI.java | Boundary.ReceivedReportsGUI |
| ReportCategory | src/main/java/Entity/ReportCategory.java | Entity.ReportCategory |

## V2-cnc-generic — Component-and-Connector

| Element | Files | Symbols |
|---|---|---|
| Domain | src/main/java/Entity/ReportCategory.java, src/main/java/Entity/ReportService.java, src/main/java/Entity/UserService.java | Entity.ReportService, Entity.UserService, Entity.ReportCategory |
| Persistence | src/main/java/Database/JpaUtil.java, src/main/java/Database/PersistenceService.java | Database.PersistenceService, Database.JpaUtil |
| Application | src/main/java/Control/ReportCreationController.java, src/main/java/Control/SystemServicesController.java, src/main/java/Control/UserLoginController.java, src/main/java/Control/UserRegistrationController.java | Control.SystemServicesController, Control.UserLoginController, Control.UserRegistrationController, Control.ReportCreationController |
| Presentation | src/main/java/Boundary/ActivityMonitoringGUI.java, src/main/java/Boundary/ReceivedReportsGUI.java, src/main/java/Boundary/ReportCreationGUI.java, src/main/java/Boundary/UserDashboardGUI.java, src/main/java/Boundary/UserLoginGUI.java | Boundary.UserLoginGUI, Boundary.UserDashboardGUI, Boundary.ReportCreationGUI, Boundary.ActivityMonitoringGUI, Boundary.ReceivedReportsGUI |
