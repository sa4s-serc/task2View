# Sequence view: user registration

**Takeaway:** a registration request passes Controller -> Facade -> UserManager, which alone validates role-specific data and checks uniqueness through UserRegistry/PersistenceManager, then builds the user with a role factory and saves it; invalid or duplicate data ends as IllegalArgumentException (HTTP 400), a failed save as RuntimeException.
Stakeholder: integration tester. Detail: balanced/detailed for one feature (7 lifelines, 22 messages incl. replies); engineering wording.

## Concern -> view
- Handles the request: AuthenticationController (msgs 1-2, 12, 19, 22); Swing form bypasses it (note).
- Validates personal data and role: UserManager self-calls 4-6.
- Role-specific data (student ID / librarian code): alt Student/Librarian (5-6), uniqueness lookup (9-10), UserFactory (13-14).
- Validity and uniqueness: UserManager + UserRegistry + PersistenceManager (7-10).
- Persistence: UserRegistry -> PersistenceManager.save (15-16, 17/20).
- Invalid/existing data: alt at 11-12; save failure alt at 17-19.
- Integration points to test: Controller-Facade-UserManager, UserManager-UserRegistry-PersistenceManager (lookups and save), UserManager-UserFactory, exception-to-HTTP mapping.

## Inventory (file:line, under JavaProject/src/main/java/it/unina/reservations)
- AuthenticationController: boundary/SpringBoot/AuthenticationController.java:22-31
- LibraryFacade: controller/LibraryFacade.java:37-40
- UserManager: controller/UserManager.java:65-97 (validation :52-58, :173-198, :199-221)
- UserFactory/StudentFactory/LibrarianFactory: controller/factory/StudentFactory.java:8-18
- UserRegistry: entity/UserRegistry.java:26-67
- PersistenceManager.save: database/PersistenceManager.java:19-37
- RestExceptionHandler (note only): boundary/SpringBoot/RestExceptionHandler.java:19-22
- Swing entry (note only): boundary/Swing/Registration.java:116-141

## Omitted
DTO mapping, JPA/JpaUtil, MySQL, web page, login flow, individual validation rules (collapsed into self-calls).

## Assumptions
- Format-validation exceptions (steps 4-6) are thrown before the lookups; the single alt at 11-12 groups all 400 outcomes for brevity.
- The unmapped RuntimeException is shown as "not mapped to 400" per RestExceptionHandler handling only IllegalArgument/IllegalState/Security; the resulting HTTP status (framework default) was not verified.

## Check
puml-check: 2 warns left (aspect: tall sequence; one alt-label crossing a lifeline), no overlaps. Image reviewed: readable, no changes needed.
