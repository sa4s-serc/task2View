# UML sequence diagram: user registration (IS-reg-L1-2)

**Takeaway:** a registration submitted in the Swing form travels form → library facade → user manager, which checks the email and identifier against the user registry (persistence manager, MySQL), builds the account through the user factories, and saves it; errors return to the form.

Stakeholder: integration tester. Detail level: balanced (the components involved and the calls between them).

## Concern: how do the components interact during registration?
- Call order and the arguments passed between components: main flow in `view.puml`.
- Duplicate-check queries before saving, and the save itself, both via registry → persistence manager → database.
- One `alt` shows the error path (invalid input, email or identifier already in use: exception back to the form, shown as a message) versus the success path (account created and saved, login opened).
- The REST endpoint `POST /api/auth/register` is an alternative entry to the same facade call; it is given in a note, not as a lifeline, to keep the sequence within size limits.
- A save failure (the registry returns false, so the manager throws) is not drawn separately.

Names match view IS-reg-L1 (component); `check_consistency.py` reports consistent. Details: `inventory.json`; `check_inventory.py` reports 0 issues (1 note: user and database have no members).

## Omitted
Authentication REST API lifeline, DTOs, Swing helpers, login screen, JpaUtil; the repeated field validations are collapsed into one self-call.

## Assumptions
The Swing form is the main flow because it is the primary client; the REST path is identical after the facade.

## Check result
`puml-check`: no warnings remaining (only an advisory note on lifeline-spanning messages); `check_view.py` clean.
