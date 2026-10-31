# Why this view looks like this
- **Level rule:** perspective "a change the stakeholder is about to make" → *detailed for that area only* (SKILL.md §1.2); budget ≤ 20, used 8.
- **Split the chain:** the concern *is* the controller → aggregate → repository chain, so it is not merged (§3 "unless the concern is about that chain"). The overview's *Owners & Pets* box is the container here, same name.
- **Area only:** OwnerController, PetController, pet types and the Veterinarians component are out; they are not on the visit path. Nothing outside the change is detailed.
- **Entities as one component:** Owner, Pet and Visit appear as the *Owner aggregate*, not as classes (one abstraction level per view, §3); the rule text goes in notes because the developer needs to know where it lives.
- **Finding for the developer:** there is no VisitRepository or service; visits are saved by cascade from `OwnerRepository.save(owner)`.
- **Interface:** the URL is a provided interface (lollipop), standard UML; no invented stereotypes.
- **Checks:** puml-check OK after moving the controller note off the container title; check_inventory 0 issues.
