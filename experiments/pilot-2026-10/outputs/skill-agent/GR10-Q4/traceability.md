# Traceability

## V1-use-case

| Element | Files | Symbols |
|---|---|---|
| municipal-report-management | pom.xml |  |
| Citizen | src/main/java/Entity/Citizen.java | Entity.Citizen |
| MunicipalOperator | src/main/java/Entity/MunicipalOperator.java | Entity.MunicipalOperator |
| createReport | src/main/java/Control/ReportCreationController.java<br>src/main/java/Control/SystemServicesController.java | Control.SystemServicesController.createReport |
| reviewReportsReceived | src/main/java/Control/ReportReviewController.java<br>src/main/java/Control/SystemServicesController.java | Control.SystemServicesController.reviewReportsReceived |
| updateReportStatus | src/main/java/Control/ReportStatusUpdateController.java<br>src/main/java/Control/SystemServicesController.java | Control.SystemServicesController.updateReportStatus |

Overflow use cases (not drawn): reviewReportsSubmitted, displayReportDetails, addInternalNote, monitorActivityTrends, registerUser, verifyCredentialsLogin, sendNotificationToCitizen
