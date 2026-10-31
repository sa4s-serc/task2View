# Why this view looks like this
- **Level rule:** perspective "whole system, high level" → *overview* (SKILL.md §1.2); budget ≤ 7 components, used 5.
- **Merged:** each area's controller → repository → entity chain is one component ("Merge a controller/service/repository chain", §3), so 3 controllers + 3 repositories become *Owners & Pets* and *Veterinarians*.
- **Left out:** the `system` package (welcome page, crash demo, i18n, cache config) and `model` superclasses are framework glue or code-level (§3 Omit); JCache, Thymeleaf and Spring Boot appear only as technology labels.
- **Database:** shown as a component with its three supported engines in the label, not as a deployment node (one abstraction level per view, §3); where it runs is in `deployment-balanced`.
- **Wording:** engineering audience → protocol labels (HTTP, JPA / JDBC) on every edge (§4).
- **Contrast:** `component-detailed` opens *Owners & Pets* for one change; same names are kept so the two views line up.
- **Checks:** puml-check OK (0 issues); check_inventory 0 issues.
