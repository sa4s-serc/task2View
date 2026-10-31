# User registration – dynamic view (UML sequence diagram)

`view.puml` shows the runtime control flow of user registration (UC1) for a Student or Librarian, derived from the code:
`Registration` (Swing) / `registration.html` + `app.js` → `AuthenticationController` (`POST /api/auth/register`) → `LibraryFacade` → `UserManager` → `StudentFactory`/`LibrarianFactory` → `UserRegistry` → `PersistenceManager` → database. `RestExceptionHandler` maps failures to HTTP responses.

## How it addresses the concern
- **Main components and responsibilities**: one lifeline per component, with stereotypes. Boundary receives the request (UI/REST controller), the facade delegates, `UserManager` validates and orchestrates, the factories build the role-specific user, `UserRegistry` checks existence and registers, `PersistenceManager` handles JPA persistence.
- **Who does what**:
  - *Handles the request*: `AuthenticationController` (web) or the Swing form via `LibraryFacade`.
  - *Validates personal data and role*: `UserManager.validate`, `validateStudent`, `validateLibrarian` (section 1).
  - *Role-specific data*: student ID format (letter + 8 digits) vs. librarian code (alphanumeric); `StudentFactory` / `LibrarianFactory` set `studentNumber` / `internalIdentifierCode`.
  - *Validity and uniqueness*: `UserRegistry` lookups by email and by identifier (section 2).
  - *Persistence*: `UserRegistry.registerUser` → `PersistenceManager.save` (section 3).
- **Invalid or existing data**: `alt` branches show validation failure, duplicate email, duplicate identifier (all `IllegalArgumentException` → HTTP 400 `{"error"}` via `RestExceptionHandler`, or an error dialog in Swing), and persistence failure (`RuntimeException`, which has no dedicated handler, so default HTTP 500).
- **Integration points to cover**: UI/REST ↔ `LibraryFacade`; `UserManager` ↔ `UserRegistry`; `UserManager` ↔ factories; `UserRegistry` ↔ `PersistenceManager` ↔ DB; exception propagation to `RestExceptionHandler`/UI.

Notes: the Swing client blocks blank fields locally before calling the backend. Uniqueness is checked (email first, then identifier) before persisting; DB unique constraints are a second line of defense that surfaces as the persistence failure branch.
