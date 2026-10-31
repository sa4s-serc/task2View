# Why this view looks like this
- **Level rule:** perspective "whole system" → *overview* (SKILL.md §1.2); budget ≤ 8 elements, used 6 use cases + 1 actor + boundary = 8. "Update owner details" and "Update pet details" were merged to stay in budget (§1.3: split or drop, never shrink).
- **One actor, on purpose:** actors must be real roles from the code (§3). PetClinic has no login, security dependency or role checks, so there is one *Clinic user*. Vets are data, not users, so no *Vet* actor; the name "Clinic user" is ours, the code does not name the role.
- **Goals, not screens:** use cases are user goals (§3); "find owner form", "owner list" and the JSON `/vets` resource are not separate use cases.
- **Wording:** business audience → no URLs, HTTP or framework names (§1.2).
- **Left out:** managing vets (no endpoint exists), language switch, the `/oups` error demo; no «include»/«extend» because the code does not show one.
- **Notation:** plain associations (no arrowheads) between actor and use cases, as in UML 2.5.1.
- **Checks:** puml-check OK; check_inventory 0 issues.
