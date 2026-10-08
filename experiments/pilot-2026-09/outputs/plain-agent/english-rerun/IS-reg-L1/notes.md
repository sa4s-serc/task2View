# IS-reg-L1 — User registration (integration-tester view)

**Goal:** Understand which system components take part in user registration and how they interact.

**Entry points (English source):**
- Swing: `Registration` → `LibraryFacade.register`
- Web: `registration.html` → `POST /api/auth/register` → `AuthenticationController` → `LibraryFacade.register`

**Core path:** `LibraryFacade` → `UserManager` (validate + uniqueness) → `StudentFactory` / `LibrarianFactory` → `UserRegistry.registerUser` → `PersistenceManager.save` (JPA via `JpaUtil`) → `UserDTO` returned.

**Entities:** `User` (abstract), `Student`, `Librarian`. API errors handled by `RestExceptionHandler`.
